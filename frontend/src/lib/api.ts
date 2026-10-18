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
}

export interface Recommendation {
  product_id: string;
  score: number;
  rank: number;
  model_version: string;
  reason: string;
  product: Product | null;
}

export interface RecommendationList {
  model_version: string;
  generated_at: string | null;
  items: Recommendation[];
}

export interface ProductEngagementMetric {
  product_id: string;
  name: string;
  score: number;
}

export interface RecommendationMetrics {
  model_version: string;
  total_products: number;
  total_users: number;
  total_interactions: number;
  interactions_by_type: Record<InteractionType, number>;
  users_with_recommendations: number;
  cold_start_users: number;
  top_products: ProductEngagementMetric[];
}

const baseUrl = import.meta.env.VITE_API_BASE_URL;

export class ApiError extends Error {
  constructor(message = 'The request could not be completed. Please try again.') {
    super(message);
    this.name = 'ApiError';
  }
}

function logRequestFailure(path: string, error: unknown) {
  if (import.meta.env.DEV) {
    console.error(`API request failed for ${path}`, error);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set('Content-Type', 'application/json');

  const { data } = await supabase.auth.getSession();
  if (data.session?.access_token) {
    headers.set('Authorization', `Bearer ${data.session.access_token}`);
  }

  let response: Response;
  try {
    response = await fetch(`${baseUrl}${path}`, { ...init, headers });
  } catch (error) {
    logRequestFailure(path, error);
    throw new ApiError('Unable to reach the recommendation service. Check your connection.');
  }

  if (!response.ok) {
    const detail = await response.text();
    logRequestFailure(path, { status: response.status, detail });
    throw new ApiError();
  }
  return (await response.json()) as T;
}

export const api = {
  listCategories: () => request<Category[]>('/categories'),
  listProducts: () => request<Product[]>('/products'),
  getRecommendations: (refresh = false) =>
    request<RecommendationList>(`/recommendations${refresh ? '?refresh=true' : ''}`),
  getRecommendationMetrics: () => request<RecommendationMetrics>('/metrics/recommendations'),
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



