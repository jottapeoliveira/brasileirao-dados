"""Consultas de leitura do painel. Todo o SQL do dashboard mora aqui; o painel.py nao tem nenhum.

O banco e aberto em read_only: o painel e consumidor, nao altera a Ouro e nao trava o dbt.
"""
import json
from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parent.parent
BANCO = RAIZ / "dados" / "ouro" / "projeto.duckdb"
PROVENIENCIA = [
    RAIZ / "dados" / "bronze" / "brasileirao" / "proveniencia.json",
    RAIZ / "dados" / "bronze" / "transfermarkt" / "proveniencia.json",
]

# Filtro comum a todas as consultas: campeonatos escolhidos e intervalo de anos.
# list_contains recebe a lista inteira como um parametro so, sem montar texto de SQL.
FILTRO = "list_contains(?, campeonato) and year(data) between ? and ?"


def _consultar(sql, parametros=None):
    con = duckdb.connect(str(BANCO), read_only=True)
    try:
        return con.execute(sql, parametros or []).df()
    finally:
        con.close()


def campeonatos():
    """Campeonatos presentes na fato, do que tem mais partidas para o que tem menos."""
    return _consultar("""
        select campeonato, count(*) as partidas
        from ouro.fato_partida
        group by campeonato
        order by partidas desc
    """)


def anos():
    """Primeiro e ultimo ano com partidas."""
    return _consultar("""
        select min(year(data)) as primeiro, max(year(data)) as ultimo
        from ouro.fato_partida
    """)


def resumo(campeonatos, ano_ini, ano_fim):
    """Total de partidas e percentual de cada resultado."""
    return _consultar(f"""
        select
            count(*)                                                      as partidas,
            round(100 * avg(case when resultado = 'mandante'  then 1 else 0 end), 1) as pct_mandante,
            round(100 * avg(case when resultado = 'empate'    then 1 else 0 end), 1) as pct_empate,
            round(100 * avg(case when resultado = 'visitante' then 1 else 0 end), 1) as pct_visitante
        from ouro.fato_partida
        where {FILTRO}
    """, [campeonatos, ano_ini, ano_fim])


def vitoria_por_valor_de_mercado(campeonatos, ano_ini, ano_fim):
    """Fora de campo: % de vitoria do mandante por faixa de diferenca de valor do elenco."""
    return _consultar(f"""
        with faixas as (
            select
                vitoria_mandante,
                case
                    when dif_valor_mercado_mi_eur < -100 then '1. visitante +100'
                    when dif_valor_mercado_mi_eur <  -30 then '2. visitante +30-100'
                    when dif_valor_mercado_mi_eur <=  30 then '3. parecidos'
                    when dif_valor_mercado_mi_eur <= 100 then '4. mandante +30-100'
                    else                                      '5. mandante +100'
                end as faixa
            from ouro.fato_partida
            where {FILTRO} and dif_valor_mercado_mi_eur is not null
        )
        select
            faixa,
            count(*)                                   as partidas,
            round(100 * avg(vitoria_mandante::int), 1) as pct_vitoria_mandante
        from faixas
        group by faixa
        order by faixa
    """, [campeonatos, ano_ini, ano_fim])


def vitoria_por_estatistica(campeonatos, ano_ini, ano_fim):
    """Dentro de campo: % de vitoria do mandante quando ele teve mais ou menos que o visitante."""
    return _consultar(f"""
        with base as (
            select * from ouro.fato_partida where {FILTRO}
        ),
        comparacoes as (
            select 'Finalizacoes' as estatistica, chutes_mandante - chutes_visitante as dif,
                   vitoria_mandante from base
            union all
            select 'Ataques', ataques_mandante - ataques_visitante, vitoria_mandante from base
            union all
            select 'Escanteios', escanteios_mandante - escanteios_visitante, vitoria_mandante from base
        )
        select
            estatistica,
            round(100 * avg(case when dif > 0 then vitoria_mandante::int end), 1) as mandante_teve_mais,
            round(100 * avg(case when dif < 0 then vitoria_mandante::int end), 1) as mandante_teve_menos,
            count(dif)                                                           as partidas_com_dado
        from comparacoes
        group by estatistica
        order by estatistica
    """, [campeonatos, ano_ini, ano_fim])


def desempenho_por_clube(campeonatos, ano_ini, ano_fim):
    """Valor do elenco de cada clube ao lado do aproveitamento em casa."""
    return _consultar(f"""
        select
            d.nome                                       as clube,
            d.valor_mercado_elenco_mi_eur                as valor_elenco_mi_eur,
            count(f.partida_id)                          as jogos_em_casa,
            round(100 * avg(f.vitoria_mandante::int), 1) as pct_vitorias_em_casa,
            round(avg(f.gols_mandante), 2)               as media_gols_em_casa
        from ouro.dim_clube d
        join ouro.fato_partida f on f.clube_mandante_id = d.clube_id
        where list_contains(?, f.campeonato) and year(f.data) between ? and ?
        group by d.nome, d.valor_mercado_elenco_mi_eur
        order by valor_elenco_mi_eur desc
    """, [campeonatos, ano_ini, ano_fim])


def fontes():
    """Le a proveniencia gravada pela ingestao, para o rodape do painel."""
    linhas = []
    for caminho in PROVENIENCIA:
        if caminho.exists():
            info = json.loads(caminho.read_text(encoding="utf-8"))
            # arquivos de aulas antigas usam outros nomes de campo
            fonte = info.get("fonte") or info.get("dataset") or caminho.parent.name
            data = info.get("extraido_em") or info.get("extraido em") or info.get("data") or "?"
            linhas.append(f"{fonte} (extraido em {str(data)[:10]})")
    return linhas
