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
JIRA_ISSUE_TYPE = _env_var("JIRA_ISSUE_TYPE", "Tarefa")

# Mapeia a gravidade da triagem para a prioridade padrão do Jira.
PRIORIDADES_JIRA = {
    "NORMAL": "Low",
    "MÉDIA": "Medium",
    "ALTA": "High",
    "CRÍTICA": "Highest",
}


def _base_config():
    """Config padrão vinda de secrets/env/.env (jamais mutável pela sessão)."""
    return {
        "email": JIRA_EMAIL,
        "token": JIRA_API_TOKEN,
        "project_key": JIRA_PROJECT_KEY,
        "issue_type": JIRA_ISSUE_TYPE,
    }


def _resolver(config=None):
    """Mescla o que a sessão preencheu sobre os padrões de secrets/env/.env."""
    cfg = _base_config()
    if config:
        cfg.update({k: v for k, v in config.items() if v})
    return cfg


def configurar(email="", token="", project_key="", issue_type=""):
    """Devolve um dict de config por-sessão (fica em st.session_state, NUNCA em global).

    Nenhuma variável global do módulo é alterada — evita vazar credenciais
    entre sessões no Streamlit (processo único).
    """
    cfg = _base_config()
    if email:
        cfg["email"] = email.strip()
    if token:
        cfg["token"] = token.strip()
    if project_key:
        cfg["project_key"] = project_key.strip().upper()
    if issue_type:
        cfg["issue_type"] = issue_type.strip()
    return cfg


def limpar_config():
    """Sessão sem credenciais (inclusive ignorando secrets/env para trocar de conta)."""
    return {}


def configurado(config=None):
    """config None = usa padrões de secrets/env/.env; dict {} = explicitamente limpo."""
    if config is None:
        cfg = _base_config()
    elif not config:
        return False
    else:
        cfg = config
    return bool(cfg.get("email") and cfg.get("token") and cfg.get("project_key"))


def _headers(config=None):
    cfg = _resolver(config)
    credencial = base64.b64encode(f"{cfg['email']}:{cfg['token']}".encode()).decode()
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


def _montar_payload(resumo, descricao, prioridade, config=None):
    """Monta o corpo da requisição Jira no formato não-ADF (simple text)."""
    cfg = _resolver(config)
    paragrafos = [p.strip() for p in descricao.splitlines() if p.strip()]
    conteudo = [{"type": "paragraph", "content": [{"type": "text", "text": p}]} for p in paragrafos]
    return {
        "fields": {
            "project": {"key": cfg["project_key"].strip().upper()},
            "issuetype": {"name": cfg["issue_type"].strip()},
            "summary": resumo,
            "priority": {"name": prioridade},
            "description": {"type": "doc", "version": 1, "content": conteudo},
        }
    }


def criar_issue(resumo, descricao, gravidade="NORMAL", timeout=30, config=None):
    """Cria uma issue do tipo Bug no Jira.

    Retorna (ok, resultado, erro):
      - ok=True -> resultado = {"key": ..., "url": ...}
      - ok=False -> erro = mensagem legível da falha (HTTP/seeding, etc.)
    """
    if not configurado(config):
        return False, None, "Configure JIRA_EMAIL, JIRA_API_TOKEN e JIRA_PROJECT_KEY."
    payload = _montar_payload(resumo, descricao, prioridade_jira(gravidade), config=config)
    url = f"{JIRA_BASE_URL}/rest/api/3/issue"
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=_headers(config),
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