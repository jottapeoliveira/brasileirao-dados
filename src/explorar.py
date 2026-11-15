"""Perfil automatico das fontes da bronze (aula 4). Roda a parte, fora do pipeline."""
import logging

import pandas as pd
from data_profiling import ProfileReport

from config import BRONZE_CLUBES, BRONZE_PARTIDAS, PADRAO_CLUBES, PADRAO_PARTIDAS, RAIZ

log = logging.getLogger(__name__)

RELATORIOS = RAIZ / "relatorios"
FONTES = [(BRONZE_PARTIDAS, PADRAO_PARTIDAS), (BRONZE_CLUBES, PADRAO_CLUBES)]


def mais_recente(pasta, padrao):
    arquivos = sorted(pasta.glob(padrao))
    if not arquivos:
        raise FileNotFoundError(f"nada em {pasta}")
    return arquivos[-1]


def gerar(caminho):
    df = pd.read_csv(caminho)
    perfil = ProfileReport(df, title=caminho.name)
    RELATORIOS.mkdir(exist_ok=True)
    saida = RELATORIOS / f"{caminho.stem}.html"
    perfil.to_file(saida)
    return saida


def main():
    for pasta, padrao in FONTES:
        caminho = mais_recente(pasta, padrao)
        log.info("perfilando %s", caminho.name)
        log.info("relatorio em %s", gerar(caminho))


if __name__ == "__main__":
    from config import configurar_log

    configurar_log()
    main()
