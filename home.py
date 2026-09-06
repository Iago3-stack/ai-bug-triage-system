import streamlit as st
import pandas as pd
from urllib.parse import quote

from triagem import triar
import ia
import hero_animado
import jira_client
import persistencia

# Configuração e Estilo
st.set_page_config(page_title="Iago Nunes | IA & QA Portfolio", page_icon="🤖", layout="wide")

# Esconde rodapé "Made with Streamlit" e o menu principal (visual mais limpo)
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
</style>
""", unsafe_allow_html=True)

# --- CABEÇALHO ---
col_foto, col_info = st.columns([1, 2])
with col_info:
    st.markdown('<h1 style="font-weight:700; line-height:1.2; letter-spacing:-0.02em; padding:0; margin:0; color:black">Iago Nunes<span style="font-size:0.5em; vertical-align:super; font-weight:400; color:#6b7280; margin-left:2px">©</span></h1>', unsafe_allow_html=True)
    hero_animado.linha()
    st.markdown('<img src="https://capsule-render.vercel.app/api?type=soft&color=gradient&customColorList=20,24,25&height=56&section=header&text=Bem-vindo%20ao%20meu%20site&fontSize=22&fontColor=fff&fontAlignY=62" width="100%" />', unsafe_allow_html=True)
    hero_animado.typing_frases()
with col_foto:    
    st.image("assets/o novo.png", width=250,caption="Iago Nunes")
    st.markdown("#### 🚀 Construo automação de QA com IA (NLP + Gemini) | Auxiliar Administrativo | Graduando IA & ML Uniasselvi (Dez/2027)")
    st.write("📍 São Luís, MA (Disponível para Remote Global)")
    
    st.divider()

# HERO animado centralizado: abaixo do Bem-vindo/digitação e acima do Sobre Mim
hero_animado.render()

esq, centro = st.columns([1, 8])
with centro:
     st.subheader("🎯 Sobre Mim 🧔🏾‍♂️️")    
    
     st.markdown("""
Sou um entusiasta de tecnologia e estudante de **IA & Machine Learning**, focado em transformar a garantia de qualidade (QA) através da automação inteligente. Minha missão no laboratório **Hack28** é construir ferramentas que não apenas encontrem falhas, mas que tragam **insights valiosos para o negócio** usando **NLP** e **Engenharia de Prompt**.

🚀 **Hoje:** Já coloco IA em produção lucidamente — motor NLP determinístico + Gemini com fallback automático, aplicação pública, open-source e **container publicada no GHCR**.

🌟 **Visão:** evoluir esse mesmo motor para a próxima geração — **agentes de IA, RAG e MLOps** — transformando QA de "caça-bugs" em **inteligência de produto**. Com a graduação em IA & ML (UNIASSELVI · Dez/2027), esse caminho está documentado passo a passo no meu GitHub aberto.

**O que eu busco agora:** Oportunidades **Home Office / Remote** para aplicar automação híbrida, acelerar ciclos de entrega e elevar o padrão de qualidade — fazendo parte de um time que constrói o futuro do software.
""")

# --- SOBRE O PROJETO ---
st.divider()
st.write("Atualmente, dedico meus estudos na UNIASSELVI para aprofundar conhecimentos em Redes Neurais e Modelos de Linguagem (LLMs). No meu dia a dia, utilizo o Linux Mint como base para desenvolver scripts em Python que integram APIs de inteligência artificial à automação de testes, buscando sempre reduzir o tempo de triagem de bugs e melhorar a precisão dos relatórios técnicos.")
st.subheader("🤖 Agente de Triagem e Documentação de Bugs 2026")
st.info("Esta ferramenta demonstra o uso de NLP para automatizar a triagem técnica e emocional de falhas de software.")

# --- FERRAMENTA (Sua ideia evoluída) ---
descricao_bug = st.text_area("Entrada do Usuário (Relato do Bug):", height=150, 
                             placeholder="Ex: Estou tentando pagar e o botão não responde, estou muito frustrado!")

usar_llm = st.checkbox(
    "🔮 Usar IA (Gemini) para esta triagem",
    value=True,
    help="Ativa a análise por LLM. Se desmarcado, só o motor local determinístico roda."
)

if st.button("Executar Triagem Inteligente"):
        if descricao_bug:
            # --- 1. TRIAGEM NLP (MOTOR LOCAL, DETERMINÍSTICO E OFFLINE) ---
            # O motor triagem.py analisa léxico PT + padrões de negação,
            # sem depender de internet nem de API de tradução.
            resultado = triar(descricao_bug)
            gravidade = resultado["gravidade"]
            sentimento = resultado["sentimento"]
            polaridade = resultado["score"]
            fatores = resultado["fatores"]
            motor = resultado["motor"]

            # Trata aspas digitadas pelo usuário (evita aspas duplicadas no relatório)
            descricao_limpa = descricao_bug.strip().strip('"\'')

            # --- 2. RELATÓRIO GHERKIN ---
            relatorio = f"""### 🛡️ Relatório de Triagem Técnica
