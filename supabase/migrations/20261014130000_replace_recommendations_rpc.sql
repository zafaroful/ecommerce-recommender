-- Atomic replacement of a user's recommendations for one model version.
-- Replacing the previous delete-then-insert (two network calls) with a single
-- transactional server-side function removes the data-loss window between them.
--
-- Only the service role executes this; client roles keep read-only access to
-- recommendations per the initial schema.

create or replace function public.replace_recommendations(
  p_user_id uuid,
  p_model_version text,
  p_rows jsonb
)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  if p_model_version is null or btrim(p_model_version) = '' then
    raise exception 'model_version must not be blank';
  end if;

  delete from public.recommendations
  where user_id = p_user_id
    and model_version = p_model_version;

  if p_rows is not null and jsonb_array_length(p_rows) > 0 then
    insert into public.recommendations (user_id, product_id, score, rank, model_version, generated_at)
    select
      p_user_id,
      (row ->> 'product_id')::uuid,
      (row ->> 'score')::double precision,
      (row ->> 'rank')::integer,
      p_model_version,
      coalesce((row ->> 'generated_at')::timestamptz, timezone('utc', now()))
    from jsonb_array_elements(p_rows) as row;
  end if;
end;
$$;

comment on function public.replace_recommendations(uuid, text, jsonb) is
  'Atomically replaces a user''s recommendation rows for one model version.';

revoke all on function public.replace_recommendations(uuid, text, jsonb) from public, anon, authenticated;
grant execute on function public.replace_recommendations(uuid, text, jsonb) to service_role;