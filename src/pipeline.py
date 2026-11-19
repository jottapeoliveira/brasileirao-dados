"""Roda o projeto do inicio ao fim, ou a partir de uma etapa.

    python src/pipeline.py                  # tudo, desde o Kaggle
    python src/pipeline.py transformacao    # retoma do meio, sem baixar de novo
"""
import logging
import subprocess
import sys
import time

import config

log = logging.getLogger(__name__)


# O import fica dentro de cada funcao: erro de import em uma etapa nao derruba as outras.
def etapa_ingestao():
    import ingerir
    import ingerir_clubes

    ingerir.main()
    ingerir_clubes.main()


def etapa_transformacao():
    import transformar
    import transformar_clubes

    transformar.main()
    transformar_clubes.main()


def etapa_enriquecimento():
    import enriquecer

    enriquecer.main()


def etapa_carga():
    import carga

    carga.main()


def dbt(comando):
    # mesmo Python do pipeline: nao depende do PATH nem de ativar o ambiente virtual
    subprocess.run(
        [sys.executable, "-m", "dbt.cli.main", comando],
        cwd=config.PASTA_DBT,
        check=True,  # se o dbt falhar, o pipeline para em vez de dizer que deu certo
    )


def etapa_modelagem():
    dbt("run")   # constroi a ouro
    dbt("test")  # cobra as regras do schema.yml e de tests/; teste que falha para o pipeline


ETAPAS = [
    ("ingestao", etapa_ingestao),
    ("transformacao", etapa_transformacao),
    ("enriquecimento", etapa_enriquecimento),
    ("carga", etapa_carga),
    ("modelagem", etapa_modelagem),
]


def executar(nome, funcao):
    log.info("etapa %s: inicio", nome)
    comeco = time.time()
    try:
        funcao()
    except Exception:
        log.exception("etapa %s falhou", nome)
        raise
    log.info("etapa %s: fim em %.0fs", nome, time.time() - comeco)


def main(a_partir_de=None):
    config.configurar_log()
    nomes = [nome for nome, _ in ETAPAS]
    if a_partir_de is not None and a_partir_de not in nomes:
        raise SystemExit(f"etapa desconhecida: {a_partir_de}. Use uma de: {', '.join(nomes)}")

    comecou = a_partir_de is None
    for nome, funcao in ETAPAS:
        if nome == a_partir_de:
            comecou = True
        if not comecou or funcao is None:
            log.info("etapa %s: pulada", nome)
            continue
        executar(nome, funcao)
    log.info("pipeline concluido")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
