import { useState } from 'react';
import { useCurrency } from '../currency/CurrencyContext';
import type { Product } from '../lib/api';

interface ProductCardProps {
  product: Product;
  onSelect: (product: Product) => void;
  onAddToCart: (product: Product) => void;
  onPurchase: (product: Product) => void;
  onRate: (product: Product, rating: number) => void;
  disabledActions: boolean;
}

const TILE_COLORS = ['bg-indigo-50', 'bg-emerald-50', 'bg-orange-50', 'bg-purple-50'];

export function ProductCard({
  product,
  onSelect,
  onAddToCart,
  onPurchase,
  onRate,
  disabledActions,
}: ProductCardProps) {
  const [added, setAdded] = useState(false);
  const [purchased, setPurchased] = useState(false);
  const [rated, setRated] = useState(0);
  const { formatPrice } = useCurrency();

  const tileColor = TILE_COLORS[product.name.charCodeAt(0) % TILE_COLORS.length];

  function handleAddToCart() {
    onAddToCart(product);
    setAdded(true);
    setTimeout(() => setAdded(false), 1500);
  }

  function handlePurchase() {
    onPurchase(product);
    setPurchased(true);
  }

  function handleRate(rating: number) {
    onRate(product, rating);
    setRated(rating);
  }

  return (
    <article className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div
        className={`flex h-28 items-center justify-center rounded-xl text-4xl font-bold text-indigo-600 ${tileColor}`}
        aria-hidden="true"
      >
        {product.name.charAt(0)}
      </div>

      <button type="button" onClick={() => onSelect(product)} className="text-left">
        <h3 className="text-base font-semibold text-slate-900">{product.name}</h3>
        <p className="mt-1 line-clamp-2 text-sm text-slate-600">{product.description}</p>
      </button>

      <span className="text-lg font-bold text-slate-900">{formatPrice(product.price)}</span>

      <div className="flex gap-2">
        <button
          type="button"
          onClick={handleAddToCart}
          disabled={disabledActions}
          className="min-h-11 flex-1 rounded-xl bg-indigo-600 px-4 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {added ? 'Added ✓' : 'Add to cart'}
        </button>
        <button
          type="button"
          onClick={handlePurchase}
          disabled={disabledActions || purchased}
          className="min-h-11 rounded-xl border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-800 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {purchased ? 'Purchased ✓' : 'Purchased'}
        </button>
      </div>

      <div className="flex items-center justify-between border-t border-slate-100 pt-2">
        <span className="text-sm text-slate-600">{rated ? `You rated ${rated}/5` : 'Rate it'}</span>
        <div className="flex items-center" aria-label={`Rate ${product.name}`}>
          {[1, 2, 3, 4, 5].map((rating) => (
            <button
              key={rating}
              type="button"
              onClick={() => handleRate(rating)}
              disabled={disabledActions}
              className={`min-h-11 min-w-9 text-xl transition disabled:cursor-not-allowed disabled:opacity-50 ${
                rating <= rated ? 'text-amber-600' : 'text-slate-400 hover:text-amber-500'
              }`}
              aria-label={`Rate ${product.name} ${rating} out of 5`}
            >
              ★
            </button>
          ))}
        </div>
      </div>

      {disabledActions && (
        <p className="text-xs text-slate-500">Sign in to add to cart, buy or rate.</p>
      )}
    </article>
  );
}