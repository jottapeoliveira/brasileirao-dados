import json
from datetime import datetime
from pathlib import Path
import pandas as pd

BRONZE = Path("dados/bronze/brasileirao")
PRATA = Path("dados/prata")
PADRAO = "partidas_*.csv"

def carregar():
    arquivos = sorted(BRONZE.glob(PADRAO))
    if not arquivos:
        raise FileNotFoundError(f"nada em {BRONZE}")
    caminho = arquivos[-1]
    df = pd.read_csv(caminho)
    return df, caminho

def remover_redundantes(df):
    colunas_remover = ["total_corners", "at_diff", "ht_diff", "at_result"]
    return df.drop(columns=colunas_remover)

def salvar(df):
    PRATA.mkdir(parents=True, exist_ok=True)
    destino = PRATA / "partidas.parquet"
    df.to_parquet(destino, index=False)
    print("salvo em:", destino, df.shape)
    return destino

def registrar(origem, destino, antes, depois, decisoes):
    info = {
        "origem": origem.name,
        "arquivo_prata": destino.name,
        "linhas_antes": antes,
        "linhas_depois": depois,
        "decisoes": decisoes,
        "transformado_em": datetime.now().isoformat(timespec="seconds")
    }
    caminho = PRATA / "proveniencia.jsonl"
    with caminho.open("a", encoding="utf-8") as f:
        f.write(json.dumps(info, ensure_ascii=False) + "\n")

def main():
    df, origem = carregar()
    antes_linhas = len(df)
    
    df = remover_redundantes(df)
    destino = salvar(df)
    
    registrar(origem, destino, antes_linhas, len(df), [
        "Colunas redundantes (total_corners, at_diff, ht_diff, at_result) removidas."
    ])

if __name__ == "__main__":
    main()