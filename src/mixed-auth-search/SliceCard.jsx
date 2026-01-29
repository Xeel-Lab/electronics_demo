import React from "react";
import { MapPin, Star, ShoppingCart } from "lucide-react";
import { Button } from "@openai/apps-sdk-ui/components/Button";
import { useCart } from "../use-cart";

function SliceCard({ place, index, onCardClick }) {
  const { addToCart, isInCart } = useCart();

  const handleAddToCart = (e) => {
    e.stopPropagation();
    addToCart({
      id: place.id,
      name: place.name,
      price: place.price,
      description: place.description,
      thumbnail: place.thumbnail,
    });
  };

  const inCart = isInCart(place.id);

  return (
    <article 
      className="min-w-[240px] sm:min-w-[270px] max-w-[270px] flex flex-col overflow-hidden rounded-2xl border border-black/10 bg-white shadow-sm cursor-pointer"
      onClick={(e) => {
        // Non aprire i dettagli se si clicca sul pulsante "Aggiungi al carrello" o sul selettore quantità
        if (e.target && e.target.closest && (e.target.closest('button') || e.target.closest('input'))) {
          return;
        }
        if (onCardClick) {
          onCardClick(place);
        }
      }}
    >
      <div className="relative h-36 w-full overflow-hidden">
        <img
          src={place.thumbnail}
          alt={place.name}
          className="h-full w-full object-cover"
        />
        <div className="absolute left-3 top-3 inline-flex items-center rounded-full bg-white/90 px-2.5 py-1 text-xs font-semibold text-black shadow-sm">
          #{index + 1}
        </div>
      </div>
      <div className="flex flex-1 flex-col gap-2 p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="truncate text-base font-semibold">{place.name}</div>
            <div className="mt-1 text-sm text-black/60">
              {place.description}
            </div>
          </div>
          <div className="rounded-full bg-black/5 px-2 py-1 text-xs text-black/70">
            {place.price}
          </div>
        </div>
        <div className="mt-auto flex items-center justify-between text-sm text-black/70">
          <div className="flex items-center gap-1">
            <Star strokeWidth={1.5} className="h-4 w-4 text-black" />
            <span>
              {place.rating?.toFixed ? place.rating.toFixed(1) : place.rating}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <MapPin strokeWidth={1.5} className="h-4 w-4" />
            <span>{place.city}</span>
          </div>
        </div>
        <div className="mt-2">
          <Button
            color={inCart ? "primary" : "secondary"}
            variant={inCart ? "soft" : "solid"}
            size="sm"
            onClick={handleAddToCart}
            disabled={inCart}
            className={
              inCart
                ? "w-full"
                : "w-full !bg-sky-200 !text-slate-900 hover:!bg-sky-300"
            }
          >
            <ShoppingCart className="h-4 w-4 mr-2" />
            {inCart ? "Nel carrello" : "Aggiungi al carrello"}
          </Button>
        </div>
      </div>
    </article>
  );
}

// Memoize component to prevent unnecessary re-renders when parent updates
export default React.memo(SliceCard);
