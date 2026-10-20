-- Un planner por usuaria. Cada una solo puede leer y escribir el suyo (RLS).
create table if not exists public.plans (
  user_id uuid primary key references auth.users (id) on delete cascade,
  data jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);

alter table public.plans enable row level security;

create policy "Ver mi planner" on public.plans
  for select to authenticated using ((select auth.uid()) = user_id);

create policy "Crear mi planner" on public.plans
  for insert to authenticated with check ((select auth.uid()) = user_id);

create policy "Actualizar mi planner" on public.plans
  for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);

create policy "Borrar mi planner" on public.plans
  for delete to authenticated using ((select auth.uid()) = user_id);
