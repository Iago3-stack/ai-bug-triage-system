# Botões "Entrar com Google / GitHub" via componente estático (zero dependências).
#
# POR QUE um componente estático em vez de st.components.html?
#   - `st.components.v1.html` é deprecado e NÃO devolve valores à Python.
#   - Em Streamlit Cloud o app roda num iframe; o Supabase (GoTrue) devolve o
#     token de OAuth no FRAGMENTO da URL (#access_token=...), que o servidor
#     Python nunca vê — só o navegador consegue ler.
#
# FLUXO (abre popup + localStorage como "ponte" entre abas):
#   1) o componente informa a URL do app (origin+path) à Python, que monta a URL
#      de autorização (GET /auth/v1/authorize) com redirect_to = URL do app.
#   2) clique no botão -> abertura de popup (window.open) + o componente passa
#      a vigiar o localStorage (polling em JS). Quando o usuário volta, a ABA DE
#      RETORNO captura o token do fragmento e grava no localStorage.
#   3) a ABA ORIGINAL lê o localStorage, devolve a sessão à Python, que
#      enriquece com GET /auth/v1/user e chama auth_supabase.guardar_sessao().
#
# No Streamlit, o valor do componente "persiste" entre renders (faz parte do
# estado do elemento). Para não reprocessar o mesmo evento, cada etapa consome
# exatamente o evento que espera e muda de etapa imediatamente (st.rerun).
# Não adiciona dependências (sem streamlit-js / streamlit-url-fragment).

import os

import auth_supabase

try:
    import streamlit as st
    import streamlit.components.v1 as components

    _PASTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "oauth_bridge")
    _bridge = components.declare_component("oauth_login", path=_PASTA)
except Exception:  # testes fora do Streamlit
    st = None
    components = None
    _bridge = None

_ETAPA = "_oauth_etapa"
_BASE = "_oauth_base"

_PROVIDERS = ("google", "github")

_LOCALE = {
    "google": "Fazer login com Google",
    "github": "Entrar com GitHub",
    "aguarde": "Aguardando autenticação…",
    "aviso": "",  # sem aviso extra
}


def _config() -> tuple[str, str] | None:
    config = auth_supabase._config()
    if not config:
        return None
    return (str(config[0]).rstrip("/") + "/auth/v1", config[1])


def _armazem():
    return st.session_state if st else {}


def _providers_disponiveis() -> list[str]:
    """Providers Google/GitHub que estão realmente habilitados no projeto."""
    ext = auth_supabase.providers_habilitados()
    if not ext:
        return []
    return [p for p in _PROVIDERS if ext.get(p) is True]


def _sessao_fragmento(dados: dict) -> dict | None:
    """Converte o que o JS devolveu numa sessão completa (token + user)."""
    if not dados or not dados.get("access_token"):
        return None
    return auth_supabase.sessao_oauth(dados)


def _url_autorizacao(provider: str, redirect_to: str, apikey: str) -> dict:
    """URL de autorização + apikey (público) para o JS montar o fluxo."""
    return {
        "url": auth_supabase.url_autorizacao(provider, redirect_to),
        "apikey": apikey,
    }


def render() -> None:
    """Processa o fluxo de OAuth na página de login. Deve ser chamada em todo rerun."""
    if st is None:
        return
    config = _config()
    providers = _providers_disponiveis()
    if not config or not providers:
        return

    armazem = _armazem()
    etapa = armazem.get(_ETAPA, "fluxourl")  # fluxourl -> botoes -> aguardando
    base = armazem.get(_BASE)

    if etapa == "fluxourl":
        # 1º render: pede a URL do app ao navegador (o iframe sabe a quadra real).
        evt = _bridge(
            primeiro=True,
            providers=providers,
            authorizeUrl={},
            locale=_LOCALE,
            apikey="",
            timeout_ms=180000,
        )
        if evt and evt.get("tipo") == "url" and evt.get("url"):
            armazem[_BASE] = evt["url"]
            armazem[_ETAPA] = "botoes"
            st.rerun()  # agora monta a URL de autorização com o redirect_to certo
        return

    if not base:
        armazem.pop(_ETAPA, None)
        st.rerun()
        return

    if etapa == "botoes":
        af = {p: _url_autorizacao(p, base, config[1]) for p in providers}
        evt = _bridge(
            primeiro=False,
            aguardando=False,
            providers=providers,
            authorizeUrl=af,
            locale=_LOCALE,
            apikey=config[1],
            timeout_ms=180000,
        )
        # O valor persiste: só a PRIMEIRA aparição de "iniciado" interessa.
        if evt and evt.get("tipo") == "iniciado" and not armazem.get("_oauth_imed"):
            armazem["_oauth_imed"] = True
            armazem[_ETAPA] = "aguardando"
            st.rerun()
        return

    if etapa == "aguardando":
        evt = _bridge(
            primeiro=False,
            aguardando=True,
            providers=providers,
            authorizeUrl={p: _url_autorizacao(p, base, config[1]) for p in providers},
            locale=_LOCALE,
            apikey=config[1],
            timeout_ms=180000,
        )
        if evt and evt.get("tipo") == "sessao":
            sessao = _sessao_fragmento(evt.get("sessao"))
            armazem.pop(_ETAPA, None)
            armazem.pop(_BASE, None)
            armazem.pop("_oauth_imed", None)
            if sessao:
                auth_supabase.guardar_sessao(sessao)
            else:
                st.error("Não foi possível autenticar com o Google/GitHub. Tente de novo.")
            st.rerun()
        return