-- Invitaciones sin necesidad de cuenta: cada evento tiene una clave secreta (se guarda su hash).
alter table public.invites alter column owner drop not null;
alter table public.invites add column if not exists owner_key_hash text;
create index if not exists invites_key_kind on public.invites (owner_key_hash, kind);
create or replace function public.yo_key_hash(p_key text) returns text language sql immutable set search_path = '' as $$
  select encode(extensions.digest(p_key, 'sha256'), 'hex');
$$;
-- upsert_invite(p_key, p_token, p_kind, p_guest_id, p_para, p_nene, p_mensaje, p_event): crea o actualiza (solo con la clave)
-- list_invites(p_key, p_kind): respuestas del evento
-- update_invites_event(p_key, p_kind, p_event): actualiza los datos del evento
-- delete_invite(p_key, p_token): borra una invitación
-- (definiciones completas aplicadas en el proyecto; ver migración "invitaciones_sin_cuenta")
