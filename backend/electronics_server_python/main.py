"""Electronics demo MCP server implemented with the Python FastMCP helper.

The server exposes widget-backed tools that render the Electronics UI bundle.
Each handler returns the HTML shell via an MCP resource and echoes structured
content so the ChatGPT client can hydrate the widget. The module also wires the
handlers into an HTTP/SSE stack so you can run the server with uvicorn on port
8000, matching the Node transport behavior.

Version: 1.0.0
MCP Protocol Version: 2024-11-05
"""

from __future__ import annotations

from dotenv import load_dotenv
import duckdb
import json
import os
from copy import deepcopy
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

import mcp.types as types
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

env_paths = [
    Path(__file__).resolve().parent.parent.parent / ".env",
]

env_path = None
for path in env_paths:
    if path.exists():
        env_path = path
        load_dotenv(dotenv_path=env_path)
        break


@dataclass(frozen=True)
class Widget:
    identifier: str
    title: str
    template_uri: str
    invoking: str
    invoked: str
    html: str
    response_text: str


ASSETS_DIR = Path(__file__).resolve().parent.parent.parent / "frontend" / "assets"


@lru_cache(maxsize=None)
def _load_widget_html(component_name: str) -> str:
    html_path = ASSETS_DIR / f"{component_name}.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf8")

    fallback_candidates = sorted(ASSETS_DIR.glob(f"{component_name}-*.html"))
    if fallback_candidates:
        return fallback_candidates[-1].read_text(encoding="utf8")

    raise FileNotFoundError(
        f'Widget HTML for "{component_name}" not found in {ASSETS_DIR}. '
        "Run `pnpm run build` to generate the assets before starting the server."
    )


widgets: List[Widget] = [
    Widget(
        identifier="electronics-carousel",
        title="Show Electronics Carousel",
        template_uri="ui://widget/electronics-carousel.html",
        invoking="Carousel some spots",
        invoked="Served a fresh carousel",
        html=_load_widget_html("electronics-carousel"),
        response_text="Rendered a carousel!",
    ),
]


MIME_TYPE = "text/html+skybridge"


WIDGETS_BY_ID: Dict[str, Widget] = {
    widget.identifier: widget for widget in widgets
}
WIDGETS_BY_URI: Dict[str, Widget] = {
    widget.template_uri: widget for widget in widgets
}


def _split_env_list(value: str | None) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _transport_security_settings() -> TransportSecuritySettings:
    allowed_hosts = _split_env_list(os.getenv("MCP_ALLOWED_HOSTS"))
    allowed_origins = _split_env_list(os.getenv("MCP_ALLOWED_ORIGINS"))
    if not allowed_hosts and not allowed_origins:
        return TransportSecuritySettings(enable_dns_rebinding_protection=False)
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=allowed_hosts,
        allowed_origins=allowed_origins,
    )

def get_motherduck_connection() -> duckdb.DuckDBPyConnection:
    md_token = os.getenv("motherduck_token") or os.getenv("MOTHERDUCK_TOKEN")
    if not md_token:
        raise ValueError("motherduck_token non trovato nelle variabili d'ambiente")
    connection = duckdb.connect(f"md:app_gpt_elettronica?motherduck_token={md_token}")
    print("Connected to MotherDuck")
    return connection


def get_products_from_motherduck() -> list[dict]:
    query = """
        SELECT *
        FROM main.prodotti_xeel_shop
    """
    with get_motherduck_connection() as con:
        df = con.execute(query).fetchdf()
        return df.to_dict(orient="records")

mcp = FastMCP(
    name="mcp-python",
    stateless_http=True,
    transport_security=_transport_security_settings(),
)

TOOL_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "limit": {
            "type": "integer",
            "description": "Max number of products to return.",
            "minimum": 1,
        }
    },
    "additionalProperties": False,
}


def _resource_description(widget: Widget) -> str:
    return f"{widget.title} widget markup"


def _tool_meta(widget: Widget) -> Dict[str, Any]:
    return {
        "openai/outputTemplate": widget.template_uri,
        "openai/toolInvocation/invoking": widget.invoking,
        "openai/toolInvocation/invoked": widget.invoked,
        "openai/widgetAccessible": True,
    }


def _tool_invocation_meta(widget: Widget) -> Dict[str, Any]:
    return {
        "openai/toolInvocation/invoking": widget.invoking,
        "openai/toolInvocation/invoked": widget.invoked,
    }


@mcp._mcp_server.list_tools()
async def _list_tools() -> List[types.Tool]:
    return [
        types.Tool(
            name=widget.identifier,
            title=widget.title,
            description=widget.title,
            inputSchema=deepcopy(TOOL_INPUT_SCHEMA),
            _meta=_tool_meta(widget),
            # To disable the approval prompt for the tools
            annotations={
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": True,
            },
        )
        for widget in widgets
    ]


@mcp._mcp_server.list_resources()
async def _list_resources() -> List[types.Resource]:
    return [
        types.Resource(
            name=widget.title,
            title=widget.title,
            uri=widget.template_uri,
            description=_resource_description(widget),
            mimeType=MIME_TYPE,
            _meta=_tool_meta(widget),
        )
        for widget in widgets
    ]


@mcp._mcp_server.list_resource_templates()
async def _list_resource_templates() -> List[types.ResourceTemplate]:
    return [
        types.ResourceTemplate(
            name=widget.title,
            title=widget.title,
            uriTemplate=widget.template_uri,
            description=_resource_description(widget),
            mimeType=MIME_TYPE,
            _meta=_tool_meta(widget),
        )
        for widget in widgets
    ]