**Resumo:** {descricao_limpa[:100]}...
**Prioridade:** {gravidade}
**Análise de Sentimento:** {sentimento} (Score: {polaridade:.2f})
**Motor de análise:** {motor}
**Fatores identificados:** {', '.join(fatores) or 'Nenhum (relato neutro)'}

**Cenário Gherkin:**
- DADO QUE o sistema recebeu um relato de erro
- QUANDO o agente processa a entrada: "{descricao_limpa[:50]}..."
- ENTÃO a prioridade deve ser definida como {gravidade}."""

            # --- 2.5 ANÁLISE POR IA (LLM opcional; fallback seguro) ---
            resultado_llm = None
            erro_llm = None
            prioridade_final = None
            divergente = None
            if usar_llm and ia._chave():
                with st.spinner("🔮 A IA está analisando sua triagem — pode levar um pouco..."):
                    resultado_llm, erro_llm = ia.analisar_llm(descricao_limpa)
                if resultado_llm:
                    llm_modelo = ia.MODELO
                    # Regra de reconciliação: o mais grave vence, e divergência vira alerta.
                    sev_local = {"NORMAL ✅": 1, "MÉDIA ⚠️": 2, "CRÍTICA 🚨": 4}[gravidade]
                    sev_ia = {"baixa": 1, "media": 2, "alta": 3, "critica": 4}.get(resultado_llm["severidade"], 2)
                    sev_final = max(sev_local, sev_ia)
                    prioridade_final = {1: "NORMAL ✅", 2: "MÉDIA ⚠️", 3: "ALTA 🚨", 4: "CRÍTICA 🚨"}[sev_final]
                    divergente = sev_local != sev_ia
                    relatorio += f"""
---
🔮 **Análise por IA ({llm_modelo}):**
- Severidade sugerida: {resultado_llm['severidade']}
- Categoria: {resultado_llm['categoria']}
- Causa raiz provável: {resultado_llm['causa_raiz']}
- Resumo técnico: {resultado_llm['resumo_tecnico']}
- Passos para reproduzir:
""" + "\n".join(f"\t{i}. {p}" for i, p in enumerate(resultado_llm["passos_repro"], 1)) + f"""

