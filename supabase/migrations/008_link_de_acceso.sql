-- Link de acceso: abre el planner en cualquier dispositivo, sin mail ni contraseña.
-- Quien tenga el link puede verlo y editarlo; la dueña lo puede desactivar.
create table if not exists public.plan_links (
  token text primary key check (char_length(token) >= 24),
  owner uuid not null references auth.users (id) on delete cascade,
  kind text not null,
  created_at timestamptz not null default now()
);
alter table public.plan_links enable row level security;
create policy "Ver mis links" on public.plan_links for select to authenticated using ((select auth.uid()) = owner);
create policy "Crear mis links" on public.plan_links for insert to authenticated with check ((select auth.uid()) = owner);
create policy "Borrar mis links" on public.plan_links for delete to authenticated using ((select auth.uid()) = owner);

create or replace function public.get_plan_by_link(p_token text) returns json
language sql stable security definer set search_path = '' as $$
  select json_build_object('kind', l.kind, 'data', p.data, 'updated_at', p.updated_at, 'owner_email', u.email)
  from public.plan_links l
  join public.plans p on p.user_id = l.owner and p.kind = l.kind
  join auth.users u on u.id = l.owner
  where l.token = p_token and char_length(coalesce(p_token, '')) >= 24;
$$;

create or replace function public.save_plan_by_link(p_token text, p_data jsonb) returns timestamptz
language sql security definer set search_path = '' as $$
  update public.plans p set data = p_data, updated_at = now()
  from public.plan_links l
  where l.token = p_token and char_length(coalesce(p_token, '')) >= 24 and p.user_id = l.owner and p.kind = l.kind
    and jsonb_typeof(p_data) = 'object'
  returning p.updated_at;
$$;

revoke all on function public.get_plan_by_link(text) from public;
revoke all on function public.save_plan_by_link(text, jsonb) from public;
grant execute on function public.get_plan_by_link(text) to anon, authenticated;
grant execute on function public.save_plan_by_link(text, jsonb) to anon, authenticated;
