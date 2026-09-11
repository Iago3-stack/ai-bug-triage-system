"""Partes comuns do app: versão, Pix, modal de configurações, sidebar e rodapé."""
import streamlit as st

import jira_client
import notificacoes
import hero_animado
import pix
import ui_tema

VERSAO = "v2.6.18"

# Símbolo oficial do Pix (Banco Central) — PD-textlogo via Wikimedia Commons.
# Símbolo oficial do Pix (Banco Central) — PD-textlogo via Wikimedia Commons.
# Só os 3 paths verdes da marca (o "losango"), sem a tipografia do logo.
_PIX_SIMBOLO_PATHS = (
    '<path d="m 596.82737,86.620206 c -3.08045,0 -5.97782,-1.19944 -8.15622,-3.37679 '
    "l -11.77678,-11.77713 c -0.82691,-0.82903 -2.26801,-0.82656 -3.09456,0 l -11.81982,11.82017 "
    "c -2.17841,2.17734 -5.07577,3.37679 -8.15623,3.37679 h -2.32092 l 14.9158,14.915444 "
    "c 4.65807,4.65808 12.21069,4.65808 16.86912,0 l 14.95813,-14.958484 z\"/>"
    '<path d="m 553.82362,44.963326 c 3.08046,0 5.97782,1.19944 8.15622,3.37679 l 11.81982,11.82193 '
    "c 0.85125,0.85161 2.2412,0.85479 3.09457,-10e-4 l 11.77678,-11.77784 c 2.1784,-2.17735 5.07576,-3.37679 "
    "8.15622,-3.37679 h 1.41852 l -14.95778,-14.95813 c -4.65878,-4.658432 -12.2114,-4.658432 -16.86948,0 "
    "l -14.91509,14.91509 z\"/>"
    '<path d="m 610.61844,57.378776 -9.03922,-9.03922 c -0.19897,0.0797 -0.41452,0.12946 -0.64206,0.12946 '
    "h -4.10986 c -2.12478,0 -4.20476,0.86184 -5.70618,2.36432 l -11.77643,11.77678 c -1.10207,1.10208 "
    "-2.55022,1.65347 -3.99697,1.65347 -1.44815,0 -2.89524,-0.55139 -3.99697,-1.65241 l -11.82088,-11.82088 "
    "c -1.50142,-1.50283 -3.5814,-2.36431 -5.70618,-2.36431 h -5.05354 c -0.21555,0 -0.41698,-0.0508 "
    "-0.60713,-0.12242 l -9.07521,9.07521 c -4.65843,4.65843 -4.65843,12.2107 0,16.86913 l 9.07486,9.07485 "
    "c 0.1905,-0.0716 0.39193,-0.12241 0.60748,-0.12241 h 5.05354 c 2.12478,0 4.20476,-0.86148 5.70618,-2.36396 "
    "l 11.81982,-11.81982 c 2.13643,-2.13466 5.8607,-2.13537 7.995,0.001 l 11.77643,11.77573 "
    "c 1.50142,1.50248 3.5814,2.36431 5.70618,2.36431 h 4.10986 c 0.22754,0 0.44309,0.0497 0.64206,0.12947 "
    "l 9.03922,-9.03922 c 4.65808,-4.65843 4.65808,-12.2107 0,-16.86913\"/>"
)


_TEXTO_APOIE = "Apoie este projeto"


def _svg_pix(tamanho: int = 16, cor: str = "#32bcad") -> str:
    # viewBox real do símbolo (paths nas coordenadas originais do logo oficial):
    # bbox medido = x 535.0..613.0, y 27.0..104.0 (78x77) -> margem de 4 unidades
    altura = max(10, round(tamanho * 85 / 86))
    return (
        f'<svg width="{tamanho}" height="{altura}" viewBox="531 23 86 85" '
        f'fill="{cor}" role="img" aria-label="Pix" style="display:inline-block">'
        f"{_PIX_SIMBOLO_PATHS}</svg>"
    )


_TEXTO_APOIE = "Apoie este projeto"

repo_url = "https://github.com/Iago3-stack/ai-bug-triage-system/"

_GITHUB_PATHS = (
    '<path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.5 7.5 0 014 0c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0016 8c0-4.42-3.58-8-8-8z"/>'
)


def _svg_github(tamanho: int = 16, cor: str = "currentColor") -> str:
    """Ícone oficial do GitHub (octocat), mesmo das colunas Repositório/Perfil."""
    return (
        f'<svg width="{tamanho}" height="{tamanho}" viewBox="0 0 16 16" fill="{cor}" '
        f'role="img" aria-label="GitHub" style="display:inline-block">{_GITHUB_PATHS}</svg>'
    )


