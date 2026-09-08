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
  <a href="https://github.com/Iago3-stack/ai-bug-triage-system/releases/latest"><img src="https://img.shields.io/github/v/release/Iago3-stack/ai-bug-triage-system?style=for-the-badge&label=Release&color=FF7043&logo=git&logoColor=white" /></a>
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
  <img src="https://img.shields.io/badge/Hist%C3%B3rico%20persistido%20%28JSONL%29-25D366?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Guardrails%20de%20PII-E91E63?style=for-the-badge" />
  <a href="https://github.com/Iago3-stack/ai-bug-triage-system/actions"><img src="https://img.shields.io/endpoint?url=https%3A%2F%2Fiago3-stack.github.io%2Fai-bug-triage-system%2Fpytest-badge.json&style=for-the-badge&logo=githubactions&logoColor=white&cacheSeconds=300" /></a>
  <img src="https://img.shields.io/badge/Sem%20falsos%20positivos-607D8B?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Identidade%20visual-FF4B4B?style=for-the-badge" />
</div>

- 🔵 **Triagem em duas camadas**
  1. **Camada técnica**: termos críticos (crash, pagamento, login, segurança, 500...) escalam a severidade.
  2. **Camada NLP**: análise de sentimento por **léxico em português** + **detecção de negação** ("não funciona", "não consigo", "parou de responder"...) + **padrões por raiz (regex)** — *lentidão* dispensa enumerar toda flexão (`lento`, `lenta`, `lentíssimo`, `lentamente`...) e o lookahead `(?!es?\b)` exclui o falso positivo *lente/lentes*.
- 🟣 **Análise por IA (Fase 3)**: se houver chave `GEMINI_API_KEY` **e o checkbox 🔮 estiver marcado**, o app chama o **Google Gemini** e complementa a triagem com severidade sugerida, categoria, **causa raiz provável**, passos para reproduzir e resumo técnico — tudo em JSON estruturado, com **fallback automático** para o motor local se a API falhar (ou se o usuário desligar a IA para aquela triagem).
- 🟢 **Prioridade final reconciliada**: os dois motores são combinados pela regra do **maior vence** (nenhum alerta grave é ignorado) e o app **sinaliza divergência** quando discordam, recomendando revisão humana.
- ⚠️ **100% offline e determinístico**: o motor `triagem.py` usa apenas a biblioteca padrão do Python — sem API de tradução, sem internet, sem custo e com resultado sempre reproduzível.
- 🔷 **Transparência de QA**: o relatório informa o **motor de análise** usado e os **fatores identificados** em cada triagem.
- 💚 **Relatório Gherkin** (`Dado/Quando/Então`) baseado na prioridade detectada.
- 🟠 **Exportação**: baixar relatório (`.md`), abrir **Issue no GitHub** pré-preenchida ou **criar issue real no Jira** via API (com prioridade mapeada automaticamente).
- ⚪ **Histórico da sessão** em tabela (`pandas`) com opção de limpar.
- 📁 **Histórico persistido (JSONL local + ☁️ Supabase)** — cada triagem vira um **snapshot fiel** em `data/historico.jsonl` (local, gitignored); quando o **Supabase** está configurado (URL + anon key nos secrets), o histórico passa a viver na **nuvem** e sobrevive a redeploys (com **failover** automático pra JSONL se a nuvem cair). **Seletor de data + download** do relatório em Markdown + vínculo com a issue criada no Jira. Backend visível no expander do histórico.
- 🛡️ **Guardrails de entrada/saída (PII)** — detecta e **mascara** token Atlassian, chaves Gemini/Google/OpenAI, tokens GitHub, e-mails, **senhas numéricas, telefones e CPFs** digitados no relato: nada sensível vai para o Gemini, o Jira, o GitHub ou o histórico.
- 🧪 **96 testes + CI** — suíte `pytest` (motor, Jira, persistência, guardrails, dashboard, RAG, nuvem e Pix) rodando a cada push via GitHub Actions (badge de qualidade em cima).
- 📈 **Dashboard de QA** — visão geral 100% local do histórico persistido: KPIs (total, CRÍTICAs, MÉDIAS, normais, score médio), **distribuição de severidade**, **volume por dia**, **funcionalidades mais afetadas** e comparativo **IA vs. motor local** (divergências).
- 📚 **RAG no histórico** — o Gemini consulta as triagens passadas (retrieval local por similaridade Jaccard) e responde se o problema **já aconteceu** e **como foi resolvido** antes, apontando os registros similares. Depois de resolver o bug, **registre a solução** no app — vira aprendizado para as próximas triagens similares.
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

