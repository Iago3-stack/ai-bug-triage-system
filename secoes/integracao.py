"""Página Integração — vitrine/tutorial das integrações Playwright e Postman."""
import streamlit as st

import roteador
from adaptadores import estruturar

_EXEMPLO_PLAYWRIGHT = """\
1) chromium › login.spec.ts:18 › teste de login com sucesso

        Error: expect(locator).toHaveText(expected)

        Expected: Bem-vindo
        Received: Erro

        at /app/tests/login.spec.ts:20:7"""

_EXEMPLO_POSTMAN = """\
❌ POST https://api.exemplo.com/v1/pagamento [500 Internal Server Error, 412B, 150ms]
→ status code is 200
AssertionError: expected response to have status code 200, but got 500
response body: {"error": "database timeout"}

• GET /health [200 OK, 24B, 5ms]"""

_ESTILO = """
<style>
/* Botão do Playwright: gradiente verde (marca Playwright) */
[data-testid="stElementContainer"]:has(.marca-int-pw) + [data-testid="stElementContainer"] [data-testid="stButton"] button,
[data-testid="stElementContainer"]:has(.marca-int-pw) + [data-testid="stElementContainer"] [data-testid="stButton"] button:hover {
    background: linear-gradient(135deg, #45ba4b 0%, #0ea5a0 100%) !important;
    color: #ffffff !important; border: none !important;
    font-weight: 800 !important; box-shadow: 0 4px 12px rgba(14, 165, 160, .35) !important;
}
[data-testid="stElementContainer"]:has(.marca-int-pw) + [data-testid="stElementContainer"] [data-testid="stButton"] button:hover {
    filter: brightness(1.08); transform: translateY(-1px);
}

/* Botão do Postman: gradiente laranja (marca Postman) */
[data-testid="stElementContainer"]:has(.marca-int-pm) + [data-testid="stElementContainer"] [data-testid="stButton"] button,
[data-testid="stElementContainer"]:has(.marca-int-pm) + [data-testid="stElementContainer"] [data-testid="stButton"] button:hover {
    background: linear-gradient(135deg, #ff6c37 0%, #f59e0b 100%) !important;
    color: #ffffff !important; border: none !important;
    font-weight: 800 !important; box-shadow: 0 4px 12px rgba(255, 108, 55, .35) !important;
}
[data-testid="stElementContainer"]:has(.marca-int-pm) + [data-testid="stElementContainer"] [data-testid="stButton"] button:hover {
    filter: brightness(1.08); transform: translateY(-1px);
}

/* Botão final "Ir para a Ferramenta": azul */
[data-testid="stElementContainer"]:has(.marca-int-fim) + [data-testid="stElementContainer"] [data-testid="stButton"] button,
[data-testid="stElementContainer"]:has(.marca-int-fim) + [data-testid="stElementContainer"] [data-testid="stButton"] button:hover {
    background: linear-gradient(135deg, #2563eb 0%, #38bdf8 100%) !important;
    color: #ffffff !important; border: none !important;
    font-weight: 800 !important; box-shadow: 0 4px 12px rgba(37, 99, 235, .35) !important;
}
[data-testid="stElementContainer"]:has(.marca-int-fim) + [data-testid="stElementContainer"] [data-testid="stButton"] button:hover {
    filter: brightness(1.08); transform: translateY(-1px);
}
</style>
"""


