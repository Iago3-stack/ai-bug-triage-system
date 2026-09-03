<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=soft&color=gradient&customColorList=20,24,25&height=80&section=header&text=AI%20Bug%20Triage%20System&fontSize=22&fontColor=fff&fontAlignY=60" width="100%" />
</div>

![Tela do app](assets/screenshot.png)

> 🌐 *English readers: this document is in PT-BR, but your browser can translate it automatically (right-click → "Translate").*

Motor de **triagem inteligente de bugs** desenvolvido para Engenharia de Garantia de Qualidade (QA). Ele combina processamento de linguagem natural (NLP) com lógica de regras para **priorizar automaticamente** relatos de erros e gerar **documentação técnica em formato Gherkin** — pronto para copiar para Jira ou GitHub Issues.

<div align="center">
  <a href="https://ai-bug-triage-system-d6vigycbjt4qxez2wrvsxf.streamlit.app/">
    <img src="https://img.shields.io/badge/Aplica%C3%A7%C3%A3o%20Publicada-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Aplicação publicada" />
  </a>
</div>

<div align="center">
  <a href="https://github.com/Iago3-stack/ai-bug-triage-system/stargazers">
    <img src="https://img.shields.io/github/stars/Iago3-stack/ai-bug-triage-system?style=for-the-badge&color=2E7CF6&logo=github&logoColor=white&label=Estrelas" />
  </a>
  <a href="https://github.com/Iago3-stack/ai-bug-triage-system/actions/workflows/ci.yml">
    <img src="https://img.shields.io/github/actions/workflow/status/Iago3-stack/ai-bug-triage-system/ci.yml?style=for-the-badge&logo=githubactions&logoColor=white&label=Testes%20CI" />
  </a>
</div>

<div align="center">
  <img src="https://img.shields.io/github/repo-size/Iago3-stack/ai-bug-triage-system?style=for-the-badge&label=Tamanho" />
  <img src="https://img.shields.io/github/last-commit/Iago3-stack/ai-bug-triage-system?style=for-the-badge&label=%C3%9Altima%20atividade" />
  <img src="https://img.shields.io/badge/release-v1.0.0-2E7CF6?style=for-the-badge" />
  <a href="docs/README.md"><img src="https://img.shields.io/badge/Doc.%20de%20Engenharia-9C27B0?style=for-the-badge&logo=bookstack&logoColor=white" /></a>
</div>

> ⭐ **Se esta triagem te ajudou, dá uma estrelinha no projeto** — quanto mais estrelas, mais QAs encontram o app na busca do GitHub. É de graça!

---

<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=soft&color=gradient&customColorList=20,24,25&height=64&section=header&text=Funcionalidades%20-%20MVP%20Atual&fontSize=24&fontColor=fff&fontAlignY=58" width="100%" />
</div>

<div align="center">
  <img src="https://img.shields.io/badge/Triagem%20em%202%20camadas-2E7CF6?style=for-the-badge" />
  <img src="https://img.shields.io/badge/An%C3%A1lise%20por%20IA%20(Fase%203)-9C27B0?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Prioridade%20reconciliada-4CAF50?style=for-the-badge" />
  <img src="https://img.shields.io/badge/100%25%20Offline%20%26%20Determin%C3%ADstico-F05032?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Transpar%C3%AAncia%20de%20QA-00ACC1?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Relat%C3%B3rio%20Gherkin-25D366?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Exporta%C3%A7%C3%A3o%20(MD%2FGitHub%2FJira)-FF9800?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Hist%C3%B3rico%20de%20sess%C3%A3o-9E9E9E?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Sem%20falsos%20positivos-607D8B?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Identidade%20visual-FF4B4B?style=for-the-badge" />
</div>

- 🔵 **Triagem em duas camadas**
  1. **Camada técnica**: termos críticos (crash, pagamento, login, segurança, 500...) escalam a severidade.
  2. **Camada NLP**: análise de sentimento por **léxico em português** + **detecção de negação** ("não funciona", "não consigo", "parou de responder"...).
