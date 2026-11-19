"""Painel da camada Ouro. So a tela: todo o SQL esta em consultas.py.

    streamlit run dashboard/painel.py
"""
import streamlit as st

import consultas

st.set_page_config(page_title="Brasileirão: o que decide a vitória", layout="wide")
st.title("O que decide a vitória no futebol brasileiro?")
st.write(
    "Estatísticas dentro de campo ou valor do elenco fora dele? "
    "Partidas de 2014 a 2023 com os dois clubes no cadastro do Transfermarkt."
)

# filtros
lista = consultas.campeonatos()["campeonato"].tolist()
limites = consultas.anos().iloc[0]
escolhidos = st.sidebar.multiselect("Campeonato", lista, default=["Serie A"])
ano_ini, ano_fim = st.sidebar.slider(
    "Anos", int(limites["primeiro"]), int(limites["ultimo"]),
    (int(limites["primeiro"]), int(limites["ultimo"])),
)
if not escolhidos:
    st.warning("Escolha ao menos um campeonato.")
    st.stop()
filtro = (escolhidos, ano_ini, ano_fim)

# números gerais
r = consultas.resumo(*filtro).iloc[0]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Partidas", int(r["partidas"]))
c2.metric("Vitórias do mandante", f"{r['pct_mandante']}%")
c3.metric("Empates", f"{r['pct_empate']}%")
c4.metric("Vitórias do visitante", f"{r['pct_visitante']}%")

# fora de campo
st.subheader("Fora de campo: valor de mercado do elenco")
valor = consultas.vitoria_por_valor_de_mercado(*filtro)
col1, col2 = st.columns([3, 2])
with col1:
    st.bar_chart(valor, x="faixa", y="pct_vitoria_mandante", horizontal=True,
                 x_label="", y_label="% de vitórias do mandante")
with col2:
    st.dataframe(valor, hide_index=True, width="stretch", column_config={
        "faixa": "Diferença de valor",
        "partidas": "Partidas",
        "pct_vitoria_mandante": st.column_config.NumberColumn("% vitória mandante", format="%.1f"),
    })
    st.caption("Faixa = quem tem o elenco mais caro e por quanto, em milhões de euros. "
               "Valor do elenco atual (2024/2025) aplicado a todas as temporadas: é uma aproximação.")

# dentro de campo
st.subheader("Dentro de campo: ter mais que o adversário ajuda?")
est = consultas.vitoria_por_estatistica(*filtro)
col1, col2 = st.columns([3, 2])
with col1:
    st.bar_chart(est, x="estatistica", y=["mandante_teve_mais", "mandante_teve_menos"],
                 stack=False, horizontal=True, x_label="", y_label="% de vitórias do mandante")
with col2:
    st.dataframe(est, hide_index=True, width="stretch", column_config={
        "estatistica": "Estatística",
        "mandante_teve_mais": st.column_config.NumberColumn("Teve mais (%)", format="%.1f"),
        "mandante_teve_menos": st.column_config.NumberColumn("Teve menos (%)", format="%.1f"),
        "partidas_com_dado": "Partidas",
    })
    st.caption("A base não tem posse de bola. Ataques entram como medida de domínio.")

# por clube
st.subheader("Valor do elenco e aproveitamento em casa, por clube")
st.dataframe(consultas.desempenho_por_clube(*filtro), hide_index=True, width="stretch", column_config={
    "clube": "Clube",
    "valor_elenco_mi_eur": st.column_config.NumberColumn("Valor do elenco (mi €)", format="%.1f"),
    "jogos_em_casa": "Jogos em casa",
    "pct_vitorias_em_casa": st.column_config.NumberColumn("% vitórias em casa", format="%.1f"),
    "media_gols_em_casa": st.column_config.NumberColumn("Gols por jogo em casa", format="%.2f"),
})

st.caption("Fontes: " + "; ".join(consultas.fontes()) + ". Dados lidos de dados/ouro/projeto.duckdb.")
