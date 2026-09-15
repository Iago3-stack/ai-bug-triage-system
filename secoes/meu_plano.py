"""Página Meu Plano — Passo 3 SaaS: plano por usuário (banco) + migração legado.

Mostra o plano salvo da conta logada (tabela `planos_usuario`), permite
trocar o plano (auto-atendimento, sem cobrança até o Passo 4/Stripe) e
reivindicar os registros legados (tenant 'global') para a própria conta.
"""
import streamlit as st

import plano
import persistencia
import ui_comum


def render():
    uid = plano.uid_logado()
    atual = plano.plano_atual()

    st.markdown("""
    <div style="height:3px;width:100%;background:linear-gradient(90deg,transparent,#25D366,#2E7CF6,#7c3aed,transparent);border-radius:999px;margin:8px 0"></div>
    """, unsafe_allow_html=True)

    if atual == "pago":
        _badge = (
            '<span style="background:rgba(251,191,36,.16);color:#fde68a;border:1px solid rgba(251,191,36,.5);'
            'border-radius:999px;padding:4px 14px;font-size:12px;font-weight:800;letter-spacing:.03em">⭐ Plano Premium</span>'
        )
        _frase = "Você está no <b style='color:#86efac'>plano Premium</b> — histórico completo, RAG \u201ccomo foi resolvido\u201d e múltiplos canais de alerta liberados."
    else:
        _badge = (
            '<span style="background:rgba(37,211,102,.16);color:#86efac;border:1px solid rgba(37,211,102,.5);'
            'border-radius:999px;padding:4px 14px;font-size:12px;font-weight:800;letter-spacing:.03em">🔓 Plano Basic</span>'
        )
        _frase = "Você está no <b style='color:#86efac'>plano Basic</b> — a ferramenta já funciona 100%. O Premium libera RAG, causas raiz via IA e alertas multi-canal."

    st.markdown(f"""
    <div class="marca-mastro" style="width:100%;background:linear-gradient(135deg,#0f172a 0%,#16233c 52%,#25D366 175%);border-radius:16px;padding:30px 34px 26px 34px;margin:4px 0 18px;box-shadow:0 8px 22px rgba(15,23,42,.18)">
      <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap">
        <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
          {_badge}
          <span style="color:#94a3b8;font-size:12px;font-weight:700;letter-spacing:.05em">💼 MEU PLANO · Passo 3 SaaS</span>
        </div>
        <span style="color:#64748b;font-size:12px;font-weight:600">{ui_comum.VERSAO}</span>
      </div>
      <div style="color:#ffffff;font-size:26px;font-weight:800;margin-top:16px;letter-spacing:-.01em">Seu plano nesta conta</div>
      <div style="color:#cbd5e1;font-size:15px;line-height:1.6;margin-top:8px;max-width:94%">{_frase}</div>
      <div style="color:#94a3b8;font-size:12px;margin-top:14px">Conta: <b style="color:#cbd5e1">{uid or "—"}</b> · tenant <b style="color:#cbd5e1">{plano.tenant_atual()}</b></div>
    </div>
    """, unsafe_allow_html=True)

    if not uid:
        st.warning("Você não está logado — faça login para gerenciar o plano da sua conta.")
        return

    # ─── Migração dos registros legados (tenant 'global') ────────────────────
    st.markdown("### 📦 Dados da sua conta")
    legados = persistencia.contar_legados_globais()
    if legados:
        st.info(
            f"Há **{legados} triagen(s) legada(s)** gravadas antes do isolamento por usuário "
            "(tenant 'global'). Elas estão invisíveis para todos até você reivindicá-las."
        )
        if st.button("✨ Reivindicar para minha conta", key="btn_migrar", type="primary"):
            feitos = persistencia.migrar_tenant_global(uid)
            st.success(f"{feitos} triagen(s) adotadas pela sua conta.")
            st.rerun()
    else:
        st.caption("Nenhum dado legado pendente — seu histórico já está isolado por usuário.")

    # ─── Troca de plano (auto-atendimento; cobrança real só no Passo 4/Stripe) ─
    st.markdown("### 💳 Plano da conta")
    st.caption(
        "Passo 3: o plano é salvo por usuário no banco. A cobrança real (Stripe) chega no Passo 4 — "
        "enquanto isso a troca é livre, para você testar os dois planos."
    )
    nova = st.radio(
        "Escolha o plano desta conta:",
        options=["free", "pago"],
        format_func=lambda v: {"free": "🔓 Basic (grátis)", "pago": "⭐ Premium"}[v],
        index=0 if atual == "free" else 1,
        horizontal=True,
        key="plano_escolha",
    )
    if st.button("💾 Salvar plano desta conta", key="btn_salvar_plano", type="primary"):
        gravado = plano.definir_plano_no_banco(uid, nova)
        if gravado:
            st.success(
                f"Plano **{nova}** salvo para esta conta! "
                + ("O histórico completo e as análises Premium já estão ativos." if nova == "pago" else "O plano Basic está ativo (histórico resumido).")
            )
            st.rerun()
        else:
            st.error("Não foi possível gravar na nuvem (sem Supabase configurado?). O plano segue pelo ambiente.")

    # ─── Comparativo Basic × Premium ─────────────────────────────────────────
    with st.expander("💼 Comparar planos — Basic × Premium", expanded=False):
        st.markdown(f"""
| Recurso | 🔓 Basic | ⭐ Premium |
|---|---|---|
| ✅ Triagem NLP + motor determinístico | liberado | liberado |
| 🔮 IA (Gemini / Groq / modelo próprio) | liberado | liberado |
| 🧠 Análises de IA — *causas raiz* e *comparativo IA×local* | — | liberado |
| 📚 RAG — consulta casos similares + \u201ccomo foi resolvido\u201d | — | liberado |
| 🧺 Histórico / Dashboard de QA | últimas **{plano.limite_historico_free()}** triagens | completo |
| 🔔 Canais de alerta (e-mail/Discord) | **1** canal | múltiplos canais |
| 🚨 Prioridade máxima ao alertar CRÍTICA/ALTA | liberado | liberado |
| **Ideal para** | testar / demonstrar | produção contínua |
""")
        st.caption(
            "O plano da conta vale para o app todo: Ferramenta, Dashboard e Início refletem "
            "o mesmo plano salvo por usuário."
        )

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    _c1, _c2, _c3 = st.columns([1, 0.7, 1])
    with _c2:
        if st.button("🔍 Ir para a Ferramenta", key="meu_plano_ferramenta", use_container_width=True):
            import roteador

            st.switch_page(roteador.PAGINAS["triagem"])