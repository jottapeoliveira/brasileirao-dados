# Projeto Brasileirão - Dados

Pipeline de dados sobre partidas do futebol brasileiro (Séries A, B, C e Copa do Brasil, 2014 a
2023), enriquecidas com o cadastro de clubes do Transfermarkt e modeladas em esquema estrela no
DuckDB.

```
Kaggle (partidas) ─┐                                          ┌─ ouro.dim_clube
                   ├─ bronze ─ prata ─ enriquecimento ─ carga ─ dbt ─┼─ ouro.fato_partida
Kaggle (clubes) ───┘   CSV     Parquet    Parquet       DuckDB       └─ ouro.vw_partida_completa
                                                                    │
                                                    dbt test (22 regras) → painel Streamlit (só lê)
```

## Tema e pergunta norteadora

**Tema:** fatores determinantes para a vitória no Brasileirão Série A: uma análise de
estatísticas de jogo e valor financeiro do elenco.

**Pergunta norteadora:** quais estatísticas dentro de campo (como maior posse de bola e volume de
finalizações no gol) e vantagens fora de campo (maior valor de mercado do elenco) possuem maior
influência na probabilidade de vitória de uma equipe em uma partida?

O que as fontes permitem responder hoje, e o que não:
* **Dentro de campo:** a base de partidas tem finalizações (`home_shots`), ataques
  (`home_attack`) e escanteios, mas **não tem posse de bola**. Ataques entram como a medida de
  domínio disponível.
* **Fora de campo:** o `total_market_value` do cadastro de clubes vem vazio para os clubes
  brasileiros. O valor de mercado do elenco é calculado somando o valor dos jogadores
  (`players.csv`, mesmo dataset do Transfermarkt). Idade média, estrangeiros, jogadores de seleção
  e saldo de transferências completam a `dim_clube`.
* **Vitória:** a `fato_partida` traz `resultado` (mandante, empate, visitante) e
  `vitoria_mandante` (verdadeiro ou falso), que é o que as outras colunas tentam explicar.

## Fontes de Dados (Camada Bronze)

* **Partidas:** dados brutos baixados via Kaggle API.
  * Origem: `cuecacuela/brazilian-football-matches`
  * Script: `src/ingerir.py` → `dados/bronze/brasileirao/partidas_AAAAMMDD.csv`
* **Clubes e jogadores (Transfermarkt):** baixados via Kaggle API, só os arquivos `clubs.csv` e
  `players.csv` (o dataset inteiro tem centenas de MB).
  * Origem: `davidcariboo/player-scores`
  * Script: `src/ingerir_clubes.py` → `dados/bronze/transfermarkt/clubs_AAAAMMDD.csv` e
    `players_AAAAMMDD.csv`

Cada pasta da bronze tem um `proveniencia.json` com a fonte e a data da extração.

## Defeitos conhecidos das fontes

### Partidas (Kaggle)
* Redundância: `total_corners` repete a informação de `home_corner` e `away_corner`.
* Redundância: Colunas de saldo e resultado (`at_diff`, `ht_diff`, `at_result`) são altamente correlacionadas com os gols.
* Dados ausentes: Aproximadamente 23% de valores nulos nas colunas de estatísticas (`home_attack`, `away_attack`, `home_shots`, `away_shots`).
* Zeros: Alta concentração de zeros nas colunas de gols e escanteios (comportamento normal da regra do esporte).
* Grafia: o mesmo clube aparece com nomes diferentes (`atletico paranaense` e `athletico paranaense`, `fortaleza fc` e `fortaleza ec`, `remo` e `clube do remo`).

### Clubes (Transfermarkt)
* O arquivo traz 796 clubes de 32 ligas; só 24 são da Série A brasileira (`domestic_competition_id = BRA1`).
* É um retrato atual (temporadas 2024 e 2025): idade média, elenco e estádio são os de hoje, não os da data de cada partida.
* `total_market_value` vem vazio para todos os clubes brasileiros.
* `net_transfer_record` vem como texto (`+€8.14m`, `€-2.84m`, `+-0`).
* No `players.csv`, jogador aposentado ou sem clube continua com o último `current_club_id`;
  o que o denuncia é o `last_season` antigo.

