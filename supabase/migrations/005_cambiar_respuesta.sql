-- Cambiar la respuesta de un invitado desde la app (solo con la clave del evento),
-- para que "Actualizar confirmaciones" no pise lo que se cambió a mano.
create or replace function public.set_invite_rsvp(p_key text, p_token text, p_rsvp text, p_plus integer)
returns boolean language plpgsql security definer set search_path = '' as $$
begin
  if char_length(coalesce(p_key, '')) < 24 or p_rsvp not in ('pend', 'si', 'no') then return false; end if;
  update public.invites
     set rsvp = p_rsvp,
         plus = greatest(0, least(20, coalesce(p_plus, 0))),
         responded_at = case when p_rsvp = 'pend' then null else now() end,
         updated_at = now()
   where token = p_token and owner_key_hash = public.yo_key_hash(p_key);
  return found;
end;
$$;
revoke all on function public.set_invite_rsvp(text, text, text, integer) from public;
grant execute on function public.set_invite_rsvp(text, text, text, integer) to anon, authenticated;
