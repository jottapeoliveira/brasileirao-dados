-- grao: uma linha por partida (um campeonato, uma data, um mandante, um visitante)
select
    partida_id,
    cast(date as date)                   as data,
    time                                 as horario,
    tournament                           as campeonato,
    club_id_mandante                     as clube_mandante_id,
    club_id_visitante                    as clube_visitante_id,
    cast(home_goal as integer)           as gols_mandante,
    cast(away_goal as integer)           as gols_visitante,
    cast(total_gols as integer)          as total_gols,
    cast(saldo_gols_mandante as integer) as saldo_gols_mandante,
    home_corner                          as escanteios_mandante,
    away_corner                          as escanteios_visitante,
    home_attack                          as ataques_mandante,
    away_attack                          as ataques_visitante,
    home_shots                           as chutes_mandante,
    away_shots                           as chutes_visitante,
    ht_result                            as resultado_intervalo,
    case
        when home_goal > away_goal then 'mandante'
        when home_goal < away_goal then 'visitante'
        else 'empate'
    end                                  as resultado,
    home_goal > away_goal                as vitoria_mandante,
    dif_idade_media,
    dif_valor_mercado_mi_eur
from {{ source('prata', 'partidas_enriquecido') }}
-- filtro de integridade que veio da juncao da aula 7: so partidas com os dois clubes no cadastro
where club_id_mandante is not null
  and club_id_visitante is not null