## Decisões de tratamento
### Partidas
* Colunas redundantes removidas: `total_corners`, `at_diff`, `ht_diff` e `at_result`. Motivo: a informação já existe na base pela soma ou diferença de outras variáveis.
* Valores ausentes em estatísticas numéricas foram mantidos. Motivo: a remoção descartaria aproximadamente 23% da base.
* `partida_id`: hash curto de `tournament`, `date`, `home` e `away`, combinação que não se repete na base. Usar hash, e não número de linha, faz o id não mudar se a fonte vier em outra ordem.

### Clubes
* Filtrados só os 24 clubes da liga `BRA1`.
* Descartadas `total_market_value` (vazia), `coach_name` e `filename`.
* `net_transfer_record` convertido para número em `saldo_transf_milhoes_eur` (`€-2.84m` → `-2.84`).
* `valor_mercado_elenco_mi_eur`: soma do `market_value_in_eur` dos jogadores cujo `current_club_id`
  é o clube **e** cujo `last_season` é a última temporada do clube (assim aposentados e ex-jogadores
  não entram). `jogadores_avaliados` conta quantos jogadores tinham valor informado.

## Atributos derivados
### total_gols
Soma dos gols marcados pelo mandante e pelo visitante na partida. Serve para analisar o volume ofensivo global de cada jogo do Brasileirão.

### saldo_gols_mandante
Diferença entre os gols do mandante e do visitante. Serve para medir a superioridade ou o desempenho do time da casa em relação ao visitante.

## Enriquecimento (junção de fontes)

Partidas juntadas ao cadastro de clubes duas vezes: uma pelo mandante, outra pelo visitante
(`src/enriquecer.py`, funções genéricas em `src/juncao.py`). Resultado em
`dados/prata/partidas_enriquecido.parquet`.

* **Grão:** à esquerda, uma linha por partida; à direita, uma linha por clube; no resultado,
  continua uma linha por partida (`validate="many_to_one"` garante que a chave não repete no
  cadastro).
* **Chave:** os nomes não batem entre as fontes ("flamengo" x "Clube de Regatas do Flamengo"),
  então um dicionário de-para (`juncao.DE_PARA_CLUBES`) traduz o nome limpo da partida para o
  `club_id` do Transfermarkt. Homônimos de outros estados ficam de fora de propósito:
  `botafogo sp`, `botafogo pb`, `santos ap`, `vitoria es`, `fluminense pi`, `bragantino pa`.
* **Tipo de junção:** `how="left"`, para que quem não casa fique visível.

| | mandante | visitante |
|---|---|---|
| Linhas antes | 10.296 | 10.296 |
| Linhas no resultado | 10.296 | 10.296 |
| Sem par no cadastro | 5.717 | 5.632 |

Partidas com os dois clubes no cadastro: **3.028** de 10.296.

### Quem não casou
São 251 nomes de times sem cadastro, em três grupos:
* **Clubes de Série B, C e Copa do Brasil** que não estão na Série A atual do Transfermarkt
  (CRB, Sampaio Corrêa, Vila Nova, Náutico, Londrina, Paysandu...). Universos diferentes: não se
  resolve, documenta-se.
* **Ex-clubes de Série A rebaixados antes de 2024**: América-MG, Atlético-GO, Avaí, Criciúma,
  CSA, Cuiabá, Figueirense, Goiás, Joinville, Paraná, Ponte Preta e Santa Cruz. Jogaram a Série A
  no período, mas o cadastro só traz quem está nela hoje. É a principal razão das 1.130 partidas
  de Série A sem os dois clubes.
* **Homônimos de outros estados** (`botafogo sp`, `santos ap`...), deixados sem par de propósito
  para não atribuir a eles os dados de outro clube.

Na base, 4.081 partidas não têm nenhum dos dois clubes no cadastro e 3.187 têm só um.

Curiosidade da fonte: `brasilia fc` e `ca taguatinga` aparecem com `tournament = Serie A`, o que
indica erro de rótulo no Kaggle.

