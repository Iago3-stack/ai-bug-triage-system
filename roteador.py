"""Registro das páginas do app (st.navigation)."""
import streamlit as st

from secoes import inicio, ferramenta, dashboard_pagina, meu_plano

PAGINAS = {
    "inicio": st.Page(inicio.render, title="Início", url_path="inicio", icon="🏠", default=True),
    "triagem": st.Page(ferramenta.render, title="Triagem de Bugs", url_path="triagem", icon="🔍"),
    "meu_plano": st.Page(meu_plano.render, title="Meu Plano", url_path="meu_plano", icon="💼"),
    "dashboard": st.Page(dashboard_pagina.render, title="Dashboard QA", url_path="dashboard", icon="📈"),
}
