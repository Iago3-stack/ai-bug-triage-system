"""Página Meu Plano: plano da conta logada, cobrança Pix própria ("nosso
Stripe"), estorno, suporte por WhatsApp e adoção de dados antigos sem dono."""
import os

import streamlit as st

import auth_supabase
import notificacoes
import pix
import pixbilling
import plano
import persistencia


def _marcador(classe: str) -> None:
    st.markdown(f'<div class="{classe}" style="display:none"></div>', unsafe_allow_html=True)


def _email_logado() -> str | None:
    try:
        sessao = auth_supabase.sessao() or {}
        return (sessao.get("user") or {}).get("email")
    except Exception:
        return None


def _eh_admin() -> bool:
    """Admin = e-mail configurado em ADMIN_EMAIL (se não configurar, ninguém)."""
    admin = os.environ.get("ADMIN_EMAIL", "").strip().lower()
    if not admin:
        return False
    return (_email_logado() or "").strip().lower() == admin


def _whatsapp_suporte() -> str:
    num = os.environ.get("WHATSAPP_NUMERO", "").strip().removeprefix("+")
    if not num:
        return ""
    texto = "Olá! Tudo bem? Vim pelo AI Bug Triage System."
    from urllib.parse import quote

    return f"https://wa.me/{num}?text={quote(texto)}"


def render():
    import ui_comum  # lazy: ui_comum importa roteador, que importa meu_plano (ciclo)

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

    # ─── Troca de plano / cobrança (Passo 4: "nosso Stripe" via Pix) ─────────
    st.markdown("### 💳 Plano da conta")
    cobrancas = pixbilling.cobrancas_do_uid(uid)
    aberta = next((c for c in cobrancas if c.get("status") == "aguardando"), None)
    paga = next((c for c in cobrancas if c.get("status") == "confirmado"), None)
    estornadas = [c for c in cobrancas if c.get("status") == "estornado"]

    if aberta and atual == "free":
        st.info(
            f"Você tem uma cobrança **aguardando pagamento** de **{pixbilling.preco_texto()}/mês**. "
            "Pague o Pix abaixo para ativar o Premium."
        )
        _exibir_checkout_pix(aberta, uid)
    elif atual == "pago" and paga:
        st.success(f"Seu **Premium** está ativo — pago em **{pixbilling.preco_texto()}/mês**.")
        _marcador("marca-plano-estorno")
        if st.button("↩️ Solicitar estorno", key="btn_solicitar_estorno"):
            pedido = pixbilling.solicitar_estorno(paga["id"], motivo="Solicitado pelo usuário")
            if pedido:
                _avisar_admin(
                    f"Estorno solicitado: cobrança {pedido['id']} de {pedido.get('uid')} "
                    f"({pixbilling.preco_texto()})"
                )
                st.success("Estorno solicitado! O responsável vai devolver o valor via Pix.")
                st.rerun()
        if estornadas:
            st.caption("Últimos estornos desta conta:")
            for e in estornadas[:3]:
                st.caption(f"• {e.get('id')} — {pixbilling.status_rotulo('estornado')} ({e.get('motivo') or '—'})")
    else:
        st.caption(
            f"Adquira o **Premium** por **{pixbilling.preco_texto()}/mês** — pague no Pix, "
            "sem cartão. O pagamento é confirmado pelo responsável."
        )
        _marcador("marca-plano-comprar")
        if st.button(f"⭐ Assinar Premium — {pixbilling.preco_texto()}/mês", key="btn_assinar", type="primary"):
            cobranca = pixbilling.gerar_cobranca(uid)
            if cobranca:
                st.rerun()

    # Painel do admin (só para o dono): fila de pagamentos + estornos
    if _eh_admin():
        _exibir_painel_admin()

    # ─── Suporte por WhatsApp ────────────────────────────────────────────────
    wa = _whatsapp_suporte()
    if wa:
        st.markdown("### 💬 Suporte")
        _c_txt, _c_wa = st.columns([3.2, 1], vertical_alignment="center")
        with _c_txt:
            st.caption("Dúvidas sobre plano, pagamento ou estorno? Fale direto com a gente pelo WhatsApp.")
        with _c_wa:
            _exibir_botao_whatsapp(wa)
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

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


