"""Integração com a API REST do Jira Cloud (criação de issues).

Usa apenas a biblioteca padrão do Python (urllib), sem novas dependências.
As credenciais NUNCA ficam no repositório:
  - Local: variáveis no arquivo .env (ignorado pelo .gitignore)
  - Streamlit Cloud: Settings -> Secrets -> JIRA_EMAIL / JIRA_API_TOKEN / JIRA_PROJECT_KEY
"""

import base64
import json
import os
import urllib.error
import urllib.request


def _ler_env():
    """Lê o arquivo .env (apenas leitura, nunca commitado). Semelha ao ia.py."""
    caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(caminho):
        return {}
    dados = {}
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            chave, _, valor = linha.partition("=")
            dados[chave.strip()] = valor.strip()
    return dados


def _env_var(nome, padrao=""):
    """Variável de ambiente, com fallback para o arquivo .env local."""
    valor = os.getenv(nome, "")
    if not valor:
        valor = _ler_env().get(nome, padrao)
    return valor


JIRA_BASE_URL = _env_var("JIRA_URL", "https://iagoqa.atlassian.net").rstrip("/")
JIRA_EMAIL = _env_var("JIRA_EMAIL")
JIRA_API_TOKEN = _env_var("JIRA_API_TOKEN")
JIRA_PROJECT_KEY = _env_var("JIRA_PROJECT_KEY")
JIRA_ISSUE_TYPE = _env_var("JIRA_ISSUE_TYPE", "Bug")

# Mapeia a gravidade da triagem para a prioridade padrão do Jira.
PRIORIDADES_JIRA = {
    "NORMAL": "Low",
    "MÉDIA": "Medium",
    "ALTA": "High",
    "CRÍTICA": "Highest",
}


def configurar(email="", token="", project_key="", issue_type=""):
    """Permite que o home.py injete credenciais digitadas no sidebar."""
    global JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT_KEY, JIRA_ISSUE_TYPE
    if email:
        JIRA_EMAIL = email
    if token:
        JIRA_API_TOKEN = token
    if project_key:
        JIRA_PROJECT_KEY = project_key
    if issue_type:
        JIRA_ISSUE_TYPE = issue_type


def configurado():
    return bool(JIRA_EMAIL and JIRA_API_TOKEN and JIRA_PROJECT_KEY)


def _headers():
    credencial = base64.b64encode(f"{JIRA_EMAIL}:{JIRA_API_TOKEN}".encode()).decode()
    return {
        "Authorization": f"Basic {credencial}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def prioridade_jira(gravidade):
    """Converte 'NORMAL ✅'/'CRÍTICA 🚨' para o nome aceito pelo Jira."""
    for chave, nome in PRIORIDADES_JIRA.items():
        if gravidade.upper().startswith(chave):
            return nome
    return "Medium"


def _montar_payload(resumo, descricao, prioridade):
    """Monta o corpo da requisição Jira no formato não-ADF (simple text)."""
    paragrafos = [p.strip() for p in descricao.splitlines() if p.strip()]
    conteudo = [{"type": "paragraph", "content": [{"type": "text", "text": p}]} for p in paragrafos]
    return {
        "fields": {
            "project": {"key": JIRA_PROJECT_KEY},
            "issuetype": {"name": JIRA_ISSUE_TYPE},
            "summary": resumo,
            "priority": {"name": prioridade},
            "description": {"type": "doc", "version": 1, "content": conteudo},
        }
    }


def criar_issue(resumo, descricao, gravidade="NORMAL", timeout=30):
    """Cria uma issue do tipo Bug no Jira.

    Retorna (ok, resultado, erro):
      - ok=True -> resultado = {"key": ..., "url": ...}
      - ok=False -> erro = mensagem legível da falha (HTTP/seeding, etc.)
    """
    if not configurado():
        return False, None, "Configure JIRA_EMAIL, JIRA_API_TOKEN e JIRA_PROJECT_KEY."
    payload = _montar_payload(resumo, descricao, prioridade_jira(gravidade))
    url = f"{JIRA_BASE_URL}/rest/api/3/issue"
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=_headers(),
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resposta:
            dados = json.loads(resposta.read().decode("utf-8"))
            chave = dados.get("key", "?")
            url_issue = f"{JIRA_BASE_URL}/browse/{chave}"
            return True, {"key": chave, "url": url_issue}, None
    except urllib.error.HTTPError as erro:
        corpo = erro.read().decode("utf-8", "ignore")
        return False, None, f"HTTP {erro.code}: {corpo[:300]}"
    except urllib.error.URLError as erro:
        return False, None, f"Erro de conexão: {erro.reason}"
    except Exception as erro:  # pragma: no cover
        return False, None, f"Erro inesperado: {erro}"


if __name__ == "__main__":
    ok, resultado, erro = criar_issue("Teste via script", "Issue de teste enviada sem GUI.")
    print("OK:", ok)
    print("Resultado:", resultado)
    print("Erro:", erro)