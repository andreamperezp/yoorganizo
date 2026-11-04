-- Compartir un planner con otras personas por email: pueden verlo y editarlo con su propia cuenta.
create table if not exists public.plan_shares (
  owner uuid not null references auth.users (id) on delete cascade,
  kind text not null,
  email text not null check (email = lower(email) and position('@' in email) > 1),
  owner_email text not null default '',
  created_at timestamptz not null default now(),
  primary key (owner, kind, email)
);
alter table public.plan_shares enable row level security;
create index if not exists plan_shares_email on public.plan_shares (email);

create policy "Ver con quién comparto" on public.plan_shares
  for select to authenticated using ((select auth.uid()) = owner);
create policy "Ver lo que me compartieron" on public.plan_shares
  for select to authenticated using (email = lower((select auth.jwt()) ->> 'email'));
create policy "Compartir mi planner" on public.plan_shares
  for insert to authenticated with check ((select auth.uid()) = owner);
create policy "Dejar de compartir" on public.plan_shares
  for delete to authenticated using ((select auth.uid()) = owner);

create policy "Ver un planner compartido" on public.plans
  for select to authenticated using (exists (
    select 1 from public.plan_shares s
    where s.owner = plans.user_id and s.kind = plans.kind and s.email = lower((select auth.jwt()) ->> 'email')));
create policy "Editar un planner compartido" on public.plans
  for update to authenticated
  using (exists (
    select 1 from public.plan_shares s
    where s.owner = plans.user_id and s.kind = plans.kind and s.email = lower((select auth.jwt()) ->> 'email')))
  with check (exists (
    select 1 from public.plan_shares s
    where s.owner = plans.user_id and s.kind = plans.kind and s.email = lower((select auth.jwt()) ->> 'email')));
