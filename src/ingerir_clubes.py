"""Bronze: baixa do Transfermarkt (Kaggle) o cadastro de clubes e o de jogadores, em copias datadas."""
import json
import logging
import os
import shutil
from datetime import date, datetime
from pathlib import Path

from config import ARQUIVO_CLUBES, ARQUIVO_JOGADORES, BRONZE_CLUBES, CACHE_KAGGLE, DATASET_CLUBES

log = logging.getLogger(__name__)

# arquivo no Kaggle -> prefixo da copia na bronze
ARQUIVOS = {ARQUIVO_CLUBES: "clubs", ARQUIVO_JOGADORES: "players"}


def baixar(arquivo):
    os.environ["KAGGLEHUB_CACHE"] = str(CACHE_KAGGLE)
    import kagglehub

    # path= baixa so o arquivo pedido, e nao o dataset inteiro (que tem centenas de MB)
    caminho = kagglehub.dataset_download(DATASET_CLUBES, path=arquivo)
    log.info("%s baixado em %s", arquivo, caminho)
    return Path(caminho)


def copiar(origem, prefixo):
    BRONZE_CLUBES.mkdir(parents=True, exist_ok=True)
    destino = BRONZE_CLUBES / f"{prefixo}_{date.today():%Y%m%d}.csv"
    shutil.copy(origem, destino)
    log.info("copiado para %s", destino.name)
    return destino


def registrar(copias):
    info = {
        "fonte": DATASET_CLUBES,
        "arquivos": {origem.name: destino.name for origem, destino in copias},
        "extraido_em": datetime.now().isoformat(timespec="seconds"),
    }
    (BRONZE_CLUBES / "proveniencia.json").write_text(
        json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def main():
    copias = []
    for arquivo, prefixo in ARQUIVOS.items():
        origem = baixar(arquivo)
        copias.append((origem, copiar(origem, prefixo)))
    registrar(copias)


if __name__ == "__main__":
    from config import configurar_log

    configurar_log()
    main()
