-- Cada invitación guarda la respuesta de cada persona: [{"n":"Ana","r":"si"}, ...]
alter table public.invites add column if not exists people jsonb not null default '[]'::jsonb;

-- Resumen de la invitación a partir de las personas: alguien viene -> 'si'; todos no -> 'no'; si no, 'pend'
create or replace function public.yo_people_summary(p jsonb) returns text language sql immutable set search_path = '' as $$
  select case
    when exists (select 1 from jsonb_array_elements(p) e where e->>'r' = 'si') then 'si'
    when jsonb_array_length(p) > 0 and not exists (select 1 from jsonb_array_elements(p) e where coalesce(e->>'r', 'pend') <> 'no') then 'no'
    else 'pend' end;
$$;

-- Guarda las respuestas de las personas (solo nombres que ya están en la invitación) y actualiza el resumen
create or replace function public.yo_apply_answers(p_token text, p_answers jsonb, p_key_hash text) returns boolean
language plpgsql security definer set search_path = '' as $$
declare cur jsonb; nxt jsonb; s text;
begin
  select people into cur from public.invites where token = p_token and (p_key_hash is null or owner_key_hash = p_key_hash);
  if not found then return false; end if;
  select coalesce(jsonb_agg(jsonb_build_object('n', e->>'n', 'r',
           coalesce((select a->>'r' from jsonb_array_elements(coalesce(p_answers, '[]'::jsonb)) a
                     where a->>'n' = e->>'n' and a->>'r' in ('pend', 'si', 'no') limit 1), e->>'r', 'pend')) order by o), '[]'::jsonb)
    into nxt from jsonb_array_elements(cur) with ordinality as x(e, o);
  s := public.yo_people_summary(nxt);
  update public.invites
     set people = nxt, rsvp = s,
         plus = greatest(0, (select count(*) from jsonb_array_elements(nxt) e where e->>'r' = 'si')::int - 1),
         responded_at = case when s = 'pend' and not exists (select 1 from jsonb_array_elements(nxt) e where e->>'r' <> 'pend') then null else now() end,
         updated_at = now()
   where token = p_token;
  return true;
end;
$$;
revoke all on function public.yo_apply_answers(text, jsonb, text) from public, anon, authenticated;

-- El invitado responde por cada persona (solo con su token)
create or replace function public.respond_people(p_token text, p_answers jsonb) returns boolean
language plpgsql security definer set search_path = '' as $$
begin
  if jsonb_typeof(p_answers) <> 'array' or jsonb_array_length(p_answers) > 30 then return false; end if;
  return public.yo_apply_answers(p_token, p_answers, null);
end;
$$;

-- La dueña del evento marca respuestas por persona desde la app (con la clave del evento)
create or replace function public.set_people_rsvp(p_key text, p_token text, p_answers jsonb) returns boolean
language plpgsql security definer set search_path = '' as $$
begin
  if char_length(coalesce(p_key, '')) < 24 or jsonb_typeof(p_answers) <> 'array' then return false; end if;
  return public.yo_apply_answers(p_token, p_answers, public.yo_key_hash(p_key));
end;
$$;

-- La app define quiénes están en la invitación; se conservan las respuestas de quienes siguen
create or replace function public.set_invite_people(p_key text, p_token text, p_names jsonb) returns boolean
language plpgsql security definer set search_path = '' as $$
declare cur jsonb; nxt jsonb; s text;
begin
  if char_length(coalesce(p_key, '')) < 24 or jsonb_typeof(p_names) <> 'array' or jsonb_array_length(p_names) > 30 then return false; end if;
  select people into cur from public.invites where token = p_token and owner_key_hash = public.yo_key_hash(p_key);
  if not found then return false; end if;
  select coalesce(jsonb_agg(jsonb_build_object('n', left(n #>> '{}', 80), 'r',
           coalesce((select c->>'r' from jsonb_array_elements(cur) c where c->>'n' = n #>> '{}' limit 1), 'pend')) order by o), '[]'::jsonb)
    into nxt from jsonb_array_elements(p_names) with ordinality as x(n, o) where coalesce(n #>> '{}', '') <> '';
  s := public.yo_people_summary(nxt);
  update public.invites
     set people = nxt, rsvp = s,
         plus = greatest(0, (select count(*) from jsonb_array_elements(nxt) e where e->>'r' = 'si')::int - 1),
         updated_at = now()
   where token = p_token;
  return true;
end;
$$;

-- Responder "todos sí / todos no" también marca a cada persona
create or replace function public.respond_invite(p_token text, p_rsvp text, p_plus integer, p_note text)
returns boolean language plpgsql security definer set search_path = '' as $$
begin
  if p_rsvp not in ('pend', 'si', 'no') then return false; end if;
  update public.invites
     set rsvp = p_rsvp,
         people = (select coalesce(jsonb_agg(jsonb_build_object('n', e->>'n', 'r', p_rsvp) order by o), '[]'::jsonb) from jsonb_array_elements(people) with ordinality as x(e, o)),
         plus = greatest(0, least(20, coalesce(p_plus, 0))),
         note = left(coalesce(p_note, ''), 500),
         responded_at = case when p_rsvp = 'pend' then null else now() end,
         updated_at = now()
   where token = p_token;
  return found;
end;
$$;
create or replace function public.set_invite_rsvp(p_key text, p_token text, p_rsvp text, p_plus integer)
returns boolean language plpgsql security definer set search_path = '' as $$
begin
  if char_length(coalesce(p_key, '')) < 24 or p_rsvp not in ('pend', 'si', 'no') then return false; end if;
  update public.invites
     set rsvp = p_rsvp,
         people = (select coalesce(jsonb_agg(jsonb_build_object('n', e->>'n', 'r', p_rsvp) order by o), '[]'::jsonb) from jsonb_array_elements(people) with ordinality as x(e, o)),
         plus = greatest(0, least(20, coalesce(p_plus, 0))),
         responded_at = case when p_rsvp = 'pend' then null else now() end,
         updated_at = now()
   where token = p_token and owner_key_hash = public.yo_key_hash(p_key);
  return found;
end;
$$;

create or replace function public.get_invite(p_token text) returns json language sql stable security definer set search_path = '' as $$
  select json_build_object('para', i.para, 'nene', i.nene, 'mensaje', i.mensaje, 'event', i.event,
                           'rsvp', i.rsvp, 'plus', i.plus, 'note', i.note, 'people', i.people)
  from public.invites i where i.token = p_token;
$$;

drop function if exists public.list_invites(text, text);
create function public.list_invites(p_key text, p_kind text)
returns table(token text, rsvp text, plus integer, note text, responded_at timestamptz, people jsonb)
language sql stable security definer set search_path = '' as $$
  select i.token, i.rsvp, i.plus, i.note, i.responded_at, i.people
  from public.invites i
  where char_length(coalesce(p_key, '')) >= 24 and i.owner_key_hash = public.yo_key_hash(p_key) and i.kind = p_kind;
$$;

revoke all on function public.respond_people(text, jsonb) from public;
revoke all on function public.set_people_rsvp(text, text, jsonb) from public;
revoke all on function public.set_invite_people(text, text, jsonb) from public;
revoke all on function public.list_invites(text, text) from public;
grant execute on function public.respond_people(text, jsonb) to anon, authenticated;
grant execute on function public.set_people_rsvp(text, text, jsonb) to anon, authenticated;
grant execute on function public.set_invite_people(text, text, jsonb) to anon, authenticated;
grant execute on function public.list_invites(text, text) to anon, authenticated;