- **Prioridade final (máx. entre motores): {prioridade_final}**
- **Divergência entre motores: {'SIM ⚠️' if divergente else 'não'}**
"""

            # --- 3. HISTÓRICO DA SESSÃO ---
            if "historico" not in st.session_state:
                st.session_state["historico"] = []
            st.session_state["historico"].append({
                "Relato": descricao_bug,
                "Score": round(polaridade, 2),
                "Gravidade": gravidade,
                "Sentimento": sentimento,
            })

            # --- 3.5 PERSISTÊNCIA (JSONL): snapshot fiel do que foi executado ---
            snapshot = {
                "resumo": descricao_limpa[:100],
                "descricao": descricao_limpa,
                "motor": motor,
                "gravidade": gravidade,
                "score": round(polaridade, 2),
                "sentimento": sentimento,
                "fatores": fatores,
                "usou_ia": bool(usar_llm),
            }
            if resultado_llm:
                snapshot.update({
                    "modelo_ia": llm_modelo,
                    "severidade_ia": resultado_llm["severidade"],
                    "categoria_ia": resultado_llm["categoria"],
                    "causa_raiz_ia": resultado_llm["causa_raiz"],
                    "resumo_tecnico_ia": resultado_llm["resumo_tecnico"],
                    "passos_ia": resultado_llm["passos_repro"],
                    "prioridade_final": prioridade_final,
                    "divergente": divergente,
                })
            else:
                snapshot["erro_ia"] = erro_llm
            snapshot["relatorio_completo"] = relatorio
            persistencia.registrar_triagem(snapshot)

            # --- 4. GUARDA O RESULTADO (sobrevive a reruns dos botões de exportação) ---
            st.session_state["resultado"] = {
                "descricao_limpa": descricao_limpa,
                "relatorio": relatorio,
                "gravidade": gravidade,
                "polaridade": polaridade,
                "resultado_llm": resultado_llm,
                "erro_llm": erro_llm,
                "prioridade_final": prioridade_final,
                "divergente": divergente,
            }
        else:
            st.warning("Digite a descrição do bug para executar a triagem.")

# --- RENDERIZAÇÃO DO RESULTADO (fora do if do botão: não some em reruns) ---
r = st.session_state.get("resultado")
if r:
    relatorio = r["relatorio"]
    gravidade = r["gravidade"]
    descricao_limpa = r["descricao_limpa"]
    resultado_llm = r["resultado_llm"]
    erro_llm = r["erro_llm"]
    prioridade_final = r["prioridade_final"]
    divergente = r["divergente"]

    # --- 4. INTERFACE DASHBOARD ---
    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("Gravidade IA", gravidade)
    c2.metric("Sentimento", f"{r['polaridade']:.2f}")
    c3.metric("Status", "Análise Determinística OK")

    st.markdown("### 📝 Relatório Gerado! ✅")
    st.code(relatorio, language="markdown")

    if resultado_llm:
        st.markdown("### 🔮 Análise por IA (Gemini)")
        ca, cb, cc = st.columns(3)
        ca.metric("Severidade (IA)", resultado_llm["severidade"].upper())
        cb.metric("Categoria", resultado_llm["categoria"].capitalize())
        cc.metric("Modelo", ia.MODELO.replace("gemini-", "Gemini "))
        st.write(f"**Causa raiz provável:** {resultado_llm['causa_raiz']}")
        st.write("**Passos para reproduzir:**")
        for i, p in enumerate(resultado_llm["passos_repro"], 1):
            st.write(f"{i}. {p}")
        st.caption("💡 Análise gerada por LLM — use como suporte à triagem determinística do motor local.")

        st.markdown("---")
        st.markdown(f"## 🎯 Prioridade Final: {prioridade_final}")
        if divergente:
            st.warning(f"⚠️ Divergência detectada: motor local **{gravidade}** x IA **{resultado_llm['severidade'].upper()}**. Sinais conflitantes — revisão humana recomendada.")
        else:
            st.success("✅ Motores concordam na prioridade.")
    elif erro_llm:
        st.info("🔮 Análise por IA indisponível no momento (API instável/sem resposta). O motor local determinístico segue no controle.")

    # --- 5. EXPORTAR: baixar relatório + abrir no GitHub + enviar ao Jira ---
    colunas = st.columns(3)
    colunas[0].download_button(
        "📥 Baixar relatório (.md)",
        data=relatorio.encode("utf-8"),
        file_name="relatorio_triagem_bug.md",
        mime="text/markdown",
    )
    titulo = quote(descricao_limpa[:80])
    corpo = quote(relatorio[:1200])
    colunas[1].link_button(
        "🐙 Nova Issue no GitHub",
        f"https://github.com/iago3-stack/ai-bug-triage-system/issues/new?title={titulo}&body={corpo}",
    )
    if colunas[2].button("📋 Exportar para Jira", use_container_width=True, key="btn_exportar_jira"):
        if jira_client.configurado():
            with st.spinner("📋 Enviando issue ao Jira..."):
                ok_export, resultado_jira, erro_jira = jira_client.criar_issue(
                    descricao_limpa[:100], relatorio, gravidade
                )
            if ok_export:
                st.session_state["exportacao_jira"] = (True, resultado_jira["key"], resultado_jira["url"])
                persistencia.registrar_exportacao_jira(resultado_jira["key"], resultado_jira["url"])
            else:
                st.session_state["exportacao_jira"] = (False, None, erro_jira)
        else:
            st.session_state["exportacao_jira"] = (
                False, None, "Configure o e-mail, o API token e a chave do projeto no sidebar."
            )

    if "exportacao_jira" in st.session_state:
        ok_export, chave_issue, detalhe = st.session_state["exportacao_jira"]
        if ok_export:
            st.success(f"✅ Issue **{chave_issue}** criada no Jira!")
            st.markdown(f"[🔗 Abrir issue no Jira]({detalhe})")
        else:
            st.error(f"❌ Não foi possível exportar para o Jira: {detalhe}")

    st.info("📋 O relatório também pode ser copiado direto da caixa acima para o Jira ou GitHub!")
    st.success("Triagem finalizada com sucesso! ✅")

    # --- 6. HISTÓRICO (TABELA pandas) ---
    with st.expander(f"📊 Histórico de triagens desta sessão ({len(st.session_state['historico'])})"):
        st.dataframe(pd.DataFrame(st.session_state["historico"]),
                     use_container_width=True, hide_index=True)
        if st.button("🗑️ Limpar histórico"):
            st.session_state["historico"] = []

# --- 6.5 HISTÓRICO PERSISTIDO (JSONL) ---
registros_totais = persistencia.carregar_registros()
if registros_totais:
    with st.expander(f"📁 Histórico persistido (JSONL) — {len(registros_totais)} triagem(ns) salva(s)"):
        datas = persistencia.datas_disponiveis()
        data_sel = st.selectbox("📅 Escolha a data", datas, key="hp_data")
        do_dia = persistencia.registros_por_data(data_sel)
        st.dataframe(pd.DataFrame([
            {
                "Hora": r["data_hora"][11:19],
                "Resumo": r["resumo"],
                "Gravidade": r["gravidade"],
                "Score": r["score"],
                "IA": "sim" if r.get("usou_ia") else "não",
                "Jira": r.get("jira_key") or "—",
            } for r in do_dia
        ]), use_container_width=True, hide_index=True)
        rotulos = [
            f"{r['data_hora'][11:19]} · {r['gravidade']} · score {r['score']:.2f} · "
            f"IA {'sim' if r.get('usou_ia') else 'não'} · Jira {r.get('jira_key') or '—'}"
            for r in do_dia
        ]
        indice = st.selectbox("📄 Selecione o relatório", range(len(do_dia)),
                              format_func=lambda i: rotulos[i], key="hp_rel")
        reg = do_dia[indice]
        st.code(reg["relatorio_completo"], language="markdown")
        st.download_button(
            "📥 Baixar relatório desta triagem (.md)",
            data=reg["relatorio_completo"].encode("utf-8"),
            file_name=f"relatorio_{reg['data']}_{reg['data_hora'][11:16].replace(':', 'h')}.md",
            mime="text/markdown",
            key="hp_download",
        )
# --- CONFIGURAÇÃO DO JIRA (sidebar) ---
if not jira_client.configurado():
    with st.sidebar.expander("🔑 Jira — configurar exportação"):
        st.caption("Cole suas credenciais para ativar o botão 'Exportar para Jira'.")
        j_email = st.text_input("E-mail Atlassian", key="jira_email")
        j_token = st.text_input("API Token", type="password", key="jira_token")
        j_key = st.text_input("Chave do projeto", placeholder="ex.: KAN", key="jira_key")
        j_issue_type = st.text_input("Tipo de item (padrão: Tarefa)", placeholder="ex.: Tarefa", key="jira_issue_type")
        if st.button("Salvar configuração (sessão)", use_container_width=True):
            jira_client.configurar(j_email, j_token, j_key, j_issue_type)
            if jira_client.configurado():
                st.success("✅ Jira configurado nesta sessão!")
            else:
                st.warning("Preencha e-mail, token e chave do projeto.")

# --- CTA: ESTRELA NO GITHUB ---
st.sidebar.markdown("### ⭐ Apoie o projeto")
st.sidebar.write("Se esta triagem te ajudou, dá uma estrelinha no repositório — é de graça e ajuda mais QAs a encontrarem o app.")

repo_url = "https://github.com/Iago3-stack/ai-bug-triage-system/"
st.sidebar.markdown(f"""
<a href="{repo_url}" target="_blank">
    <button style="background-color: #2E7CF6; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; width: 100%;">
        ⭐ Dar estrela no GitHub
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
