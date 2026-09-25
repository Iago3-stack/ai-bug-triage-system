"""Telemetria de produto (PostHog) — métricas agregadas, nunca dados sensíveis.

Objetivo: enxergar o funil (cadastro → primeira triagem → exportação), a saúde da
IA (fallback/falha por provedor) e o uso real das features — sem gravar nada do
conteúdo dos relatos. O PostHog fica DENTRO do app (captura server-side no
Python; a página não embarca JS de terceiros).

Regras de segurança:
  - No-op por padrão: sem POSTHOG_API_KEY nada é enviado, nem rede nem custo.
  - Nunca levanta exceção: qualquer falha de config/rede é engolida (try/except)
    para a telemetria NUNCA derrubar nem atrasar a triagem.
  - Só métricas de produto viram propriedades (severidade, provedor, plano...) —
    nenhum fragmento do relato, e-mail ou dado pessoal é enviado. O e-mail/logado
    só vira o distinct_id (identificador padrão de produto, como no próprio
    Supabase/PostHog), nunca uma propriedade.
  - Host padrão da EU (https://eu.i.posthog.com) — dados ficam na União
    Europeia (LGPD). Sobrescrevível via POSTHOG_HOST.

Config (Secrets/`.env`):
  POSTHOG_API_KEY  — chave do projeto (sem ela: tudo desligado)
  POSTHOG_HOST     — (opcional) default https://eu.i.posthog.com
"""

import os

try:
    import posthog
except Exception:  # pragma: no cover — dependência ausente no ambiente
    posthog = None

_HOST_PADRAO = "https://eu.i.posthog.com"
_CHAVE_ENV = "POSTHOG_API_KEY"
_HOST_ENV = "POSTHOG_HOST"

# Lazy: False = desligado (sem chave), None = ainda não inicializado, senão o SDK.
_status: object | None = None


def _ler_do_env(nome: str) -> str | None:
    """Lê uma chave do .env local (apenas leitura, nunca commitado)."""
    caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(caminho):
        return None
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            chave, _, valor = linha.partition("=")
            if chave.strip() == nome:
                return valor.strip().strip('"').strip("'")
    return None


def _ler(nome: str) -> str | None:
    """Lê config na ordem: st.secrets → os.environ → .env local."""
    try:
        import streamlit as st

        v = st.secrets.get(nome)
        if v:
            return str(v)
    except Exception:
        pass
    v = os.getenv(nome, "").strip()
    if v:
        return v
    return _ler_do_env(nome)


def _obter_sdk():
    """Client PostHog (lazy). None quando desligado (sem chave). Nunca levanta."""
    global _status
    if _status is not None:
        return _status if _status is not False else None
    chave = _ler(_CHAVE_ENV)
    if not chave or posthog is None:
        _status = False
        return None
    try:
        posthog.api_key = chave
        posthog.host = _ler(_HOST_ENV) or _HOST_PADRAO
        posthog.debug = False
        _status = posthog
        return posthog
    except Exception:  # pragma: no cover — falha rara de config
        _status = False
        return None


def disponivel() -> bool:
    """True se o PostHog está configurado e pronto (sem disparar nada)."""
    return _obter_sdk() is not None


def capturar(evento: str, **props) -> bool:
    """Registra um evento de produto. False = desligado/falha (nunca levanta).

    Use `usuario=` para o distinct_id (ex.: e-mail ou uid da conta logada).
    """
    try:
        sdk = _obter_sdk()
        if sdk is None:
            return False
        uid = str(props.pop("usuario", None) or "anonimo")
        sdk.capture(distinct_id=uid, event=evento, properties=props or None)
        return True
    except Exception:
        return False


def identificar(uid: str, **props) -> bool:
    """Vincula propriedades estáveis ao usuário (plano, conta criada em...).

    No PostHog moderno o identify virou `set` (propriedades do usuário).
    Sem efeito quando desligado. Nunca levanta.
    """
    try:
        sdk = _obter_sdk()
        if sdk is None or not uid:
            return False
        sdk.set(distinct_id=str(uid), properties=props or None)
        return True
    except Exception:
        return False