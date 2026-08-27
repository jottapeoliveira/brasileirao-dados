# Projeto Brasileirão - Dados

Projeto focado na ingestão e estruturação de estatísticas do Campeonato Brasileiro.

## Fontes de Dados (Camada Bronze)

* **Partidas do Brasileirão:** Dados brutos baixados via Kaggle API.
  * Origem: `cuecacuela/brazilian-football-matches`
  * Script: `dados/bronze/ingerir.py`
* **Informações de Países:** Dados baixados via API Aberta (Banco Mundial).
  * Origem: `https://api.worldbank.org/v2/country`
  * Script: `dados/bronze/ingerir_paises.py`