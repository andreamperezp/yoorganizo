-- Un planner por usuaria y por tipo de evento (baby shower, cumpleaños, ...).
alter table public.plans add column if not exists kind text not null default 'babyshower';
alter table public.plans drop constraint if exists plans_pkey;
alter table public.plans add primary key (user_id, kind);
