# Botões "Entrar com Google / GitHub" via componente estático (zero dependências).
#
# POR QUE um componente estático em vez de st.components.html?
#   - `st.components.v1.html` é deprecado e NÃO devolve valores à Python.
#   - Em Streamlit Cloud o app roda num iframe; o Supabase (GoTrue) devolve o
#     token de OAuth no FRAGMENTO da URL (#access_token=...), que o servidor
#     Python nunca vê — só o navegador consegue ler.
#
# FLUXO (popup, como o login do próprio Supabase):
#   1) o componente informa a URL do app (origin+path) à Python, que monta a URL
#      de autorização (GET /auth/v1/authorize) com redirect_to = URL do app.
#   2) clique no botão -> JS abre uma POPUP (window.open; o sandbox do componente
#      tem allow-popups na Cloud) com a authorize URL. O app principal NÃO sai da
#      tela, só mostra "Aguardando autenticação…" + poll de retorno.
#   3) o Supabase redireciona a POPUP de volta para a URL do app (allowlistada)
#      com #access_token. DENTRO da popup volta a rodar o próprio app; o
#      componente na popup captura o token e grava no localStorage (mesma origin
#      => ponte com a janela principal).
#   4) quando o token aparece, o POLL da janela principal (1) o lê e devolve à
#      Python (que enriquece com GET /auth/v1/user e guarda a sessão) e (2)
#      NAVEGA a popup até a "close page" fim.html (fimUrl, mesma origin). Como
#      fim.html roda no NÍVEL TOPO da popup (aberta por script), o window.close()
#      dela funciona — coisa que NÃO acontece com window.close()/top.close()
#      chamados de dentro do componente sandboxed, nem com _popupRef.close() do
#      opener sandboxed. fim.html NÃO precisa estar na allowlist do Supabase:
#      ele só é usado como close page, nunca como redirect_to do provider.
#   FALLBACK: se o navegador bloquear o popup (window.open => null), o botão
#   avisa a Python sem o flag "popup" e ela navega a PRÓPRIA aba via
#   <meta http-equiv="refresh"> no documento principal.
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
        # 1º render: pergunta a URL do app ao navegador (o iframe sabe a quadra)
        # e detecta se já voltamos do OAuth (fragmento com token).
        evt = _bridge(
            primeiro=True,
            providers=providers,
            authorizeUrl={},
            locale=_LOCALE,
            apikey="",
            timeout_ms=180000,
        )
        if evt:
            tipo = evt.get("tipo")
            if tipo == "url" and evt.get("url"):
                # Vinda limpa: monta os botões.
                armazem[_BASE] = evt["url"]
                armazem[_ETAPA] = "botoes"
                st.rerun()
            elif tipo in ("captura", "sessao"):
                # Retorno do OAuth na MESMA aba (fragmento já capturado). O JS
                # manda a url junto: sem ela o Python não tem _BASE e o fluxo
                # "reseta" para fluxourl (voltava à tela de login).
                if evt.get("url"):
                    armazem[_BASE] = evt["url"]
                armazem[_ETAPA] = "aguardando"
                st.rerun()
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
        # O valor persiste: só a primeira aparição de "iniciado" importa.
        if evt and evt.get("tipo") == "iniciado" and not armazem.get("_oauth_imed"):
            armazem["_oauth_imed"] = True
            armazem[_ETAPA] = "aguardando"
            popup = bool(evt.get("popup"))
            url_auth = (af.get(evt.get("provider")) or {}).get("url")
            if not popup:
                # Fallback (popup bloqueado): navega a própria aba/iframe via
                # meta-refresh. IMPORTANTE: NÃO chamar st.rerun() neste run —
                # o rerun descarta o <meta http-equiv=refresh> antes de navegar.
                if url_auth:
                    st.markdown(
                        f'<meta http-equiv="refresh" content="0; url={url_auth}">',
                        unsafe_allow_html=True,
                    )
                else:
                    st.error("Provedor de login não configurado.")
            # Mostra o estado "aguardando" (spinner) e arma o poll de retorno.
            _bridge(
                primeiro=False,
                aguardando=True,
                providers=providers,
                authorizeUrl=af,
                locale=_LOCALE,
                apikey=config[1],
                timeout_ms=180000,
            )
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