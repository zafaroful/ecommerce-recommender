-- Initial schema for the e-commerce recommendation system.
-- Creates profile, catalogue, interaction, and recommendation tables with
-- constraints, indexes, a signup trigger, and Row Level Security policies.

-- ---------------------------------------------------------------------------
-- Enums
-- ---------------------------------------------------------------------------

create type public.interaction_type as enum (
  'view',
  'click',
  'add_to_cart',
  'purchase',
  'rating'
);

-- ---------------------------------------------------------------------------
-- Tables
-- ---------------------------------------------------------------------------

create table public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  email text,
  full_name text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

comment on table public.profiles is 'Application profile mirrored from auth.users.';

create table public.categories (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  slug text not null unique,
  description text,
  created_at timestamptz not null default timezone('utc', now()),
  constraint categories_name_not_blank check (btrim(name) <> ''),
  constraint categories_slug_not_blank check (btrim(slug) <> '')
);

comment on table public.categories is 'Product categories for catalogue browsing.';

create table public.products (
  id uuid primary key default gen_random_uuid(),
  category_id uuid not null references public.categories (id) on delete restrict,
  name text not null,
  description text,
  price numeric(12, 2) not null,
  image_url text,
  is_active boolean not null default true,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint products_name_not_blank check (btrim(name) <> ''),
  constraint products_price_non_negative check (price >= 0)
);

comment on table public.products is 'Sellable catalogue products.';

create table public.interactions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles (id) on delete cascade,
  product_id uuid not null references public.products (id) on delete cascade,
  interaction_type public.interaction_type not null,
  rating smallint,
  created_at timestamptz not null default timezone('utc', now()),
  constraint interactions_rating_range check (rating is null or rating between 1 and 5),
  constraint interactions_rating_requires_rating_type check (
    interaction_type = 'rating' or rating is null
  ),
  constraint interactions_rating_type_requires_rating check (
    interaction_type <> 'rating' or rating is not null
  )
);

comment on table public.interactions is 'Implicit and explicit user product interactions.';

create table public.recommendations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles (id) on delete cascade,
  product_id uuid not null references public.products (id) on delete cascade,
  score double precision not null,
  rank integer not null,
  model_version text not null,
  generated_at timestamptz not null default timezone('utc', now()),
  constraint recommendations_rank_positive check (rank > 0),
  constraint recommendations_model_version_not_blank check (btrim(model_version) <> ''),
  constraint recommendations_user_product_version_unique unique (user_id, product_id, model_version),
  constraint recommendations_user_rank_version_unique unique (user_id, model_version, rank)
);

comment on table public.recommendations is 'Model-generated recommendation rows with version tracking.';

-- ---------------------------------------------------------------------------
-- Indexes
-- ---------------------------------------------------------------------------

create index interactions_user_id_idx on public.interactions (user_id);
create index interactions_product_id_idx on public.interactions (product_id);
create index interactions_type_idx on public.interactions (interaction_type);
create index interactions_created_at_idx on public.interactions (created_at desc);
create index interactions_user_type_created_idx
  on public.interactions (user_id, interaction_type, created_at desc);

create index recommendations_user_id_idx on public.recommendations (user_id);
create index recommendations_rank_idx on public.recommendations (rank);
create index recommendations_model_version_idx on public.recommendations (model_version);
create index recommendations_user_version_rank_idx
  on public.recommendations (user_id, model_version, rank);

create index products_category_id_idx on public.products (category_id);
create index products_is_active_idx on public.products (is_active);

-- ---------------------------------------------------------------------------
-- Triggers
-- ---------------------------------------------------------------------------

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;

create trigger profiles_set_updated_at
  before update on public.profiles
  for each row execute function public.set_updated_at();

create trigger products_set_updated_at
  before update on public.products
  for each row execute function public.set_updated_at();

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, email, full_name)
  values (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data ->> 'full_name', '')
  )
  on conflict (id) do nothing;
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- ---------------------------------------------------------------------------
-- Row Level Security
-- ---------------------------------------------------------------------------

alter table public.profiles enable row level security;
alter table public.categories enable row level security;
alter table public.products enable row level security;
alter table public.interactions enable row level security;
alter table public.recommendations enable row level security;

-- Profiles: users read and update only their own profile.
create policy "Profiles are viewable by owner"
  on public.profiles for select
  to authenticated
  using (auth.uid() = id);

create policy "Profiles are updatable by owner"
  on public.profiles for update
  to authenticated
  using (auth.uid() = id)
  with check (auth.uid() = id);

-- Categories: readable by everyone, writable only by service role (no client policy).
create policy "Categories are viewable by everyone"
  on public.categories for select
  to anon, authenticated
  using (true);

-- Products: active products readable by everyone, writable only by service role.
create policy "Active products are viewable by everyone"
  on public.products for select
  to anon, authenticated
  using (is_active);

-- Interactions: users insert and read only their own rows.
create policy "Users insert their own interactions"
  on public.interactions for insert
  to authenticated
  with check (auth.uid() = user_id);

create policy "Users read their own interactions"
  on public.interactions for select
  to authenticated
  using (auth.uid() = user_id);

-- Recommendations: users read only their own rows; clients cannot write them.
create policy "Users read their own recommendations"
  on public.recommendations for select
  to authenticated
  using (auth.uid() = user_id);

-- ---------------------------------------------------------------------------
-- Privileges
-- ---------------------------------------------------------------------------
-- Clients only get read access where policies allow it, plus interaction inserts.
-- Recommendation writes are intentionally not granted to client roles; the
-- service role bypasses RLS and performs trusted writes server-side.

grant usage on schema public to anon, authenticated;

grant select on public.categories to anon, authenticated;
grant select on public.products to anon, authenticated;
grant select, update on public.profiles to authenticated;
grant select, insert on public.interactions to authenticated;
grant select on public.recommendations to authenticated;

grant all on public.profiles to service_role;
grant all on public.categories to service_role;
grant all on public.products to service_role;
grant all on public.interactions to service_role;
grant all on public.recommendations to service_role;
grant usage on type public.interaction_type to authenticated, service_role;