### 🔗 Exportação para o Jira (API REST)

O botão **📋 Exportar para Jira** cria a issue do tipo **Tarefa** direto no seu projeto Jira Cloud. Você configura de **dois jeitos**:

- 🖱️ **Pela interface**: no app, abra `🔑 Jira — configurar exportação` no sidebar e preencha **e-mail Atlassian**, **API Token** e **chave do projeto**. Basta login+token (Basic Auth) — **não** é preciso OAuth nem senha.
- ⚙️ **Por variáveis de ambiente** (`.env` ou Streamlit Secrets): `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_PROJECT_KEY` e, opcionalmente, `JIRA_URL` (padrão `https://iagoqa.atlassian.net`).

🔑 **Para gerar o API Token:** acesse `https://id.atlassian.com/manage-profile/security/api-tokens` → **Create API token** → copie o token (ele só aparece uma vez). A **chave do projeto** (ex.: `KAN` para "Rastreamento de bugs") aparece na URL do seu projeto: `https://iagoqa.atlassian.net/browse/KAN-4` → `KAN`.

**Tipo de item (importante):** o app assume `Tarefa` por padrão (compatível com projetos **Kanban**, onde `Bug` não existe). Os tipos válidos do template Kanban são: `Tarefa`, `História`, `Epic`, `Subtask`. Para outro projeto, troque via `JIRA_ISSUE_TYPE`.

**Prioridades mapeadas automaticamente:** NORMAL ✅ → `Low` · MÉDIA ⚠️ → `Medium` · ALTA 🚨 → `High` · CRÍTICA 🚨 → `Highest`.

🧪 Teste rápido do cliente sem interface (`python jira_client.py`) — exige as credenciais no ambiente:

```bash
python jira_client.py   # 🧪 cria uma issue de teste via API
```

🧪 Teste rápido dos motores sem interface:

```bash
python triagem.py   # 🟢 motor determinístico local
python ia.py        # 🔮 análise por IA (Gemini) — exige a chave
```

---

<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=soft&color=gradient&customColorList=20,24,25&height=64&section=header&text=Estrutura&fontSize=24&fontColor=fff&fontAlignY=58" width="100%" />
</div>

> 🧩 **Conheça a engenharia por trás do AI Bug Triage System** — o processo completo de requisitos, casos de teste e estratégia de QA está em [📚 docs/](docs/README.md).

<div align="center">
  <a href="docs/01-requisitos.md"><img src="https://img.shields.io/badge/Requisitos-2E7CF6?style=for-the-badge&logo=bookstack&logoColor=white" /></a>
  <a href="docs/02-casos-de-teste.md"><img src="https://img.shields.io/badge/Casos%20de%20Teste-4CAF50?style=for-the-badge&logo=checkmarx&logoColor=white" /></a>
  <a href="docs/03-arquitetura.md"><img src="https://img.shields.io/badge/Arquitetura-9C27B0?style=for-the-badge&logo=diagramdotnet&logoColor=white" /></a>
  <a href="docs/04-estrategia-de-qualidade.md"><img src="https://img.shields.io/badge/Estrat%C3%A9gia%20de%20QA-FF9800?style=for-the-badge&logo=quality&logoColor=white" /></a>