def abrir_configuracoes():
    @st.dialog("⚙️ Configurações", width="large")
    def abrir_configuracoes():
        st.markdown('<div class="marca-config" style="display:none"></div>', unsafe_allow_html=True)

        # 🎨 Tema (claro/escuro — fonte de verdade é a URL ?tema=)
        st.markdown('<div class="campo-tit tit-modal-sec" style="font-weight:600;color:#0f172a;margin-bottom:2px">🎨 Tema</div>', unsafe_allow_html=True)
        _tcols = st.columns(2)
        for _tc, (_tv, _tl) in zip(_tcols, (("claro", "☀️ Claro"), ("escuro", "🌙 Escuro"))):
            _ativo = ui_tema.tema_atual() == _tv
            with _tc:
                st.markdown(
                    f'<div class="marca-tema marca-tema-{_tv}{" tema-ativo" if _ativo else ""}" style="display:none"></div>',
                    unsafe_allow_html=True,
                )
                if st.button(_tl, key=f"tema_{_tv}", width="stretch"):
                    st.session_state["tema"] = _tv
                    st.query_params["tema"] = _tv
                    st.session_state["_reabrir_config"] = True  # st.rerun() fecha o dialog; reabre abaixo
                    st.rerun()

        st.markdown("---")

        # 🔑 Jira — exportação de relatórios (sub-expander azul persistente p/ ficar visível no tema claro)
        with st.expander("🔑 Jira — configurar exportação"):
            st.markdown('<div class="marca-jira" style="display:none"></div>', unsafe_allow_html=True)
            if not jira_client.configurado():
                st.caption("Cole suas credenciais para ativar o botão 'Exportar para Jira'.")
                _jc1, _jc2 = st.columns(2)
                j_email = _jc1.text_input("E-mail Atlassian", key="jira_email")
                j_token = _jc2.text_input("API Token", type="password", key="jira_token")
                j_key = _jc1.text_input("Chave do projeto", placeholder="ex.: KAN", key="jira_key")
                j_issue_type = _jc2.text_input("Tipo de item (padrão: Tarefa)", placeholder="ex.: Tarefa", key="jira_issue_type")
                if st.button("Salvar configuração (sessão)", use_container_width=True):
                    jira_client.configurar(j_email, j_token, j_key, j_issue_type)
                    if jira_client.configurado():
                        st.success("✅ Jira configurado nesta sessão!")
                    else:
                        st.error("Preencha e-mail, token e chave do projeto.")
            else:
                st.markdown("**🔑 Jira**")
                st.success("✅ Jira configurado nesta sessão")
                st.caption("Botão 'Exportar para Jira' ativo.")
                if st.button("🔄 Reconectar / trocar credenciais", use_container_width=True):
                    limpar = getattr(jira_client, "limpar_config", None)
                    if limpar is not None:
                        limpar()
                        st.session_state["_reabrir_config"] = True
                        st.rerun()
                    else:
                        st.error("Cache antigo detectado — clique em 'Manage app' > 'Rebuild' (limpa o cache) e rode a triagem de novo.")

        st.markdown("---")

        # 🔔 Notificações — cada usuário/empresa configura o seu (só nesta sessão)
        with st.expander("🔔 Notificações (CRÍTICA/ALTA)"):
            st.markdown('<div class="marca-notif" style="display:none"></div>', unsafe_allow_html=True)
            st.caption("Alerta automático quando uma triagem resultar em **CRÍTICA** ou **ALTA**. "
                       "O que você salvar aqui vale **só para a sua sessão** (seu navegador) — cada visitante tem o seu; "
                       "o config do dono (secrets/.env) continua como padrão e nada é gravado em disco.")
            _nc1, _nc2 = st.columns(2)
            _ovr = notificacoes.config_sessao()
            n_discord = _nc1.text_input(
                "Webhook do Discord (só se quiser receber no seu canal)", key="cfg_discord",
                placeholder="https://discord.com/api/webhooks/...",
                value=_ovr.get("DISCORD_WEBHOOK", ""))
            n_para = _nc2.text_input(
                "E-mail de destino (só se quiser receber no seu e-mail)", key="cfg_para",
                placeholder="ex.: qa@empresa.com",
                value=_ovr.get("ALERTA_EMAIL_TO", ""))
            n_user = _nc1.text_input(
                "Usuário SMTP (remetente)", key="cfg_user",
                placeholder="ex.: app@gmail.com",
                value=_ovr.get("SMTP_USER", ""))
            n_senha = _nc2.text_input(
                "Senha / App Password (SMTP)", type="password", key="cfg_senha",
                placeholder="Digite seu App Password (o do dono fica em Secrets, preenchido automaticamente no envio)",
                value=_ovr.get("SMTP_PASS", ""))
            n_host = _nc1.text_input(
                "Host SMTP", key="cfg_host", placeholder="smtp.gmail.com",
                value=_ovr.get("SMTP_HOST", ""))
            n_porta = _nc2.text_input(
                "Porta", key="cfg_porta", placeholder="587",
                value=_ovr.get("SMTP_PORT", ""))
            with st.container():
                if st.button("💾 Salvar notificações (sessão)", key="cfg_salvar", use_container_width=True):
                    notificacoes.set_config(
                        DISCORD_WEBHOOK=n_discord, ALERTA_EMAIL_TO=n_para, SMTP_USER=n_user,
                        SMTP_PASS=n_senha, SMTP_HOST=n_host, SMTP_PORT=n_porta,
                    )
                    st.success("✅ Notificações desta sessão salvas.")
                st.markdown('<div class="marca-notif-salvar" style="display:none"></div>', unsafe_allow_html=True)

            _t1, _t2 = st.columns(2)
            with _t1:
                st.markdown('<div class="marca-notif-disc" style="display:none"></div>', unsafe_allow_html=True)
                if st.button("🔔 Testar Discord", key="cfg_teste_disc", width="stretch"):
                    try:
                        _ok, _msg = notificacoes.testar_discord()
                    except Exception as _e:
                        _ok, _msg = False, f"Falha inesperada ao testar o Discord ({type(_e).__name__})."
                    (st.success if _ok else st.error)(_msg)
            with _t2:
                st.markdown('<div class="marca-notif-mail" style="display:none"></div>', unsafe_allow_html=True)
                if st.button("✉️ Testar e-mail", key="cfg_teste_email", width="stretch"):
                    try:
                        _ok, _msg = notificacoes.testar_email()
                    except Exception as _e:
                        _ok, _msg = False, f"Falha inesperada ao testar o e-mail ({type(_e).__name__})."
                    (st.success if _ok else st.error)(_msg)
            with st.container():
                if st.button("↩️ Limpar meu config (voltar ao do dono)", key="cfg_limpar", width="stretch"):
                    if notificacoes.config_sessao():
                        notificacoes.limpar_config_sessao()
                        st.success("Override desta sessão removido.")
                    else:
                        st.info("Nenhum override ativo — já usa o config do dono.")
                st.markdown('<div class="marca-notif-limpar" style="display:none"></div>', unsafe_allow_html=True)

            # Status renderizado DEPOIS das ações para refletir o estado pós-clique no mesmo run
            st.markdown('<div class="notif-st-tit">📊 Status</div>', unsafe_allow_html=True)
            disc_ok = notificacoes.discord_configurado()
            mail_ok = notificacoes.email_configurado()
            st.markdown(
                f'<div class="notif-st-linha"><span class="notif-st-lb">🔔 Discord:</span> '
                f'<span class="notif-st-{"ok" if disc_ok else "falta"}">{"✅ configurado" if disc_ok else "❌ sem webhook"}</span></div>',
                unsafe_allow_html=True)
            st.markdown(
                f'<div class="notif-st-linha"><span class="notif-st-lb">✉️ E-mail:</span> '
                f'<span class="notif-st-{"ok" if mail_ok else "falta"}">{"✅ configurado" if mail_ok else "❌ sem destinatário/usuário/senha"}</span></div>',
                unsafe_allow_html=True)



