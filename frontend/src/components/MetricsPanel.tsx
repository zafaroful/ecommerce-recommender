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
    <section className="flex flex-col gap-4">
      <div>
        <h2 className="text-2xl font-semibold text-slate-900">Insights</h2>
        <p className="mt-1 text-sm text-slate-600">How the recommender is performing on your data.</p>
      </div>

      {loading && <p className="text-sm text-slate-600">Loading insights…</p>}
      {!loading && !metrics && (
        <p className="rounded-2xl border border-dashed border-slate-300 bg-white p-4 text-sm text-slate-600">
          Insights are unavailable right now. Try again in a moment.
        </p>
      )}

      {metrics && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
            <MetricCard label="Products" value={metrics.total_products} />
            <MetricCard label="Users" value={metrics.total_users} />
            <MetricCard label="Interactions" value={metrics.total_interactions} />
            <MetricCard label="Recommended users" value={metrics.users_with_recommendations} />
            <MetricCard label="Cold-start users" value={metrics.cold_start_users} />
            <MetricCard label="Model" value={metrics.model_version} />
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <h3 className="mb-3 text-sm font-semibold text-slate-900">Interaction mix</h3>
              <div className="flex flex-col gap-2">
                {Object.entries(metrics.interactions_by_type).map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between text-sm">
                    <span className="text-slate-600">{interactionLabels[type] ?? type}</span>
                    <span className="font-semibold text-slate-900">{count}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <h3 className="mb-3 text-sm font-semibold text-slate-900">Top engaged products</h3>
              {metrics.top_products.length === 0 ? (
                <p className="text-sm text-slate-600">No engagement has been recorded yet.</p>
              ) : (
                <ol className="flex flex-col gap-2">
                  {metrics.top_products.map((product) => (
                    <li
                      key={product.product_id}
                      className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2 text-sm"
                    >
                      <span className="text-slate-900">{product.name}</span>
                      <span className="font-semibold text-indigo-700">{product.score.toFixed(1)}</span>
                    </li>
                  ))}
                </ol>
              )}
            </div>
          </div>
        </>
      )}
    </section>
  );
}

function MetricCard({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-sm text-slate-600">{label}</p>
      <p className="mt-1 text-2xl font-bold text-slate-900">{value}</p>
    </div>
  );
}