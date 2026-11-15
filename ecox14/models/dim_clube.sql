-- grao: uma linha por clube do cadastro do Transfermarkt
select
    club_id                  as clube_id,
    name                     as nome,
    club_code                as codigo,
    stadium_name             as estadio,
    stadium_seats            as capacidade_estadio,
    squad_size               as tamanho_elenco,
    average_age              as idade_media,
    foreigners_percentage    as pct_estrangeiros,
    national_team_players    as jogadores_selecao,
    saldo_transf_milhoes_eur as saldo_transferencias_mi_eur,
    last_season              as ultima_temporada,
    valor_mercado_elenco_mi_eur,
    jogadores_avaliados
from {{ source('prata', 'clubes') }}
