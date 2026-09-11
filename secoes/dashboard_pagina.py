"""Página Dashboard de QA — visão consolidada do histórico persistido."""
import streamlit as st

import persistencia
import plano
import dashboard as dashboard_qa


def render():
    registros_totais = persistencia.carregar_registros()
    if not plano.pago() and len(registros_totais) > plano.limite_historico_free():
        registros_totais = registros_totais[-plano.limite_historico_free():]

    st.markdown("""
<div style="font-size:1.6em;font-weight:800;line-height:1.25;background:linear-gradient(90deg,#7c3aed 0%,#2E7CF6 50%,#25D366 100%);-webkit-background-clip:text;background-clip:text;color:transparent;display:inline-block">📈 Dashboard de QA</div>
""", unsafe_allow_html=True)
    st.info("Visão consolidada do histórico persistido: severidades, sentimento, canais de alerta, divergência IA×local e guardrails — por dia e por funcionalidade.")

    if not registros_totais:
        st.warning("Nenhuma triagem persistida ainda — faça uma triagem e volte aqui para ver o painel.")
        return

    with st.expander("📖 Como ler este dashboard", expanded=False):
        st.markdown(dashboard_qa.GUIA_DASHBOARD)

    if not plano.pago():
        st.caption(
            f"🔓 Plano **Basic**: dashboard resumido às últimas "
            f"{plano.limite_historico_free()} triagens. O Premium libera o histórico completo."
        )
    dashboard_qa.render_dashboard(registros_totais)
    st.caption("Backend: " + (
        "☁️ Supabase (nuvem)" if persistencia._usar_nuvem() else "💾 JSONL local (efêmero)"
    ))
