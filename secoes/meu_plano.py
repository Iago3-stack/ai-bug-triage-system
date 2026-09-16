"""Página Meu Plano: plano da conta logada, cobrança Pix própria ("nosso
Stripe"), estorno, suporte por WhatsApp e adoção de dados antigos sem dono."""
import os

import streamlit as st
import streamlit.components.v1 as components

import auth_supabase
import notificacoes
import pagbank
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

    _lembrete = st.session_state.pop("meu_plano_lembrete", None)
    if _lembrete:
        st.success(_lembrete)

    st.markdown("""
    <div style="height:3px;width:100%;background:linear-gradient(90deg,transparent,#25D366,#2E7CF6,#7c3aed,transparent);border-radius:999px;margin:8px 0"></div>
    """, unsafe_allow_html=True)

    if atual == "pago":
        _teste = plano.teste_premium_restante(uid)
        if _teste:
            _badge = (
                '<span style="background:rgba(46,124,246,.16);color:#60a5fa;border:1px solid rgba(46,124,246,.5);'
                'border-radius:999px;padding:4px 14px;font-size:12px;font-weight:800;letter-spacing:.03em">🎁 Teste Premium 7 dias</span>'
            )
            _frase = ("Você está no <b style='color:#60a5fa'>Teste Premium 7 dias</b> — acesso completo liberado "
                      "até esta data expirar. Depois disso, a conta volta ao Basic.")
        else:
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

    with st.container(border=True):
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

        if aberta:
            if aberta.get("pix_copia_pagbank"):
                st.info(
                    "Você tem uma cobrança **aguardando pagamento** para ativar o Premium. "
                    "Pague o Pix abaixo — a confirmação é automática."
                )
            else:
                st.info(
                    "Você tem uma cobrança **aguardando pagamento** para ativar o Premium. "
                    "Pague o Pix abaixo e clique em **✅ Já paguei**."
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
                    _lembrete_refresh("↩️ Pedido de estorno enviado ao responsável!")
                    st.rerun()
            if estornadas:
                st.caption("Últimos estornos desta conta:")
                for e in estornadas[:3]:
                    st.caption(f"• {e.get('id')} — {pixbilling.status_rotulo('estornado')} ({e.get('motivo') or '—'})")
        else:
            st.caption(
                f"Adquira o **Premium** por **{pixbilling.preco_texto()}/mês** — pague no Pix, "
                "sem cartão."
            )
            if pagbank.configurado():
                st.caption(
                    "Pagamento com **confirmação automática**: pague o QR Code abaixo e o "
                    "Premium libera sozinho (webhook PagBank)."
                )
                _cpf = st.text_input(
                    "CPF do titular (para o Pix)",
                    key="cpf_premium",
                    placeholder="000.000.000-00",
                    help="O CPF identifica o pagador no Pix do PagBank. Campo opcional.",
                )
                _nome_premium = st.text_input(
                    "Nome do titular (opcional)", key="nome_premium",
                    placeholder="Como aparece na sua conta",
                )
            _marcador("marca-plano-comprar")
            if st.button(f"⭐ Assinar Premium — {pixbilling.preco_texto()}/mês", key="btn_assinar", type="primary"):
                _nome = ""
                _email = ""
                if pagbank.configurado():
                    _nome = _nome_premium
                    _email = _email_logado() or ""
                cobranca = pixbilling.gerar_cobranca(uid, cpf=_cpf if pagbank.configurado() else "", nome=_nome, email=_email)
                if cobranca:
                    _lembrete_refresh(
                        "⭐ Cobrança criada! Pague o Pix e aguarde a confirmação."
                        if not cobranca.get("pix_copia_pagbank")
                        else "⭐ Cobrança criada! O Premium é liberado automaticamente após o pagamento."
                    )
                    st.rerun()

        # Painel do admin (só para o dono): fila de pagamentos + estornos
        if _eh_admin():
            _exibir_painel_admin()

        # ─── Suporte por WhatsApp ────────────────────────────────────────────────
        wa = _whatsapp_suporte()
        if wa:
            st.markdown("### 💬 Suporte")
            st.markdown(
                'Dúvidas sobre plano, pagamento ou estorno? Fale direto com a gente '
                f'pelo WhatsApp. <a href="{wa}" target="_blank" rel="noopener" '
                'style="text-decoration:none;vertical-align:middle">'
                '<span style="display:inline-flex;align-items:center;background:#25D366;'
                'color:#ffffff;padding:7px 14px 7px 10px;border-radius:10px;font-weight:700;'
                'font-size:13px;box-shadow:0 4px 12px rgba(37,211,102,.35);white-space:nowrap;">'
                f'{_icone_whatsapp_inline()}<span style="margin-left:-4px">WhatsApp</span>'
                '</span></a>',
                unsafe_allow_html=True,
            )
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # ─── Comparativo Basic × Premium ─────────────────────────────────────────
    with st.expander("💼 Comparar planos — Basic × Premium", expanded=False):
        st.markdown('<div class="marca-plano" style="display:none"></div>', unsafe_allow_html=True)
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

    _aviso_fixo_atualizar(automatico=pagbank.configurado())


def _exibir_checkout_pix(cobranca: dict, uid: str) -> None:
    """Mostra o QR Pix + copia-e-cola da cobrança pendente e o botão 'Já paguei'."""
    automatico = bool(cobranca.get("pix_copia_pagbank"))
    _c1, _c2 = st.columns([1, 1.4])
    with _c1:
        payload = pixbilling.pix_da_cobranca(cobranca)
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
            _exibir_copia_e_cola(payload)
        if automatico:
            st.caption(
                "🔔 **Responsável é avisado e o Premium libera automaticamente** assim que o "
                "PagBank confirmar o pagamento (webhook). O botão abaixo é só um reforço manual."
            )
        else:
            st.caption("Pague no app do seu banco e clique em 'Já paguei' para avisar o responsável.")
        _marcador("marca-plano-paguei")
        if st.button("✅ Já paguei", key=f"btn_paguei_{cobranca['id']}", type="primary"):
            _avisar_admin(
                f"Pagamento avisado: {pixbilling.preco_texto()} de {uid} (cobrança {cobranca['id']})"
            )
            _lembrete_refresh("✅ Pagamento avisado! Aguarde a confirmação do responsável.")
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
                        _lembrete_refresh(f"✅ Premium confirmado! {c.get('uid')} ganhou acesso.")
                        st.rerun()
                _marcador("marca-plano-admin-canc")
                if st.button("✖️ Cancelar cobrança", key=f"admin_cancelar_{c['id']}"):
                    if pixbilling.cancelar_cobranca(c["id"]):
                        _lembrete_refresh("✖️ Cobrança cancelada.")
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
                        _lembrete_refresh("↩️ Estorno registrado — o usuário voltou ao Basic.")
                        st.rerun()


def _avisar_admin(mensagem: str) -> None:
    """Dispara alerta ao dono (e-mail/Discord) quando algo exige ação."""
    if not mensagem:
        return
    notificacoes.notificar_evento("Ação necessária — pagamento", mensagem)


def _lembrete_refresh(mensagem: str) -> None:
    """Guarda um aviso para exibir logo após o rerun do próximo passo do fluxo."""
    st.session_state["meu_plano_lembrete"] = mensagem


def _aviso_fixo_atualizar(automatico: bool = False) -> None:
    """Barra fixa (sticky) lembrando como o pagamento é confirmado.

    Fica sempre visível no topo da página Meu Plano — usuário e admin
    lembram de atualizar a tela para ver as mudanças refletidas.
    """
    _texto = (
        "A confirmação do Pix é automática após o pagamento. "
        "<b>Atualize a página</b> para ver o Premium ativo na tela."
        if automatico
        else "Este fluxo depende da confirmação manual do responsável. "
        "<b>Atualize a página</b> para ver as mudanças refletidas na tela."
    )
    st.markdown(
        f"""
        <style>
        /* Barra fixa "atualize a página" — tema padrão (claro) */
        .aviso-atualizar-fixo {{
            position: sticky !important;
            top: 0;
            z-index: 99;
            display: flex;
            align-items: center;
            gap: 8px;
            width: 100%;
            padding: 9px 14px;
            margin: 2px 0 14px;
            border-radius: 12px;
            background: linear-gradient(90deg, rgba(37,211,102,.18), rgba(2,132,199,.08));
            border: 1px solid rgba(37,211,102,.55);
            color: #134e34;
            font-size: 12.5px;
            font-weight: 600;
            box-shadow: 0 4px 14px rgba(15,23,42,.14);
        }}
        .aviso-atualizar-fixo b {{ color: #047857; }}
        .aviso-atualizar-fixo .icone {{ font-size: 15px; }}

        /* Tema escuro — fundo sólido escuro, texto claro */
        body:has([data-st-tema="escuro"]) .aviso-atualizar-fixo {{
            background: linear-gradient(90deg, rgba(37,211,102,.16), rgba(37,211,102,.05));
            border: 1px solid rgba(37,211,102,.4);
            color: #cff7e3;
            box-shadow: 0 4px 14px rgba(15,23,42,.25);
        }}
        body:has([data-st-tema="escuro"]) .aviso-atualizar-fixo b {{ color: #86efac; }}
        </style>
        <div class="aviso-atualizar-fixo">
            <span class="icone">🔄</span>
            <span>{_texto}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _icone_whatsapp_inline() -> str:
    """Símbolo do WhatsApp embutido como SVG (mesmo jeito do 'G' do Google no login)."""
    return (
        '<svg viewBox="0 0 24 24" width="17" height="17" '
        'style="vertical-align:middle;margin-right:9px" xmlns="http://www.w3.org/2000/svg">'
        '<path fill="currentColor" d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/>'
        '</svg>'
    )


def _exibir_copia_e_cola(payload: str) -> None:
    """Cartão 'Pix Copia e Cola' profissional: código mascarado + botão Copiar.

    O código completo fica oculto na tela (e não vaza para o histórico da
    página); um toque no botão copia o valor para a área de transferência e
    o usuário só cola no banco. O iframe roda o JS de cópia (a Clipboard API
    exige contexto seguro — https, ok na Cloud).
    """
    import html as _html
    import json as _json

    final = _html.escape(payload[-4:] if payload else "")
    js = _json.dumps(payload, ensure_ascii=False)
    cartao = f"""
    <style>
      .pix-card {{
        font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
        background:#0b1526; border:1px solid #22334f; border-radius:14px;
        padding:14px 16px 12px; color:#cbd5e1; min-width:280px;
        box-shadow:0 4px 14px rgba(15,23,42,.28);
      }}
      .pix-top {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }}
      .pix-rot {{ font-size:10px; letter-spacing:.16em; font-weight:800; color:#94a3b8; }}
      .pix-seg {{ font-size:11px; color:#4ade80; font-weight:700; }}
      .pix-masc {{
        font-family:ui-monospace,'SF Mono',Consolas,monospace; font-size:13px;
        color:#94a3b8; letter-spacing:.08em; text-align:center; user-select:none;
        background:#101c31; border:1px dashed #2b3d5c; border-radius:9px; padding:9px 10px;
        margin-bottom:11px; overflow:hidden; white-space:nowrap;
      }}
      .pix-copiar {{
        width:100%; padding:11px; border:none; border-radius:10px; cursor:pointer;
        font-weight:800; font-size:14px; letter-spacing:.02em; color:#022c0e;
        background:#25D366; box-shadow:0 4px 12px rgba(37,211,102,.30);
        transition:transform .12s ease, filter .12s ease;
      }}
      .pix-copiar:hover {{ transform:translateY(-1px); filter:brightness(1.05); }}
      .pix-aviso {{ display:block; text-align:center; margin-top:9px; font-size:12px;
        font-weight:700; color:#4ade80; opacity:0; transition:opacity .25s ease; min-height:14px; }}
    </style>
    <div class="pix-card">
      <div class="pix-top">
        <span class="pix-rot">PIX COPIA E COLA</span>
        <span class="pix-seg">&#128274; oculto</span>
      </div>
      <div class="pix-masc" title="Clique em Copiar para usar o código">•••• •••• •••• •••• <span style="color:#e2e8f0">{final}</span></div>
      <button class="pix-copiar" onclick="copiar()">&#128203; Copiar código do Pix</button>
      <span class="pix-aviso" id="pixtoast">Copiado! Cole no app do banco e pague.</span>
    </div>
    <script>
      var _pix = {js};
      function copiar() {{
        var avisar = function() {{
          var a = document.getElementById('pixtoast');
          if (a) {{ a.style.opacity = 1; setTimeout(function(){{ a.style.opacity = 0; }}, 2600); }}
        }};
        var tradicional = function() {{
          var e = document.createElement('textarea');
          e.value = _pix; e.style.position = 'fixed'; e.style.opacity = '0';
          document.body.appendChild(e); e.select(); e.setSelectionRange(0, e.value.length);
          try {{ document.execCommand('copy'); }} catch (_) {{}}
          document.body.removeChild(e); avisar();
        }};
        if (navigator.clipboard && window.isSecureContext) {{
          navigator.clipboard.writeText(_pix).then(avisar, tradicional);
        }} else {{ tradicional(); }}
      }}
    </script>
    """
    components.html(cartao, height=175)


