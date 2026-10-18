import { supabase } from './supabase';

export type InteractionType = 'view' | 'click' | 'add_to_cart' | 'purchase' | 'rating';

export interface Category {
  id: string;
  name: string;
  slug: string;
  description: string | null;
}

export interface Product {
  id: string;
  category_id: string;
  name: string;
  description: string | null;
  price: number;
  image_url: string | null;
  is_active: boolean;
}

export interface Recommendation {
  product_id: string;
  score: number;
  rank: number;
  model_version: string;
  product: Product | null;
}

export interface RecommendationList {
  model_version: string;
  generated_at: string | null;
  items: Recommendation[];
}

const baseUrl = import.meta.env.VITE_API_BASE_URL;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set('Content-Type', 'application/json');

  const { data } = await supabase.auth.getSession();
  if (data.session?.access_token) {
    headers.set('Authorization', `Bearer ${data.session.access_token}`);
  }

  const response = await fetch(`${baseUrl}${path}`, { ...init, headers });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Request failed (${response.status}): ${detail}`);
  }
  return (await response.json()) as T;
}

export const api = {
  listCategories: () => request<Category[]>('/categories'),
  listProducts: () => request<Product[]>('/products'),
  getRecommendations: (refresh = false) =>
    request<RecommendationList>(`/recommendations${refresh ? '?refresh=true' : ''}`),
  recordInteraction: (productId: string, type: InteractionType, rating?: number) =>
    request('/interactions', {
      method: 'POST',
      body: JSON.stringify({
        product_id: productId,
        interaction_type: type,
        rating: rating ?? null,
      }),
    }),
};