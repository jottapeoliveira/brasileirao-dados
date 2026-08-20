import pandas as pd

caminho_partidas = "dados/bronze/partidas.csv"
caminho_clubes = "dados/bronze/clubs.csv"

df_partidas = pd.read_csv(caminho_partidas)
df_clubes = pd.read_csv(caminho_clubes)

print("--- DADOS DAS PARTIDAS ---")
print(df_partidas.head())

print("\n--- DADOS DOS CLUBES ---")
print(df_clubes.head())