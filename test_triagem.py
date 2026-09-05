# Testes unitários do motor de triagem (triagem.py)
# Roda com: pytest -v
# Confirma: severidade, negação, ausência de falso-positivo e sentimento.

import pytest

from triagem import triar, _aplicar_lexico, _aplicar_negacoes


# --- Severidade: caso crítico (crash/login) ---
def test_crash_login_eh_critico():
    r = triar("o aplicativo está dando crash toda vez que tento fazer login")
    assert "CRÍTICA" in r["gravidade"]


def test_perda_de_dados_eh_critica():
    r = triar("perdi todos os meus dados depois do vazamento de segurança")
    assert "CRÍTICA" in r["gravidade"]


# --- Severidade: caso médio (frustração/negação) ---
def test_negacao_pagamento_eh_media_ou_critica():
    r = triar("não consigo pagar e estou muito frustrado")
    assert "MÉDIA" in r["gravidade"] or "CRÍTICA" in r["gravidade"]


def test_botao_nao_responde_eh_media_ou_critica():
    r = triar("o botão não responde quando tento salvar")
    assert "MÉDIA" in r["gravidade"] or "CRÍTICA" in r["gravidade"]


def test_botao_nao_funciona_eh_media():
    r = triar("o botão não funciona")
    assert "MÉDIA" in r["gravidade"]


# --- Falso-positivo: "erro" e "bug" são vocab de teste, não escalam sozinhos ---
def test_erro_de_digitacao_nao_dispara():
    r = triar("achei um erro de digitação no rodapé da página")
    assert "NORMAL" in r["gravidade"]


def test_bug_nao_dispara_sozinho():
    r = triar("encontrei um bug no rodapé da página inicial")
    assert "NORMAL" in r["gravidade"]


# --- Sentimentos ---
def test_frustracao_detecta_sentimento_negativo():
    r = triar("estou desesperado, isso é inaceitável")
    assert "Frustrado" in r["sentimento"] or "Negativo" in r["sentimento"]


def test_sucesso_retorna_normal_positivo():
    r = triar("a funcionalidade está funcionando perfeitamente, ótimo")
    assert "NORMAL" in r["gravidade"]
    assert "Satisfeito" in r["sentimento"]


# --- Motor offline/determinístico ---
def test_motor_eh_deterministico():
    r1 = triar("o app está travando ao abrir relatório")
    r2 = triar("o app está travando ao abrir relatório")
    assert r1 == r2


def test_motor_oferece_fatores():
    r = triar("não consigo salvar e o botão não responde")
    assert isinstance(r["fatores"], list)
    assert len(r["fatores"]) >= 1


# --- Funções internas (comportamento dos léxicos) ---
def test_aplicar_lexico_detecta_termos():
    score, acertos = _aplicar_lexico("isso está crashando todo dia")
    assert score < 0
    assert "crashando" in acertos


def test_aplicar_negacoes_detecta_padrao():
    score, acertos = _aplicar_negacoes("o botão não funciona")
    assert score < 0
    assert len(acertos) >= 1


# --- Lentidão por raiz (regex PADROES_LEXICO) ---
def test_lento_e_lenta_eh_media():
    assert "MÉDIA" in triar("o app ficou muito lento")["gravidade"]
    assert "MÉDIA" in triar("a página está lenta")["gravidade"]


def test_lentidao_flexoes_eh_media():
    r = triar("o aplicativo está lentíssimo hoje")
    assert "MÉDIA" in r["gravidade"]


def test_lente_nao_dispara_falso_positivo():
    r = triar("troquei a lente da câmera do aplicativo")
    assert "NORMAL" in r["gravidade"]


def test_lento_nao_conta_duplo():
    r = triar("o app está lento e carrega lentamente")
    assert r["score"] == -0.7
    assert sum(1 for f in r["fatores"] if "lent" in f) == 1


def test_lento_maiusculo_e_composto():
    r = triar("O sistema está LENTÍSSIMO e o botão não responde")
    assert "CRÍTICA" in r["gravidade"]
    assert any("lent" in f for f in r["fatores"])