### Atributos que só existem depois da junção
* **dif_idade_media:** idade média do elenco do mandante menos a do visitante. Responde à parte
  "vantagens fora de campo" da pergunta norteadora: permite ver se o elenco mais experiente vence
  mais. Como o cadastro é atual, vale como aproximação para as temporadas recentes.
* **capacidade_estadio_mandante:** lugares no estádio do mandante. Outra vantagem fora de campo:
  permite testar se o fator casa pesa mais em estádios maiores.
* **dif_valor_mercado_mi_eur:** valor de mercado do elenco do mandante menos o do visitante, em
  milhões de euros. É a "vantagem fora de campo" principal da pergunta norteadora: positivo quando
  o mandante tem o elenco mais caro. Também é um retrato atual do elenco.

## Como executar

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

python src/pipeline.py                  # tudo, desde o Kaggle
python src/pipeline.py transformacao    # retoma do meio, sem baixar de novo
python src/pipeline.py modelagem        # só o dbt: constrói a ouro e roda os testes

streamlit run dashboard/painel.py       # o painel, depois do pipeline (Ctrl+C para parar)
```

As etapas, em ordem: `ingestao`, `transformacao`, `enriquecimento`, `carga`, `modelagem`.
Precisa do `kaggle.json` na pasta `.kaggle` do usuário para a ingestão.

## Configuração (`src/config.py`)

Caminhos (calculados a partir do próprio arquivo, então o projeto roda de qualquer pasta), nomes
dos datasets, código da liga e a função `configurar_log`. Nenhuma lógica e nenhum segredo.

Quem importa quem: `pipeline` importa as etapas; as etapas importam `config`, `limpeza` e
`juncao`; `config`, `limpeza` e `juncao` não importam ninguém.

## Log (`pipeline.log`)

Toda etapa usa `logging` em vez de `print`: a mensagem sai na tela e no `pipeline.log` (fora do
Git), com hora, nível e módulo. `WARNING` marca o que é estranho mas não para o pipeline, como as
linhas sem par na junção. Se uma etapa falhar, `log.exception` grava o erro com a linha exata e o
pipeline para.

## Modelagem (camada Ouro)

As camadas viram esquemas no `dados/ouro/projeto.duckdb`: `prata` (as três tabelas Parquet,
carregadas pelo `src/carga.py`) e `ouro` (construída pelo dbt).

### O grão de cada tabela
* **`ouro.dim_clube`:** uma linha por clube do cadastro do Transfermarkt (24 linhas).
* **`ouro.fato_partida`:** uma linha por partida, ou seja, um campeonato, uma data, um mandante
  e um visitante (3.028 linhas). Chave: `partida_id`.
* **`ouro.vw_partida_completa`:** view, mesma linha da fato com os nomes dos clubes.

### Como as tabelas se ligam
```
             dim_clube (clube_id)
              ▲                ▲
clube_mandante_id      clube_visitante_id
              └── fato_partida ──┘
```
A dimensão entra duas vezes, uma para cada papel do clube na partida.

### Decisões de modelagem
* **Filtro de integridade:** a fato só tem partidas com os dois clubes no cadastro
  (`club_id_mandante` e `club_id_visitante` não nulos), herança direta da junção. As 7.268
  partidas sem um dos clubes continuam na prata.
* **Variável de resultado:** `resultado` e `vitoria_mandante` saem dos gols na própria fato, para
  que a pergunta norteadora seja respondida com um `GROUP BY`, sem recalcular nada.
* **Nomes de negócio:** a ouro troca os nomes da fonte (`home_goal`, `ht_result`) por nomes que
  uma pessoa entende (`gols_mandante`, `resultado_intervalo`).
* **Tipos:** gols viram inteiro e a data vira `DATE`.
* **Sem `dim_tempo`:** a data está na fato e basta para as perguntas do projeto.

### Conferências da ouro
Desde a aula 11 são testes do dbt (ver "Testes do dado" abaixo). As consultas da aula 9 ficaram
em `carga.conferir`, sem ser chamadas, para comparar.

### Exemplo de consulta para a pergunta norteadora
O mandante vence mais quando tem o elenco mais caro?
```sql
SELECT
    dif_valor_mercado_mi_eur > 0              AS mandante_mais_caro,
    COUNT(*)                                  AS partidas,
    ROUND(AVG(vitoria_mandante::INT) * 100, 1) AS pct_vitoria_mandante
