import { useCallback, useEffect, useRef, useState } from 'react';
import { AuthPanel } from './components/AuthPanel';
import { ProductCard } from './components/ProductCard';
import { RecommendationsPanel } from './components/RecommendationsPanel';
import { useAuth } from './auth/AuthContext';
import { api, type Product, type Recommendation } from './lib/api';

const REFRESH_DEBOUNCE_MS = 2000;

export function App() {
  const { session } = useAuth();
  const [products, setProducts] = useState<Product[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [modelVersion, setModelVersion] = useState<string | null>(null);
  const [loadingRecommendations, setLoadingRecommendations] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inFlight = useRef(false);
  const refreshTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    api
      .listProducts()
      .then(setProducts)
      .catch((err: Error) => setError(err.message));
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
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load recommendations.');
      } finally {
        inFlight.current = false;
        setLoadingRecommendations(false);
      }
    },
    [session],
  );

  useEffect(() => {
    void loadRecommendations();
  }, [loadRecommendations]);

  useEffect(
    () => () => {
      if (refreshTimer.current) clearTimeout(refreshTimer.current);
    },
    [],
  );

  async function track(productId: string, type: 'view' | 'click' | 'add_to_cart') {
    if (!session) return;
    try {
      await api.recordInteraction(productId, type);
      if (refreshTimer.current) clearTimeout(refreshTimer.current);
      refreshTimer.current = setTimeout(() => void loadRecommendations(true), REFRESH_DEBOUNCE_MS);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to record interaction.');
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-12 text-slate-100">
      <div className="mx-auto flex max-w-5xl flex-col gap-8">
        <header className="flex flex-wrap items-center justify-between gap-4 rounded-3xl border border-slate-800 bg-slate-900/70 p-6">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.3em] text-cyan-300">Phase 3</p>
            <h1 className="text-3xl font-bold tracking-tight">E-commerce Recommender</h1>
          </div>
          <AuthPanel />
        </header>

        {error && (
          <p className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
            {error}
          </p>
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

        <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
          <h2 className="mb-4 text-xl font-semibold text-slate-100">Catalogue</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {products.map((product) => (
              <ProductCard
                key={product.id}
                product={product}
                onSelect={(p) => void track(p.id, 'view')}
                onAddToCart={(p) => void track(p.id, 'add_to_cart')}
              />
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}