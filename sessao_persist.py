# Persistência da sessão de login no navegador (localStorage + cookie).
#
# O st.session_state vive apenas na memória do servidor do Streamlit e morre
# quando o usuário recarrega a página (F5). Este módulo guarda uma cópia da
# sessão no navegador (localStorage E cookie do app) e a devolve no boot
# seguinte, de modo que o usuário permanece logado ao recarregar.
#
# Uso:
#   sessao_persist.salvar(dados)         -> enfileira gravação (após login/confirmação)
#   sessao_persist.carregar()            -> lê do navegador e restaura no boot
#   sessao_persist.limpar()              -> apaga (no logout)
#   sessao_persist.processar_pendente()  -> renderiza a ponte de escrita (home.py)
#
# Por que enfileirar (e não gravar na hora)? O login chama salvar() e dispara
# um st.rerun() logo em seguida (login.py). Um componente custom renderizado
# durante essa ação é DESCARTADO pela rerun antes de o navegador montar o iframe
# e processar o evento — a gravação se perdia silenciosamente. Agora a escrita é
# uma "pendência" em st.session_state e um componente-ponte (montado em home.py,
# DENTRO do fluxo normal, sem rerun da ação) re-renderiza até o iframe confirmar.
#
# Segurança: o refresh_token em localStorage/cookie na origem do app é o padrão
# do próprio Supabase JS; fica na origem do app e em conexão HTTPS.

import os
import time

import streamlit as st
import streamlit.components.v1 as components

import auth_supabase

_PASTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "sessao_persist")

# O Streamlit só retorna o valor do componente na renderização SEGUINTE à
# primeira: na 1ª passada recebemos o default (sentinela) e na 2ª passada o valor
# real devolvido pelo navegador chega.
# O default PRECISA ser serializável (JSON) — usamos uma string que nunca é
# valor legítimo.
_SENTINELA = "__sessao_persist_nao_lida__"

_bridge = components.declare_component("sessao_persist", path=_PASTA)


# Keys distintas por operação: no MESMO run pode haver ler (boot) + ponte de
# escrita (pendência). Com a mesma key o Streamlit levanta DuplicatedWidgetIDError.
_KEY_LER = "sessao_persist_ler"
_KEY_PONTE = "sessao_persist_ponte"
_KEY_BOOT = "_sessao_persist_boot"
_KEY_TENTATIVAS = "_sessao_persist_tentativas"
# Pendência de escrita: ("salvar", dados) ou ("limpar", None). Fica em
# st.session_state até o iframe confirmar (retorno != sentinela).
_KEY_FILA = "_sessao_persist_fila"
# Cookie com o refresh_token gravado pelo JS do componente (o iframe roda com
# allow-same-origin, então o cookie pertence à origem do app). O Python lê esse
# cookie direto do handshake do WebSocket via st.context.cookies — sem depender
# do timing do componente — garantindo restauração mesmo se o localStorage do
# iframe falhar.
_COOKIE_RF = "_auth_sessao_persist_rf"
_BOOT_FEITO = "feito"
# Motivo da falha de restauração, exibido na tela de login (diagnóstico):
# "tempo" (componente não respondeu a tempo), "expirada" (refresh_token recusado),
# "ausente" (não há sessão salva) ou "erro" (falha inesperada).
_KEY_MOTIVO = "_sessao_persist_motivo"
# Timestamp (ms) da última gravação no localStorage (diagnóstico exibido na
# tela de login quando a restauração falha).
_KEY_TS = "_sessao_persist_ts"
# Máximo de segundos esperando o valor do componente no boot. O browser precisa
# carregar o iframe do componente e devolver o localStorage; uma contagem cega de
# reruns esgotava em milissegundos (todos os reruns aconteciam antes de o navegador
# responder). O orçamento é por relógio (8s) com respiro real (0.3s) entre tentativas.
_MAX_ESPERA_S = 8.0
_PASSO_S = 0.3


def _render(comando: str, key: str, valor=None):
    return _bridge(comando=comando, valor=valor, default=_SENTINELA, key=key)


def _restaurar(valor) -> str:
    """Reidrata a sessão com o refresh_token salvo, renovando o access_token.

    Retorna status: "ok", "ausente" (sem refresh_token), "expirada" (recusado pelo
    Supabase) ou "erro" (falha inesperada). Serve para exibir o motivo na tela
    de login quando a restauração falha.
    """
    if not isinstance(valor, dict) or not valor.get("refresh_token"):
        return "ausente"
    try:
        ok, _, nova = auth_supabase.renovar_sessao(valor["refresh_token"])
    except Exception:
        return "erro"
    if ok and nova and nova.get("access_token"):
        auth_supabase.guardar_sessao(nova)
        salvar(nova)  # atualiza tokens no navegador (access_token é renovado)
        return "ok"
    return "expirada"


def salvar(dados: dict) -> None:
    """Enfileira a gravação da sessão no navegador (após login/confirmação).

    A gravação real acontece no run seguinte, via processar_pendente() — porque
    renderizar o componente aqui (dentro da ação de login, seguida de st.rerun())
    fazia a árvore ser descartada antes de o iframe processar o evento.
    """
    st.session_state[_KEY_FILA] = ("salvar", dados)


def limpar() -> None:
    """Enfileira a limpeza da sessão salva no navegador (no logout)."""
    st.session_state[_KEY_FILA] = ("limpar", None)
    st.session_state.pop(_KEY_BOOT, None)
    st.session_state.pop(_KEY_TENTATIVAS, None)
    st.session_state.pop(_KEY_MOTIVO, None)
    st.session_state.pop(_KEY_TS, None)


