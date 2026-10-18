import type { Recommendation } from '../lib/api';

interface RecommendationsPanelProps {
  items: Recommendation[];
  modelVersion: string | null;
  loading: boolean;
  onSelect: (productId: string) => void;
  onRefresh: () => void;
}

export function RecommendationsPanel({
  items,
  modelVersion,
  loading,
  onSelect,
  onRefresh,
}: RecommendationsPanelProps) {
  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-100">Recommended for you</h2>
          {modelVersion && (
            <p className="text-xs uppercase tracking-widest text-slate-500">{modelVersion}</p>
          )}
        </div>
        <button
          type="button"
          onClick={onRefresh}
          disabled={loading}
          className="rounded-lg border border-slate-700 px-3 py-1.5 text-sm text-slate-200 transition hover:border-cyan-400 hover:text-cyan-300 disabled:opacity-50"
        >
          Refresh
        </button>
      </div>

      {loading && <p className="text-sm text-slate-400">Loading recommendations…</p>}
      {!loading && items.length === 0 && (
        <p className="text-sm text-slate-400">View a few products to get personalised picks.</p>
      )}

      <ul className="flex flex-col gap-2">
        {items.map((item) => (
          <li key={item.product_id}>
            <button
              type="button"
              onClick={() => onSelect(item.product_id)}
              className="flex w-full items-center justify-between rounded-xl border border-slate-800 bg-slate-950/60 px-4 py-3 text-left transition hover:border-cyan-400"
            >
              <span>
                <span className="block text-slate-100">
                  <span className="mr-2 text-slate-500">#{item.rank}</span>
                  {item.product?.name ?? item.product_id}
                </span>
                <span className="mt-1 block text-xs text-slate-400">{item.reason}</span>
              </span>
              <span className="text-sm text-cyan-300">score {item.score.toFixed(2)}</span>
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
