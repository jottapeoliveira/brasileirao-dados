"""Carga: leva a Prata para dentro do DuckDB. A Ouro e construida pelo dbt (pasta ecox14/).

construir_ouro() ficou aqui, sem ser chamada, para comparar com o dbt: e o SQL da aula 9.
"""
import logging

import duckdb

from config import BANCO, OURO, PRATA

log = logging.getLogger(__name__)

TABELAS_PRATA = ["partidas", "clubes", "partidas_enriquecido"]


def conectar():
    OURO.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(BANCO))  # cria o arquivo se ele nao existir


def criar_esquemas(con):
    con.execute("CREATE SCHEMA IF NOT EXISTS prata")
    con.execute("CREATE SCHEMA IF NOT EXISTS ouro")


def um_valor(con, sql):
    return con.execute(sql).fetchone()[0]


def carregar_prata(con):
    for nome in TABELAS_PRATA:
        caminho = (PRATA / f"{nome}.parquet").as_posix()  # barra comum, que o SQL espera
        con.execute(f"""
            CREATE OR REPLACE TABLE prata.{nome} AS
            SELECT * FROM read_parquet('{caminho}')
        """)
        log.info("prata.%s: %d linhas", nome, um_valor(con, f"SELECT COUNT(*) FROM prata.{nome}"))


def construir_ouro(con):
    """Versao da aula 9, em SQL dentro do Python. Desde a aula 10 quem faz isto e o dbt."""
    con.execute("""
        CREATE OR REPLACE TABLE ouro.dim_clube AS
        SELECT
            club_id                  AS clube_id,
            name                     AS nome,
            club_code                AS codigo,
            stadium_name             AS estadio,
            stadium_seats            AS capacidade_estadio,
            squad_size               AS tamanho_elenco,
            average_age              AS idade_media,
            foreigners_percentage    AS pct_estrangeiros,
            national_team_players    AS jogadores_selecao,
            saldo_transf_milhoes_eur AS saldo_transferencias_mi_eur,
            last_season              AS ultima_temporada,
            valor_mercado_elenco_mi_eur,
            jogadores_avaliados
        FROM prata.clubes
    """)
    con.execute("""
        CREATE OR REPLACE TABLE ouro.fato_partida AS
        SELECT
            partida_id,
            CAST(date AS DATE)       AS data,
            time                     AS horario,
            tournament               AS campeonato,
            club_id_mandante         AS clube_mandante_id,
            club_id_visitante        AS clube_visitante_id,
            CAST(home_goal AS INTEGER)  AS gols_mandante,
            CAST(away_goal AS INTEGER)  AS gols_visitante,
            CAST(total_gols AS INTEGER) AS total_gols,
            CAST(saldo_gols_mandante AS INTEGER) AS saldo_gols_mandante,
            home_corner              AS escanteios_mandante,
            away_corner              AS escanteios_visitante,
            home_attack              AS ataques_mandante,
            away_attack              AS ataques_visitante,
            home_shots               AS chutes_mandante,
            away_shots               AS chutes_visitante,
            ht_result                AS resultado_intervalo,
            CASE
                WHEN home_goal > away_goal THEN 'mandante'
                WHEN home_goal < away_goal THEN 'visitante'
                ELSE 'empate'
            END                      AS resultado,
            home_goal > away_goal    AS vitoria_mandante,
            dif_idade_media,
            dif_valor_mercado_mi_eur
        FROM prata.partidas_enriquecido
        WHERE club_id_mandante IS NOT NULL
          AND club_id_visitante IS NOT NULL
    """)
    con.execute("""
        CREATE OR REPLACE VIEW ouro.vw_partida_completa AS
        SELECT
            f.*,
            m.nome               AS mandante,
            m.estadio            AS estadio,
            m.capacidade_estadio AS capacidade_estadio,
            m.valor_mercado_elenco_mi_eur AS valor_mercado_mandante_mi_eur,
            v.nome               AS visitante,
            v.valor_mercado_elenco_mi_eur AS valor_mercado_visitante_mi_eur
        FROM ouro.fato_partida f
        JOIN ouro.dim_clube m ON f.clube_mandante_id = m.clube_id
        JOIN ouro.dim_clube v ON f.clube_visitante_id = v.clube_id
    """)


CONFERENCIAS = {
    "dim_clube: clube_id repetido (grao)": """
        SELECT COUNT(*) FROM (SELECT clube_id FROM ouro.dim_clube
                              GROUP BY clube_id HAVING COUNT(*) > 1)""",
    "fato_partida: partida_id repetido (grao)": """
        SELECT COUNT(*) FROM (SELECT partida_id FROM ouro.fato_partida
                              GROUP BY partida_id HAVING COUNT(*) > 1)""",
    "fato_partida sem o mandante na dim_clube": """
        SELECT COUNT(*) FROM ouro.fato_partida f
        LEFT JOIN ouro.dim_clube d ON f.clube_mandante_id = d.clube_id
        WHERE d.clube_id IS NULL""",
    "fato_partida sem o visitante na dim_clube": """
        SELECT COUNT(*) FROM ouro.fato_partida f
        LEFT JOIN ouro.dim_clube d ON f.clube_visitante_id = d.clube_id
        WHERE d.clube_id IS NULL""",
    "vw_partida_completa com linhas a mais ou a menos que a fato": """
        SELECT ABS((SELECT COUNT(*) FROM ouro.vw_partida_completa)
                 - (SELECT COUNT(*) FROM ouro.fato_partida))""",
}


def conferir(con):
    """Todas precisam dar zero. Se alguma nao der, o pipeline para."""
    for nome in ["dim_clube", "fato_partida", "vw_partida_completa"]:
        log.info("ouro.%s: %d linhas", nome, um_valor(con, f"SELECT COUNT(*) FROM ouro.{nome}"))
    problemas = 0
    for descricao, sql in CONFERENCIAS.items():
        n = um_valor(con, sql)
        log.info("conferido: %s = %d", descricao, n)
        problemas += n
    if problemas:
        raise ValueError(f"a ouro nao passou nas conferencias ({problemas} problemas)")


def conferir_ouro():
    """Chamada pelo pipeline depois do dbt, numa conexao propria."""
    con = conectar()
    try:
        conferir(con)
    finally:
        con.close()


def main():
    con = conectar()
    try:
        criar_esquemas(con)
        carregar_prata(con)
        # construir_ouro(con)   <- agora e o dbt (etapa modelagem)
        # conferir(con)         <- roda depois do dbt; aqui a ouro pode ainda nao existir
    finally:
        con.close()  # libera o arquivo para o dbt, senao da "file is locked"
    log.info("banco pronto em %s", BANCO)


if __name__ == "__main__":
    from config import configurar_log

    configurar_log()
    main()
