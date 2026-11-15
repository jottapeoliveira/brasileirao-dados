"""Ferramentas de juncao: o de-para de nomes e a conferencia de contagens. Nao le nem grava arquivo."""
import logging

log = logging.getLogger(__name__)

# Nome do time nas partidas (ja passado pela chave_texto) -> club_id do Transfermarkt.
# As grafias diferem entre as fontes ("flamengo" x "Clube de Regatas do Flamengo"), por isso
# o mapeamento e feito a mao. Homonimos de outros estados ficam DE FORA de proposito:
# "botafogo sp", "botafogo pb", "santos ap", "vitoria es", "fluminense pi", "bragantino pa"...
DE_PARA_CLUBES = {
    "athletico paranaense": 679, "atletico paranaense": 679,  # mudou de grafia em 2019
    "atletico mineiro": 330,
    "botafogo rj": 537,
    "bragantino": 8793,                                      # virou Red Bull Bragantino em 2020
    "ceara": 2029,
    "chapecoense": 17776,
    "clube do remo": 10997, "remo": 10997, "remo pa": 10997,
    "corinthians": 199,
    "coritiba": 776, "coritiba pr": 776,
    "cruzeiro": 609,
    "ec bahia": 10010,
    "ec juventude": 10492, "juventude": 10492,
    "flamengo": 614,
    "fluminense": 2462, "fluminense rj": 2462,
    "fortaleza fc": 10870, "fortaleza ec": 10870,
    "gremio": 210, "gremio rs": 210,
    "internacional": 6600, "internacional rs": 6600,
    "mirassol": 3876,
    "palmeiras": 1023,
    "santos": 221,
    "sao paulo": 585,
    "sport recife": 8718,
    "vasco da gama rj": 978,
    "vitoria": 2125, "vitoria ec": 2125, "ec vitoria": 2125,
}


def conferir_chaves(esquerda, direita, nome):
    """Passo 1 da aula 7: prever o resultado da juncao antes de junta-la."""
    esq, dir_ = set(esquerda.dropna()), set(direita.dropna())
    log.info("%s: so na esquerda=%d, so na direita=%d, nos dois=%d",
             nome, len(esq - dir_), len(dir_ - esq), len(esq & dir_))
    return esq - dir_, dir_ - esq


def juntar(esquerda, direita, left_on, right_on, sufixo):
    """Left join que falha se a chave repetir na direita (validate)."""
    direita = direita.add_suffix(sufixo)
    return esquerda.merge(
        direita,
        left_on=left_on,
        right_on=right_on + sufixo,
        how="left",
        validate="many_to_one",
    )


def validar(antes, resultado, coluna_da_direita, nome):
    """Passo 3: a conta precisa fechar. Devolve as linhas que ficaram sem par."""
    sem_par = resultado[coluna_da_direita].isna()
    log.info("%s: antes=%d, resultado=%d, sem par=%d",
             nome, len(antes), len(resultado), int(sem_par.sum()))
    if len(resultado) != len(antes):
        raise ValueError(f"{nome}: o numero de linhas mudou na juncao")
    if sem_par.any():
        log.warning("%s: %d linhas sem par no cadastro", nome, int(sem_par.sum()))
    return resultado[sem_par]
