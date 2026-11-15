{{ config(materialized='view') }}

-- a tabela achatada, recriada a partir da estrela: a dim_clube entra duas vezes
select
    f.*,
    m.nome               as mandante,
    m.estadio            as estadio,
    m.capacidade_estadio as capacidade_estadio,
    m.valor_mercado_elenco_mi_eur as valor_mercado_mandante_mi_eur,
    v.nome               as visitante,
    v.valor_mercado_elenco_mi_eur as valor_mercado_visitante_mi_eur
from {{ ref('fato_partida') }} f
join {{ ref('dim_clube') }} m on f.clube_mandante_id = m.clube_id
join {{ ref('dim_clube') }} v on f.clube_visitante_id = v.clube_id