def render() -> None:
    st.markdown(
        '<div style="height:3px;width:100%;background:linear-gradient(90deg,transparent,#25D366,#2E7CF6,#7c3aed,transparent);border-radius:999px;margin:8px 0"></div>',
        unsafe_allow_html=True,
    )
    st.markdown(_ESTILO, unsafe_allow_html=True)

    st.markdown(
        """
        <div style="background:linear-gradient(135deg,#0f172a 0%,#1e293b 100%);
                     border:1px solid rgba(255,255,255,0.08);border-radius:12px;
                     padding:26px 28px;margin-bottom:18px">
          <div role="heading" aria-level="2"
               style="font-size:25px;font-weight:900;color:#fff;text-shadow:0 1px 4px rgba(0,0,0,.45);margin:0 0 8px">
            🔌 Integração Playwright & Postman
          </div>
          <p style="color:#cbd5e1;font-size:14.5px;line-height:1.7;margin:0">
            O <b style="color:#86efac">AI Bug Triage System</b> não substitui suas ferramentas —
            ele <b style="color:#fff">conversa com o resultado delas</b>. Você roda seus testes
            como sempre (Playwright, Postman, newman…) e, quando um falha, cola a saída aqui.
            O app <b style="color:#fff">identifica a ferramenta, extrai os campos-chave</b> e
            monta o relato completo pronto pra triagem.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### Como funciona a ponte")
    with st.container(border=True):
        _ac_cards = [
            ("🖥️", "1. Rode o teste", "Playwright, Postman Runner ou newman na sua máquina — mesmo fluxo de sempre.", "#22c55e", "#86efac"),
            ("📋", "2. Cole a falha aqui", "Copie a saída do erro e cole no campo da Ferramenta (ou use um exemplo pronto).", "#f59e0b", "#fde68a"),
            ("🤖", "3. App estrutura e analisa", "Motor NLP + IA (Gemini/Groq) + RAG → relatório Gherkin pronto para JIRA/GitHub.", "#8b5cf6", "#c4b5fd"),
        ]
        cols = st.columns(3)
        for col, (icone, titulo, desc, _cor, _cor_titulo) in zip(cols, _ac_cards):
            with col:
                st.markdown(
                    f"""
                    <div style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.12);
                                 border-radius:12px;padding:18px 16px;text-align:center;min-height:150px">
                      <div style="font-size:30px;margin-bottom:6px">{icone}</div>
                      <div style="color:{_cor_titulo};font-weight:800;font-size:14.5px;margin-bottom:6px">{titulo}</div>
                      <div style="color:#cbd5e1;font-size:13px;line-height:1.6">{desc}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown("---")

    st.markdown("#### Exemplos de saída que o app reconhece")

    pw, pm = st.columns(2)

    with pw:
        st.markdown("##### 🎭 Playwright")
        st.code(_EXEMPLO_PLAYWRIGHT, language="bash")
        e_pw = estruturar(_EXEMPLO_PLAYWRIGHT)
        if e_pw:
            st.markdown(
                f"""
                <div style="background:rgba(34,197,94,0.10);border:1px solid rgba(34,197,94,0.40);
                             border-radius:10px;padding:14px 16px;font-size:14px;line-height:1.75;color:#f8fafc">
                  <div style="display:inline-block;background:rgba(34,197,94,0.18);color:#bbf7d0;
                               border:1px solid rgba(34,197,94,0.45);border-radius:999px;padding:2px 12px;
                               font-size:12px;font-weight:800;margin-bottom:8px">✨ Extraído automaticamente:</div><br>
                  <b style="color:#86efac">• Título:</b> <code>{e_pw.get('titulo','')}</code><br>
                  <b style="color:#86efac">• Arquivo:</b> <code>{e_pw.get('local','')}</code> · <b style="color:#86efac">Linguagem:</b> <code>{e_pw.get('linguagem','')}</code><br>
                  <b style="color:#86efac">• Esperado:</b> <code>{e_pw.get('esperado','')}</code> · <b style="color:#86efac">Recebido:</b> <code>{e_pw.get('recebido','')}</code><br>
                  <b style="color:#86efac">• Severidade prévia:</b> <b style="color:#bbf7d0">{e_pw.get('severidade','')}</b>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown('<div class="marca-int-pw" style="display:none"></div>', unsafe_allow_html=True)
        if st.button("🚀 Testar isso na Ferramenta", key="vitrine_pw_ir", use_container_width=True):
            st.session_state["colar_falha_bruta"] = _EXEMPLO_PLAYWRIGHT
            st.switch_page(roteador.PAGINAS["triagem"])

    with pm:
        st.markdown("##### 📬 Postman · Newman")
        st.code(_EXEMPLO_POSTMAN, language="bash")
        e_pm = estruturar(_EXEMPLO_POSTMAN)
        if e_pm:
            st.markdown(
                f"""
                <div style="background:rgba(245,158,11,0.10);border:1px solid rgba(245,158,11,0.40);
                             border-radius:10px;padding:14px 16px;font-size:14px;line-height:1.75;color:#f8fafc">
                  <div style="display:inline-block;background:rgba(245,158,11,0.18);color:#fde68a;
                               border:1px solid rgba(245,158,11,0.45);border-radius:999px;padding:2px 12px;
                               font-size:12px;font-weight:800;margin-bottom:8px">✨ Extraído automaticamente:</div><br>
                  <b style="color:#fbbf24">• Requisição:</b> <code>{e_pm.get('requisicao','')}</code><br>
                  <b style="color:#fbbf24">• Esperado:</b> <code>{e_pm.get('status_esperado','')}</code> · <b style="color:#fbbf24">Recebido:</b> <code>{e_pm.get('status_recebido','')}</code><br>
                  <b style="color:#fbbf24">• Erro:</b> <code>{e_pm.get('erro','')}</code><br>
                  <b style="color:#fbbf24">• Severidade prévia:</b> <b style="color:#fde68a">{e_pm.get('severidade','')}</b>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown('<div class="marca-int-pm" style="display:none"></div>', unsafe_allow_html=True)
        if st.button("🚀 Testar isso na Ferramenta", key="vitrine_pm_ir", use_container_width=True):
            st.session_state["colar_falha_bruta"] = _EXEMPLO_POSTMAN
            st.switch_page(roteador.PAGINAS["triagem"])

    st.markdown("---")

    st.markdown(
        """
        <div style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.10);
                     border-radius:10px;padding:18px 20px;margin-top:4px">
          <div style="color:#fff;font-weight:700;font-size:14px;margin-bottom:6px">💡 Não tem Playwright ou Postman instalados?</div>
          <div style="color:#cbd5e1;font-size:13px;line-height:1.65">
            Sem problema. Abaixo do campo <b style="color:#fff">Colar falha bruta</b> na
            <b style="color:#86efac">Ferramenta</b> já existem botões
            <code>🎯 Exemplo Playwright</code> e <code>🎯 Exemplo Postman</code> que
            preenchem o campo automaticamente com um caso real. Clique, revise e execute —
            nenhum software extra necessário.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="marca-int-fim" style="display:none"></div>', unsafe_allow_html=True)
    if st.button("🔍 Ir para a Ferramenta de Triagem", key="vitrine_cta_final", use_container_width=True):
        st.switch_page(roteador.PAGINAS["triagem"])