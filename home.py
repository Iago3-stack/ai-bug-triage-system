import streamlit as st
import pandas as pd
from urllib.parse import quote

from triagem import triar

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
    st.markdown("#### 🚀 QA Automation Engineer | AI & Machine Learning | Student of UNIASSELVI")
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

            # --- 5. EXPORTAR: baixar relatório + abrir no GitHub/Jira ---
            col_exp, col_gh, col_jira = st.columns(3)
            col_exp.download_button(
                "📥 Baixar relatório (.md)",
                data=relatorio.encode("utf-8"),
                file_name="relatorio_triagem_bug.md",
                mime="text/markdown",
            )
            titulo = quote(descricao_limpa[:80])
            corpo = quote(relatorio[:1200])
            col_gh.link_button(
                "🐙 Nova Issue no GitHub",
                f"https://github.com/iago3-stack/ai-bug-triage-system/issues/new?title={titulo}&body={corpo}",
            )
            if JIRA_CREATE_URL:
                col_jira.link_button("📋 Novo Item no Jira",
                                     f"{JIRA_CREATE_URL}?summary={titulo}&description={corpo}")
            else:
                col_jira.caption("⚙️ Configure `JIRA_CREATE_URL` no topo do código para ativar o botão Jira.")

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