def sidebar_comum():
    if st.sidebar.button("⚙️ Configurações", key="abrir_config", type="primary", width="stretch", help="Tema, Jira e notificações"):
        abrir_configuracoes()

    # Um botão DENTRO do dialog usou st.rerun() (ex.: trocar tema), que fecha o modal.
    # Este flag reabre o modal com o corpo re-renderizado (marcas/estilos atualizados).
    if st.session_state.pop("_reabrir_config", False):
        abrir_configuracoes()

    # --- AUTENTICAÇÃO (Supabase Auth — passo 2 SaaS) ---
    try:
        import auth_supabase

        if auth_supabase.disponivel():
            _usuario = auth_supabase.usuario_logado()
            if _usuario:
                st.sidebar.markdown(
                    f"""
                    <div style="display:flex;align-items:center;gap:8px;background:rgba(46,124,246,.10);
                                border:1px solid rgba(46,124,246,.25);border-radius:10px;padding:8px 10px;
                                font-size:12px;color:#e2e8f0;margin-bottom:8px">
                      👤 <b>{_usuario}</b>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.sidebar.button("🚪 Sair", use_container_width=True, key="btn_sair"):
                    auth_supabase.sair_da_conta()
                    st.rerun()
            else:
                st.sidebar.markdown(
                    '<div style="margin-bottom:10px;padding:8px 10px;border-radius:10px;'
                    "background:rgba(232,121,249,.10);border:1px solid rgba(232,121,249,.25);"
                    'font-size:12px;line-height:1.4">🔒 <b>Faça login</b> para usar a <b>Ferramenta</b> e o <b>Dashboard</b>.</div>',
                    unsafe_allow_html=True,
                )
    except Exception:
        pass

    # --- CTA: ESTRELA NO GITHUB ---
    st.sidebar.markdown("### ⭐ Apoie o projeto")
    st.sidebar.write("Se esta triagem te ajudou, dá uma estrelinha no repositório — é de graça e ajuda mais QAs a encontrarem o app.")

    st.sidebar.markdown(f"""
    <a href="{repo_url}" target="_blank">
        <button style="display:inline-flex;align-items:center;justify-content:center;gap:8px;background-color: #2E7CF6; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; width: 100%;">
            {_svg_github(16)}
            <span>Dar estrela no GitHub</span>
        </button>
    </a>
    """, unsafe_allow_html=True)
    # --- RODAPÉ DE CONTATO ---
    with st.sidebar:
        st.markdown("### Contate-me")
        hero_animado.render_contato()
    st.sidebar.markdown("""
    <div style="margin-top:14px;padding:10px 12px;border:1px solid rgba(46,124,246,.28);border-radius:10px;background:rgba(46,124,246,.06);font-size:13px;line-height:1.6">
      🐧 <b>Linux Mint Debian</b> · 🧠 Lab <b>Hack28</b><br/>
      ⚡ <i>Automatizando qualidade — um bug de cada vez.</i>
    </div>
    """, unsafe_allow_html=True)


def rodape():
    # --- RODAPÉ DE CRÉDITO (autoria blindada, visível mesmo em forks) ---
    pix_bloco = ""
    _link_pix = pix.link_pagamento()
    if _link_pix:
        pix_bloco = f"""
      <div style="flex:1 1 320px;text-align:center">
        <div style="display:inline-flex;align-items:center;gap:8px;font-size:15px;font-weight:800;color:#ffffff">{_svg_pix(18)}{_TEXTO_APOIE} 🤝</div>
        <div style="color:#94a3b8;font-size:13px;margin:6px auto 12px;max-width:340px">Este é um projeto independente, feito por uma pessoa. Se ele te ajudou, considere uma contribuição voluntária via Pix.</div>
        <a href="{_link_pix}" target="_blank" style="text-decoration:none">
          <button style="display:inline-flex;align-items:center;gap:8px;background:#25D366;color:#0b1e14;font-weight:800;font-size:14px;border:none;padding:12px 24px;border-radius:10px;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.25)">
            {_svg_pix(16, "#0b1e14")}
            Pagar com Pix via link
          </button>
        </a>
        <div style="color:#64748b;font-size:12px;margin-top:8px">Link de pagamento com valor fixo — sem desconto aplicado.</div>
      </div>"""
    elif pix.configurado():
        try:
            _payload_pix = pix.payload_configurado()
            _qr_pix = pix.qrcode_png_base64(_payload_pix)
            _chave_pix = pix.chave()
            _bloco_copia = (
                f"""
        <div style="text-align:center;margin-top:12px">
          <button id="btn-copiar-pix" onclick="copiarChave()"
                  style="display:inline-flex;align-items:center;gap:8px;background:#25D366;color:#0b1e14;font-weight:700;font-size:14px;border:none;padding:10px 22px;border-radius:8px;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.25)">
            {_svg_pix(14, "#0b1e14")}
            <span id="lbl-copiar-pix">copiar chave pix</span>
          </button>
        </div>
        <div style="color:#94a3b8;font-size:12px;margin-top:8px">Escaneie o QR Code com a câmera do seu banco — ou use o botão para copiar a chave acima.</div>
        <script>
        function copiarChave() {{
          navigator.clipboard.writeText("{pix.chave_copia()}").then(function() {{
            var l = document.getElementById('lbl-copiar-pix');
            l.textContent = '✓ chave copiada!';
            setTimeout(function() {{ l.textContent = 'copiar chave pix'; }}, 2200);
          }});
        }}
        </script>""" if _chave_pix else "\n    <div style=\"color:#64748b;font-size:12px;margin-top:8px\">Escaneie o QR Code com a câmera do seu banco — e ajude a manter este projeto open source.</div>"
            )
            pix_bloco = f"""
      <div style="flex:1 1 320px;text-align:center">
        <div style="display:inline-flex;align-items:center;gap:8px;font-size:15px;font-weight:800;color:#ffffff">{_svg_pix(18)}{_TEXTO_APOIE} 🤝</div>
        <div style="color:#94a3b8;font-size:13px;margin:6px auto 12px;max-width:340px">Este é um projeto independente, feito por uma pessoa. Se ele te ajudou, considere uma contribuição voluntária via Pix.</div>
        <img src="{_qr_pix}" width="140" style="border-radius:10px;background:#ffffff;padding:6px" alt="QR Code Pix"/>
        {_bloco_copia}
      </div>"""
        except Exception:
            pix_bloco = ""
    _footer_html = f"""
    <div style="margin-top:32px;width:100%;background:linear-gradient(135deg,#0f172a 0%,#16233c 55%,#25D366 170%);border-radius:18px 18px 0 0;color:#e2e8f0;font-size:14px;line-height:1.55">
      <div style="display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:24px;padding:26px 26px 20px">
        <div style="flex:1 1 320px;text-align:center">
          <div style="font-size:17px;font-weight:700;color:#ffffff">Gostou do <span style="color:#25D366">AI Bug Triage System</span>?</div>
          <div style="color:#94a3b8;font-size:13px;margin:6px 0 14px">Uma estrelinha no repositório ajuda mais QAs a encontrarem o app.</div>
          <a href="{repo_url}" target="_blank" style="text-decoration:none">
            <button style="display:inline-flex;align-items:center;gap:8px;background:#2E7CF6;color:#ffffff;font-weight:700;font-size:14px;border:none;padding:10px 22px;border-radius:8px;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.25)">
              {_svg_github(14)}
              Dar estrela no GitHub
            </button>
          </a>
        </div>
        {pix_bloco}
      </div>
      <div style="display:flex;justify-content:center;gap:26px;flex-wrap:wrap;padding:14px 16px;font-size:13px;color:#cbd5e1;border-top:1px solid rgba(255,255,255,.12)">
        <a href="{repo_url}" target="_blank" style="color:#cbd5e1;text-decoration:none;display:inline-flex;align-items:center;gap:6px">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.5 7.5 0 014 0c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
          Repositório
        </a>
        <a href="{repo_url}blob/main/README.md" target="_blank" style="color:#cbd5e1;text-decoration:none;display:inline-flex;align-items:center;gap:6px">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M0 1.75A.75.75 0 01.75 1h4.253c1.227 0 2.317.59 3 1.501A3.744 3.744 0 0111.006 1h4.245a.75.75 0 01.75.75v10.5a.75.75 0 01-.75.75h-4.507a2.25 2.25 0 00-1.591.659l-.622.621a.75.75 0 01-1.06 0l-.622-.621A2.25 2.25 0 005.258 13H.75a.75.75 0 01-.75-.75V1.75zm8.755 3a2.25 2.25 0 012.25-2.25H14.5v9h-3.757c-.71 0-1.4.201-1.988.557V4.75zM7.25 12.307c.588-.356 1.278-.557 1.988-.557H7.25v.557zM1.5 2.5h3.735a2.25 2.25 0 012.015 1.25v7.307a3.74 3.74 0 00-1.988-.557H1.5V2.5z"/></svg>
          Documentação
        </a>
        <a href="https://github.com/Iago3-stack" target="_blank" style="color:#cbd5e1;text-decoration:none;display:inline-flex;align-items:center;gap:6px">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.5 7.5 0 014 0c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
          Perfil
        </a>
        <a href="{repo_url}blob/main/LICENSE" target="_blank" style="color:#cbd5e1;text-decoration:none;display:inline-flex;align-items:center;gap:6px">
          ⚖️ Licença MIT
        </a>
        <a href="https://www.gov.br/anpd/pt-br" target="_blank" rel="noopener" style="color:#cbd5e1;text-decoration:none;display:inline-flex;align-items:center;gap:6px">
          🛡️ LGPD · Proteção de Dados
        </a>
      </div>
      <div style="padding:12px 16px;text-align:center;font-size:12px;color:#64748b;border-top:1px solid rgba(255,255,255,.08)">
        © {VERSAO} <b style="color:#94a3b8">Iago Nunes de Araújo</b> · 🚀 QA Automation Engineer · Estudante de IA &amp; ML (UNIASSELVI)<br/>
        Projeto original, documentado e publicado por <b style="color:#94a3b8">Iago Nunes (Iago3-stack)</b> — qualquer cópia deve manter o crédito (MIT).
      </div>
    </div>
    """
    st.iframe(_footer_html, height=560)

