"""Entrada do app: rota (st.navigation) + CSS global + sidebar/rodapé comuns."""
import streamlit as st

import ui_tema
import roteador
import ui_comum
from secoes import login as pagina_login

ui_tema.config_pagina()
pg = st.navigation(list(roteador.PAGINAS.values()), position="sidebar")

ui_tema.aplicar_css()

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
