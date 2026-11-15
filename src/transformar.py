"""Prata: partidas. Remove redundancias, padroniza textos, cria atributos e o identificador da partida."""
import hashlib
import json
import logging
from datetime import datetime

import pandas as pd

import limpeza
from config import BRONZE_PARTIDAS, PADRAO_PARTIDAS, PRATA

log = logging.getLogger(__name__)

COLUNAS_REDUNDANTES = ["total_corners", "at_diff", "ht_diff", "at_result"]
CHAVE = ["tournament", "date", "home", "away"]  # combinacao unica, conferida na aula 5


def carregar():
    arquivos = sorted(BRONZE_PARTIDAS.glob(PADRAO_PARTIDAS))
    if not arquivos:
        raise FileNotFoundError(f"nada em {BRONZE_PARTIDAS}")
    caminho = arquivos[-1]
    df = pd.read_csv(caminho)
    log.info("partidas: %d linhas lidas de %s", len(df), caminho.name)
    return df, caminho


def remover_redundantes(df):
    return df.drop(columns=COLUNAS_REDUNDANTES)


def padronizar_textos(df):
    df = limpeza.tirar_espacos(df)
    df["home_limpo"] = limpeza.chave_texto(df["home"])
    df["away_limpo"] = limpeza.chave_texto(df["away"])
    return df


def criar_atributos_derivados(df):
    df["total_gols"] = df["home_goal"] + df["away_goal"]
    df["saldo_gols_mandante"] = df["home_goal"] - df["away_goal"]
    return df


def criar_id(df):
    """partida_id: hash curto da chave. Nao muda se a fonte for baixada de novo em outra ordem."""
    duplicadas = df.duplicated(CHAVE).sum()
    if duplicadas:
        raise ValueError(f"{duplicadas} partidas repetidas na chave {CHAVE}")
    texto = df[CHAVE].astype(str).agg("|".join, axis=1)
    df.insert(0, "partida_id", texto.map(lambda t: hashlib.md5(t.encode()).hexdigest()[:12]))
    return df


def salvar(df):
    PRATA.mkdir(parents=True, exist_ok=True)
    destino = PRATA / "partidas.parquet"
    df.to_parquet(destino, index=False)
    log.info("partidas: %d linhas, %d colunas salvas em %s", *df.shape, destino.name)
    return destino


def registrar(origem, destino, antes, depois, decisoes):
    info = {
        "origem": origem.name,
        "arquivo_prata": destino.name,
        "linhas_antes": antes,
        "linhas_depois": depois,
        "decisoes": decisoes,
        "transformado_em": datetime.now().isoformat(timespec="seconds"),
    }
    with (PRATA / "proveniencia.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(info, ensure_ascii=False) + "\n")


def main():
    df, origem = carregar()
    antes = len(df)

    df = remover_redundantes(df)
    df = padronizar_textos(df)
    df = criar_atributos_derivados(df)
    df = criar_id(df)

    destino = salvar(df)
    registrar(origem, destino, antes, len(df), [
        "Colunas redundantes removidas: " + ", ".join(COLUNAS_REDUNDANTES),
        "Textos padronizados com o modulo limpeza.py.",
        "Atributos derivados: total_gols e saldo_gols_mandante.",
        "partida_id criado a partir de " + ", ".join(CHAVE),
    ])


if __name__ == "__main__":
    from config import configurar_log

    configurar_log()
    main()
