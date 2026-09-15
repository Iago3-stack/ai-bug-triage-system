"""Página Meu Plano: plano da conta logada (banco), troca livre e adoção de
dados antigos sem dono (registros legados) pela própria conta."""
import streamlit as st

import plano
import persistencia
import ui_comum


def _marcador(classe: str) -> None:
    st.markdown(f'<div class="{classe}" style="display:none"></div>', unsafe_allow_html=True)


def render():
    uid = plano.uid_logado()
    atual = plano.plano_atual()

    try:
        import auth_supabase
        sessao = auth_supabase.sessao() or {}
        email_conta = (sessao.get("user") or {}).get("email")
    except Exception:
        email_conta = None

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
          <span style="color:#94a3b8;font-size:12px;font-weight:700;letter-spacing:.05em">💼 MEU PLANO</span>
        </div>
        <span style="color:#64748b;font-size:12px;font-weight:600">{ui_comum.VERSAO}</span>
      </div>
      <div style="color:#ffffff;font-size:26px;font-weight:800;margin-top:16px;letter-spacing:-.01em">Seu plano nesta conta</div>
      <div style="color:#cbd5e1;font-size:15px;line-height:1.6;margin-top:8px;max-width:94%">{_frase}</div>
      <div style="color:#94a3b8;font-size:12px;margin-top:14px">Conta: <b style="color:#cbd5e1">{email_conta or uid or "—"}</b></div>
    </div>
    """, unsafe_allow_html=True)

    if not uid:
        st.warning("Você não está logado — faça login para gerenciar o plano da sua conta.")
        return

    # ─── Migração dos registros legados (dados antigos sem dono) ─────────────
    st.markdown("### 📦 Dados da sua conta")
    legados = persistencia.contar_legados_globais()
    if legados:
        st.info(
            f"Há **{legados} triagen(s)** gravadas antes da separação por usuário. "
            "Elas estão guardadas no sistema, invisíveis — se você reconhecer que são suas, "
            "pode trazê-las para a sua conta."
        )
        _marcador("marca-plano-migrar")
        if st.button("✨ Trazer para a minha conta", key="btn_migrar", type="primary"):
            feitos = persistencia.migrar_tenant_global(uid)
            st.success(f"{feitos} triagen(s) foram adicionadas à sua conta.")
            st.rerun()
    else:
        st.caption("Opa, seu histórico já está todo separado por usuário — nenhum dado antigo pendente. 🎉")

    # ─── Troca de plano (auto-atendimento) ───────────────────────────────────
    st.markdown("### 💳 Plano da conta")
    st.caption(
        "A troca de plano é livre por enquanto — experimente à vontade, sem cobrança. "
        "Em breve o pagamento integrado chega."
    )
    nova = st.radio(
        "Escolha o plano desta conta:",
        options=["free", "pago"],
        format_func=lambda v: {"free": "🔓 Basic (grátis)", "pago": "⭐ Premium"}[v],
        index=0 if atual == "free" else 1,
        horizontal=True,
        key="plano_escolha",
    )
    _marcador("marca-plano-salvar")
    if st.button("💾 Salvar plano desta conta", key="btn_salvar_plano", type="primary"):
        gravado = plano.definir_plano_no_banco(uid, nova)
        if gravado:
            st.success(
                f"Plano **{nova}** salvo para esta conta! "
                + ("O histórico completo e as análises Premium já estão ativos." if nova == "pago" else "O plano Basic está ativo (histórico resumido).")
            )
            st.rerun()
        else:
            st.error("Não foi possível salvar agora. O plano continua valendo neste acesso — tente novamente mais tarde.")

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
        _marcador("marca-plano-ferramenta")
        if st.button("🔍 Ir para a Ferramenta", key="meu_plano_ferramenta", use_container_width=True):
            import roteador

            st.switch_page(roteador.PAGINAS["triagem"])