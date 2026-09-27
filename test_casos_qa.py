# Testes do ground truth (casos_qa.py). O corpus é a referência de TODA
# métrica de motor: se alguém edita um caso, o teste abaixo avisa.

import pytest

from casos_qa import CASOS, CASOS_ESTRITOS, N_CASOS, N_ESTRITOS

CANONICOS = {"CRÍTICA", "MÉDIA", "NORMAL"}


def test_contagens_do_corpus():
    assert N_CASOS == 30
    assert N_ESTRITOS == 23
    assert len(CASOS) == N_CASOS
    assert len(CASOS_ESTRITOS) == N_ESTRITOS


def test_todo_roteulo_e_canonico():
    for texto, esperados in CASOS:
        assert esperados, texto
        assert esperados <= CANONICOS, f"{esperados - CANONICOS} fora dos 3 níveis: {texto[:40]}"


def test_textos_sao_unicos_e_nao_vazios():
    textos = [t for t, _ in CASOS]
    assert all(t.strip() for t in textos)
    repetidos = {t for t in textos if textos.count(t) > 1}
    assert not repetidos, f"caso repetido (contaria 2x na métrica): {repetidos}"


def test_cada_classe_aparece_nos_casos_estritos():
    """Sem as 3 classes no treino, classificador não tem o que aprender."""
    rotulos = {r for _, e in CASOS_ESTRITOS for r in e}
    assert rotulos == CANONICOS


def test_ambiguos_sempre_tem_2_alternativas():
    for texto, esperados in CASOS:
        if len(esperados) > 1:
            assert len(esperados) == 2, texto


def test_ambiguos_estao_entre_niveis_adjacentes():
    """'MÉDIA ou ALTA' etc. — nunca 'CRÍTICA ou NORMAL' (seria ambiguidade de outro tipo)."""
    ordem = {"NORMAL": 0, "MÉDIA": 1, "CRÍTICA": 2}
    for texto, esperados in CASOS:
        if len(esperados) == 2:
            niveis = sorted(ordem[r] for r in esperados)
            assert niveis[1] - niveis[0] == 1, f"{esperados} não são adjacentes: {texto[:40]}"


@pytest.mark.parametrize("indice", range(N_CASOS))
def test_medir_ignora_previsao_ausente(indice):
    """medir() precisa contar um texto como errado, nunca como certo por omissão."""
    from avaliar_embeddings import medir  # noqa: PLC0415

    previsoes = ["NORMAL"] * N_CASOS
    previsoes[indice] = "SEVERIDADE_INEXISTENTE"
    tol, est = medir(previsoes)
    assert tol < N_CASOS and est < N_ESTRITOS