</div>

| Arquivo | Papel |
|---|---|
| 🖥️ `home.py` | Interface web (Streamlit): cabeçalho, ferramenta, export e histórico |
| 🧠 `triagem.py` | Motor NLP: léxico PT, padrões de negação e classificação de severidade (offline) |
| 🔗 `jira_client.py` | Cliente da API REST v3 do Jira: cria issues (Tarefa) com prioridade mapeada |
| 🔮 `ia.py` | Análise por IA via Google Gemini: causa raiz, categoria e passos (com fallback) |
| 📚 `rag.py` | RAG leve no histórico: retrieval por similaridade Jaccard (offline) + geração que responde "já aconteceu? como resolvemos?" |
| 🧪 `test_triagem.py` | 18 testes unitários do motor (rodam no CI) |
| 🧪 `test_jira_client.py` | 15 testes unitários do cliente Jira (rodam no CI) |
| 📁 `persistencia.py` | Histórico em `data/historico.jsonl` (JSONL local, gitignored) — **facade**: com nuvem configurada, grava no Supabase; senão, JSONL puro |
| ☁️ `nuvem_supabase.py` | Backend de persistência na nuvem (Supabase REST): insert/select/update e vínculo Jira — credenciais só em secrets/.env |
| 🛡️ `guardrails.py` | Bloqueia vazamento de credenciais/PII: mascara tokens, chaves, e-mails, senhas numéricas, telefones e CPFs antes de IA/Jira/GitHub/histórico |
| 🧪 `test_persistencia.py` | 8 testes unitários da persistência (rodam no CI) |
| 🧪 `test_guardrails.py` | 14 testes de detecção/máscara de credenciais e PII (rodam no CI) |
| 🧪 `test_dashboard.py` | 6 testes das agregações do Dashboard de QA (rodam no CI) |
| 🧪 `test_rag.py` | 13 testes do RAG: tokenização, similaridade, recuperação top-k, contexto (com resolução) e orquestração (rodam no CI) |
| 🧪 `test_nuvem_supabase.py` | 14 testes da persistência em nuvem: config, conversão, HTTP (mockado), resolução, failover e dispatch do facade (rodam no CI) |
| 📈 `dashboard.py` | Dashboard de QA: KPIs + severidade + volume/dia + funcionalidades + IA vs. léxico (leitura do JSONL) |
| 📦 `requirements.txt` | Dependências pinadas |
| 🎨 `.streamlit/config.toml` | Tema e configurações da app |
| 📚 `docs/` | Documentação de engenharia e qualidade |

---

<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=soft&color=gradient&customColorList=20,24,25&height=64&section=header&text=Roadmap&fontSize=24&fontColor=fff&fontAlignY=58" width="100%" />
</div>

<div align="center">
  <img src="https://img.shields.io/badge/10%20conclu%C3%ADdas-4CAF50?style=for-the-badge" />
  <img src="https://img.shields.io/badge/0%20em%20aberto-brightgreen?style=for-the-badge" />
</div>

