"""Caminhos e parametros do projeto. Nada aqui decide coisa alguma: so guarda valores."""
import logging
from pathlib import Path

# A raiz e calculada a partir deste arquivo, entao o projeto roda de qualquer pasta.
RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "dados"

BRONZE = DADOS / "bronze"
PRATA = DADOS / "prata"
OURO = DADOS / "ouro"

# Fonte 1: partidas do futebol brasileiro (Kaggle)
DATASET_PARTIDAS = "cuecacuela/brazilian-football-matches"
BRONZE_PARTIDAS = BRONZE / "brasileirao"
PADRAO_PARTIDAS = "partidas_*.csv"

# Fonte 2: cadastro de clubes do Transfermarkt (Kaggle)
DATASET_CLUBES = "davidcariboo/player-scores"
ARQUIVO_CLUBES = "clubs.csv"
ARQUIVO_JOGADORES = "players.csv"  # mesmo dataset: valor de mercado de cada jogador
BRONZE_CLUBES = BRONZE / "transfermarkt"
PADRAO_CLUBES = "clubs_*.csv"
PADRAO_JOGADORES = "players_*.csv"
LIGA_BRASIL = "BRA1"  # codigo da Serie A no Transfermarkt

# Cache do kagglehub fica dentro do projeto (e fora do Git)
CACHE_KAGGLE = DADOS / "cache" / "kagglehub"

# Banco da camada ouro
BANCO = OURO / "projeto.duckdb"
PASTA_DBT = RAIZ / "ecox14"


def configurar_log():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.FileHandler(RAIZ / "pipeline.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
