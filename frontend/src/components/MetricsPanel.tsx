import type { RecommendationMetrics } from '../lib/api';

interface MetricsPanelProps {
  metrics: RecommendationMetrics | null;
  loading: boolean;
}

const interactionLabels: Record<string, string> = {
  view: 'Views',
  click: 'Clicks',
  add_to_cart: 'Carts',
  purchase: 'Purchases',
  rating: 'Ratings',
};

export function MetricsPanel({ metrics, loading }: MetricsPanelProps) {
  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
      <div className="mb-4">
        <p className="text-xs font-semibold uppercase tracking-[0.25em] text-cyan-300">Phase 7</p>
        <h2 className="text-xl font-semibold text-slate-100">Recommendation quality dashboard</h2>
      </div>

      {loading && <p className="text-sm text-slate-400">Loading recommendation metrics...</p>}
      {!loading && !metrics && (
        <p className="text-sm text-slate-400">Metrics are unavailable right now.</p>
      )}

      {metrics && (
        <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <MetricCard label="Products" value={metrics.total_products} />
            <MetricCard label="Users" value={metrics.total_users} />
            <MetricCard label="Interactions" value={metrics.total_interactions} />
            <MetricCard label="Recommended users" value={metrics.users_with_recommendations} />
            <MetricCard label="Cold-start users" value={metrics.cold_start_users} />
            <MetricCard label="Model" value={metrics.model_version} />
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-widest text-slate-400">
              Interaction mix
            </h3>
            <div className="flex flex-col gap-2">
              {Object.entries(metrics.interactions_by_type).map(([type, count]) => (
                <div key={type} className="flex items-center justify-between text-sm">
                  <span className="text-slate-400">{interactionLabels[type] ?? type}</span>
                  <span className="font-semibold text-slate-100">{count}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 lg:col-span-2">
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-widest text-slate-400">
              Top engaged products
            </h3>
            {metrics.top_products.length === 0 ? (
              <p className="text-sm text-slate-400">No engagement has been recorded yet.</p>
            ) : (
              <ol className="flex flex-col gap-2">
                {metrics.top_products.map((product) => (
                  <li
                    key={product.product_id}
                    className="flex items-center justify-between rounded-lg bg-slate-900/70 px-3 py-2 text-sm"
                  >
                    <span className="text-slate-100">{product.name}</span>
                    <span className="text-cyan-300">{product.score.toFixed(1)}</span>
                  </li>
                ))}
              </ol>
            )}
          </div>
        </div>
      )}
    </section>
  );
}

function MetricCard({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
      <p className="text-xs uppercase tracking-widest text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-100">{value}</p>
    </div>
  );
}
