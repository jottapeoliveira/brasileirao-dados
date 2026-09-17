import json
from datetime import datetime
from pathlib import Path
import pandas as pd
import limpeza  # Importando o módulo genérico que criamos

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

def padronizar_textos(df):
    """Usa o módulo de limpeza para padronizar as colunas de texto dos times."""
    df = limpeza.tirar_espacos(df)
    
    # Criando chaves de texto limpas para futuros cruzamentos (sem acento e minúsculo)
    if "home" in df.columns:
        df["home_limpo"] = limpeza.chave_texto(df["home"])
    if "away" in df.columns:
        df["away_limpo"] = limpeza.chave_texto(df["away"])
        
    return df

def criar_atributos_derivados(df):
    """Cria colunas novas que ajudam a responder à pergunta norteadora do projeto."""
    if "home_goal" in df.columns and "away_goal" in df.columns:
        df["total_gols"] = df["home_goal"] + df["away_goal"]
        df["saldo_gols_mandante"] = df["home_goal"] - df["away_goal"]
        
    print("Atributos derivados criados: total_gols, saldo_gols_mandante")
    return df

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
    df = padronizar_textos(df)
    df = criar_atributos_derivados(df)
    
    destino = salvar(df)
    
    registrar(origem, destino, antes_linhas, len(df), [
        "Colunas redundantes removidas.",
        "Textos padronizados com o módulo limpeza.py.",
        "Atributos derivados criados: total_gols e saldo_gols_mandante."
    ])

if __name__ == "__main__":
    main()