# Autenticação via Supabase Auth (GoTrue REST).
#
# V2.6.16 — passo 2 do caminho SaaS: login real de usuários. Usa o MESMO projeto
# Supabase da persistência (`nuvem_supabase`), então as credenciais são as mesmas:
#   - Streamlit Cloud: Settings -> Secrets -> SUPABASE_URL / SUPABASE_ANON_KEY
#   - Local: arquivo .env (gitignored)
#
# Endpoints usados (https://<projeto>.supabase.co/auth/v1):
#   POST /signup                     -> cria conta (+ e-mail de confirmação)
#   POST /token (grant_type=password)-> login (access_token + refresh_token + user)
#   POST /logout                     -> invalida a sessão
#
# Nenhum dado sensível vai para o repositório; chaves ficam em secrets/.env.
# Requisito no painel do Supabase: Authentication -> Providers -> Email habilitado.
# Com "Confirm email" ativo, o cadastro exige confirmação antes do 1º login.

import json
import os

import requests

from nuvem_supabase import _config

_SESSAO_KEY = "_auth_sessao"

_ARMARIO: dict = {}


def _armazem():
    """st.session_state em runtime; dict simples fora dele (testes)."""
    try:
        import streamlit as st

        return st.session_state
    except Exception:
        return _ARMARIO


def _mensagem_erro(status: int, texto: str) -> str:
    """Traduz o erro do GoTrue em uma mensagem amigável em pt-BR."""
    detalhe = ""
    erro = ""
    try:
        dados = json.loads(texto)
    except Exception:
        dados = None
    if dados:
        detalhe = (
            dados.get("error_description")
            or dados.get("message")
            or dados.get("msg")
            or ""
        )
        erro = str(dados.get("error") or dados.get("error_code") or "")
    baixo = (str(detalhe) + " " + erro).lower()
    if "email_not_confirmed" in baixo:
        return "Confirme seu e-mail antes de entrar (veja a caixa de entrada)."
    if "invalid_grant" in baixo or "invalid login credentials" in baixo:
        return "E-mail ou senha inválidos."
    if status == 429 or "rate" in baixo or "signups are disabled" in baixo:
        if "disabled" in baixo or "signup" in baixo:
            return (
                "Cadastro por e-mail está desativado no Supabase — ative "
                "'Enable email signups' (Auth → Sign In / Providers → Email)."
            )
        if "over_email_send_rate_limit" in erro or "email rate limit" in baixo:
            return (
                "Limite de e-mails de confirmação atingido (Supabase): aguarde até 1 hora "
                "ou configure SMTP próprio (Auth → Emails → SMTP) para enviar sem esse limite."
            )
        return "Muitas tentativas em sequência. Aguarde ~1 minuto e tente de novo."
    if status == 422 or "already" in baixo:
        return "Este e-mail já está cadastrado — tente fazer login."
    if detalhe:
        return f"Erro: {detalhe}"
    return f"Falha inesperada (código {status})."


def disponivel() -> bool:
    return _config() is not None


def _base_auth_url() -> str:
    url, _ = _config()
    return str(url).rstrip("/") + "/auth/v1"


def _headers_anon() -> dict:
    _, chave = _config()
    return {
        "apikey": chave,
        "Content-Type": "application/json",
    }


def _headers_auth(token: str) -> dict:
    headers = _headers_anon()
    headers["Authorization"] = f"Bearer {token}"
    return headers


def _valida_email_senha(email: str, senha: str) -> tuple[bool, str]:
    email = (email or "").strip()
    if not email or "@" not in email or "." not in email.split("@")[-1]:
        return False, "Informe um e-mail válido."
    if len(senha or "") < 8:
        return False, "A senha precisa ter pelo menos 8 caracteres."
    return True, ""


def cadastrar(email: str, senha: str) -> tuple[bool, str, dict | None]:
    """Cria a conta. Retorna (ok, mensagem, dados). Sucesso pode exigir confirmação de e-mail."""
    if not disponivel():
        return False, "Supabase não configurado neste ambiente (sem SUPABASE_URL/ANON_KEY).", None
    ok, msg = _valida_email_senha(email, senha)
    if not ok:
        return False, msg, None
    payload = {"email": email.strip().lower(), "password": senha}
    try:
        resposta = requests.post(
            f"{_base_auth_url()}/signup",
            json=payload,
            headers=_headers_anon(),
            timeout=15,
        )
    except requests.RequestException:
        return False, "Falha de rede ao criar a conta. Tente de novo.", None

    dados = resposta.json() if resposta.text else {}
    if resposta.status_code in (200, 201):
        user = dados.get("user") or ({"email": dados.get("email")} if dados.get("email") else None)
        if user and (user.get("confirmed_at") or user.get("email_confirmed_at")):
            return True, "Conta criada! Você já pode entrar.", dados
        return True, "Conta criada! Confirme o e-mail antes do primeiro login.", dados
    if resposta.status_code == 422:
        return False, "Este e-mail já está cadastrado — faça login.", None
    return False, _mensagem_erro(resposta.status_code, resposta.text), None


