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


def _render(comando: str, valor=None):
    return _bridge(comando=comando, valor=valor, default=_SENTINELA, key="sessao_persist")


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
        _render("salvar", valor=dados)
    except Exception:
        pass


def limpar() -> None:
    """Apaga a sessão do localStorage (no logout)."""
    try:
        _render("limpar", valor=None)
    except Exception:
        pass


def carregar() -> None:
    """Restaura a sessão salva no navegador, se houver.

    Chame no topo do boot do app. Na 1ª passada o componente ainda não devolveu
    valor (default = sentinela) e disparamos um rerun; na 2ª passada a sessão
    gravada chega e é restaurada. Retorna silenciosamente se nada foi gravado.
    """
    if not auth_supabase.disponivel():
        return

    # Já logado nesta sessão do Streamlit (ex.: login recém-feito)? Nada a fazer.
    if auth_supabase.sessao():
        return

    tentativas = st.session_state.get("_sessao_persist_volta", 0)
    valor = _render("ler", valor=None)
    if valor == _SENTINELA and tentativas < 2:
        st.session_state["_sessao_persist_volta"] = tentativas + 1
        st.rerun()
        return

    st.session_state.pop("_sessao_persist_volta", None)

    if isinstance(valor, dict):
        _restaurar(valor)