# 🤖 AI-Powered Bug Triage System (IA + QA) Main.py

[English version below]

## 📌 Visão Geral (Português)
Este projeto é um motor de **triagem híbrida** desenvolvido para Engenharia de Garantia de Qualidade (QA). Ele combina a lógica técnica tradicional com **Inteligência Artificial (NLP)** para priorizar automaticamente relatórios de erros (bugs).

### 🚀 Como funciona
O sistema utiliza uma abordagem de **Triagem em Duas Camadas**:
1. **Camada Técnica:** Analisa palavras-chave críticas (ex: "crash", "security", "payment").
2. **Camada de IA (NLP):** Utiliza a biblioteca **TextBlob** para analisar o sentimento do usuário. Se uma frustração elevada for detectada, a prioridade é aumentada automaticamente.

### 🛠️ Tecnologias
- **Python 3.x**
- **TextBlob** (Natural Language Processing)
- **Lógica:** Híbrida (Baseada em Regras + Análise de Sentimento)

---

## 📌 Project Overview (English)
This project is a **hybrid triage engine** developed for Quality Assurance (QA) Engineering. It combines traditional technical logic with **Artificial Intelligence (NLP)** to automatically prioritize software bug reports.

### 🚀 How it Works
The system utilizes a **Two-Layer Triage** approach:
1. **Technical Layer:** Scans for critical keywords (e.g., "crash", "security", "payment").
2. **AI Layer (NLP):** Uses the **TextBlob** library to analyze user sentiment. If high frustration is detected, the priority is automatically escalated, even if technical keywords are missing.

### 🛠️ Technologies
- **Python 3.x**
- **TextBlob** (Natural Language Processing)
- **Logic:** Hybrid (Rule-Based + Sentiment Analysis)

---
**Developed by Iago Nunes** - AI & Machine Learning Student | QA Enthusiast

---
🤖 Segunda versão com interface web AI Bug Triage System - Iago Nunes home.py

Sistema inteligente desenvolvido para otimizar a triagem de bugs utilizando Processamento de Linguagem Natural (NLP). Este projeto transforma relatos de utilizadores em documentação técnica estruturada (Gherkin), facilitando o trabalho de equipas de QA e Desenvolvimento.

## 🌐 Versão Web do Projeto
🚀 O sistema está disponível para testes em tempo real através do Streamlit Cloud:
🔗 [Aceder ao AI Bug Triage System](https://ai-bug-triage-system-d6vigycbjt4qxez2wrvsxf.streamlit.app/)

## 🛠️ Tecnologias Utilizadas
- **Python**: Lógica de backend e processamento.
- **Streamlit**: Interface de utilizador e deploy na nuvem.
- **TextBlob**: Análise de sentimento e polaridade para definir a gravidade do bug.
- **Ambiente**: Desenvolvido em Linux Mint Debian (Laboratório Hack28).
---
## ⚠️ Status do Projeto
Atualmente em **Fase Alpha**. Próximas atualizações incluirão integração com **LLMs (Gemini/GPT)** para análises de causa raiz automatizadas.

## 🚀 Roadmap de Evolução
- [ ] **Integração com LLMs**: Utilização de modelos como Gemini ou GPT para análise de causa raiz.
- [ ] **Exportação Direta**: Integração com APIs do Jira e GitHub Issues.
- [ ] **Relatórios Customizados**: Diferentes templates de saída baseados na prioridade detetada.

---
**Desenvolvido por: Iago Nunes** | QA Automation Engineer | Estudante de IA & ML na UNIASSELVI.
