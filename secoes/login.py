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
    tema = ui_tema.tema_atual()
    st.markdown(
        f"""
        <div style="text-align:center;opacity:.75;font-size:13px">
          <a href="/?tema={tema}" style="text-decoration:none">🏠 Voltar ao Início</a>
        </div>
        """,
        unsafe_allow_html=True,
    )
    return True