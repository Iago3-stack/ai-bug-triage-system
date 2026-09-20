<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=soft&color=gradient&customColorList=20,24,25&height=80&section=header&text=AI%20Bug%20Triage%20System&fontSize=22&fontColor=fff&fontAlignY=60" width="100%" />
</div>

![Tela do app](assets/screenshot.png?v=202609)

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
  <img src="https://img.shields.io/badge/Login%20multi-tenant-7C3AED?style=for-the-badge" />
  <a href="https://github.com/Iago3-stack/ai-bug-triage-system/actions"><img src="https://img.shields.io/endpoint?url=https%3A%2F%2Fai-bug-triage.com.br%2Fpytest-badge.json&style=for-the-badge&logo=githubactions&logoColor=white&cacheSeconds=300" /></a>
  <img src="https://img.shields.io/badge/Sess%C3%A3o%20persiste%20no%20F5-0EA5E9?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Plano%20Basic%20%2F%20Premium-F59E0B?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Identidade%20visual-FF4B4B?style=for-the-badge" />
</div>

- 🔵 **Triagem em duas camadas**
  1. **Camada técnica**: termos críticos (crash, pagamento, login, segurança, 500...) escalam a severidade.
  2. **Camada NLP**: análise de sentimento por **léxico em português** + **detecção de negação** ("não funciona", "não consigo", "parou de responder"...) + **padrões por raiz (regex)** — *lentidão* dispensa enumerar toda flexão (`lento`, `lenta`, `lentíssimo`, `lentamente`...) e o lookahead `(?!es?\b)` exclui o falso positivo *lente/lentes*.
