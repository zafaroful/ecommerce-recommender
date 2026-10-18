import type { Product } from '../lib/api';

interface ProductCardProps {
  product: Product;
  onSelect: (product: Product) => void;
  onAddToCart: (product: Product) => void;
  onPurchase: (product: Product) => void;
  onRate: (product: Product, rating: number) => void;
  disabledActions: boolean;
}

export function ProductCard({
  product,
  onSelect,
  onAddToCart,
  onPurchase,
  onRate,
  disabledActions,
}: ProductCardProps) {
  return (
    <article className="flex flex-col gap-3 rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
      <button type="button" onClick={() => onSelect(product)} className="text-left">
        <h3 className="text-lg font-semibold text-slate-100">{product.name}</h3>
        <p className="mt-1 line-clamp-2 text-sm text-slate-400">{product.description}</p>
      </button>
      <div className="mt-auto flex items-center justify-between">
        <span className="text-cyan-300">${product.price.toFixed(2)}</span>
        <button
          type="button"
          onClick={() => onAddToCart(product)}
          disabled={disabledActions}
          className="rounded-lg border border-slate-700 px-3 py-1.5 text-sm text-slate-200 transition hover:border-cyan-400 hover:text-cyan-300 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Add to cart
        </button>
      </div>
      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-800 pt-3">
        <button
          type="button"
          onClick={() => onPurchase(product)}
          disabled={disabledActions}
          className="rounded-lg bg-cyan-400 px-3 py-1.5 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Mark purchased
        </button>
        <div className="flex items-center gap-1" aria-label={`Rate ${product.name}`}>
          {[1, 2, 3, 4, 5].map((rating) => (
            <button
              key={rating}
              type="button"
              onClick={() => onRate(product, rating)}
              disabled={disabledActions}
              className="rounded-md px-1.5 py-1 text-sm text-amber-300 transition hover:bg-amber-300/10 disabled:cursor-not-allowed disabled:opacity-50"
              aria-label={`Rate ${product.name} ${rating} out of 5`}
            >
              {rating}
            </button>
          ))}
        </div>
      </div>
    </article>
  );
}
