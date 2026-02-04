import streamlit as st
from textblob import TextBlob
import pandas as pd

# Configuração e Estilo
st.set_page_config(page_title="Iago Nunes | IA & QA Portfolio", page_icon="🤖", layout="wide")

# --- CABEÇALHO ---
col_foto, col_info = st.columns([1, 2])
with col_info:
    st.title("Iago Nunes")
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
        analise = TextBlob(descricao_bug)
        polaridade = analise.sentiment.polarity # Pega o "tom" da mensagem
        
        # Define a Gravidade e o Sentimento com base na polaridade
        if polaridade < -0.3:
            gravidade = "CRÍTICA 🚨"
            sentimento = "Frustrado/Urgente"
            cor = "red"
        elif polaridade < 0:
            gravidade = "MÉDIA ⚠️"
            sentimento = "Negativo/Insatisfeito"
            cor = "orange"
        else:
            gravidade = "NORMAL ✅"
            sentimento = "Neutro/Calmo"
            cor = "green"

        # Exibição melhorada para o usuário
        st.divider()
        c1, c2, c3 = st.columns(3)
        c1.metric("Gravidade IA", gravidade)
        c2.metric("Sentimento", f"{polaridade:.2f}")
        c3.metric("Status", "Pronto para Report")

        st.success(f"### 📝 Relatório Técnico Gerado\n"
                   f"**Contexto Emocional:** Usuário demonstra nível de {sentimento}.\n\n"
                   f"**Sugestão de Prioridade:** {gravidade}")
        st.code(relatorio, language="markdown")
        st.success("Relatório pronto para ser copiado para o Jira/GitHub!")

# --- RODAPÉ DE CONTATO ---
st.sidebar.markdown("### Contate-me")
st.sidebar.write("📧 [Enviar E-mail](mailto:viago4415@gmail.com)")
st.sidebar.write("🔗 [Meu LinkedIn](https://www.linkedin.com/in/iago-nunes%E2%9D%87%EF%B8%8F-897a5832b?lipi=urn%3Ali%3Apage%3Ad_flagship3_profile_view_base_contact_details%3BtQ3Tyk98R5mM9Ej2tDUiTw%3D%3D)")
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