FROM ouro.fato_partida
WHERE campeonato = 'Serie A' AND dif_valor_mercado_mi_eur IS NOT NULL
GROUP BY 1;
```

## Transformação declarativa (dbt)

A construção da ouro saiu do `carga.py` e virou o projeto dbt em `ecox14/`. Ler os Parquet e
abrir o banco continuam em Python, porque não são transformação.

```
ecox14/
  dbt_project.yml          nome, pastas, materialização padrão (tabela)
  profiles.yml             como conectar: ../dados/ouro/projeto.duckdb, esquema ouro
  models/
    sources.yml            prata.clubes e prata.partidas_enriquecido
    dim_clube.sql          tabela
    fato_partida.sql       tabela
    vw_partida_completa.sql view, usa ref nos dois modelos
```

* **`profiles.yml` dentro do repositório**, com caminho relativo, em vez de
  `C:\Users\<usuario>\.dbt`: o projeto roda em qualquer máquina sem editar nada, e o arquivo não
  tem senha.
* **O pipeline chama `python -m dbt.cli.main run` e depois `test`** com o mesmo Python do
  pipeline, com `check=True`: se o dbt falhar ou um teste falhar, o pipeline para.
* **`construir_ouro` ficou comentada no `carga.py`** para comparar as duas formas.
* **Verificação da migração:** a ouro do dbt foi comparada com a do SQL antigo (`EXCEPT` nos dois
  sentidos): 24, 3.028 e 3.028 linhas, zero diferença.

```
cd ecox14
dbt debug                        # mostra qual profiles.yml lê e testa a conexão
dbt run                          # constrói os 3 modelos
dbt run --select dim_clube+      # só a dimensão e o que depende dela
```

`Database Error: file is locked` significa que o banco está aberto em outro lugar (um notebook,
outro terminal): feche a outra conexão e rode de novo.

## Testes do dado

Um teste é uma consulta que precisa devolver **zero linhas**: ele procura o defeito, e passar é não
achar nada. Os testes rodam na etapa `modelagem`, logo depois do `dbt run`, e se um falhar o
pipeline para. As conferências que antes só imprimiam um número no log viraram regras cobradas.

**Testes prontos** (declarados em `ecox14/models/schema.yml`, o dbt escreve o SQL):

| Coluna | Regra |
|---|---|
| `dim_clube.clube_id` | `unique`, `not_null` |
| `dim_clube.nome`, `valor_mercado_elenco_mi_eur` | `not_null` |
| `fato_partida.partida_id` | `unique`, `not_null` |
| `fato_partida.clube_mandante_id`, `clube_visitante_id` | `not_null`, `relationships` com `dim_clube` (nenhum fato órfão) |
| `fato_partida.campeonato` | `accepted_values`: Serie A, B, C, Copa do Brasil |
| `fato_partida.resultado` | `accepted_values`: mandante, empate, visitante |
| `fato_partida.resultado_intervalo` | `accepted_values`: WON, DRAW, LOST |
| `fato_partida.data`, gols, `vitoria_mandante` | `not_null` |
| `vw_partida_completa.partida_id` | `unique` |

**Testes escritos à mão** (`ecox14/tests/`), para o que nenhum teste pronto cobre:
* `grao_fato_partida.sql`: o grão composto (campeonato, data, mandante, visitante) não se repete.
* `view_mesmo_tamanho_da_fato.sql`: a view, que junta a `dim_clube` duas vezes, não ganha nem perde
  partidas.
* `gols_coerentes.sql`: `total_gols`, `saldo_gols_mandante` e `resultado` batem com os gols, e
  nenhum gol é negativo.

Total: 22 testes, todos passando. Foi conferido que um erro proposital no `fato_partida.sql` faz
dois testes falharem e o pipeline parar.

```
cd ecox14
dbt test                                           # roda os 22
dbt test --select fato_partida                     # só os da fato
dbt test --select gols_coerentes --store-failures  # grava as linhas que falharam, para investigar
```

## Documentação (dbt docs)

As descrições de tabelas e colunas estão no mesmo `schema.yml` dos testes, então não ficam
desatualizadas: se o modelo muda, a descrição está ao lado.

```
cd ecox14
dbt docs generate
dbt docs serve        # abre o site com o grafo dos modelos e a descrição de cada coluna
```

Para ver as linhas de verdade, a interface do DuckDB (o `duckdb.exe`, baixado de duckdb.org,
fica na raiz e fora do Git):

```
.\duckdb.exe -ui dados/ouro/projeto.duckdb     # abre em localhost:4213
```

Feche o painel e o pipeline antes: o DuckDB trava o arquivo.

## Painel (Streamlit)

O painel é **consumidor**: lê a ouro e não escreve nada, por isso fica fora do pipeline, na pasta
`dashboard/`, e abre o banco com `read_only=True` (não trava o dbt, e o banco recusa qualquer
consulta que altere dado).

```
dashboard/
  consultas.py    todo o SQL de leitura, uma função por pergunta, valores sempre como parâmetro (?)
  painel.py       só a tela, sem nenhuma linha de SQL
