# 🤖 AI Bug Triage System — IA + QA

> 🌐 *English readers: this document is in PT-BR, but your browser can translate it automatically (right-click → "Translate").*

Motor de **triagem inteligente de bugs** desenvolvido para Engenharia de Garantia de Qualidade (QA). Ele combina processamento de linguagem natural (NLP) com lógica de regras para **priorizar automaticamente** relatos de erros e gerar **documentação técnica em formato Gherkin** — pronto para copiar para Jira ou GitHub Issues.

🚀 **Aplicação publicada:** [ai-bug-triage-system.streamlit.app](https://ai-bug-triage-system-d6vigycbjt4qxez2wrvsxf.streamlit.app/)

---

## ⭐ Funcionalidades (MVP atual)

- **Triagem em duas camadas**
  1. **Camada técnica**: termos críticos (crash, pagamento, login, segurança, 500...) escalam a severidade.
  2. **Camada NLP**: análise de sentimento por **léxico em português** + **detecção de negação** ("não funciona", "não consigo", "parou de responder"...).
- **100% offline e determinístico**: o motor `triagem.py` usa apenas a biblioteca padrão do Python — sem API de tradução, sem internet, sem custo e com resultado sempre reproduzível.
- **Transparência de QA**: o relatório informa o **motor de análise** usado e os **fatores identificados** em cada triagem.
- **Sem falsos positivos técnicos**: palavras como *erro*, *bug* e *falha* são vocabulário normal de teste e **não** disparam severidade sozinhas.
- **Relatório Gherkin** (`Dado/Quando/Então`) baseado na prioridade detectada.
- **Exportação**: baixar relatório (`.md`), abrir **Issue no GitHub** pré-preenchida ou enviar ao **Jira** (configurável).
- **Histórico da sessão** em tabela (`pandas`) com opção de limpar.
- Interface com identidade visual própria (tema Streamlit em `config.toml`).

---

## 🛠️ Tecnologias

- **Python 3.13** — lógica e motor NLP (biblioteca `re` / stdlib)
- **Streamlit 1.62** — interface web e deploy na nuvem
- **pandas** — tabela de histórico de triagens
- Desenvolvido em **Linux Mint Debian** (Laboratório Hack28)

---

## ▶️ Como rodar localmente

```bash
git clone https://github.com/Iago3-stack/ai-bug-triage-system.git
cd ai-bug-triage-system
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run home.py
```

Teste rápido do motor sem interface:

```bash
python triagem.py
```

---

## 📁 Estrutura

| Arquivo | Papel |
|---|---|
| `home.py` | Interface web (Streamlit): cabeçalho, ferramenta, export e histórico |
| `triagem.py` | Motor NLP: léxico PT, padrões de negação e classificação de severidade |
| `requirements.txt` | Dependências pinadas |
| `.streamlit/config.toml` | Tema e configurações da app |

---

## 🚧 Roadmap

- [x] **Fase 1** — Motor NLP offline (léxico PT + negação, sem TextBlob/Google Translate)
- [x] **Fase 2** — Exportação do relatório, histórico de sessão e identidade visual
- [ ] **Fase 3** — Integração com **LLMs** (Gemini) para análise de causa raiz
- [ ] Exportação direta via **API do Jira**
- [ ] Testes unitários do motor (`pytest`)
- [ ] Persistência do histórico (banco de dados)

---

**Desenvolvido por [Iago Nunes](https://github.com/Iago3-stack)** | QA Automation Engineer | Estudante de IA & Machine Learning na UNIASSELVI.