- 🟣 **Análise por IA (Fase 3)**: quando houver chave `GEMINI_API_KEY`, o app chama o **Google Gemini** e complementa a triagem com severidade sugerida, categoria, **causa raiz provável**, passos para reproduzir e resumo técnico — tudo em JSON estruturado, com **fallback automático** para o motor local se a API falhar.
- 🟢 **Prioridade final reconciliada**: os dois motores são combinados pela regra do **maior vence** (nenhum alerta grave é ignorado) e o app **sinaliza divergência** quando discordam, recomendando revisão humana.
- ⚠️ **100% offline e determinístico**: o motor `triagem.py` usa apenas a biblioteca padrão do Python — sem API de tradução, sem internet, sem custo e com resultado sempre reproduzível.
- 🔷 **Transparência de QA**: o relatório informa o **motor de análise** usado e os **fatores identificados** em cada triagem.
- 💚 **Relatório Gherkin** (`Dado/Quando/Então`) baseado na prioridade detectada.
- 🟠 **Exportação**: baixar relatório (`.md`), abrir **Issue no GitHub** pré-preenchida ou enviar ao **Jira** (configurável).
- ⚪ **Histórico da sessão** em tabela (`pandas`) com opção de limpar.
- 🟫 **Sem falsos positivos técnicos**: palavras como *erro*, *bug* e *falha* são vocabulário normal de teste e **não** disparam severidade sozinhas.
- 🟥 **Interface com identidade visual própria** (tema Streamlit em `config.toml`).

---

<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=soft&color=gradient&customColorList=20,24,25&height=64&section=header&text=Tecnologias&fontSize=24&fontColor=fff&fontAlignY=58" width="100%" />
</div>

<div align="center">
  <img src="https://img.shields.io/badge/Python%203.13-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" />
  <img src="https://img.shields.io/badge/Google%20Gemini-8E75B2?style=for-the-badge&logo=googlegemini&logoColor=white" />
  <img src="https://img.shields.io/badge/pandas-150458?style=for-the-badge&logo=pandas&logoColor=white" />
  <img src="https://img.shields.io/badge/Linux%20Mint-87CF3E?style=for-the-badge&logo=linuxmint&logoColor=white" />
</div>

- 🐍 **Python 3.13** — lógica e motor NLP (biblioteca `re` / stdlib)
- 🚀 **Streamlit 1.62** — interface web e deploy na nuvem
- 🔮 **Google Gemini (`google-genai`)** — análise de causa raiz via LLM (Fase 3)
- 🐼 **pandas** — tabela de histórico de triagens
- 🐧 Desenvolvido em **Linux Mint Debian** (Laboratório Hack28)

---

<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=soft&color=gradient&customColorList=20,24,25&height=64&section=header&text=Como%20Rodar%20Localmente&fontSize=24&fontColor=fff&fontAlignY=58" width="100%" />
</div>

<div align="center">
  <img src="https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white" />
  <img src="https://img.shields.io/badge/Python%20venv-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/pip-3776AB?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" />
</div>

```bash
git clone https://github.com/Iago3-stack/ai-bug-triage-system.git   # 📥 clona o repo
cd ai-bug-triage-system                                             # 📂 entra na pasta
python3 -m venv .venv                                                # 🐍 cria o ambiente virtual
source .venv/bin/activate                                            # ⚡ ativa o venv
pip install -r requirements.txt                                      # 📦 instala as dependências
streamlit run home.py                                                # 🚀 roda a aplicação
```

