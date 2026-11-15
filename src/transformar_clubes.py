"""Prata: clubes do Transfermarkt. Fica so com a Serie A brasileira e converte o saldo de transferencias."""
import json
import logging
import re
from datetime import datetime

import pandas as pd

from config import BRONZE_CLUBES, LIGA_BRASIL, PADRAO_CLUBES, PADRAO_JOGADORES, PRATA

log = logging.getLogger(__name__)

COLUNAS = [
    "club_id", "club_code", "name", "squad_size", "average_age",
    "foreigners_number", "foreigners_percentage", "national_team_players",
    "stadium_name", "stadium_seats", "net_transfer_record", "last_season", "url",
]


def carregar():
    arquivos = sorted(BRONZE_CLUBES.glob(PADRAO_CLUBES))
    if not arquivos:
        raise FileNotFoundError(f"nada em {BRONZE_CLUBES}")
    caminho = arquivos[-1]
    df = pd.read_csv(caminho)
    log.info("clubes: %d linhas lidas de %s", len(df), caminho.name)
    return df, caminho


def filtrar_brasil(df):
    """O arquivo traz 32 ligas. So os clubes da Serie A do Brasil interessam ao projeto."""
    brasil = df[df["domestic_competition_id"] == LIGA_BRASIL]
    log.info("clubes: %d de %d sao da liga %s", len(brasil), len(df), LIGA_BRASIL)
    return brasil[COLUNAS].copy()


def para_milhoes(texto):
    """'+€8.14m' -> 8.14 | '€-2.84m' -> -2.84 | '+€500k' -> 0.5 | '+-0' -> 0.0"""
    if pd.isna(texto):
        return None
    t = str(texto).replace("€", "").replace("+", "").strip()
    if t in ("-0", "0", ""):
        return 0.0
    m = re.fullmatch(r"(-?[\d.]+)([mk]?)", t)
    if not m:
        log.warning("saldo de transferencia nao reconhecido: %r", texto)
        return None
    valor = float(m.group(1))
    return valor / 1000 if m.group(2) == "k" else valor


def converter_saldo(df):
    df["saldo_transf_milhoes_eur"] = df["net_transfer_record"].map(para_milhoes)
    return df.drop(columns=["net_transfer_record"])


def valor_de_mercado(clubes):
    """O total_market_value do cadastro vem vazio para o Brasil. A soma do valor de mercado dos
    jogadores de cada clube (players.csv, mesmo dataset) preenche esse buraco."""
    arquivos = sorted(BRONZE_CLUBES.glob(PADRAO_JOGADORES))
    if not arquivos:
        log.warning("jogadores: nenhum %s na bronze; valor de mercado fica vazio", PADRAO_JOGADORES)
        clubes["valor_mercado_elenco_mi_eur"] = float("nan")
        clubes["jogadores_avaliados"] = float("nan")
        return clubes

    jog = pd.read_csv(arquivos[-1], usecols=["player_id", "current_club_id", "last_season",
                                             "market_value_in_eur"])
    log.info("jogadores: %d linhas lidas de %s", len(jog), arquivos[-1].name)

    # So quem ainda esta no elenco: jogador aposentado ou sem clube continua com o ultimo
    # current_club_id, mas com last_season antigo. Fica quem jogou a ultima temporada do clube.
    jog = jog.merge(clubes[["club_id", "last_season"]], left_on="current_club_id",
                    right_on="club_id", suffixes=("", "_clube"), validate="many_to_one")
    elenco = jog[jog["last_season"] == jog["last_season_clube"]]

    soma = (elenco.groupby("club_id")
            .agg(valor_mercado_elenco_mi_eur=("market_value_in_eur", "sum"),
                 jogadores_avaliados=("market_value_in_eur", "count"))
            .reset_index())
    soma["valor_mercado_elenco_mi_eur"] = (soma["valor_mercado_elenco_mi_eur"] / 1e6).round(2)

    clubes = clubes.merge(soma, on="club_id", how="left", validate="one_to_one")
    sem_valor = clubes["valor_mercado_elenco_mi_eur"].isna().sum()
    if sem_valor:
        log.warning("jogadores: %d clubes ficaram sem valor de mercado", sem_valor)
    log.info("jogadores: valor de mercado somado para %d clubes", len(clubes) - sem_valor)
    return clubes


def salvar(df):
    PRATA.mkdir(parents=True, exist_ok=True)
    destino = PRATA / "clubes.parquet"
    df.to_parquet(destino, index=False)
    log.info("clubes: %d linhas salvas em %s", len(df), destino.name)
    return destino


def registrar(origem, destino, antes, depois):
    info = {
        "origem": origem.name,
        "arquivo_prata": destino.name,
        "linhas_antes": antes,
        "linhas_depois": depois,
        "decisoes": [
            f"Filtrados so os clubes da liga {LIGA_BRASIL}.",
            "Descartadas colunas vazias ou sem uso: total_market_value, coach_name, filename.",
            "net_transfer_record convertido para numero em milhoes de euros.",
            "valor_mercado_elenco_mi_eur: soma do valor de mercado dos jogadores do elenco atual.",
        ],
        "transformado_em": datetime.now().isoformat(timespec="seconds"),
    }
    with (PRATA / "proveniencia.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(info, ensure_ascii=False) + "\n")


def main():
    df, origem = carregar()
    antes = len(df)
    df = filtrar_brasil(df)
    df = converter_saldo(df)
    df = valor_de_mercado(df)
    destino = salvar(df)
    registrar(origem, destino, antes, len(df))


if __name__ == "__main__":
    from config import configurar_log

    configurar_log()
    main()