- ✅ **Fase 1** — Motor NLP offline (léxico PT + negação, sem TextBlob/Google Translate)
- ✅ **Fase 2** — Exportação do relatório, histórico de sessão e identidade visual
- ✅ **Fase 3** — Integração com **LLMs** (Gemini) para análise de causa raiz, categoria e passos — com fallback automático
- ✅ **Seletor de IA por triagem (checkbox 🔮)** — você decide quando o Gemini entra: desligue para triagem 100% local ou ligue para ganhar causa raiz e passos
- ✅ **Testes unitários do motor (`pytest`)** — 96 testes (motor + Jira + persistência + guardrails + dashboard + RAG + nuvem + Pix), rodam automaticamente via CI (GitHub Actions)
- ✅ **Exportação via API do Jira** — cria issue do tipo Tarefa no `iagoqa.atlassian.net` (prioridade mapeada automaticamente)
- ✅ **Persistência do histórico (JSONL)** — cada triagem vira um snapshot fiel em `data/historico.jsonl` (local, gitignored): com IA salva o relatório completo; sem IA, só o léxico. Seletor de data + download do relatório
- ✅ **Guardrails de entrada/saída (PII/credenciais)** — detecta e mascara tokens Atlassian, chaves Gemini/Google/OpenAI, tokens GitHub, e-mails, senhas numéricas, telefones e CPFs digitados no relato: nada sensível vai para o Gemini, o Jira, o GitHub ou o histórico
- ✅ **Dashboard de QA** — visão geral do histórico persistido: KPIs, distribuição de severidade, volume por dia, funcionalidades mais afetadas e comparativo IA vs. motor local (100% local, sem enviar nada)
- ✅ **RAG no histórico** — o Gemini consulta as triagens passadas (top-k similares, retrieval local por Jaccard) e responde **"isso já aconteceu? como resolvemos?"** com a resolução anterior; se não acha, sinaliza caso novo
- - ✅ **Roadmap 10/10 🎉** — MVP concluído; próximos passos rumo ao SaaS abaixo

**🚀 Rumo a um SaaS de QA** (roadmap futuro):
> Depois de esgotar o MVP, a visão é evoluir para um **produto tipo SaaS/CRM de triagem**:
> - ☁️ **Persistência em nuvem** (Supabase/Postgres) — histórico real entre sessões (hoje o disco da nuvem é efêmero)
> - 🔐 **Autenticação (login)** — cada usuário vê só o seu histórico (multi-tenant)
> - 🧠 **Causa raiz com histórico** (evolução do RAG ✅) → sugerir a correção que resolveu da última vez → *triage agent*
> - 🔁 **Modelos alternativos** (Groq/Llama-Ollama) no mesmo `ia.py`, sem depender só do Gemini
> - 🔔 **Notificações** (Slack/Discord/e-mail) em CRÍTICA · 🌐 **webhook/API** · 📧 **relatório agendado** · 📊 **LLMOps/evals**
> Roadmap completo acompanhado no brainstorming do projeto (`~/Documentos/roadmap-ia.md`).

---

<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=soft&color=gradient&customColorList=20,24,25&height=64&section=header&text=Licen%C3%A7a%20e%20Autoria&fontSize=24&fontColor=fff&fontAlignY=58" width="100%" />
</div>

<div align="center">
  <a href="CHANGELOG.md"><img src="https://img.shields.io/badge/Changelog-4CAF50?style=for-the-badge&logo=github&logoColor=white" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/Licen%C3%A7a-MIT-4CAF50?style=for-the-badge&logo=opensourceinitiative&logoColor=white" /></a>
  <a href="AUTORIA.md"><img src="https://img.shields.io/badge/Autoria-2E7CF6?style=for-the-badge&logo=github&logoColor=white" /></a>
  <img src="https://img.shields.io/badge/Autor-Iago%20Nunes-2E7CF6?style=for-the-badge&logo=github&logoColor=white" />
  <img src="https://img.shields.io/badge/GitHub-Iago3%20stack-181717?style=for-the-badge&logo=github&logoColor=white" />
</div>

**🧑‍💻 Autor:** [Iago Nunes (Iago3-stack)](https://github.com/Iago3-stack) — QA Automation Engineer | Estudante de IA & Machine Learning na UNIASSELVI.

📜 Este projeto é distribuído sob a **licença MIT** (ver arquivo [`LICENSE`](LICENSE)). Qualquer uso, cópia ou modificação **deve manter a atribuição de crédito** ao autor original — remover ou ocultar a autoria viola a licença. Veja [`AUTORIA.md`](AUTORIA.md) para a origem e as provas públicas de autoria.

🕓 O histórico completo de construção (commits, datas e motivações) está público em [github.com/Iago3-stack/ai-bug-triage-system](https://github.com/Iago3-stack/ai-bug-triage-system).