def _exibir_checkout_pix(cobranca: dict, uid: str) -> None:
    """Mostra o QR Pix + copia-e-cola da cobrança pendente e o botão 'Já paguei'."""
    _c1, _c2 = st.columns([1, 1.4])
    with _c1:
        payload = pixbilling.payload_pix(cobranca.get("valor"))
        if payload:
            st.image(pix.qrcode_png_base64(payload), width=210, caption="Pix QR Code")
        else:
            st.caption("Pix não configurado neste ambiente (PIX_KEY/PIX_COPIA).")
    with _c2:
        st.markdown(
            f"**Valor:** {pixbilling.preco_texto()}/mês  \n"
            f"**Status:** {pixbilling.status_rotulo(cobranca.get('status'))}"
        )
        if payload:
            st.code(payload, language=None)
        st.caption("Pague no app do seu banco e clique em 'Já paguei' para avisar o responsável.")
        _marcador("marca-plano-paguei")
        if st.button("✅ Já paguei", key=f"btn_paguei_{cobranca['id']}", type="primary"):
            _avisar_admin(
                f"Pagamento avisado: {pixbilling.preco_texto()} de {uid} (cobrança {cobranca['id']})"
            )
            st.success("Aviso enviado! O responsável vai confirmar seu pagamento.")
            st.rerun()


def _exibir_painel_admin() -> None:
    """Painel do dono: confirma pagamentos e processa estornos."""
    st.markdown("### 🛠️ Painel do responsável")
    pendentes = pixbilling.pendentes()
    if pendentes:
        st.success(f"**{len(pendentes)}** pagamento(s) aguardando confirmação.")
        for c in pendentes:
            with st.expander(f"💳 {pixbilling.preco_texto()} de {c.get('uid')} ({c.get('criado_em')})"):
                st.caption(f"cobrança {c['id']} · status: {pixbilling.status_rotulo(c.get('status'))}")
                _marcador("marca-plano-admin-conf")
                if st.button("✅ Confirmar pagamento", key=f"admin_confirmar_{c['id']}", type="primary"):
                    feito = pixbilling.confirmar_cobranca(c["id"])
                    if feito:
                        _avisar_admin(f"Premium confirmado para {c.get('uid')}")
                        st.success(f"Premium ativado para {c.get('uid')}.")
                        st.rerun()
                _marcador("marca-plano-admin-canc")
                if st.button("✖️ Cancelar cobrança", key=f"admin_cancelar_{c['id']}"):
                    if pixbilling.cancelar_cobranca(c["id"]):
                        st.success("Cobrança cancelada.")
                        st.rerun()
    else:
        st.caption("Nenhum pagamento aguardando confirmação.")

    estornos = pixbilling.estornos()
    if estornos:
        st.warning("**Estornos solicitados** — devolva o valor via Pix e marque abaixo:")
        for c in estornos:
            with st.expander(f"↩️ Estorno de {c.get('uid')} ({pixbilling.preco_texto()})"):
                st.caption(f"cobrança {c['id']} · motivo: {c.get('motivo') or '—'}")
                _marcador("marca-plano-admin-estorno")
                if st.button("↩️ Marcar como devolvido", key=f"admin_estornar_{c['id']}", type="primary"):
                    if pixbilling.estornar(c["id"], motivo="Devolvido via Pix pelo responsável"):
                        st.success("Estorno registrado. O usuário voltou ao Basic.")
                        st.rerun()


def _avisar_admin(mensagem: str) -> None:
    """Dispara alerta para o dono (e-mail/Discord) quando algo exige ação."""
    if not mensagem:
        return
    try:
        # notificacoes só dispara para CRÍTICA/ALTA; usamos "ALTA" para chamar atenção.
        notificacoes.notificar_discord("ALTA", mensagem)
        notificacoes.notificar_email("ALTA", mensagem)
    except Exception:
        pass


def _icone_whatsapp_inline() -> str:
    """Símbolo do WhatsApp embutido como SVG (mesmo jeito do 'G' do Google no login)."""
    return (
        '<svg viewBox="0 0 24 24" width="17" height="17" '
        'style="vertical-align:middle;margin-right:9px" xmlns="http://www.w3.org/2000/svg">'
        '<path fill="currentColor" d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/>'
        '</svg>'
    )


def _exibir_botao_whatsapp(link: str) -> None:
    """Botão quadrado do WhatsApp (só o símbolo, centralizado) no verde da marca."""
    st.markdown(
        f"""
        <style>
        .wa-quadrado {{
            display:flex; align-items:center; justify-content:center;
            width:52px; height:52px; border-radius:12px;
            background:#25D366; color:#ffffff; border:none; cursor:pointer;
            box-shadow:0 4px 12px rgba(37,211,102,.35);
            transition:transform .15s ease, filter .15s ease;
        }}
        .wa-quadrado:hover {{ transform:scale(1.06); filter:brightness(1.06); }}
        </style>
        <a href="{link}" target="_blank" style="text-decoration:none">
            <button class="wa-quadrado">{_icone_whatsapp_inline()}</button>
        </a>
        """,
        unsafe_allow_html=True,
    )