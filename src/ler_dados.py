import pandas as pd

# 1. Mapear o caminho onde os arquivos estão
caminho_partidas = "dados/bronze/partidas.csv"
caminho_clubes = "dados/bronze/clubs.csv"

# 2. Pedir para o Pandas ler os CSVs
df_partidas = pd.read_csv(caminho_partidas)
df_clubes = pd.read_csv(caminho_clubes)

# 3. Mostrar as 5 primeiras linhas de cada tabela no terminal
print("--- DADOS DAS PARTIDAS ---")
print(df_partidas.head())

print("\n--- DADOS DOS CLUBES ---")
print(df_clubes.head())