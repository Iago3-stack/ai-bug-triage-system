"""Página Dashboard de QA — visão consolidada do histórico persistido."""
import streamlit as st

import persistencia
import plano
import dashboard as dashboard_qa


def render():
    registros_totais = persistencia.carregar_registros()
    if not plano.pago() and len(registros_totais) > plano.limite_historico_free():
        registros_totais = registros_totais[-plano.limite_historico_free():]

    st.markdown('<div style="height:3px;width:100%;background:linear-gradient(90deg,transparent,#25D366,#2E7CF6,#7c3aed,transparent);border-radius:999px;margin:8px 0"></div>', unsafe_allow_html=True)

    st.markdown("""
    <div style="width:100%;background:linear-gradient(135deg,#0f172a 0%,#1a2740 55%,#7c3aed 180%);border-radius:16px;padding:30px 34px 28px 34px;margin:4px 0 16px;box-shadow:0 8px 22px rgba(15,23,42,.18);border:1px solid rgba(139,92,246,.22)">
      <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap">
        <span style="background:rgba(139,92,246,.18);color:#c4b5fd;border:1px solid rgba(139,92,246,.5);border-radius:999px;padding:4px 14px;font-size:12px;font-weight:800;letter-spacing:.04em">📊 VISÃO CONSOLIDADA DO QA</span>
        <span style="color:#94a3b8;font-size:12px;font-weight:700;letter-spacing:.04em">POR DIA · POR FUNCIONALIDADE</span>
      </div>
      <div style="color:#ffffff;font-size:29px;font-weight:800;margin-top:18px;letter-spacing:-.01em;line-height:1.25">📈️ Dashboard de QA</div>
      <div style="color:#cbd5e1;font-size:16.5px;line-height:1.7;margin-top:8px;max-width:96%">Visão consolidada do histórico persistido: <b style="color:#86efac">severidades, sentimento, canais de alerta, divergência IA×local e guardrails</b> — por dia e por funcionalidade.</div>
    </div>
    """, unsafe_allow_html=True)

    if not registros_totais:
        st.warning("Nenhuma triagem persistida ainda — faça uma triagem e volte aqui para ver o painel.")
        return

    if not plano.pago():
        st.caption(
            f"🔓 Plano **Basic**: dashboard resumido às últimas "
            f"{plano.limite_historico_free()} triagens. O Premium libera o histórico completo."
        )
    dashboard_qa.render_dashboard(registros_totais)
    st.caption("Backend: " + (
        "☁️ Supabase (nuvem)" if persistencia._usar_nuvem() else "💾 JSONL local (efêmero)"
    ))
