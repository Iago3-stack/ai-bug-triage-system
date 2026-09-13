# Persistência da sessão de login no navegador (localStorage).
#
# O st.session_state vive apenas na memória do servidor do Streamlit e morre
# quando o usuário recarrega a página (F5). Este módulo guarda uma cópia da
# sessão no localStorage do navegador e a devolve no boot seguinte, de modo que
# o usuário permanece logado ao recarregar.
#
# Uso:
#   sessao_persist.salvar(dados)   -> grava no navegador (após login/confirmação)
#   sessao_persist.carregar()      -> lê do navegador e restaura a sessão no boot
#   sessao_persist.limpar()        -> apaga (no logout)
#
# Segurança: o refresh_token em localStorage é o padrão do próprio Supabase JS;
# fica na origem do app e em conexão HTTPS.

import os

import streamlit as st
import streamlit.components.v1 as components

import auth_supabase

_PASTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "sessao_persist")

# O Streamlit só retorna o valor do componente na renderização SEGUINTE à
# primeira: na 1ª passada recebemos o default (sentinela), pedimos um rerun e
# na 2ª passada o valor real do localStorage chega.
# O default PRECISA ser serializável (JSON) — um objeto Python não passa pelo
# marshal do componente, então usamos uma string que nunca é valor legítimo.
_SENTINELA = "__sessao_persist_nao_lida__"

_bridge = components.declare_component("sessao_persist", path=_PASTA)


# Keys distintas por operação: no MESMO run pode haver ler (boot) + salvar
# (login). Com a mesma key o Streamlit levanta DuplicatedWidgetIDError.
_KEY_LER = "sessao_persist_ler"
_KEY_SALVAR = "sessao_persist_salvar"
_KEY_LIMPAR = "sessao_persist_limpar"
_KEY_BOOT = "_sessao_persist_boot"
_KEY_TENTATIVAS = "_sessao_persist_tentativas"
_BOOT_FEITO = "feito"
# Máximo de reruns esperando o valor do componente no boot. O browser precisa
# carregar o iframe do componente e devolver o localStorage; se desistíssemos
# no 1º "vazio", um reload lento nunca restauraria a sessão. Este limite evita
# loop infinito e nunca bloqueia interações (cliques) depois que o boot conclui.
_MAX_TENTATIVAS = 8


def _render(comando: str, key: str, valor=None):
    return _bridge(comando=comando, valor=valor, default=_SENTINELA, key=key)


def _restaurar(valor) -> None:
    """Reidrata a sessão com o refresh_token salvo, renovando o access_token."""
    if not isinstance(valor, dict) or not valor.get("refresh_token"):
        return
    ok, _, nova = auth_supabase.renovar_sessao(valor["refresh_token"])
    if ok and nova and nova.get("access_token"):
        auth_supabase.guardar_sessao(nova)
        salvar(nova)  # atualiza tokens no navegador (access_token é renovado)


def salvar(dados: dict) -> None:
    """Grava a sessão no localStorage (após login ou confirmação de e-mail)."""
    try:
        _render("salvar", _KEY_SALVAR, valor=dados)
    except Exception:
        pass


def limpar() -> None:
    """Apaga a sessão do localStorage (no logout)."""
    try:
        _render("limpar", _KEY_LIMPAR, valor=None)
    except Exception:
        pass


def carregar() -> None:
    """Restaura a sessão salva no navegador, se houver.

    Tenta uma vez por sessão do Streamlit: enquanto o componente não devolve o
    valor do localStorage (default = sentinela), pedimos rerun até receber o
    valor real ou esgotar _MAX_TENTATIVAS. Nominalmente 1-2 reruns; nunca nos
    runs de interação (botões/formulários) porque o boot conclui antes.
    """
    if not auth_supabase.disponivel():
        return

    # Já logado nesta sessão do Streamlit (ex.: login recém-feito)? Nada a fazer.
    if auth_supabase.sessao():
        return

    # Boot concluído (valor aplicado ou desistimos): não mexer de novo.
    if st.session_state.get(_KEY_BOOT) == _BOOT_FEITO:
        return

    valor = _render("ler", _KEY_LER, valor=None)

    if valor == _SENTINELA:
        # Componente ainda não respondeu: espera mais um ciclo, com limite.
        tentativas = st.session_state.get(_KEY_TENTATIVAS, 0) + 1
        if tentativas > _MAX_TENTATIVAS:
            st.session_state[_KEY_BOOT] = _BOOT_FEITO
            return
        st.session_state[_KEY_TENTATIVAS] = tentativas
        st.rerun()
        return

    st.session_state[_KEY_BOOT] = _BOOT_FEITO

    if isinstance(valor, dict):
        _restaurar(valor)