import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "electronics_server_python"
REQUIREMENTS = BACKEND_DIR / "requirements.txt"
DEFAULT_CADDYFILE = ROOT / "Caddyfile"

BACKEND_PORT = int(os.environ.get("BACKEND_PORT", "8000"))
FRONTEND_PORT = int(os.environ.get("FRONTEND_PORT", "3000"))
PROXY_PORT = int(os.environ.get("PROXY_PORT", "4444"))


def resolve_tool(env_var: str, command_name: str, fallback_paths: list[Path] | None = None) -> str | None:
    env_path = os.environ.get(env_var)
    if env_path:
        return env_path
    if fallback_paths:
        for candidate in fallback_paths:
            if candidate.exists():
                return str(candidate)
    return shutil.which(command_name)


def run_step(label: str, args: list[str] | str, *, shell: bool = False) -> None:
    print(f"[start-local] {label}...")
    subprocess.run(args, check=True, shell=shell)


def start_process(label: str, args: list[str] | str, *, shell: bool = False) -> subprocess.Popen:
    print(f"[start-local] starting {label}")
    return subprocess.Popen(args, shell=shell)

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Start backend, frontend, Caddy proxy, and ngrok in one command."
    )
    parser.add_argument(
        "--skip-install",
        action="store_true",
        help="Skip pip/pnpm install steps.",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip pnpm build before pnpm serve.",
    )
    args = parser.parse_args()

    caddyfile_path = Path(
        os.environ.get("CADDYFILE_PATH", str(DEFAULT_CADDYFILE))
    ).resolve()
    if not caddyfile_path.exists():
        print(
            f"[start-local] Caddyfile not found: {caddyfile_path}\n"
            "Set CADDYFILE_PATH or create a Caddyfile in the repo root."
        )
        return 1

    caddy = resolve_tool(
        "CADDY_PATH",
        "caddy",
        fallback_paths=[Path(r"C:\Tools\caddy\caddy.exe")],
    )
    ngrok = resolve_tool("NGROK_PATH", "ngrok")
    if not caddy:
        print(
            "[start-local] caddy not found. Set CADDY_PATH or add it to PATH."
        )
        return 1
    if not ngrok:
        print(
            "[start-local] ngrok not found. Set NGROK_PATH or add it to PATH."
        )
        return 1
    try:
        if not args.skip_install:
            run_step(
                "installing backend deps",
                [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS)],
            )
            run_step("installing frontend deps", "pnpm install", shell=True)

        if not args.skip_build:
            run_step("building frontend", "pnpm build", shell=True)

        processes: list[subprocess.Popen] = []
        try:
            processes.append(
                start_process(
                    "backend (uvicorn)",
                    [
                        sys.executable,
                        "-m",
                        "uvicorn",
                        "electronics_server_python.main:app",
                        "--host",
                        "0.0.0.0",
                        "--port",
                        str(BACKEND_PORT),
                    ],
                )
            )
            frontend_cmd = f"pnpm exec serve -s ./assets -p {FRONTEND_PORT} --cors"
            processes.append(
                start_process("frontend (serve)", frontend_cmd, shell=True)
            )
            processes.append(
                start_process(
                    "caddy proxy",
                    [caddy, "run", "--config", str(caddyfile_path)],
                )
            )
            processes.append(
                start_process(
                    "ngrok",
                    [ngrok, "http", f"http://localhost:{PROXY_PORT}"],
                )
            )

            print("[start-local] all services started.")
            print(f"[start-local] frontend/proxy: http://localhost:{PROXY_PORT}")
            print("[start-local] press Ctrl+C to stop.")

            while True:
                time.sleep(1)
                for proc in processes:
                    if proc.poll() is not None:
                        print(
                            f"[start-local] process exited with code {proc.returncode}. "
                            "Stopping all."
                        )
                        raise KeyboardInterrupt
        except KeyboardInterrupt:
            print("[start-local] stopping processes...")
            for proc in processes:
                if proc.poll() is None:
                    proc.terminate()
            time.sleep(1)
            for proc in processes:
                if proc.poll() is None:
                    proc.kill()
            return 0
    except subprocess.CalledProcessError as exc:
        print(f"[start-local] step failed with code {exc.returncode}")
        return exc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
