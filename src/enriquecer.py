"""Prata: junta as partidas ao cadastro de clubes, uma vez pelo mandante e outra pelo visitante."""
import json
import logging
from datetime import datetime

import pandas as pd

import juncao
from config import PRATA

log = logging.getLogger(__name__)

# Do cadastro, so o que o projeto usa. O club_id fica para virar chave da ouro.
ATRIBUTOS_CLUBE = ["club_id", "name", "average_age", "stadium_seats", "valor_mercado_elenco_mi_eur"]


def carregar():
    partidas = pd.read_parquet(PRATA / "partidas.parquet")
    clubes = pd.read_parquet(PRATA / "clubes.parquet")
    return partidas, clubes[ATRIBUTOS_CLUBE]


def mapear_ids(partidas):
    """Grafia diferente: o de-para traduz o nome das partidas para o club_id do cadastro."""
    partidas["club_id_mandante"] = partidas["home_limpo"].map(juncao.DE_PARA_CLUBES).astype("Int64")
    partidas["club_id_visitante"] = partidas["away_limpo"].map(juncao.DE_PARA_CLUBES).astype("Int64")
    return partidas


def juntar_clubes(partidas, clubes):
    clubes = clubes.astype({"club_id": "Int64"})

    juncao.conferir_chaves(partidas["club_id_mandante"], clubes["club_id"], "mandante")
    juncao.conferir_chaves(partidas["club_id_visitante"], clubes["club_id"], "visitante")

    # com o sufixo, o club_id do cadastro vira club_id_mandante: mesmo nome da chave da
    # esquerda, entao o pandas mantem uma coluna so
    r = juncao.juntar(partidas, clubes, "club_id_mandante", "club_id", "_mandante")
    juncao.validar(partidas, r, "name_mandante", "mandante")

    r = juncao.juntar(r, clubes, "club_id_visitante", "club_id", "_visitante")
    juncao.validar(partidas, r, "name_visitante", "visitante")
    return r


def criar_atributos(df):
    """So existem depois da juncao: dependem de informacao que estava no cadastro."""
    df["dif_idade_media"] = (df["average_age_mandante"] - df["average_age_visitante"]).round(1)
    df["capacidade_estadio_mandante"] = df["stadium_seats_mandante"]
    df["dif_valor_mercado_mi_eur"] = (
        df["valor_mercado_elenco_mi_eur_mandante"] - df["valor_mercado_elenco_mi_eur_visitante"]
    ).round(2)
    return df


def relatar_sem_par(df):
    """Quem nao casou e o achado: separa os grupos para o README."""
    sem = df["name_mandante"].isna() | df["name_visitante"].isna()
    log.info("partidas com os dois clubes no cadastro: %d de %d", int((~sem).sum()), len(df))
    por_campeonato = df[sem]["tournament"].value_counts().to_dict()
    log.info("partidas com algum clube sem cadastro, por campeonato: %s", por_campeonato)
    times = pd.concat([
        df.loc[df["name_mandante"].isna(), "home_limpo"],
        df.loc[df["name_visitante"].isna(), "away_limpo"],
    ])
    log.info("times sem cadastro: %d nomes diferentes", times.nunique())
    return times.value_counts()


def salvar(df):
    destino = PRATA / "partidas_enriquecido.parquet"
    df.to_parquet(destino, index=False)
    log.info("enriquecido: %d linhas, %d colunas salvas em %s", *df.shape, destino.name)
    return destino


def registrar(destino, linhas, completas):
    info = {
        "origem": ["partidas.parquet", "clubes.parquet"],
        "arquivo_prata": destino.name,
        "linhas_antes": linhas,
        "linhas_depois": linhas,
        "partidas_com_os_dois_clubes": completas,
        "decisoes": [
            "Left join pelo mandante e pelo visitante, com validate many_to_one.",
            "Nomes traduzidos para club_id por um de-para (juncao.DE_PARA_CLUBES).",
            "Atributos pos-juncao: dif_idade_media, capacidade_estadio_mandante e dif_valor_mercado_mi_eur.",
        ],
        "transformado_em": datetime.now().isoformat(timespec="seconds"),
    }
    with (PRATA / "proveniencia.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(info, ensure_ascii=False) + "\n")


def main():
    partidas, clubes = carregar()
    partidas = mapear_ids(partidas)
    df = juntar_clubes(partidas, clubes)
    df = criar_atributos(df)
    relatar_sem_par(df)
    destino = salvar(df)
    completas = int((df["name_mandante"].notna() & df["name_visitante"].notna()).sum())
    registrar(destino, len(df), completas)


if __name__ == "__main__":
    from config import configurar_log

    configurar_log()
    main()
