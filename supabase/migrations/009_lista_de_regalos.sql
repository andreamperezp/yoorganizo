-- Lista de regalos: la dueña del evento arma la lista (con la clave del evento)
-- y cada invitado elige qué regala desde su invitación (con su token), dejando su nombre.
create table if not exists public.gifts (
  owner_key_hash text not null,
  kind text not null,
  id text not null check (char_length(id) between 1 and 40),
  cat text not null default '' check (char_length(cat) <= 60),
  name text not null check (char_length(name) between 1 and 120),
  detail text not null default '' check (char_length(detail) <= 200),
  qty int not null default 1 check (qty between 1 and 99),
  grp boolean not null default false,
  pos int not null default 0,
  updated_at timestamptz not null default now(),
  primary key (owner_key_hash, kind, id)
);
create table if not exists public.gift_claims (
  id uuid primary key default gen_random_uuid(),
  owner_key_hash text not null,
  kind text not null,
  gift_id text not null,
  token text,
  name text not null check (char_length(name) between 1 and 80),
  created_at timestamptz not null default now(),
  foreign key (owner_key_hash, kind, gift_id) references public.gifts (owner_key_hash, kind, id) on delete cascade
);
create index if not exists gift_claims_event on public.gift_claims (owner_key_hash, kind, gift_id);
create index if not exists gift_claims_token on public.gift_claims (token);
-- Sin políticas: solo se accede con las funciones de abajo
alter table public.gifts enable row level security;
alter table public.gift_claims enable row level security;

-- La dueña reemplaza la lista completa (se conservan las elecciones de los regalos que siguen)
create or replace function public.set_gifts(p_key text, p_kind text, p_items jsonb) returns boolean
language plpgsql security definer set search_path = '' as $$
declare h text;
begin
  if char_length(coalesce(p_key, '')) < 24 or jsonb_typeof(p_items) <> 'array' or jsonb_array_length(p_items) > 200 then return false; end if;
  h := public.yo_key_hash(p_key);
  delete from public.gifts g where g.owner_key_hash = h and g.kind = p_kind
    and g.id not in (select e->>'id' from jsonb_array_elements(p_items) e where coalesce(e->>'id', '') <> '');
  insert into public.gifts (owner_key_hash, kind, id, cat, name, detail, qty, grp, pos, updated_at)
  select h, p_kind, left(e->>'id', 40), left(coalesce(e->>'cat', ''), 60), left(e->>'name', 120), left(coalesce(e->>'detail', ''), 200),
         greatest(1, least(99, coalesce((e->>'qty')::int, 1))), coalesce((e->>'grp')::boolean, false), o::int, now()
  from jsonb_array_elements(p_items) with ordinality as x(e, o)
  where coalesce(e->>'id', '') <> '' and coalesce(trim(e->>'name'), '') <> ''
  on conflict (owner_key_hash, kind, id) do update
    set cat = excluded.cat, name = excluded.name, detail = excluded.detail, qty = excluded.qty, grp = excluded.grp, pos = excluded.pos, updated_at = now();
  return true;
end;
$$;

-- La dueña ve la lista con quién regala qué
create or replace function public.list_gifts_admin(p_key text, p_kind text) returns json
language sql stable security definer set search_path = '' as $$
  select coalesce(json_agg(json_build_object(
           'id', g.id, 'cat', g.cat, 'name', g.name, 'detail', g.detail, 'qty', g.qty, 'grp', g.grp,
           'claims', (select coalesce(json_agg(json_build_object('id', c.id, 'name', c.name, 'token', c.token, 'at', c.created_at) order by c.created_at), '[]'::json)
                      from public.gift_claims c where c.owner_key_hash = g.owner_key_hash and c.kind = g.kind and c.gift_id = g.id)
         ) order by g.pos), '[]'::json)
  from public.gifts g
  where char_length(coalesce(p_key, '')) >= 24 and g.owner_key_hash = public.yo_key_hash(p_key) and g.kind = p_kind;
$$;

-- El invitado ve la lista de su evento: cuántos quedan de cada regalo y cuáles eligió él (no ve nombres de otros)
create or replace function public.get_invite_gifts(p_token text) returns json
language sql stable security definer set search_path = '' as $$
  select coalesce(json_agg(json_build_object(
           'id', g.id, 'cat', g.cat, 'name', g.name, 'detail', g.detail, 'qty', g.qty, 'grp', g.grp,
           'taken', (select count(*) from public.gift_claims c where c.owner_key_hash = g.owner_key_hash and c.kind = g.kind and c.gift_id = g.id),
           'mine', (select coalesce(json_agg(json_build_object('id', c.id, 'name', c.name)), '[]'::json)
                    from public.gift_claims c where c.owner_key_hash = g.owner_key_hash and c.kind = g.kind and c.gift_id = g.id and c.token = p_token)
         ) order by g.pos), '[]'::json)
  from public.invites i
  join public.gifts g on g.owner_key_hash = i.owner_key_hash and g.kind = i.kind
  where i.token = p_token and char_length(coalesce(p_token, '')) >= 20;
