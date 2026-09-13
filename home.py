"""Entrada do app: rota (st.navigation) + CSS global + sidebar/rodapé comuns."""
import streamlit as st

import auth_supabase
import ui_tema
import roteador
import ui_comum
from secoes import login as pagina_login


def _processar_confirmacao_email() -> None:
    """Confirma o cadastro quando a URL traz o token_hash vindo do e-mail.

    O template de e-mail do Supabase aponta o link para
    `SiteURL?token_hash=...&type=signup` (query param). O Streamlit lê a query
    string, mas ignora o fragmento (#) que o fluxo padrão usa — por isso o
    template usa token_hash. Aqui trocamos o hash por uma sessão real.
    """
    try:
        parametros = st.query_params
    except Exception:
        parametros = {}
    if not parametros or not parametros.get("token_hash"):
        return
    if parametros.get("type") not in ("signup", None):
        return

    token_hash = parametros.get("token_hash")
    if isinstance(token_hash, list):
        token_hash = token_hash[0]
    if not token_hash:
        return

    ok, msg, sessao = auth_supabase.confirmar_cadastro(token_hash)
    if ok and sessao and sessao.get("user"):
        auth_supabase.guardar_sessao(sessao)
        st.success("E-mail confirmado! Bem-vindo(a).")
    elif ok:
        st.success("E-mail confirmado! Agora é só entrar com e-mail e senha.")
    else:
        st.error(msg)

    # Limpa o link (senão todo rerun reprocessaria o token_hash já consumido).
    try:
        del parametros["token_hash"]
        del parametros["type"]
    except Exception:
        pass


ui_tema.config_pagina()
pg = st.navigation(list(roteador.PAGINAS.values()), position="sidebar")

ui_tema.aplicar_css()

# Confirmação de cadastro vinda do link do e-mail (query param, não fragmento):
# ?token_hash=...&type=signup -> troca o hash por uma sessão e loga o usuário.
_processar_confirmacao_email()

with st.sidebar:
    ui_comum.sidebar_comum()

# Passo 2 (SaaS): Início é público; Ferramenta e Dashboard exigem login quando o
# Supabase Auth está configurado. Sem configuração, o app segue integralmente aberto.
if pg.url_path in ("triagem", "dashboard") and pagina_login.render():
    st.stop()

pg.run()
ui_comum.rodape()

# Botão interno do dialog usou st.rerun() (ex.: trocar tema), que fecha o modal.
# Este flag reabre o modal com o corpo re-renderizado.
if st.session_state.pop("_reabrir_config", False):
    ui_comum.abrir_configuracoes()
