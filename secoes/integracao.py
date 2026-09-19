"""Página Integração — vitrine/tutorial das integrações Playwright e Postman."""
import streamlit as st

import hero_animado
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
            ("🖥️", "1. Rode o teste", "Playwright, Postman Runner ou newman na sua máquina — mesmo fluxo de sempre.", "#15803d"),
            ("📋", "2. Cole a falha aqui", "Copie a saída do erro e cole no campo da Ferramenta (ou use um exemplo pronto).", "#b45309"),
            ("🤖", "3. App estrutura e analisa", "Motor NLP + IA (Gemini/Groq) + RAG → relatório Gherkin pronto para JIRA/GitHub.", "#6d28d9"),
        ]
        cols = st.columns(3)
        for col, (icone, titulo, desc, cor) in zip(cols, _ac_cards):
            with col:
                st.markdown(
                    f"""
                    <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;
                                 padding:18px 16px;text-align:center;min-height:150px;
                                 box-shadow:0 4px 10px rgba(15,23,42,.10)">
                      <div style="font-size:32px;margin-bottom:6px">{icone}</div>
                      <div style="color:{cor};font-weight:800;font-size:15px;margin-bottom:6px">{titulo}</div>
                      <div style="color:#0f172a;font-size:13.5px;line-height:1.65;font-weight:500">{desc}</div>
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
            _sev_pw = e_pw.get("severidade", "")
            _cor_sev_pw = "#b91c1c" if ("CRÍTICA" in _sev_pw or "ALTA" in _sev_pw) else ("#b45309" if "MÉDIA" in _sev_pw else "#0f172a")
            st.markdown(
                f"""
                <div style="background:#ffffff;border:1px solid #16a34a;border-radius:12px;
                             padding:16px 18px;font-size:14px;line-height:1.9;color:#0f172a;
                             box-shadow:0 4px 12px rgba(15,23,42,.08)">
                  <div style="display:inline-block;background:#16a34a;color:#ffffff;
                               border-radius:999px;padding:5px 15px;
                               font-size:14px;font-weight:800;letter-spacing:.02em;margin:0 0 10px">✨ Extraído automaticamente:</div><br>
                  <b style="color:#15803d">• Título:</b> <code style="background:#f1f5f9;color:#0f172a;padding:1px 7px;border-radius:6px;font-weight:600">{e_pw.get('titulo','')}</code><br>
                  <b style="color:#15803d">• Arquivo:</b> <code style="background:#f1f5f9;color:#0f172a;padding:1px 7px;border-radius:6px;font-weight:600">{e_pw.get('local','')}</code> · <b style="color:#15803d">Linguagem:</b> <code style="background:#f1f5f9;color:#0f172a;padding:1px 7px;border-radius:6px;font-weight:600">{e_pw.get('linguagem','')}</code><br>
                  <b style="color:#15803d">• Esperado:</b> <code style="background:#f1f5f9;color:#0f172a;padding:1px 7px;border-radius:6px;font-weight:600">{e_pw.get('esperado','')}</code> · <b style="color:#15803d">Recebido:</b> <code style="background:#f1f5f9;color:#0f172a;padding:1px 7px;border-radius:6px;font-weight:600">{e_pw.get('recebido','')}</code><br>
                  <b style="color:#15803d">• Severidade prévia:</b> <b style="color:{_cor_sev_pw}">{_sev_pw}</b>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown('<div class="marca-int-pw" style="display:none"></div>', unsafe_allow_html=True)
        if st.button("🚀 Testar isso na Ferramenta", key="vitrine_pw_ir", use_container_width=True):
            st.session_state["colar_falha_bruta"] = _EXEMPLO_PLAYWRIGHT
            st.switch_page(roteador.PAGINAS["triagem"])

    with pm:
        st.markdown(
            f'<h5 style="display:flex;align-items:center;gap:8px;margin:0">{hero_animado._svg_postman(20)}<span>Postman · Newman</span></h5>',
            unsafe_allow_html=True,
        )
        st.code(_EXEMPLO_POSTMAN, language="bash")
        e_pm = estruturar(_EXEMPLO_POSTMAN)
        if e_pm:
            _sev_pm = e_pm.get("severidade", "")
            _cor_sev_pm = "#b91c1c" if ("CRÍTICA" in _sev_pm or "ALTA" in _sev_pm) else ("#b45309" if "MÉDIA" in _sev_pm else "#0f172a")
            st.markdown(
                f"""
                <div style="background:#ffffff;border:1px solid #d97706;border-radius:12px;
                             padding:16px 18px;font-size:14px;line-height:1.9;color:#0f172a;
                             box-shadow:0 4px 12px rgba(15,23,42,.08)">
                  <div style="display:inline-block;background:#d97706;color:#ffffff;
                               border-radius:999px;padding:5px 15px;
                               font-size:14px;font-weight:800;letter-spacing:.02em;margin:0 0 10px">✨ Extraído automaticamente:</div><br>
                  <b style="color:#b45309">• Requisição:</b> <code style="background:#f1f5f9;color:#0f172a;padding:1px 7px;border-radius:6px;font-weight:600">{e_pm.get('requisicao','')}</code><br>
                  <b style="color:#b45309">• Esperado:</b> <code style="background:#f1f5f9;color:#0f172a;padding:1px 7px;border-radius:6px;font-weight:600">{e_pm.get('status_esperado','')}</code> · <b style="color:#b45309">Recebido:</b> <code style="background:#f1f5f9;color:#0f172a;padding:1px 7px;border-radius:6px;font-weight:600">{e_pm.get('status_recebido','')}</code><br>
                  <b style="color:#b45309">• Erro:</b> <code style="background:#f1f5f9;color:#0f172a;padding:1px 7px;border-radius:6px;font-weight:600">{e_pm.get('erro','')}</code><br>
                  <b style="color:#b45309">• Severidade prévia:</b> <b style="color:{_cor_sev_pm}">{_sev_pm}</b>
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
        <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;
                     padding:20px 22px;margin-top:4px;box-shadow:0 4px 12px rgba(15,23,42,.10)">
          <div style="color:#0f172a;font-weight:800;font-size:15.5px;margin-bottom:8px">💡 Não tem Playwright ou Postman instalados?</div>
          <div style="color:#1e293b;font-size:14.5px;line-height:1.75;font-weight:500">
            Sem problema. Abaixo do campo <b style="color:#15803d">Colar falha bruta</b> na
            <b style="color:#15803d">Ferramenta</b> já existem botões
            <code style="background:#16a34a;color:#ffffff;padding:2px 8px;border-radius:6px;font-weight:700">🎯 Exemplo Playwright</code>
            e
            <code style="background:#d97706;color:#ffffff;padding:2px 8px;border-radius:6px;font-weight:700">🎯 Exemplo Postman</code>
            que preenchem o campo automaticamente com um caso real. Clique, revise e execute —
            nenhum software extra necessário.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="marca-int-fim" style="display:none"></div>', unsafe_allow_html=True)
    if st.button("🔍 Ir para a Ferramenta de Triagem", key="vitrine_cta_final", use_container_width=True):
        st.switch_page(roteador.PAGINAS["triagem"])