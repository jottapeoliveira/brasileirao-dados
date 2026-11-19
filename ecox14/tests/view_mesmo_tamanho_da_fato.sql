-- passa quando devolve ZERO linhas
-- a view junta a dim_clube duas vezes: nao pode ganhar nem perder partidas
select
    (select count(*) from {{ ref('vw_partida_completa') }}) as linhas_view,
    (select count(*) from {{ ref('fato_partida') }})        as linhas_fato
where linhas_view <> linhas_fato
