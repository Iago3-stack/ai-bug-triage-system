import streamlit as st
import pandas as pd
from urllib.parse import quote

from triagem import triar
import ia

# Configure com o endpoint do seu Jira Cloud (opcional).
# Enquanto vazio, o botão "Novo Item no Jira" exibe um aviso.
JIRA_CREATE_URL = ""

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
    st.title("Iago Nunes©️")
    st.write("Bem-vindo 🤝️ ao meu site!🌐️")
    st.write("Aqui👇️ você pode encontrar informações sobre mim e meus projetos 🇧🇷️.")
with col_foto:    
    st.image("o novo.png", width=250,caption="Iago Nunes")
    st.markdown("#### 🚀 Construo automação de QA com IA (NLP + Gemini) | Auxiliar Administrativo | Graduando IA & ML Uniasselvi (Dez/2027)")
    st.write("📍 São Luís, MA (Disponível para Remote Global)")
    
    st.divider()
esq, centro, dir = st.columns([1, 4, 1])
with centro:
     st.subheader("🎯 Sobre Mim 🧔🏾‍♂️️")    
    
     st.markdown("""
Sou um entusiasta de tecnologia e estudante de **IA & Machine Learning**, focado em transformar a garantia de qualidade (QA) através da automação inteligente. 
Minha missão no laboratório **Hack28** é desenvolver ferramentas que não apenas encontrem falhas, mas que tragam insights valiosos para o negócio usando **NLP** e **Engenharia de Prompt**.

**O que eu busco:** Oportunidades **Home Office** onde eu possa aplicar automação híbrida para acelerar ciclos de entrega e elevar o padrão de qualidade dos produtos.
""")

# --- SOBRE O PROJETO ---
st.divider()
st.write("Atualmente, dedico meus estudos na UNIASSELVI para aprofundar conhecimentos em Redes Neurais e Modelos de Linguagem (LLMs). No meu dia a dia, utilizo o Linux Mint como base para desenvolver scripts em Python que integram APIs de inteligência artificial à automação de testes, buscando sempre reduzir o tempo de triagem de bugs e melhorar a precisão dos relatórios técnicos.")
st.subheader("🤖 Agente de Triagem e Documentação de Bugs 2026")
st.info("Esta ferramenta demonstra o uso de NLP para automatizar a triagem técnica e emocional de falhas de software.")

# --- FERRAMENTA (Sua ideia evoluída) ---
descricao_bug = st.text_area("Entrada do Usuário (Relato do Bug):", height=150, 
                             placeholder="Ex: Estou tentando pagar e o botão não responde, estou muito frustrado!")

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
            # Se não houver chave GEMINI_API_KEY configurada (st.secrets ou .env),
            # a análise LLM é pulada e o motor local segue no comando.
            resultado_llm = None
            erro_llm = None
            if ia._chave():
                with st.spinner("🔮 IA analisando causa raiz... (pode levar ~15s)"):
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

            # --- 4. INTERFACE DASHBOARD ---
            st.divider()
            c1, c2, c3 = st.columns(3)
            c1.metric("Gravidade IA", gravidade)
            c2.metric("Sentimento", f"{polaridade:.2f}")
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

            # --- 5. EXPORTAR: baixar relatório + abrir no GitHub (e no Jira, se configurado) ---
            colunas = st.columns(3) if JIRA_CREATE_URL else st.columns(2)
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
            if JIRA_CREATE_URL:
                colunas[2].link_button("📋 Novo Item no Jira",
                                       f"{JIRA_CREATE_URL}?summary={titulo}&description={corpo}")

            st.info("📋 O relatório também pode ser copiado direto da caixa acima para o Jira ou GitHub!")
            st.success("Triagem finalizada com sucesso! ✅")

            # --- 6. HISTÓRICO (TABELA pandas) ---
            with st.expander(f"📊 Histórico de triagens desta sessão ({len(st.session_state['historico'])})"):
                st.dataframe(pd.DataFrame(st.session_state["historico"]),
                             use_container_width=True, hide_index=True)
                if st.button("🗑️ Limpar histórico"):
                    st.session_state["historico"] = []
        else:
            st.warning("Digite a descrição do bug para executar a triagem.")
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
st.sidebar.markdown("### Contate-me")
st.sidebar.write("📧 [Enviar E-mail](mailto:viago4415@gmail.com)")
st.sidebar.write("🔗 [Meu LinkedIn](https://www.linkedin.com/in/iago-nunes-897a5832b/?lipi=urn%3Ali%3Apage%3Ad_flagship3_profile_view_base_contact_details%3B%2F15y3S36T5SI8UZodVDXGw%3D%3D)")
# --- CONTATO DIRETO (WhatsApp) ---
# Substitua pelo seu número real com DDD
numero_whatsapp = "5598985914235" 
mensagem_automatica = "Olá Iago, vi seu portfólio de IA e QA e gostaria de conversar sobre uma oportunidade!"
link_wa = f"https://wa.me/{numero_whatsapp}?text={mensagem_automatica.replace(' ', '%20')}"

st.sidebar.markdown(f"""
<a href="{link_wa}" target="_blank">
    <button style="background-color: #25D366; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; width: 100%;">
        💬 Falar com Iago no WhatsApp
    </button>
</a>
""", unsafe_allow_html=True)
st.sidebar.info("Executado em: Linux Mint Debian Lab 🧠️ (Hack28)☢️")
