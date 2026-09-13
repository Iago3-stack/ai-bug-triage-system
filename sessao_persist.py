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
_BOOT_PENDENTE = "pendente"
_BOOT_FEITO = "feito"


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

    Tenta UMA vez por sessão do Streamlit: na 1ª renderização o componente
    ainda não devolveu valor (default = sentinela) e pedimos um rerun; na 2ª,
    marcamos a sessão como "boot feito" e aplicamos o que vier. Nominalmente um
    único rerun no boot — nunca nos runs de interação (botões/formulários).
    """
    if not auth_supabase.disponivel():
        return

    # Já logado nesta sessão do Streamlit (ex.: login recém-feito)? Nada a fazer.
    if auth_supabase.sessao():
        return

    # Boot da sessão já concluído (valor lido ou desistimos): não mexer de novo.
    if st.session_state.get(_KEY_BOOT) == _BOOT_FEITO:
        return

    valor = _render("ler", _KEY_LER, valor=None)

    if valor == _SENTINELA:
        # Segunda tentativa veio vazia também (ex.: componente não respondeu):
        # desistir para nunca travar em loop nem bloquear interações futuras.
        if st.session_state.get(_KEY_BOOT) == _BOOT_PENDENTE:
            st.session_state[_KEY_BOOT] = _BOOT_FEITO
            return
        # Ainda não chegou o valor real do componente: marca o boot em andamento
        # e re-executa para a 2ª renderização devolver o localStorage.
        st.session_state[_KEY_BOOT] = _BOOT_PENDENTE
        st.rerun()
        return

    st.session_state[_KEY_BOOT] = _BOOT_FEITO

    if isinstance(valor, dict):
        _restaurar(valor)