async def _handle_read_resource(req: types.ReadResourceRequest) -> types.ServerResult:
    widget = WIDGETS_BY_URI.get(str(req.params.uri))
    if widget is None:
        return types.ServerResult(
            types.ReadResourceResult(
                contents=[],
                _meta={"error": f"Unknown resource: {req.params.uri}"},
            )
        )

    contents = [
        types.TextResourceContents(
            uri=widget.template_uri,
            mimeType=MIME_TYPE,
            text=widget.html,
            _meta=_tool_meta(widget),
        )
    ]

    return types.ServerResult(types.ReadResourceResult(contents=contents))


def _first_present_value(item: Dict[str, Any], keys: List[str]) -> Any | None:
    for key in keys:
        value = item.get(key)
        if value is not None and value != "":
            return value
    return None


def _extract_first_image(value: Any) -> str | None:
    if not value:
        return None
    if isinstance(value, list):
        for entry in value:
            if entry:
                return str(entry)
        return None
    if isinstance(value, str):
        trimmed = value.strip()
        if not trimmed:
            return None
        if trimmed.startswith("["):
            try:
                parsed = json.loads(trimmed)
            except json.JSONDecodeError:
                return trimmed
            if isinstance(parsed, list) and parsed:
                return str(parsed[0])
            if isinstance(parsed, str):
                return parsed
        if "," in trimmed:
            first = trimmed.split(",", 1)[0].strip()
            return first or trimmed
        return trimmed
    return str(value)


def _coerce_list(value: Any) -> List[str] | None:
    if value is None or value == "":
        return None
    if isinstance(value, list):
        return [str(item) for item in value if item is not None and item != ""]
    if isinstance(value, str):
        trimmed = value.strip()
        if not trimmed:
            return None
        if trimmed.startswith("["):
            try:
                parsed = json.loads(trimmed)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, list):
                return [str(item) for item in parsed if item is not None and item != ""]
        return [item.strip() for item in trimmed.split(",") if item.strip()]
    return [str(value)]


def _normalize_product(item: Dict[str, Any], index: int) -> Dict[str, Any]:
    product_id = _first_present_value(
        item, ["id", "product_id", "sku", "code", "uuid"]
    )
    name = _first_present_value(
        item, ["name", "title", "product_name", "nome", "short_name"]
    )
    price = _first_present_value(
        item, ["price", "prezzo", "amount", "cost", "unit_price"]
    )
    description = _first_present_value(
        item,
        [
            "description",
            "descrizione",
            "descrizione_prodotto",
            "details",
            "detail",
            "long_description",
            "descrizione_lunga",
        ],
    )
    thumbnail = _extract_first_image(
        _first_present_value(
            item,
            [
                "imageURLS",
                "imageUrls",
                "image_urls",
                "thumbnail",
                "image",
                "img",
                "image_url",
                "url",
                "foto",
                "picture",
                "immagine",
            ],
        )
    )
    rating = _first_present_value(
        item,
        ["voto_prodotto1_5", "rating", "rating_value", "stars", "score"],
    )
    city = _first_present_value(item, ["city", "citta", "location"])
    brand = _first_present_value(item, ["brand", "marca"])
    categories = _coerce_list(
        _first_present_value(item, ["categories", "category", "categorie"])
    )
    primary_categories = _coerce_list(
        _first_present_value(
            item, ["primaryCategories", "primaryCategory", "categoria_principale"]
        )
    )
    pro = _first_present_value(item, ["pro", "pros", "vantaggi", "prodotto_pro"])
    contro = _first_present_value(
        item, ["contro", "cons", "svantaggi", "prodotto_contro"]
    )

    return {
        "id": str(product_id) if product_id is not None else f"md-{index}",
        "name": str(name) if name is not None else "Prodotto",
        "price": price,
        "description": description,
        "thumbnail": thumbnail,
        "rating": rating,
        "city": city,
        "brand": brand,
        "categories": categories,
        "primaryCategories": primary_categories,
        "pro": pro,
        "contro": contro,
    }


async def _call_tool_request(req: types.CallToolRequest) -> types.ServerResult:
    widget = WIDGETS_BY_ID.get(req.params.name)
    if widget is None:
        return types.ServerResult(
            types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=f"Unknown tool: {req.params.name}",
                    )
                ],
                isError=True,
            )
        )

    meta = _tool_invocation_meta(widget)

    if widget.identifier == "electronics-carousel":
        arguments = req.params.arguments or {}
        limit = arguments.get("limit")
        try:
            products = get_products_from_motherduck()
        except Exception as e:
            print(f"Error fetching products from MotherDuck: {e}")
            return types.ServerResult(
                types.CallToolResult(
                    content=[
                        types.TextContent(
                            type="text",
                            text="MotherDuck connection failed while fetching products.",
                        )
                    ],
                    isError=True,
                )
            )
        if isinstance(limit, int) and limit > 0:
            products = products[:limit]
        places = [
            _normalize_product(product, index)
            for index, product in enumerate(products)
        ]
        return types.ServerResult(
            types.CallToolResult(
                content=[types.TextContent(type="text", text="Fetched products.")],
                structuredContent={"places": places},
                _meta=meta,
            )
        )

    return types.ServerResult(
        types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=widget.response_text,
                )
            ],
            _meta=meta,
        )
    )

@mcp._mcp_server.call_tool()
async def product_list_tool(req: types.CallToolRequest) -> types.ServerResult:
    products = get_products_from_motherduck()
    return types.ServerResult(
        types.CallToolResult(
            content=[types.TextContent(type="text", text="Fetched products.")],
            structuredContent={"products": products},
        )
    )

mcp._mcp_server.request_handlers[types.CallToolRequest] = _call_tool_request
mcp._mcp_server.request_handlers[types.ReadResourceRequest] = _handle_read_resource


app = mcp.streamable_http_app()

try:
    from starlette.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=False,
    )
except Exception:
    pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000)