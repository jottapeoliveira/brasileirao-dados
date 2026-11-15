"""Bronze: baixa as partidas do Kaggle e guarda uma copia datada, sem mexer no conteudo."""
import json
import logging
import os
import shutil
from datetime import date, datetime

from config import BRONZE_PARTIDAS, CACHE_KAGGLE, DATASET_PARTIDAS

log = logging.getLogger(__name__)


def baixar():
    os.environ["KAGGLEHUB_CACHE"] = str(CACHE_KAGGLE)
    import kagglehub

    pasta = kagglehub.dataset_download(DATASET_PARTIDAS)
    log.info("partidas baixadas em %s", pasta)
    return pasta


def localizar(pasta):
    from pathlib import Path

    arquivos = sorted(Path(pasta).glob("*.csv"))
    if not arquivos:
        raise FileNotFoundError(f"nenhum CSV em {pasta}")
    log.debug("encontrados: %s", [a.name for a in arquivos])
    return arquivos[0]


def copiar(origem):
    BRONZE_PARTIDAS.mkdir(parents=True, exist_ok=True)
    destino = BRONZE_PARTIDAS / f"partidas_{date.today():%Y%m%d}.csv"
    shutil.copy(origem, destino)
    log.info("copiado para %s", destino.name)
    return destino


def registrar(origem, destino):
    info = {
        "fonte": DATASET_PARTIDAS,
        "arquivo_origem": origem.name,
        "arquivo_bronze": destino.name,
        "extraido_em": datetime.now().isoformat(timespec="seconds"),
    }
    (BRONZE_PARTIDAS / "proveniencia.json").write_text(
        json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def main():
    origem = localizar(baixar())
    destino = copiar(origem)
    registrar(origem, destino)


if __name__ == "__main__":
    from config import configurar_log

    configurar_log()
    main()
