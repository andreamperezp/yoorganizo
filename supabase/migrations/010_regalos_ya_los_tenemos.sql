-- "Ya lo tenemos": la dueña tacha regalos que ya tiene o que le regalaron; nadie más los puede elegir.
alter table public.gifts add column if not exists have boolean not null default false;
-- set_gifts, list_gifts_admin y get_invite_gifts ahora guardan y devuelven "have";
-- claim_gift responde 'agotado' si el regalo está tachado.
-- (definiciones completas aplicadas en el proyecto; ver migración "regalos_ya_los_tenemos",
--  iguales a las de 009 con la columna have agregada)
