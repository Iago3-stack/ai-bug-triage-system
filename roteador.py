"""Registro das páginas do app (st.navigation)."""
import streamlit as st

from secoes import inicio, ferramenta, dashboard_pagina, meu_plano, painel_dono

PAGINAS = {
    "inicio": st.Page(inicio.render, title="Início", url_path="inicio", icon="🏠", default=True),
    "triagem": st.Page(ferramenta.render, title="Triagem de Bugs", url_path="triagem", icon="🔍"),
    "meu_plano": st.Page(meu_plano.render, title="Meu Plano", url_path="meu_plano", icon="💼"),
    "dashboard": st.Page(dashboard_pagina.render, title="Dashboard QA", url_path="dashboard", icon="📈️"),
    "painel_dono": st.Page(painel_dono.render, title="Painel do Dono", url_path="painel_dono", icon="🛠️"),
}


def paginas_visiveis() -> list:
    """Páginas registradas, sem o Painel do Dono para quem não é o dono."""
    try:
        import admin

        if admin.eh_dono():
            return list(PAGINAS.values())
    except Exception:
        pass
    dono = id(PAGINAS["painel_dono"])
    return [p for p in PAGINAS.values() if id(p) != dono]