- 🟣 **Análise por IA (Fase 3)**: se houver chave `GEMINI_API_KEY` **e o checkbox 🔮 estiver marcado**, o app chama o **Google Gemini** e complementa a triagem com severidade sugerida, categoria, **causa raiz provável**, passos para reproduzir e resumo técnico — tudo em JSON estruturado, com **fallback automático** para o **Groq (open-weight, `gpt-oss-120b`)** se o Gemini cair (503/429/chave expirada) — ou se o usuário desligar a IA para aquela triagem. Há um **seletor de provedor** (Automático / Gemini / Groq) para forçar um dos dois — e o botão **➕ Adicionar modelo próprio**: **traga sua API** de qualquer provedor (OpenAI-compatível como `gpt-4o`, DeepSeek ou um endpoint local — ou um modelo Gemini pago) para testar dentro do app. A chave fica **só na sessão** (nunca é gravada em disco/histórico).
- 🟢 **Prioridade final reconciliada**: os dois motores são combinados pela regra do **maior vence** (nenhum alerta grave é ignorado) e o app **sinaliza divergência** quando discordam, recomendando revisão humana.
- ⚠️ **100% offline e determinístico**: o motor `triagem.py` usa apenas a biblioteca padrão do Python — sem API de tradução, sem internet, sem custo e com resultado sempre reproduzível.
- 📋 **Colar falha bruta e preencher relato sozinho (Pilar 1 de automação)** — na Ferramenta, cole um **stack trace, log ou a mensagem do usuário** e o app extrai **título, categoria, módulo, versão, severidade prévia, erro principal (com local do frame) e passos para reproduzir**, preenchendo o relato pronto para revisar. 100% local, funciona sem internet e reconhece traces **Python, Java, JS/TS, C#/.NET, Go e Ruby**.
- 🔷 **Transparência de QA**: o relatório informa o **motor de análise** usado e os **fatores identificados** em cada triagem.
- 💚 **Relatório Gherkin** (`Dado/Quando/Então`) baseado na prioridade detectada.
- 🟠 **Exportação**: baixar relatório (`.md`), abrir **Issue no GitHub** pré-preenchida ou **criar issue real no Jira** via API (com prioridade mapeada automaticamente).
- ⚪ **Histórico da sessão** em tabela (`pandas`) com opção de limpar.
- 📁 **Histórico persistido (JSONL local + ☁️ Supabase)** — cada triagem vira um **snapshot fiel** em `data/historico.jsonl` (local, gitignored); quando o **Supabase** está configurado (URL + anon key nos secrets), o histórico passa a viver na **nuvem** e sobrevive a redeploys (com **failover** automático pra JSONL se a nuvem cair). **Seletor de data + download** do relatório em Markdown + vínculo com a issue criada no Jira. Backend visível no expander do histórico.
- 🛡️ **Guardrails de entrada/saída (PII)** — detecta e **mascara** token Atlassian, chaves Gemini/Google/OpenAI, tokens GitHub, e-mails, **senhas numéricas, telefones e CPFs** digitados no relato: nada sensível vai para o Gemini, o Jira, o GitHub ou o histórico.
- 🧪 **Testes + CI** — suíte `pytest` com dezenas de arquivos (motor, colar falha, Jira, persistência, guardrails, dashboard, RAG, nuvem, Pix, IA, Auth/Supabase, notificações, plano e persistência de sessão) rodando a cada push via GitHub Actions. A **contagem exata de testes aprovados aparece no badge dinâmico acima** (atualiza automaticamente a cada CI) — veja o número atual ao vivo em [`ai-bug-triage.com.br`](https://ai-bug-triage.com.br).
- 📈 **Dashboard de QA completo** — visão geral 100% local do histórico (JSONL/cloud), sem enviar nada: KPIs + **saúde da suíte (0–10)**, **gauge de % de críticas/altas**, **filtro por funcionalidade**, **evolução do score médio por dia**, **top causas raiz da IA**, **taxa + lista das divergências IA vs. léxico** e coluna IA com o **provedor real** que respondeu.
- 📚 **RAG no histórico** — o Gemini consulta as triagens passadas (retrieval local por similaridade Jaccard) e responde se o problema **já aconteceu** e **como foi resolvido** antes, apontando os registros similares. Depois de resolver o bug, **registre a solução** no app — vira aprendizado para as próximas triagens similares.
- 🟦 **Rodapé de doação Pix** — card no rodapé do app com o **símbolo oficial do Banco Central** (SVG inline, teal — sem depender de serviço externo), botão **"Pagar com Pix via link"** e **QR Code** com a chave com `+55` (payload EMV/CRC válido) + botão que **copia a chave sem o DDI** (os apps de banco completam sozinhos). Tudo dentro de um **iframe local** do Streamlit (`st.iframe`).
- 🟫 **Sem falsos positivos técnicos**: palavras como *erro*, *bug* e *falha* são vocabulário normal de teste e **não** disparam severidade sozinhas.
- 🟥 **Interface com identidade visual própria** (tema Streamlit em `config.toml`).
- 🔐 **Login real (Supabase Auth, multi-tenant)** — cadastro com confirmação de e-mail e login (e-mail + senha); **Início público**, **Ferramenta e Dashboard exigem login** quando o Supabase está configurado (sem config, o app segue aberto). Sidebar mostra 👤 usuário + "Sair". Cada conta vê só o seu histórico (registros persistidos com `tenant_id`).
- 🔄 **Sessão persiste no F5** — ao recarregar a página, o usuário continua logado: cookie `_auth_sessao_persist_rf` + "ponte de escrita" persistente (JSON → iframe `localStorage` → confirm), com falha degradando para tela de login com mensagem honesta.

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

### 🔔 Alerta de triagens CRÍTICAS/ALTAS (e-mail ou Discord)

Quando uma triagem resulta em **CRÍTICA 🚨 ou ALTA 🚨**, o app avisa automaticamente — vira "monitor de QA". Dois canais (pode configurar os dois):

**✉️ E-mail (Gmail/SMTP) — não precisa criar conta nova:**
1. No Google, ative a "verificação em 2 etapas" e gere um **app password** em `https://myaccount.google.com/apppasswords` (a senha do Gmail normal não funciona no SMTP).
2. Configure nos Secrets (Cloud) ou `.env` (local): `ALERTA_EMAIL_TO` (para onde chega o alerta), `SMTP_USER` (seu Gmail) e `SMTP_PASS` (o app password). Opcionais: `SMTP_HOST`/`SMTP_PORT` (padrão `smtp.gmail.com:587`).

**🔔 Discord (opcional):** servidor/canal → Configurações → **Integrações → Webhooks → Novo webhook** → copie a URL e configure `DISCORD_WEBHOOK` (`https://discord.com/api/webhooks/...`).

Sem canal configurado (ou em falha de rede), o alerta é silencioso — nunca interrompe a triagem.

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
  <a href="docs/05-persistencia-nuvem.md"><img src="https://img.shields.io/badge/Persist%C3%AAncia%20em%20Nuvem-38BDF8?style=for-the-badge&logo=libpostal&logoColor=white" /></a>
</div>

| Arquivo | Papel |
|---|---|
| 🖥️ `home.py` | Interface web (Streamlit): cabeçalho, ferramenta, export, histórico e **rodapé de doação Pix via `st.iframe`** |
| 🧠 `triagem.py` | Motor NLP: léxico PT, padrões de negação e classificação de severidade (offline) |
| 🔗 `jira_client.py` | Cliente da API REST v3 do Jira: cria issues (Tarefa) com prioridade mapeada |
| 🔮 `ia.py` | Análise por IA via Google Gemini: causa raiz, categoria e passos (com fallback Groq e **modelo próprio** OpenAI-compatível/Gemini) |
| 📚 `rag.py` | RAG leve no histórico: retrieval por similaridade Jaccard (offline) + geração que responde "já aconteceu? como resolvemos?" |
| 🧪 `test_triagem.py` | 18 testes unitários do motor (rodam no CI) |
| 🧪 `test_jira_client.py` | 15 testes unitários do cliente Jira (rodam no CI) |
| 📁 `persistencia.py` | Histórico em `data/historico.jsonl` (JSONL local, gitignored) — **facade**: com nuvem configurada, grava no Supabase; senão, JSONL puro |
| ☁️ `nuvem_supabase.py` | Backend de persistência na nuvem (Supabase REST): insert/select/update e vínculo Jira — credenciais só em secrets/.env |
| 🛡️ `guardrails.py` | Bloqueia vazamento de credenciais/PII: mascara tokens, chaves, e-mails, senhas numéricas, telefones e CPFs antes de IA/Jira/GitHub/histórico |
| 🧪 `test_persistencia.py` | 11 testes unitários da persistência (rodam no CI) |
| 🧪 `test_guardrails.py` | 18 testes de detecção/máscara de credenciais e PII (rodam no CI) |
| 🧪 `test_dashboard.py` | 17 testes do Dashboard de QA: saúde da suíte, gauge, filtro por funcionalidade, top causas, divergências e provedor real (rodam no CI) |
| 🧪 `test_rag.py` | 13 testes do RAG: tokenização, similaridade, recuperação top-k, contexto (com resolução) e orquestração (rodam no CI) |
| 🧪 `test_nuvem_supabase.py` | 14 testes da persistência em nuvem: config, conversão, HTTP (mockado), resolução, failover e dispatch do facade (rodam no CI) |
| 🧪 `test_pix.py` | 10 testes do Pix: payload EMV, CRC-CCITT, precedência link/QR e `chave_copia()` sem `+55` (rodam no CI) |
| 🧪 `test_ia.py` | 32 testes da IA: dispatch de provedor (auto/Gemini/Groq/modelo próprio OpenAI-compatível e Gemini custom), JSON, fallback, mensagens de erro e orquestração RAG (rodam no CI) |
| 🔐 `auth_supabase.py` | Autenticação (Supabase Auth/GoTrue via REST, stdlib): cadastro com confirmação, login e logout — credenciais reutilizam `SUPABASE_URL`/`SUPABASE_ANON_KEY` |
| 🧪 `test_auth_supabase.py` | 29 testes do login: parser de erros, cadastro/login/logout, isolação por sessão e integração com a UI (rodam no CI) |
| 🔔 `notificacoes.py` | Canais de alerta (e-mail SMTP + Discord) configuráveis por usuário/sessão, com testadores à prova de exceção |
| 🧪 `test_notificacoes.py` | 30 testes dos alertas: envio SMTP/Discord (mockado), override por sessão e erros amigáveis (rodam no CI) |
| 💳 `plano.py` | Planos Basic/Premium e isolamento por tenant: `PLANO=free|pago` liga/desliga recursos e `TENANT_ID` segmenta registros |
| 🧪 `test_plano.py` | 10 testes do plano: gating de recursos free×pago e filtro por `tenant_id` (rodam no CI) |
| 💾 `sessao_persist.py` | Persistência de sessão no F5: enfileira salvar/limpar e grava via ponte persistente (cookie + iframe `localStorage`) |
| 🧪 `test_sessao_persist.py` | 5 testes da ponte de escrita e da failover da sessão (rodam no CI) |
| 🧪 `test_ferramenta.py` | 3 testes da página ferramenta: UI/triagem e integração (rodam no CI) |
| 📈 `dashboard.py` | Dashboard de QA: KPIs + saúde da suíte (0–10) + gauge de críticas + filtro por funcionalidade + top causas (IA) + score/dia + divergências IA vs. léxico + provedor real (leitura do JSONL/Cloud) |
| 🟦 `pix.py` | Gerador de pagamento Pix: payload EMV/QR (CRC-CCITT), QR Code PNG (base64), **link de pagamento** com valor fixo e chaves com/sem `+55` (`chave`/`chave_copia`) |
| 📦 `requirements.txt` | Dependências pinadas |
| 🎨 `.streamlit/config.toml` | Tema e configurações da app |
| 📚 `docs/` | Documentação de engenharia e qualidade |

---

<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=soft&color=gradient&customColorList=20,24,25&height=64&section=header&text=Roadmap&fontSize=24&fontColor=fff&fontAlignY=58" width="100%" />
</div>

<div align="center">
  <img src="https://img.shields.io/badge/12%20conclu%C3%ADdas-4CAF50?style=for-the-badge" />
  <img src="https://img.shields.io/badge/0%20em%20aberto-brightgreen?style=for-the-badge" />
</div>

- ✅ **Fase 1** — Motor NLP offline (léxico PT + negação, sem TextBlob/Google Translate)
- ✅ **Fase 2** — Exportação do relatório, histórico de sessão e identidade visual
- ✅ **Fase 3** — Integração com **LLMs** (Gemini) para análise de causa raiz, categoria e passos — com fallback automático
- ✅ **Seletor de IA por triagem (checkbox 🔮 + provedor)** — você decide quando a IA entra: desligue para triagem 100% local, ou escolha **Automático (Gemini → Groq)**, **só Gemini** ou **só Groq** — ou **➕ adicione um modelo próprio** com a sua API (OpenAI-compatível ou Gemini pago), **renomeável e editável**, com chave que fica só na sessão. O relatório mostra qual provedor/modelo respondeu
- ✅ **Testes unitários do motor (`pytest`)** — suíte extensa de arquivos (motor + Jira + persistência + guardrails + dashboard + RAG + nuvem + Pix + IA + Auth/Supabase + notificações + plano + persistência de sessão) rodando automaticamente via CI (GitHub Actions) com **contagem exibida ao vivo no badge dinâmico acima**
- ✅ **Exportação via API do Jira** — cria issue do tipo Tarefa no `iagoqa.atlassian.net` (prioridade mapeada automaticamente)
- ✅ **Persistência do histórico (JSONL)** — cada triagem vira um snapshot fiel em `data/historico.jsonl` (local, gitignored): com IA salva o relatório completo; sem IA, só o léxico. Seletor de data + download do relatório
- ✅ **Guardrails de entrada/saída (PII/credenciais)** — detecta e mascara tokens Atlassian, chaves Gemini/Google/OpenAI, tokens GitHub, e-mails, senhas numéricas, telefones e CPFs digitados no relato: nada sensível vai para o Gemini, o Jira, o GitHub ou o histórico
- ✅ **Dashboard de QA completo** — saúde da suíte (0–10), gauge de % de críticas/altas, filtro por funcionalidade, evolução do score médio/dia, top causas raiz (IA), taxa + lista das divergências IA vs. motor local e provedor real na coluna IA (100% local, sem enviar nada)
- ✅ **RAG no histórico** — o Gemini consulta as triagens passadas (top-k similares, retrieval local por Jaccard) e responde **"isso já aconteceu? como resolvemos?"** com a resolução anterior; se não acha, sinaliza caso novo
- ✅ **Alerta CRÍTICA/ALTA (e-mail SMTP + Discord)** — "monitor de QA": canais configuráveis por sessão no modal ⚙️ (nada em disco), com testadores que nunca derrubam o app e status real do envio
- ✅ **App multi-página + Login multi-tenant** — `Início`/`Triagem`/`Dashboard` via `st.navigation`; cadastro com confirmação de e-mail e login (Supabase Auth); histórico isolado por conta (`tenant_id`); **sessão persiste no F5** (cookie + ponte)
- ✅ **Roadmap 12/12 🎉** — MVP + SaaS esboçado concluídos; próximos passos rumo a billing/compartilhamento abaixo

**🚀 Rumo a um SaaS de QA** (próximos passos):
> - 💳 **Assinatura/billing** (Stripe) ligada ao `PLANO` atual + cobrança por plano pago (PASSO 4)
> - 🧠 **Causa raiz com histórico** (evolução do RAG ✅) → sugerir a correção que resolveu da última vez → *triage agent*
> - 🔁 **Limpeza de warnings** de deprecação do Streamlit (`use_container_width` → `width='stretch'`)
> - 🌐 **webhook/API** · 📧 **relatório agendado** · 📊 **LLMOps/evals**
> - Roadmap completo acompanhado no brainstorming do projeto (`~/Documentos/roadmap-ia.md`).
>
> *Persistência em nuvem ☁️, login 🔐 e modelo alternativo (Groq) 🔁 já estão feitos (v2.6.x).*

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