$$;

-- El invitado elige un regalo con su nombre. Respuestas: ok, agotado, ya_elegido, invalido
create or replace function public.claim_gift(p_token text, p_gift_id text, p_name text) returns text
language plpgsql security definer set search_path = '' as $$
declare h text; k text; g record; n int; nm text;
begin
  nm := left(trim(coalesce(p_name, '')), 80);
  if nm = '' or char_length(coalesce(p_token, '')) < 20 then return 'invalido'; end if;
  select owner_key_hash, kind into h, k from public.invites where token = p_token;
  if h is null then return 'invalido'; end if;
  select * into g from public.gifts where owner_key_hash = h and kind = k and id = p_gift_id for update;
  if not found then return 'invalido'; end if;
  if exists (select 1 from public.gift_claims c where c.owner_key_hash = h and c.kind = k and c.gift_id = p_gift_id and c.token = p_token) then return 'ya_elegido'; end if;
  if (select count(*) from public.gift_claims c where c.token = p_token) >= 15 then return 'invalido'; end if;
  select count(*) into n from public.gift_claims c where c.owner_key_hash = h and c.kind = k and c.gift_id = p_gift_id;
  if not g.grp and n >= g.qty then return 'agotado'; end if;
  insert into public.gift_claims (owner_key_hash, kind, gift_id, token, name) values (h, k, p_gift_id, p_token, nm);
  return 'ok';
end;
$$;

-- El invitado se arrepiente: borra solo una elección suya
create or replace function public.unclaim_gift(p_token text, p_claim_id uuid) returns boolean
language sql security definer set search_path = '' as $$
  with d as (delete from public.gift_claims c where c.id = p_claim_id and c.token = p_token and char_length(coalesce(p_token, '')) >= 20 returning 1)
  select exists (select 1 from d);
$$;

-- La dueña anota a mano quién regala algo (por ejemplo, si se lo dijeron en persona) o lo borra
create or replace function public.admin_add_claim(p_key text, p_kind text, p_gift_id text, p_name text) returns boolean
language plpgsql security definer set search_path = '' as $$
declare h text; nm text;
begin
  nm := left(trim(coalesce(p_name, '')), 80);
  if char_length(coalesce(p_key, '')) < 24 or nm = '' then return false; end if;
  h := public.yo_key_hash(p_key);
  if not exists (select 1 from public.gifts where owner_key_hash = h and kind = p_kind and id = p_gift_id) then return false; end if;
  insert into public.gift_claims (owner_key_hash, kind, gift_id, token, name) values (h, p_kind, p_gift_id, null, nm);
  return true;
end;
$$;
create or replace function public.admin_delete_claim(p_key text, p_claim_id uuid) returns boolean
language sql security definer set search_path = '' as $$
  with d as (delete from public.gift_claims c where c.id = p_claim_id and char_length(coalesce(p_key, '')) >= 24
               and c.owner_key_hash = public.yo_key_hash(p_key) returning 1)
  select exists (select 1 from d);
$$;

revoke all on function public.set_gifts(text, text, jsonb) from public;
revoke all on function public.list_gifts_admin(text, text) from public;
revoke all on function public.get_invite_gifts(text) from public;
revoke all on function public.claim_gift(text, text, text) from public;
revoke all on function public.unclaim_gift(text, uuid) from public;
revoke all on function public.admin_add_claim(text, text, text, text) from public;
revoke all on function public.admin_delete_claim(text, uuid) from public;
grant execute on function public.set_gifts(text, text, jsonb) to anon, authenticated;
grant execute on function public.list_gifts_admin(text, text) to anon, authenticated;
grant execute on function public.get_invite_gifts(text) to anon, authenticated;
grant execute on function public.claim_gift(text, text, text) to anon, authenticated;
grant execute on function public.unclaim_gift(text, uuid) to anon, authenticated;
grant execute on function public.admin_add_claim(text, text, text, text) to anon, authenticated;
grant execute on function public.admin_delete_claim(text, uuid) to anon, authenticated;