A análise por IA usa a chave `GEMINI_API_KEY` (gratuita em [aistudio.google.com/apikey](https://aistudio.google.com/apikey)). Sem a chave, o app funciona normalmente só com o motor local:

- 🔑 **Local**: crie um arquivo `.env` na raiz com `GEMINI_API_KEY=...` (ele é ignorado pelo `.gitignore`).
- ☁️ **Streamlit Cloud**: `Settings → Secrets → GEMINI_API_KEY` (nunca coloque a chave em código ou no repositório).

🧪 Teste rápido dos motores sem interface:

```bash
python triagem.py   # 🟢 motor determinístico local
python ia.py        # 🔮 análise por IA (Gemini) — exige a chave
```

---

<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=soft&color=gradient&customColorList=20,24,25&height=64&section=header&text=Estrutura&fontSize=24&fontColor=fff&fontAlignY=58" width="100%" />
</div>

| Arquivo | Papel |
|---|---|
| 🖥️ `home.py` | Interface web (Streamlit): cabeçalho, ferramenta, export e histórico |
| 🧠 `triagem.py` | Motor NLP: léxico PT, padrões de negação e classificação de severidade (offline) |
| 🔮 `ia.py` | Análise por IA via Google Gemini: causa raiz, categoria e passos (com fallback) |
| 📦 `requirements.txt` | Dependências pinadas |
| 🎨 `.streamlit/config.toml` | Tema e configurações da app |
| 📚 `docs/` | [Documentação de Engenharia de Software](docs/README.md) — requisitos, casos de teste, arquitetura e estratégia de QA |

---

<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=soft&color=gradient&customColorList=20,24,25&height=64&section=header&text=Roadmap&fontSize=24&fontColor=fff&fontAlignY=58" width="100%" />
</div>

<div align="center">
  <img src="https://img.shields.io/badge/4%20conclu%C3%ADdas-4CAF50?style=for-the-badge" />
  <img src="https://img.shields.io/badge/2%20em%20aberto-FF9800?style=for-the-badge" />
</div>

- ✅ **Fase 1** — Motor NLP offline (léxico PT + negação, sem TextBlob/Google Translate)
- ✅ **Fase 2** — Exportação do relatório, histórico de sessão e identidade visual
- ✅ **Fase 3** — Integração com **LLMs** (Gemini) para análise de causa raiz, categoria e passos — com fallback automático
- ✅ **Testes unitários do motor (`pytest`)** — 12 testes, rodam automaticamente via CI (GitHub Actions)
- ⬜ **Exportação direta via API do Jira**
- ⬜ **Persistência do histórico (banco de dados)**

---

<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=soft&color=gradient&customColorList=20,24,25&height=64&section=header&text=Licen%C3%A7a%20e%20Autoria&fontSize=24&fontColor=fff&fontAlignY=58" width="100%" />
</div>

<div align="center">
  <a href="CHANGELOG.md"><img src="https://img.shields.io/badge/Changelog-4CAF50?style=for-the-badge&logo=github&logoColor=white" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/Licen%C3%A7a-MIT-4CAF50?style=for-the-badge&logo=opensourceinitiative&logoColor=white" /></a>
  <img src="https://img.shields.io/badge/Autor-Iago%20Nunes-2E7CF6?style=for-the-badge&logo=github&logoColor=white" />
  <img src="https://img.shields.io/badge/GitHub-Iago3%20stack-181717?style=for-the-badge&logo=github&logoColor=white" />
</div>

**🧑‍💻 Autor:** [Iago Nunes (Iago3-stack)](https://github.com/Iago3-stack) — QA Automation Engineer | Estudante de IA & Machine Learning na UNIASSELVI.

📜 Este projeto é distribuído sob a **licença MIT** (ver arquivo [`LICENSE`](LICENSE)). Qualquer uso, cópia ou modificação **deve manter a atribuição de crédito** ao autor original — remover ou ocultar a autoria viola a licença.

🕓 O histórico completo de construção (commits, datas e motivações) está público em [github.com/Iago3-stack/ai-bug-triage-system](https://github.com/Iago3-stack/ai-bug-triage-system).