def logar(email: str, senha: str) -> tuple[bool, str, dict | None]:
    """Faz login com e-mail/senha. Retorna (ok, mensagem, dados com access_token)."""
    if not disponivel():
        return False, "Supabase não configurado neste ambiente (sem SUPABASE_URL/ANON_KEY).", None
    if not (email or "").strip() or not (senha or ""):
        return False, "Informe e-mail e senha.", None
    payload = {"email": email.strip().lower(), "password": senha}
    try:
        resposta = requests.post(
            f"{_base_auth_url()}/token",
            params={"grant_type": "password"},
            json=payload,
            headers=_headers_anon(),
            timeout=15,
        )
    except requests.RequestException:
        return False, "Falha de rede ao entrar. Tente de novo.", None

    if resposta.status_code == 200:
        dados = resposta.json()
        if dados.get("access_token"):
            return True, "ok", dados
        return False, _mensagem_erro(resposta.status_code, resposta.text), None
    return False, _mensagem_erro(resposta.status_code, resposta.text), None


def renovar_sessao(refresh_token: str) -> tuple[bool, str, dict | None]:
    """Troca o refresh_token por uma sessão nova (access_token renovado).

    Usado quando a página é recarregada (F5): a sessão salva no navegador pode
    ter access_token expirado, então renovamos com o refresh_token antes de
    restaurar. Retorna (ok, mensagem, sessão nova).
    """
    if not disponivel():
        return False, "Supabase não configurado neste ambiente (sem SUPABASE_URL/ANON_KEY).", None
    if not refresh_token:
        return False, "Sessão sem refresh_token.", None
    payload = {"grant_type": "refresh_token", "refresh_token": refresh_token}
    try:
        resposta = requests.post(
            f"{_base_auth_url()}/token",
            json=payload,
            headers=_headers_anon(),
            timeout=15,
        )
    except requests.RequestException:
        return False, "Falha de rede ao renovar a sessão. Refaça o login.", None

    if resposta.status_code == 200:
        dados = resposta.json()
        if dados.get("access_token"):
            return True, "ok", dados
        return False, _mensagem_erro(resposta.status_code, resposta.text), None
    return False, _mensagem_erro(resposta.status_code, resposta.text), None


def confirmar_cadastro(token_hash: str) -> tuple[bool, str, dict | None]:
    """Confirma o cadastro pelo link do e-mail (fluxo do template com token_hash).

    Troca o token_hash do link (`?token_hash=...&type=signup`) por uma sessão via
    POST /auth/v1/verify. O link aponta para o app como QUERY PARAM (não
    fragmento), pois o Streamlit consegue ler query string mas ignora o
    fragmento (#...) que o fluxo padrão do Supabase usa. Retorna
    (ok, mensagem, sessão) — sessão só quando há access_token.
    """
    if not token_hash:
        return False, "Link inválido ou incompleto.", None
    if not disponivel():
        return False, "Supabase não configurado neste ambiente (sem SUPABASE_URL/ANON_KEY).", None
    try:
        resposta = requests.post(
            f"{_base_auth_url()}/verify",
            json={"type": "signup", "token_hash": token_hash},
            headers=_headers_anon(),
            timeout=15,
        )
    except requests.RequestException:
        return False, "Falha de rede ao confirmar o e-mail. Tente de novo.", None

    if resposta.status_code == 200:
        dados = resposta.json()
        sessao = dict(dados or {})
        if sessao.get("user") or sessao.get("access_token"):
            return True, "E-mail confirmado! Entrando…", sessao
        return True, "E-mail confirmado! Você já pode entrar.", sessao
    baixo = resposta.text.lower()
    if "expired" in baixo or "invalid" in baixo or "token" in baixo:
        return False, "Link de confirmação expirado ou inválido. Peça um novo cadastro.", None
    return False, _mensagem_erro(resposta.status_code, resposta.text), None


def sair(token: str | None) -> None:
    """Encerra a sessão no servidor (best-effort) e limpa localmente.

    A limpeza local vem PRIMEIRO: o botão Sair precisa deslogar na hora
    (o POST de logout é só um detalhe de higiene e nunca pode bloquear a UI).
    """
    limpar_sessao()
    if token and disponivel():
        try:
            requests.post(
                f"{_base_auth_url()}/logout",
                headers=_headers_auth(token),
                timeout=3,
            )
        except requests.RequestException:
            pass


def sair_da_conta() -> None:
    """Encerra a sessão (server + local) do usuário logado. Usado no botão Sair."""
    dados = sessao()
    sair((dados or {}).get("access_token"))


def guardar_sessao(dados: dict) -> None:
    _armazem()[_SESSAO_KEY] = dados


def sessao() -> dict | None:
    return _armazem().get(_SESSAO_KEY)


def usuario_logado() -> str | None:
    dados = sessao()
    if not dados:
        return None
    user = dados.get("user") or {}
    return user.get("email") or user.get("id") or None


def limpar_sessao() -> None:
    armazem = _armazem()
    if _SESSAO_KEY in armazem:
        del armazem[_SESSAO_KEY]