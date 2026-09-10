# Projeto Brasileirão - Dados

Projeto focado na ingestão e estruturação de estatísticas do Campeonato Brasileiro.

## Fontes de Dados (Camada Bronze)

* **Partidas do Brasileirão:** Dados brutos baixados via Kaggle API.
  * Origem: `cuecacuela/brazilian-football-matches`
  * Script: `dados/bronze/ingerir.py`
* **Informações de Países:** Dados baixados via API Aberta (Banco Mundial).
  * Origem: `https://api.worldbank.org/v2/country`
  * Script: `dados/bronze/ingerir_paises.py`

## Defeitos conhecidos das fontes

### Brasileirão (Kaggle)
* Redundância: `total_corners` repete a informação de `home_corner` e `away_corner`.
* Redundância: Colunas de saldo e resultado (`at_diff`, `ht_diff`, `at_result`) são altamente correlacionadas com os gols.
* Dados ausentes: Aproximadamente 23% de valores nulos nas colunas de estatísticas (`home_attack`, `away_attack`, `home_shots`, `away_shots`).
* Zeros: Alta concentração de zeros nas colunas de gols e escanteios (comportamento normal da regra do esporte).