import type { Product } from '../lib/api';

interface ProductCardProps {
  product: Product;
  onSelect: (product: Product) => void;
  onAddToCart: (product: Product) => void;
}

export function ProductCard({ product, onSelect, onAddToCart }: ProductCardProps) {
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
          className="rounded-lg border border-slate-700 px-3 py-1.5 text-sm text-slate-200 transition hover:border-cyan-400 hover:text-cyan-300"
        >
          Add to cart
        </button>
      </div>
    </article>
  );
}