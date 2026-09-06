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


def test_payload_issue_tipo_bug(monkeypatch):
    monkeypatch.setattr(jira_client, "JIRA_ISSUE_TYPE", "Bug")
    payload = jira_client._montar_payload("Resumo", "Descrição", "Medium")
    assert payload["fields"]["issuetype"]["name"] == "Bug"


def test_payload_transforma_linhas_em_paragrafos_adf():
    payload = jira_client._montar_payload("Resumo", "Linha 1\n\nLinha 2", "Medium")
    textos = [c["content"][0]["text"] for c in payload["fields"]["description"]["content"]]
    assert textos == ["Linha 1", "Linha 2"]


# --- Leitura de credenciais (variável de ambiente com fallback no .env) ---
def test_env_var_cai_no_env_quando_falta_variavel(monkeypatch):
    monkeypatch.setattr("os.getenv", lambda nome, padrao="": "")
    monkeypatch.setattr(jira_client, "_ler_env", lambda: {"JIRA_PROJECT_KEY": "KAN"})
    assert jira_client._env_var("JIRA_PROJECT_KEY") == "KAN"


def test_env_var_prioriza_variavel_de_ambiente(monkeypatch):
    monkeypatch.setattr("os.getenv", lambda nome, padrao="": "XPTO")
    monkeypatch.setattr(jira_client, "_ler_env", lambda: {"JIRA_PROJECT_KEY": "KAN"})
    assert jira_client._env_var("JIRA_PROJECT_KEY") == "XPTO"


def test_configurado_true_quando_preenche_tudo(monkeypatch):
    for attr, valor in [("JIRA_EMAIL", "a@b.com"), ("JIRA_API_TOKEN", "tok"), ("JIRA_PROJECT_KEY", "KAN")]:
        monkeypatch.setattr(jira_client, attr, valor)
    assert jira_client.configurado() is True


def test_configurado_false_com_algum_campo_vazio(monkeypatch):
    for attr, valor in [("JIRA_EMAIL", "a@b.com"), ("JIRA_API_TOKEN", ""), ("JIRA_PROJECT_KEY", "KAN")]:
        monkeypatch.setattr(jira_client, attr, valor)
    assert jira_client.configurado() is False


# --- Normalização de entradas digitadas no sidebar ---
def test_configurar_normaliza_chave_do_projeto(monkeypatch):
    monkeypatch.setattr(jira_client, "JIRA_PROJECT_KEY", "xpto")
    jira_client.configurar(project_key="  kan  ")
    assert jira_client.JIRA_PROJECT_KEY == "KAN"


def test_payload_normaliza_chave_inclusive_com_espacos():
    jira_client.JIRA_PROJECT_KEY = " kan "
    payload = jira_client._montar_payload("R", "D", "Medium")
    assert payload["fields"]["project"]["key"] == "KAN"


# --- Sem credenciais: falha amigável, sem rede ---
def test_criar_issue_sem_credenciais_retorna_erro():
    jira_client.JIRA_EMAIL = ""
    jira_client.JIRA_API_TOKEN = ""
    jira_client.JIRA_PROJECT_KEY = ""
    ok, resultado, erro = jira_client.criar_issue("T", "D", timeout=5)
    assert ok is False
    assert resultado is None
    assert "configure" in erro.lower()