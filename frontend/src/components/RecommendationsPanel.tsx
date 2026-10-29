import type { Recommendation } from '../lib/api';

interface RecommendationsPanelProps {
  items: Recommendation[];
  modelVersion: string | null;
  loading: boolean;
  onSelect: (productId: string) => void;
  onRefresh: () => void;
}

const TILE_COLORS = ['bg-indigo-50', 'bg-emerald-50', 'bg-orange-50', 'bg-purple-50'];

function badgeFor(reason: string | undefined, rank: number): string {
  if (rank === 1) return 'Top match';
  if (reason?.toLowerCase().startsWith('similar')) return 'Because of your activity';
  if (reason?.toLowerCase().includes('category')) return 'Popular in your category';
  return 'Popular with shoppers';
}

export function RecommendationsPanel({
  items,
  modelVersion,
  loading,
  onSelect,
  onRefresh,
}: RecommendationsPanelProps) {
  return (
    <section className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-semibold text-slate-900">Recommended for you</h2>
          <p className="mt-1 text-sm text-slate-600">
            Picked from what you viewed, bought and rated.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {modelVersion && (
            <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700">
              {modelVersion}
            </span>
          )}
          <button
            type="button"
            onClick={onRefresh}
            disabled={loading}
            className="min-h-11 rounded-xl border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-800 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? 'Loading…' : 'Refresh'}
          </button>
        </div>
      </div>

      {!loading && items.length === 0 && (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-6 text-center">
          <p className="font-semibold text-slate-900">No recommendations yet</p>
          <p className="mt-1 text-sm text-slate-600">
            Add a few products to your cart, buy or rate them, then press Refresh.
          </p>
        </div>
      )}

      <ul className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {items.map((item) => {
          const name = item.product?.name ?? item.product_id;
          const tileColor = TILE_COLORS[name.charCodeAt(0) % TILE_COLORS.length];
          return (
            <li key={item.product_id}>
              <button
                type="button"
                onClick={() => onSelect(item.product_id)}
                className="flex h-full w-full flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-4 text-left shadow-sm transition hover:border-indigo-400"
              >
                <div
                  className={`flex h-24 w-full items-center justify-center rounded-xl text-4xl font-bold text-indigo-600 ${tileColor}`}
                  aria-hidden="true"
                >
                  {name.charAt(0)}
                </div>
                <span className="self-start rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700">
                  {badgeFor(item.reason, item.rank)}
                </span>
                <span className="text-base font-semibold text-slate-900">{name}</span>
                <span className="text-sm text-slate-600">{item.reason}</span>
              </button>
            </li>
          );
        })}
      </ul>
    </section>
  );
}