def processar_pendente() -> None:
    """Processa a pendência de escrita (se houver) mantendo a ponte SEMPRE montada.

    Chamado do home.py em todo run (fluxo normal, sem rerun da ação de login).
    O componente fica permanentemente na árvore com a mesma key mexmo sem
    pendência (comando "ocioso"): montar/desmontar o iframe a cada confirmação
    deslocava os IDs dos elementos seguintes na árvore de deltas do Streamlit e
    fazia o frontend deixar elementos "fantasma"/duplicados na página
    (ex.: expanders repetidos, sombras de formulários). Árvore estável = sem
    artefatos.
    """
    fila = st.session_state.get(_KEY_FILA)
    if fila:
        comando, valor = fila
        ret = _render(comando, _KEY_PONTE, valor=valor)
        if ret != _SENTINELA:
            st.session_state.pop(_KEY_FILA, None)
    else:
        # Sem pendência: renderiza a ponte em modo inerte, preservando a posição
        # e a key do componente na árvore do Streamlit entre todos os runs.
        _render("ocioso", _KEY_PONTE, valor=None)


def _ler_cookie_refresh() -> str | None:
    """Lê o refresh_token do cookie (JS) — caminho determinístico de restauração.

    O cookie do componente viaja no handshake do WebSocket e o Streamlit o expõe
    via st.context.cookies. Retorna o refresh_token cru ou None.
    """
    try:
        valor = st.context.cookies.get(_COOKIE_RF)
    except Exception:
        return None
    if not valor:
        return None
    try:
        import urllib.parse

        return urllib.parse.unquote(valor)
    except Exception:
        return valor


def _tem_limpar_pendente() -> bool:
    """True se há um logout ("limpar") enfileirado e ainda não confirmado.

    Guarda o boot: enquanto a ponte não terminar de limpar o navegador, o cookie
    ainda traz o refresh_token — e reidratar nesse momento transformaria o
    botão Sair em login imediato.
    """
    fila = st.session_state.get(_KEY_FILA)
    return bool(fila and fila[0] == "limpar")


def carregar() -> None:
    """Restaura a sessão salva no navegador, se houver.

    Ordem de confiança:
      1. Cookie (refresh_token gravado pelo JS) — lido direto do request, sem
         esperar o componente. Funciona no 1º run e sobrevive a localStorage
         bloqueado/falho.
      2. Componente/localStorage — fallback, mantido para navegadores que
         bloqueiam cookies.
    """
    if not auth_supabase.disponivel():
        return

    # Já logado nesta sessão do Streamlit (ex.: login recém-feito)? Nada a fazer.
    if auth_supabase.sessao():
        return

    # ACABOU DE CLICAR EM SAIR: a ponte limpará localStorage+cookie neste run.
    # Não tentar reidratar do cookie (ainda presente até a ponte executar) —
    # senão o logout se transforma em login imediato.
    if _tem_limpar_pendente():
        st.session_state[_KEY_BOOT] = _BOOT_FEITO
        return

    # Boot concluído (valor aplicado ou desistimos): não mexer de novo.
    if st.session_state.get(_KEY_BOOT) == _BOOT_FEITO:
        return

    # 1º caminho (determinístico): cookie. Se restaurar, fim.
    refresh = _ler_cookie_refresh()
    if refresh:
        st.session_state[_KEY_BOOT] = _BOOT_FEITO
        st.session_state.pop(_KEY_TENTATIVAS, None)
        status = _restaurar({"refresh_token": refresh})
        if status == "ok":
            st.session_state.pop(_KEY_MOTIVO, None)
            return
        st.session_state[_KEY_MOTIVO] = "expirada" if status != "erro" else "erro"
        return

    valor = _render("ler", _KEY_LER, valor=None)

    if valor == _SENTINELA:
        # Componente ainda não respondeu: dá um respiro real ao navegador para
        # montar o iframe e devolver o localStorage, com orçamento de relógio.
        agora = time.monotonic()
        inicio = st.session_state.get(_KEY_TENTATIVAS)
        if inicio is None:
            inicio = agora
            st.session_state[_KEY_TENTATIVAS] = inicio
        if agora - inicio > _MAX_ESPERA_S:
            st.session_state[_KEY_BOOT] = _BOOT_FEITO
            st.session_state[_KEY_MOTIVO] = "tempo"
            return
        time.sleep(_PASSO_S)
        st.rerun()
        return

    st.session_state[_KEY_BOOT] = _BOOT_FEITO
    st.session_state.pop(_KEY_MOTIVO, None)
    st.session_state.pop(_KEY_TENTATIVAS, None)

    # Envelope novo: {sessao, ts}; valores antigos no localStorage eram o dict
    # cru com "refresh_token". Aceitamos os dois formatos.
    if isinstance(valor, dict) and set(valor) >= {"sessao", "ts"}:
        ts = valor.get("ts")
        if isinstance(ts, int):
            st.session_state[_KEY_TS] = ts
        interno = valor.get("sessao")
        if isinstance(interno, dict) and interno.get("refresh_token"):
            if _restaurar(interno) != "ok":
                st.session_state[_KEY_MOTIVO] = "expirada"
        else:
            st.session_state[_KEY_MOTIVO] = "ausente"
    elif isinstance(valor, dict) and valor.get("refresh_token"):
        if _restaurar(valor) != "ok":
            st.session_state[_KEY_MOTIVO] = "expirada"
    else:
        st.session_state[_KEY_MOTIVO] = "ausente"