"""Integração com a API REST do GitHub (criação de issues no repositório do usuário).

A API correta é `https://api.github.com/repos/{dono}/{repo}/issues` (POST), NÃO a
página `https://github.com/{dono}/repo/issues`. Usa apenas urllib (sem novas
dependências), como jira_client.py.

Segurança: o token e o repositório são SEMPRE do próprio usuário da sessão
(st.session_state), nunca persistidos em disco nem no banco — cada conta
configura o seu em ⚙️ Configurações.
"""

import json
import urllib.error
import urllib.request


def normalizar_repo(entrada=""):
    """Limpa 'dono/repo' de formatos copiados (URL completa, .git, espaços)."""
    texto = (entrada or "").strip().rstrip("/")
    for prefixo in (
        "https://github.com/",
        "http://github.com/",
        "www.github.com/",
        "github.com/",
    ):
        if texto.lower().startswith(prefixo):
            texto = texto[len(prefixo):]
    texto = texto.removesuffix(".git")
    partes = [p for p in texto.split("/") if p]
    if len(partes) == 2:
        return f"{partes[0]}/{partes[1]}"
    return texto


def configurado(config=None):
    """True quando a sessão tem token + repositório 'dono/repo' configurados."""
    config = config or {}
    token = (config.get("token") or "").strip()
    repo = normalizar_repo(config.get("repo"))
    return bool(token) and bool(repo) and "/" in repo


def _url_issues(repo):
    return f"https://api.github.com/repos/{repo}/issues"


def _headers(token):
    return {
        "Authorization": f"Bearer {token.strip()}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "ai-bug-triage-system",
    }


def criar_issue(config, titulo, corpo, timeout=30):
    """Cria uma issue no repositório configurado pelo usuário da sessão.

    Não envia labels de propósito (labels inexistentes no repo de destino
    retornam 422).

    Retorna (ok, resultado, erro):
      - ok=True  -> resultado = {"number": ..., "html_url": ...}
      - ok=False -> erro = mensagem legível da falha.
    """
    if not configurado(config):
        return False, None, "Configure seu token e repositório em ⚙️ Configurações."
    repo = normalizar_repo(config.get("repo"))
    payload = {"title": (titulo or "").strip(), "body": (corpo or "").strip()}
    request = urllib.request.Request(
        _url_issues(repo),
        data=json.dumps(payload).encode("utf-8"),
        headers=_headers(config.get("token")),
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resposta:
            dados = json.loads(resposta.read().decode("utf-8"))
            return (
                True,
                {
                    "number": dados.get("number", "?"),
                    "html_url": dados.get("html_url", ""),
                },
                None,
            )
    except urllib.error.HTTPError as erro:
        if erro.code == 404:
            msg = "Repositório não encontrado ou sem acesso — confira 'dono/repo' e o escopo do token."
        elif erro.code in (401, 403):
            msg = "Token inválido ou sem permissão 'Issues: write' neste repositório."
        else:
            corpo_erro = erro.read().decode("utf-8", "ignore")
            msg = f"HTTP {erro.code}: {corpo_erro[:300]}"
        return False, None, msg
    except urllib.error.URLError as erro:
        return False, None, f"Erro de conexão: {erro.reason}"
    except Exception as erro:  # pragma: no cover
        return False, None, f"Erro inesperado: {erro}"