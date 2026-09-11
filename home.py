"""Entrada do app: rota (st.navigation) + CSS global + sidebar/rodapé comuns."""
import streamlit as st

import ui_tema
import roteador
import ui_comum

ui_tema.config_pagina()
pg = st.navigation(list(roteador.PAGINAS.values()), position="sidebar")

ui_tema.aplicar_css()

with st.sidebar:
    ui_comum.sidebar_comum()

pg.run()
ui_comum.rodape()

# Botão interno do dialog usou st.rerun() (ex.: trocar tema), que fecha o modal.
# Este flag reabre o modal com o corpo re-renderizado.
if st.session_state.pop("_reabrir_config", False):
    ui_comum.abrir_configuracoes()
