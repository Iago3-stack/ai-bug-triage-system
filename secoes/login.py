# Passo 2 (SaaS) — Tela de login/cadastro via Supabase Auth.
#
# A renderiza() DEVE rodar ANTES da página protegida: quando o usuário não está
# logado e o Supabase está configurado, exibe o formulário e bloqueia a página
# (retorna True). Assim a Ferramenta e o Dashboard ficam privados, e a Início
# continua pública.

import streamlit as st

import auth_supabase
import ui_tema
import sessao_persist


def render() -> bool:
    """Bloqueia (e desenha o login) quando necessário. Retorna True se bloqueou."""
    if auth_supabase.usuario_logado() or not auth_supabase.disponivel():
        return False

    st.markdown(
        """
        <div style="text-align:center;margin:26px 0 4px">
          <div style="font-size:42px;line-height:1">🔐</div>
          <div style="font-size:24px;font-weight:700;margin-top:8px">Acesso à Ferramenta de QA</div>
          <div style="opacity:.7;font-size:13px;margin-top:4px">Ferramenta e Dashboard exigem conta · o Início continua público</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    esquerda, direita = st.columns([1.25, 1])

    with st.container(border=True):
        st.markdown(
            "<div style='display:flex;align-items:center;gap:10px;margin:6px 0'>"
            "<div style='flex:1;height:1px;background:rgba(128,128,128,.25)'></div>"
            "<span style='opacity:.55;font-size:12px'>seu e-mail</span>"
            "<div style='flex:1;height:1px;background:rgba(128,128,128,.25)'></div>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.markdown("#### Entre na sua conta")
        with st.form("form_login", clear_on_submit=False):
            st.markdown(
                '<div style="display:flex;align-items:center;gap:8px;margin:2px 0 10px">'
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="20" height="20">'
                '<path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>'
                '<path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>'
                '<path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>'
                '<path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>'
                '</svg>'
                '<span class="marca-g-google">Cadastre ou entre com seu e-mail do Google</span>'
                '</div>',
                unsafe_allow_html=True,
            )
            email = st.text_input("E-mail", placeholder="voce@empresa.com", key="_auth_email")
            senha = st.text_input(
                "Senha",
                type="password",
                placeholder="mínimo 8 caracteres",
                key="_auth_senha",
            )
            entrar_col, criar_col = st.columns(2)
            with entrar_col:
                st.markdown('<div class="marca-entrar" style="display:none"></div>', unsafe_allow_html=True)
                entrar = st.form_submit_button("🚪 Entrar", use_container_width=True)
            with criar_col:
                st.markdown('<div class="marca-criar" style="display:none"></div>', unsafe_allow_html=True)
                criar = st.form_submit_button("✨ Criar conta grátis", use_container_width=True)

        if entrar or criar:
            if criar:
                ok, msg, dados = auth_supabase.cadastrar(email, senha)
                if ok:
                    if dados and (dados.get("user") or {}).get("confirmed_at"):
                        st.success(msg)
                    else:
                        st.success(
                            "Conta criada! Enviamos um e-mail de confirmação — "
                            "acesse o link antes de entrar."
                        )
                else:
                    st.error(msg)
            else:
                ok, msg, dados = auth_supabase.logar(email, senha)
                if ok:
                    auth_supabase.guardar_sessao(dados)
                    sessao_persist.salvar(dados)  # permanece logado ao recarregar (F5)
                    st.rerun()
                else:
                    st.error(msg)

    with esquerda:
        st.caption("")
        st.markdown("""
### Por que criar uma conta?
- Seu histórico de triagens fica **isolado por usuário** no Supabase.
- Você recupera **testes, confiança (RAG) e regras** em qualquer dispositivo.
- O plano pago (**Premium**) chega por assinatura — tudo pronto aqui.
        """)

    with direita:
        st.caption("")
        st.info("""
**Já tem conta?** é só entrar com o mesmo e-mail.

**Acabou de criar?** lembre de confirmar o e-mail no link que enviarmos.
""")

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    import roteador

    with st.container():
        st.markdown('<div class="marca-voltar" style="display:none"></div>', unsafe_allow_html=True)
        _c1, _c2, _c3 = st.columns([1, 0.7, 1])
        with _c2:
            st.button(
                "🏠 Voltar ao Início",
                key="voltar_inicio",
                use_container_width=True,
                on_click=lambda: st.switch_page(roteador.PAGINAS["inicio"]),
            )
    return True