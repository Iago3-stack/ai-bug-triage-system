# Testes unitários do cliente Jira (jira_client.py)
# Roda com: pytest -v
# Confirma: mapeamento de prioridade, montagem do payload e falta de credenciais.

import pytest

import jira_client


# --- Mapeamento de prioridade (gravidade do app -> Jira) ---
def test_prioridade_normal_mapa_low():
    assert jira_client.prioridade_jira("NORMAL ✅") == "Low"


def test_prioridade_media_mapa_medium():
    assert jira_client.prioridade_jira("MÉDIA ⚠️") == "Medium"


def test_prioridade_alta_mapa_high():
    assert jira_client.prioridade_jira("ALTA 🚨") == "High"


def test_prioridade_critica_mapa_highest():
    assert jira_client.prioridade_jira("CRÍTICA 🚨") == "Highest"


def test_prioridade_desconhecida_cai_em_medium():
    assert jira_client.prioridade_jira("INVÁLIDA") == "Medium"


# --- Montagem do payload (sem rede) ---
def test_payload_usa_chave_do_projeto():
    jira_client.JIRA_PROJECT_KEY = "RD"
    payload = jira_client._montar_payload("Resumo", "Descrição", "Medium")
    assert payload["fields"]["project"]["key"] == "RD"


def test_payload_issue_tipo_bug():
    payload = jira_client._montar_payload("Resumo", "Descrição", "Medium")
    assert payload["fields"]["issuetype"]["name"] == "Bug"


def test_payload_transforma_linhas_em_paragrafos_adf():
    payload = jira_client._montar_payload("Resumo", "Linha 1\n\nLinha 2", "Medium")
    textos = [c["content"][0]["text"] for c in payload["fields"]["description"]["content"]]
    assert textos == ["Linha 1", "Linha 2"]


# --- Sem credenciais: falha amigável, sem rede ---
def test_criar_issue_sem_credenciais_retorna_erro():
    jira_client.JIRA_EMAIL = ""
    jira_client.JIRA_API_TOKEN = ""
    jira_client.JIRA_PROJECT_KEY = ""
    ok, resultado, erro = jira_client.criar_issue("T", "D", timeout=5)
    assert ok is False
    assert resultado is None
    assert "configure" in erro.lower()