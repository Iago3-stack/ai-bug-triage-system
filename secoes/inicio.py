"""Página Início — portfólio + vitrine do plano SaaS."""
import streamlit as st

import plano
import hero_animado
import ui_comum
import ui_tema


def render():
    import roteador  # lazy: roteador importa inicio (ciclo) — só dentro de render()
    # --- MASTHEAD ("rodapé superior"): card do plano — fica acima do nome do site ---
    if plano.pago():
        _badge_plano = (
            '<span style="background:rgba(251,191,36,.16);color:#fde68a;border:1px solid rgba(251,191,36,.5);'
            'border-radius:999px;padding:4px 14px;font-size:12px;font-weight:800;letter-spacing:.03em">⭐ Plano Premium</span>'
        )
        _frase_plano = "Você está no <b style='color:#86efac'>plano Premium</b> — histórico completo, RAG com \u201ccomo foi resolvido\u201d e múltiplos canais de alerta liberados."
        _emojis_feats = "🧠 📚 🔔 🧺"
    else:
        _badge_plano = (
            '<span style="background:rgba(37,211,102,.16);color:#86efac;border:1px solid rgba(37,211,102,.5);'
            'border-radius:999px;padding:4px 14px;font-size:12px;font-weight:800;letter-spacing:.03em">🔓 Plano Basic</span>'
        )
        _frase_plano = "Você está no <b style='color:#86efac'>plano Basic</b> — a ferramenta já funciona 100%. O plano Premium libera RAG, causas raiz via IA e canais de alerta múltiplos (veja a tabela abaixo)."
        _emojis_feats = "🧠 📚 🔔 🧺"

    _pill_on = 'background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.18);border-radius:999px;padding:4px 13px;font-size:12px;color:#e2e8f0'
    _pill_off = 'background:rgba(255,255,255,.05);border:1px dashed rgba(255,255,255,.20);border-radius:999px;padding:4px 13px;font-size:12px;color:#94a3b8'
    _pill_feat = lambda on: _pill_on if on else _pill_off

    st.markdown(f"""
    <div class="marca-mastro" style="width:100%;background:linear-gradient(135deg,#0f172a 0%,#16233c 52%,#25D366 175%);border-radius:16px;padding:30px 34px 26px 34px;margin:4px 0 18px;box-shadow:0 8px 22px rgba(15,23,42,.18)">
      <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap">
        <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
          {_badge_plano}
          <span style="color:#94a3b8;font-size:12px;font-weight:700;letter-spacing:.05em">💼 CONHEÇA O PLANO · SaaS de QA com IA</span>
        </div>
        <span style="color:#64748b;font-size:12px;font-weight:600">{ui_comum.VERSAO}</span>
      </div>
      <div style="color:#ffffff;font-size:26px;font-weight:800;margin-top:16px;letter-spacing:-.01em">Conheça o plano {'⭐' if plano.pago() else '💎'}</div>
      <div style="color:#cbd5e1;font-size:16px;line-height:1.65;margin-top:8px;max-width:94%">{_frase_plano}</div>
      <div style="display:flex;gap:9px;flex-wrap:wrap;margin-top:18px">
        <span style="{_pill_feat(True)}">✅ Triagem NLP + IA (Gemini/Groq)</span>
        <span style="{_pill_feat(plano.pago())}">🧠 Causas raiz + comparativo IA×local</span>
        <span style="{_pill_feat(plano.pago())}">📚 RAG · \u201ccomo foi resolvido\u201d</span>
        <span style="{_pill_feat(plano.pago())}">🔔 Alertas multi-canal (e-mail + Discord)</span>
        <span style="{_pill_feat(plano.pago())}">🧺 Histórico completo (Dashboard)</span>
      </div>
      <div style="color:#94a3b8;font-size:13px;margin-top:18px">🔽 Abra a tabela <b>💼 Comparar planos — Basic × Premium</b> logo abaixo para ver tudo que cada um libera.</div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("💼 Comparar planos — Basic × Premium", expanded=False):
        st.markdown(f"""
    | Recurso | 🔓 Basic | ⭐ Premium |
    |---|---|---|
    | ✅ Triagem NLP + motor determinístico | liberado | liberado |
    | 🔮 IA (Gemini / Groq / modelo próprio) | liberado | liberado |
    | 🧠 Análises de IA — *causas raiz* e *comparativo IA×local* | — | 🔒 liberado |
    | 📚 RAG — consulta casos similares + \u201ccomo foi resolvido\u201d | — | 🔒 liberado |
    | 🧺 Histórico / Dashboard de QA | últimas **{plano.limite_historico_free()}** triagens | completo |
    | 🔔 Canais de alerta (e-mail/Discord) | **1** canal | múltiplos canais |
    | 🚨 Prioridade máxima ao alertar CRÍTICA/ALTA | liberado | liberado |
    | **Ideal para** | testar / demonstrar | produção contínua |
    """)
        st.caption("O plano é uma variável de ambiente no seu deploy: `PLANO = \"pago\"`. Sem cobrança neste projeto — é a vitrine de um produto real.")

    # --- CABEÇALHO ---
    col_foto, col_info = st.columns([1, 2])
    with col_info:
        st.markdown('<h1 class="nome-site" style="font-weight:700; line-height:1.2; letter-spacing:-0.02em; padding:0; margin:0; color:black">Iago Nunes<span style="font-size:0.5em; vertical-align:super; font-weight:400; color:#6b7280; margin-left:2px">©</span></h1>', unsafe_allow_html=True)
        hero_animado.linha()
        hero_animado.render()
    with col_foto:    
        st.image("assets/o novo.png", width=250,caption="Iago Nunes")

        st.markdown("""
    <div style="height:3px;width:100%;background:linear-gradient(90deg,transparent,#25D366,#2E7CF6,#7c3aed,transparent);border-radius:999px;margin:8px 0"></div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-top:14px;width:100%;background:linear-gradient(135deg,#0f172a 0%,#16233c 55%,#25D366 170%);border-radius:16px;color:#e2e8f0;font-size:15px;line-height:1.6;padding:22px 24px">
      <div style="font-size:19px;font-weight:800;color:#ffffff;margin-bottom:12px">🎯 Sobre Mim 🧔🏾‍♂️️</div>
      <p style="margin:0 0 12px">Sou um entusiasta de tecnologia e estudante de <b style="color:#25D366">IA &amp; Machine Learning</b>, focado em transformar a garantia de qualidade (QA) através da automação inteligente. Minha missão no laboratório <b style="color:#94a3b8">Hack28</b> é construir ferramentas que não apenas encontrem falhas, mas que tragam <b style="color:#94a3b8">insights valiosos para o negócio</b> usando <b style="color:#94a3b8">NLP</b> e <b style="color:#94a3b8">Engenharia de Prompt</b>.</p>
      <p style="margin:0 0 12px">🚀 <b style="color:#94a3b8">Hoje:</b> Já coloco IA em produção lucidamente — motor NLP determinístico + Gemini com fallback automático, aplicação pública, open-source e <b style="color:#94a3b8">container publicada no GHCR</b>.</p>
      <p style="margin:0 0 12px">🌟 <b style="color:#94a3b8">Visão:</b> evoluir esse mesmo motor para a próxima geração — <b style="color:#94a3b8">agentes de IA, RAG e MLOps</b> — transformando QA de "caça-bugs" em <b style="color:#94a3b8">inteligência de produto</b>. Com a graduação em IA &amp; ML (UNIASSELVI · Dez/2027), esse caminho está documentado passo a passo no meu GitHub aberto.</p>
      <p style="margin:0"><b style="color:#94a3b8">O que eu busco agora:</b> Oportunidades <b style="color:#94a3b8">Home Office / Remote</b> para aplicar automação híbrida, acelerar ciclos de entrega e elevar o padrão de qualidade — fazendo parte de um time que constrói o futuro do software.</p>
      <div style="margin:16px 0 0;height:2px;background:linear-gradient(90deg,transparent,#25D366,#7c3aed,transparent);border-radius:999px"></div>
      <div style="font-size:16px;font-weight:800;color:#7aa5ff;margin:14px 0 8px">🎓 Formação &amp; Stack</div>
      <p style="margin:0 0 12px">Atualmente, dedico meus estudos na <b style="color:#7aa5ff">UNIASSELVI</b> para aprofundar conhecimentos em <b style="color:#7aa5ff">Redes Neurais</b> e <b style="color:#7aa5ff">Modelos de Linguagem (LLMs)</b>. No meu dia a dia, utilizo o <b style="color:#7aa5ff">Linux Mint</b> como base para desenvolver scripts em <b style="color:#7aa5ff">Python</b> que integram APIs de inteligência artificial à automação de testes, buscando sempre reduzir o tempo de triagem de bugs e melhorar a precisão dos relatórios técnicos.</p>
      <p style="margin:0">💼 <b style="color:#94a3b8">SaaS em construção:</b> esse mesmo motor está sendo transformado em um <b style="color:#25D366">produto SaaS de QA</b> — planos <b style="color:#94a3b8">Basic</b> e <b style="color:#fde68a">Premium</b> controlados por variável de ambiente, RAG com "como foi resolvido", comparação IA × motor local e alertas multi-canal. É a prova prática de como transformar engenharia em produto.</p>
    </div>
    """, unsafe_allow_html=True)
    # --- CTA: convite para usar a ferramenta / ver o dashboard ---
    st.markdown("""
<div style="height:3px;width:100%;background:linear-gradient(90deg,transparent,#25D366,#2E7CF6,#7c3aed,transparent);border-radius:999px;margin:8px 0"></div>
""", unsafe_allow_html=True)
    st.html(f"""
<div style="width:100%;background:linear-gradient(135deg,#0f172a 0%,#16233c 55%,#25D366 175%);border-radius:16px;color:#e2e8f0;font-size:15px;line-height:1.6;padding:22px 24px 18px;text-align:center;box-sizing:border-box">
  <div style="font-size:19px;font-weight:800;color:#ffffff;margin-bottom:8px">🤖 Pronto para triar bugs?</div>
  <div style="color:#94a3b8;font-size:14px;max-width:640px;margin:0 auto 18px">Cole um relato de bug e receba a triagem técnica e emocional com NLP + IA, com RAG e plano de ação. Veja também o Dashboard de QA consolidado.</div>
</div>
""")
    c1, c2 = st.columns(2)
    with c1:
        st.page_link(roteador.PAGINAS["triagem"], label="🚀 Ir para a Ferramenta", use_container_width=True)
    with c2:
        st.page_link(roteador.PAGINAS["dashboard"], label="📈 Ver Dashboard de QA", use_container_width=True)
