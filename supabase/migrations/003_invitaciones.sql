-- Invitaciones online con confirmación: una fila por invitado, identificada por un token difícil de adivinar.
create table if not exists public.invites (
  token text primary key check (char_length(token) >= 20),
  owner uuid not null default auth.uid() references auth.users (id) on delete cascade,
  kind text not null default 'babyshower',
  guest_id text not null,
  para text not null default '',
  nene text not null default '',
  mensaje text not null default '',
  event jsonb not null default '{}'::jsonb,
  rsvp text not null default 'pend' check (rsvp in ('pend', 'si', 'no')),
  plus int not null default 0 check (plus between 0 and 20),
  note text not null default '' check (char_length(note) <= 500),
  responded_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists invites_owner_kind on public.invites (owner, kind);
alter table public.invites enable row level security;
create policy "Ver mis invitaciones" on public.invites for select to authenticated using ((select auth.uid()) = owner);
create policy "Crear mis invitaciones" on public.invites for insert to authenticated with check ((select auth.uid()) = owner);
create policy "Editar mis invitaciones" on public.invites for update to authenticated using ((select auth.uid()) = owner) with check ((select auth.uid()) = owner);
create policy "Borrar mis invitaciones" on public.invites for delete to authenticated using ((select auth.uid()) = owner);

-- El invitado (sin cuenta) solo lee y responde SU invitación, con su token.
create or replace function public.get_invite(p_token text) returns json language sql stable security definer set search_path = '' as $$
  select json_build_object('para', i.para, 'nene', i.nene, 'mensaje', i.mensaje, 'event', i.event, 'rsvp', i.rsvp, 'plus', i.plus, 'note', i.note)
  from public.invites i where i.token = p_token;
$$;
create or replace function public.respond_invite(p_token text, p_rsvp text, p_plus int, p_note text) returns boolean language plpgsql security definer set search_path = '' as $$
begin
  if p_rsvp not in ('pend', 'si', 'no') then return false; end if;
  update public.invites set rsvp = p_rsvp, plus = greatest(0, least(20, coalesce(p_plus, 0))), note = left(coalesce(p_note, ''), 500),
         responded_at = case when p_rsvp = 'pend' then null else now() end, updated_at = now()
   where token = p_token;
  return found;
end;
$$;
revoke all on function public.get_invite(text) from public;
revoke all on function public.respond_invite(text, text, int, text) from public;
grant execute on function public.get_invite(text) to anon, authenticated;
grant execute on function public.respond_invite(text, text, int, text) to anon, authenticated;