```

O que a tela mostra, com filtro de campeonato e de anos:
* **Números gerais:** partidas e percentual de vitória do mandante, empate e visitante.
* **Fora de campo:** % de vitória do mandante por faixa de diferença de valor do elenco.
* **Dentro de campo:** % de vitória do mandante quando teve mais ou menos finalizações, ataques e
  escanteios que o visitante.
* **Por clube:** valor do elenco ao lado do aproveitamento em casa.
* **Rodapé:** as fontes e a data de extração, lidas da proveniência da bronze.

### O que os dados mostram (Série A, 2014 a 2023, 2.559 partidas)

| Diferença de valor do elenco | Partidas | % vitória do mandante |
|---|---|---|
| visitante mais de 100 mi € mais caro | 322 | 36,0 |
| visitante 30 a 100 mi € mais caro | 608 | 43,6 |
| elencos parecidos (até 30 mi €) | 698 | 54,7 |
| mandante 30 a 100 mi € mais caro | 607 | 50,2 |
| mandante mais de 100 mi € mais caro | 324 | 59,3 |

* **Fora de campo, o valor do elenco pesa:** o mandante vence 36% quando o visitante é muito mais
  caro e 59% quando ele é que é muito mais caro.
* **Dentro de campo, o sinal se inverte:** o mandante vence 57% das partidas em que teve **menos**
  ataques ou escanteios, e 41% a 45% das que teve mais. A explicação provável é o efeito placar:
  quem está perdendo ataca mais, e quem está ganhando recua. Finalizações quase não separam (48% x
  46%). Ou seja, estatística de volume mede como o jogo se desenrolou, não o que o decidiu.
* **Cautela:** o valor do elenco é o atual, aplicado a temporadas antigas, e Ceará, Fortaleza,
  Juventude e Sport têm só 4 a 8 jogadores com valor no cadastro, então o valor deles está
  subestimado. A base não tem posse de bola nem chutes no gol.

## Governança

* **De onde veio cada número:** a proveniência é gravada desde a ingestão (`proveniencia.json` na
  bronze e `proveniencia.jsonl` na prata) e o painel mostra a fonte no rodapé.
* **Quem pode ver:** o projeto só usa dados públicos e agregados por clube e partida; o banco e o
  painel rodam na máquina local.
* **Dado pessoal (LGPD):** o `players.csv` tem nome e data de nascimento de jogadores, mas o
  projeto só usa o valor de mercado **somado por clube**; nenhum dado de jogador chega à prata
  agregada nem à ouro. Com dado pessoal de verdade, o certo seria coletar só o necessário, dizer
  para que serve, ter prazo de descarte e controlar quem acessa.
* **Se um número estiver errado:** os 22 testes impedem que a ouro seja publicada quebrada, e
  como bronze, prata e ouro ficam guardadas, dá para refazer o cálculo de qualquer número.
