import { useCallback, useEffect, useRef, useState } from 'react';
import { AuthPanel } from './components/AuthPanel';
import { MetricsPanel } from './components/MetricsPanel';
import { ProductCard } from './components/ProductCard';
import { RecommendationsPanel } from './components/RecommendationsPanel';
import { useAuth } from './auth/AuthContext';
import { ApiError, api, type Product, type Recommendation, type RecommendationMetrics } from './lib/api';

const REFRESH_DEBOUNCE_MS = 2000;

export function App() {
  const { session } = useAuth();
  const [products, setProducts] = useState<Product[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [metrics, setMetrics] = useState<RecommendationMetrics | null>(null);
  const [modelVersion, setModelVersion] = useState<string | null>(null);
  const [loadingProducts, setLoadingProducts] = useState(true);
  const [loadingRecommendations, setLoadingRecommendations] = useState(false);
  const [loadingMetrics, setLoadingMetrics] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const inFlight = useRef(false);
  const refreshTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    setLoadingProducts(true);
    api
      .listProducts()
      .then((items) => {
        setProducts(items);
        setError(null);
      })
      .catch((err: Error) => {
        setError(
          err instanceof ApiError
            ? err.message
            : 'Catalogue is temporarily unavailable. Please try again shortly.',
        );
      })
      .finally(() => setLoadingProducts(false));
  }, []);

  const loadRecommendations = useCallback(
    async (refresh = false) => {
      if (!session) {
        setRecommendations([]);
        return;
      }
      if (inFlight.current) return;
      inFlight.current = true;
      setLoadingRecommendations(true);
      try {
        const result = await api.getRecommendations(refresh);
        setRecommendations(result.items);
        setModelVersion(result.model_version);
        setError(null);
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : 'Recommendations are temporarily unavailable. Please try again shortly.',
        );
      } finally {
        inFlight.current = false;
        setLoadingRecommendations(false);
      }
    },
    [session],
  );

  const loadMetrics = useCallback(async () => {
    if (!session) {
      setMetrics(null);
      return;
    }
    setLoadingMetrics(true);
    try {
      const result = await api.getRecommendationMetrics();
      setMetrics(result);
      setError(null);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : 'Recommendation metrics are temporarily unavailable. Please try again shortly.',
      );
    } finally {
      setLoadingMetrics(false);
    }
  }, [session]);

  useEffect(() => {
    void loadRecommendations();
  }, [loadRecommendations]);

  useEffect(() => {
    void loadMetrics();
  }, [loadMetrics]);

  useEffect(
    () => () => {
      if (refreshTimer.current) clearTimeout(refreshTimer.current);
    },
    [],
  );

  async function track(
    productId: string,
    type: 'view' | 'click' | 'add_to_cart' | 'purchase' | 'rating',
    rating?: number,
  ) {
    if (!session) return;
    try {
      await api.recordInteraction(productId, type, rating);
      setError(null);
      void loadMetrics();
      if (refreshTimer.current) clearTimeout(refreshTimer.current);
      refreshTimer.current = setTimeout(() => void loadRecommendations(true), REFRESH_DEBOUNCE_MS);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : 'We could not save that interaction. Please try again shortly.',
      );
    }
  }

  const visibleProducts = products.filter((product) =>
    product.name.toLowerCase().includes(query.trim().toLowerCase()),
  );

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-4">
          <h1 className="text-xl font-bold tracking-tight">
            Reco<span className="text-indigo-600">Shop</span>
          </h1>
          <AuthPanel />
        </div>
      </header>

      <main className="mx-auto flex max-w-6xl flex-col gap-10 px-6 py-8">
        {error && (
          <p
            role="alert"
            className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800"
          >
            {error} If this keeps happening, the server may be waking up. Wait about a minute and
            refresh the page.
          </p>
        )}

        {!session && (
          <section className="rounded-2xl border border-indigo-100 bg-indigo-50 p-6">
            <h2 className="text-lg font-semibold text-indigo-900">Get picks made for you</h2>
            <p className="mt-1 text-sm text-indigo-900">
              Sign in or create an account, then add products to your cart, buy or rate them. The
              recommender learns from your activity.
            </p>
          </section>
        )}

        {session && (
          <RecommendationsPanel
            items={recommendations}
            modelVersion={modelVersion}
            loading={loadingRecommendations}
            onSelect={(productId) => void track(productId, 'click')}
            onRefresh={() => void loadRecommendations(true)}
          />
        )}

        <section className="flex flex-col gap-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-2xl font-semibold text-slate-900">Catalogue</h2>
            <div>
              <label htmlFor="catalogue-search" className="sr-only">
                Search products
              </label>
              <input
                id="catalogue-search"
                type="search"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search products"
                className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm text-slate-900 placeholder:text-slate-500 sm:w-64"
              />
            </div>
          </div>

          {loadingProducts && (
            <p className="text-sm text-slate-600">
              Loading catalogue… the first load can take up to a minute while the server wakes up.
            </p>
          )}
          {!loadingProducts && products.length === 0 && (
            <p className="rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900">
              Catalogue data is unavailable right now. Check the API connection and try again.
            </p>
          )}
          {!loadingProducts && products.length > 0 && visibleProducts.length === 0 && (
            <p className="text-sm text-slate-600">No products match “{query}”.</p>
          )}

          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {visibleProducts.map((product) => (
              <ProductCard
                key={product.id}
                product={product}
                onSelect={(p) => void track(p.id, 'view')}
                onAddToCart={(p) => void track(p.id, 'add_to_cart')}
                onPurchase={(p) => void track(p.id, 'purchase')}
                onRate={(p, rating) => void track(p.id, 'rating', rating)}
                disabledActions={!session}
              />
            ))}
          </div>
        </section>

        {session && <MetricsPanel metrics={metrics} loading={loadingMetrics} />}
      </main>
    </div>
  );
}