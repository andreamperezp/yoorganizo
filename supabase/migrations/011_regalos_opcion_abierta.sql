-- Opción abierta: el invitado cuenta que regala algo fuera de la lista.
-- gift_claims.note guarda qué regala; los pedidos quedan en un regalo especial "otro" (grupal),
-- que set_gifts nunca borra. Nueva función claim_other(p_token, p_name, p_what).
-- (definiciones completas aplicadas en el proyecto; ver migración "regalos_opcion_abierta")
alter table public.gift_claims add column if not exists note text not null default '' check (char_length(note) <= 200);
