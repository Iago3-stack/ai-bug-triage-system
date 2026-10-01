# 03 — Arquitetura e Fluxo

Visão da arquitetura do **AI Bug Triage System** e do fluxo de processamento de um relato de bug.

## 1. Visão geral

O sistema trabalha com **dois motores de análise** que se **reconciliam** pela regra do **maior vence**:

```
┌─────────────┐     descrição       ┌──────────────────────────────┐
│    Usuário   │ ──────────────────▶ │         home.py (UI)          │
│  (QA/Dev)    │                     │  Streamlit                  │
└─────────────┘                     └──────────────┬───────────────┘
                                                   │
                              ┌────────────────────┴────────────────────┐
                              │                                         │
                    ┌─────────▼─────────┐                      ┌────────▼─────────┐
                    │  triagem.py       │                      │  ia.py (Fase 3)   │
                    │  Motor NLP local  │                      │  Google Gemini     │
                    │  (stdlib, offline)│                      │  JSON estruturado  │
                    └─────────┬─────────┘                      └────────┬─────────┘
                              │                                         │
                              └────────────┬────────────────────────────┘
                                           ▼
                              ┌──────────────────────────────┐
                              │  Reconciliador (maior vence)  │
                              │  + sinal de divergência       │
                              └──────────────┬───────────────┘
                                             ▼
                              ┌──────────────────────────────┐
                              │  Relatório: severidade +      │
                              │  fatores + Gherkin + export   │
                              └──────────────────────────────┘
```

## 2. Componentes

| Módulo | Papel | Dependência |
|---|---|---|
| `home.py` | **App shell** (Streamlit): `st.navigation` com as páginas do `roteador.py` (Início público × demais com `pagina_login` quando o Supabase está configurado), CSS global (`ui_tema`), sidebar comum e rodapé (`ui_comum`) com navegação para Termos/Privacidade e scroll-to-top — **sem doação**: a cobrança virou plano (pixbilling/PagBank) | streamlit |
| `pix.py` | Gerador de pagamento Pix: payload EMV **COPIA-e-Coloca** com CRC-CCITT, QR Code PNG (base64), **link de pagamento** com valor fixo e chave com/sem `+55` (`chave`/`chave_copia`) | **stdlib apenas** + `qrcode` |
| `triagem.py` | Motor NLP **offline determinístico**: léxico PT + negações | **stdlib apenas** |
| `colar_falha.py` | **Pilar 1 de automação**: transforma a falha bruta colada (stack trace/log/mensagem) em **relato estruturado** (título, categoria na taxonomia da IA, módulo, versão, severidade prévia via `triagem`, erro principal, local do frame e passos) — 100% local; `estruturar_automatico` escolhe o extrator certo (adaptador → genérico) | **stdlib apenas** + `triagem` |
| `adaptadores.py` | **Pilar 2 de automação** — adapta a saída do **Playwright** (nome/erro de asserção do teste, Expected/Received, arquivo:linha; texto ou JSON do relator) e do **Postman/newman** (método+URL, **HTTP esperado × recebido**, asserção, erro do corpo JSON) para o relato estruturado; `None` → o parser genérico assume | **stdlib apenas** + `colar_falha` |
| `webhook.py` | **Pilar 3 de automação** — micro-servidor HTTP `POST /webhook/falha`: valida `evidencia` (max 200 KB), extrai via `colar_falha.estruturar_automatico`, monta o relato, com IA (`ia:true`/`WEBHOOK_IA`) e persistência (`WEBHOOK_PERSISTE`) opcionais; token `WEBHOOK_TOKEN` (comparado em **tempo constante**, `WEBHOOK_REQUIRE_TOKEN=1` o torna obrigatório sempre), `/health`, nunca levanta. **Também recebe `POST /webhook/pagamento`**: consulta o estado real do pedido no PagBank e ativa o Premium sozinho quando `PAID` (idempotente) | **stdlib** + `colar_falha`/`pagbank` |
| `pagbank.py` | **Cobrança Pix automática (API de Pedidos do PagBank)**: cria pedido com QR Code dinâmico (valor, expiração e URL de notificação), valida CPF e consulta o status; o webhook confirma (`PAID`) sem ação manual. Config `PAGBANK_TOKEN`/`PAGBANK_API`/`PAGBANK_WEBHOOK_URL` | **stdlib** + requests |
| `ia.py` | Análise por IA: causa raiz, categoria, passos — **seletor de provedor** (Automático → Gemini com fallback Groq `gpt-oss-120b`, forçado, ou **modelo próprio** via dict: Gemini custom ou OpenAI-compatível), expondo quem respondeu (`ULTIMO_PROVEDOR/MODELO`) | google-genai + groq + requests |
| `rag.py` | RAG híbrido no histórico: **retrieval BM25 com IDF** (sinônimos técnicos + ponderação por campo/recência/resolução, offline e determinístico) + **rerank vetorial** com embeddings Gemini (`text-embedding-004`) que cai silencioso para o lexical; geração via `PROMPT_RAG` que responde "já aconteceu? como resolvemos?" — aprende com a resolução registrada | google-genai + `ia.py` |
| `jira_client.py` | Exportação Jira (REST v3): cria issues tipo `Tarefa`, prioridade mapeada | **stdlib apenas** |
| `persistencia.py` | Histórico persistido em `data/historico.jsonl` (JSONL, fuso Brasil) — **facade**: dispatches para o Supabase quando configurado, senão JSONL | **stdlib** (+ nuvem quando `nuvem_supabase` configura) |
| `nuvem_supabase.py` | Backend de persistência na nuvem via Supabase REST (Postgres): insert/select/update + vínculo da issue do Jira + tabelas `planos_usuario` (plano por usuário + `teste_ate`), **`perfis_usuario` (perfil: nome/empresa/fuso/avatar)**, **`solicitacoes_pagamento` (cobranças Pix)** e **`usuarios` (contas: e-mail/último login — painel do dono)** | requests |
| `guardrails.py` | Detecta/mascara credenciais e PII no relato (tokens, chaves, e-mails, senhas numéricas, telefones, CPFs) | **stdlib apenas** |
| `test_triagem.py` | Testes unitários do motor (90) | pytest |
| `casos_qa.py` | **Ground truth (corpus de QA)**: casos canônicos (`CRÍTICA`/`MÉDIA`/`NORMAL`) + casos estritos de severidade — é a referência de **toda** métrica do motor | **stdlib** |
| `test_casos_qa.py` | Testes do ground truth (36): o corpus é canônico — editar um caso quebra o teste de propósito | pytest |
| `avaliacao.py` | **Rótulo humano de severidade**: concilia o motor com a avaliação do dono (Supabase, mockado/hermético) | **stdlib** |
| `test_avaliacao.py` | Testes do rótulo humano (30): herméticos, mockam o REST do Supabase e nunca tocam a rede | pytest |
| `test_colar_falha.py` | Testes do Colar Falha (13): erro/local do traceback Python e Java, categorias, módulo, versão (ignora datas), severidade prévia, relato montado e robustez (nunca levanta) | pytest |
| `test_adaptadores.py` | Testes dos adaptadores Playwright/Postman (16): detecção de formato, extração de teste/asserção/Expected/Received/local, método+URL e **esperado × recebido** do Postman, erro do corpo JSON, fallback para o parser genérico, relato com "Ferramenta de origem"/"Requisição" e robustez | pytest |
| `test_webhook.py` | Testes do webhook de CI + pagamento (29): payloads Playwright/Postman/livre, payload inválido, teto de 200 KB, token (ausente/ok/errado, comparação em tempo constante e `WEBHOOK_REQUIRE_TOKEN` sem segredo), IA/persistência por env e transporte HTTP real (servidor na porta 0): `/health`, `POST /webhook/falha` **e `POST /webhook/pagamento`**, 401/404/400 | pytest |
| `test_jira_client.py` | Testes do cliente Jira (18): payload, erro amigável e **config por-sessão** (nada de global; `{}` limpa e ignora env) | pytest |
| `test_persistencia.py` | Testes da persistência (15): fuso, append, filtro por data, vínculo Jira, tenant por usuário e **migração dos registros legados "global" → uid** | pytest |
| `test_guardrails.py` | Testes dos guardrails (18): detecção/máscara de PII e falso-positivo | pytest |
| `dashboard.py` | Dashboard de QA completo: KPIs + saúde da suíte (0–10), gauge de críticas, filtro por funcionalidade, top causas raiz (IA), score médio/dia, taxa + lista de divergências IA vs. léxico, provedor real na tabela (leitura do JSONL/cloud) | streamlit |
| `test_rag.py` | Testes do RAG (23): tokenização, Jaccard, BM25, sinônimos, recência/resolução, rerank vetorial híbrido com vetores mockados, contexto e orquestração sem chave | pytest |
| `test_dashboard.py` | Testes do dashboard (17): tabela recente (com/sem Jira), funcionalidades, falso-positivo, ordenação, provedor na coluna IA, taxa de divergência, top causas e saúde da suíte | pytest |
| `test_nuvem_supabase.py` | Testes do backend em nuvem (38): config, conversão linha↔doc, HTTP mockado, dispatch do facade e failover | pytest |
| `test_pix.py` | Testes do Pix (10): payload EMV, CRC-CCITT (`29B1`), precedência PIX_COPIA/link, chave e `chave_copia()` sem `+55` | pytest |
| `test_ia.py` | Testes da IA (38): dispatch de provedor (auto/Gemini/Groq/modelo próprio OpenAI-compatível e Gemini custom, com retry sem JSON mode), JSON esperado, fallback, mensagens de erro, `disponivel()` com modelo próprio, embeddings Gemini (normalização e fallback) e orquestração RAG | pytest |
| `auth_supabase.py` | **Autenticação (Supabase Auth/GoTrue via REST, stdlib)**: cadastro com confirmação de e-mail, login e logout — reusa `SUPABASE_URL`/`SUPABASE_ANON_KEY`; sessão em `st.session_state` com **armário por-contexto (ContextVar)** fora do Streamlit (sem global compartilhado) | **stdlib** (+ requests) |
| `test_auth_supabase.py` | Testes de auth (46): parser de erros, cadastro/login/logout, isolação por sessão, recuperação via link (`type=recovery`), **troca de senha via `PUT /user`** (GoTrue), link de uso único reutilizado (silencioso) e mensagens distintas (senha igual/fraca/requisitos); gate de sessão por runtime Streamlit | pytest |
| `notificacoes.py` | **Alertas CRÍTICA/ALTA** (e-mail SMTP + Discord): override por usuário/sessão (**ContextVar** quando fora do Streamlit, sem dict global), testadores à prova de exceção, status real do envio e **`notificar_evento`** para avisos genéricos (pagamento/estorno) com template limpo, sem formato de triagem; URL Discord passa por guarda anti-SSRF (`_webhook_seguro`) | **stdlib** |
| `test_notificacoes.py` | Testes de notificações (45): envio SMTP/Discord (mockado), override por sessão (sem dict global, ContextVar), erros amigáveis, **avisos genéricos de evento** (neutros, sem "Relato/Motor") e **isolamento de overrides entre contextos** (threads) | pytest |
| `plano.py` | **Planos Basic/Premium POR USUÁRIO**: plano salvo no banco (`planos_usuario`) e `tenant_id` = UID da conta logada (fallback: `PLANO`/`TENANT_ID` env). **Usuário logado com nuvem ativa SEMPRE vem do banco: sem linha = `free`** (novo usuário) — env legado só vale sem login/nuvem off | **stdlib** |
| `perfil.py` | **Perfil do usuário (Passo 5 SaaS)**: nome de exibição, empresa, fuso horário e avatar (base64 compacto) — nuvem (`perfis_usuario`) com fallback JSONL (`data/perfis.jsonl`); **nuvem ganha do local**, fuso inválido cai em América/São_Paulo e `nome_exibicao` (nome → empresa → parte do e-mail) | **stdlib** |
| `pixbilling.py` | **Cobrança própria ("nosso Stripe") — Passo 4 SaaS**: gera cobrança `aguardando` (QR + copia-e-cola via `pix.py`), confirmação manual ativa Premium, cancelamento, estorno (volta a Basic) e preço por env `PLANO_PRECO` (R$ 19,99/mês) — nuvem (`solicitacoes_pagamento`) com fallback JSONL. Payload da assinatura prioriza `PIX_COPIA_PLANO` → `PIX_COPIA` → padrão | **stdlib** + requests |
| `github_client.py` | **Issues no repositório do próprio usuário/empresa**: cada conta configura token (Issues: write) + `dono/repo` na sessão (⚙️ Configurações) e o app cria via `POST api.github.com/repos/{dono}/{repo}/issues` — sem labels (evita 422) e com mensagens amigáveis (404/401/403); nada de token em disco/banco | **stdlib** |
| `admin.py` | **Dono do app**: `email_logado()` (conta logada via `auth_supabase`) e `eh_dono()` — dono = e-mail igual ao env `ADMIN_EMAIL` | **stdlib** |
| `secoes/painel_dono.py` | **🛠️ Painel do Dono (Passo 6 SaaS)**: restrito a `ADMIN_EMAIL`, com métricas (contas/Basic/Premium/em teste), lista de contas (e-mail, perfil, plano, último login) e ações diretas — **Ativar Premium**, **Dar teste 7 dias** e **Voltar a Basic** | streamlit |
| `secoes/meu_plano.py` | **Página Meu Plano (SaaS)**: mostra o plano da conta logada, **checkout Premium via Pix** ("nosso Stripe": QR + copia-e-cola + "Já paguei"), **painel do responsável** (confirma/cancela pagamentos e processa estornos), suporte por WhatsApp, migração dos registros legados "global" → seu tenant e **checkout visível sempre que há cobrança aberta** (mesmo se o plano atual não for free) | streamlit |
| `test_plano.py` | Testes do plano (48): gating free×pago, filtro por `tenant_id`, plano por usuário (banco ganha do env), **novo usuário com nuvem ativa = Basic mesmo com env `PLANO=pago`**, fallbacks offline e upsert do plano | pytest |
| `test_pixbilling.py` | Testes da cobrança Pix (21): preço configurável, geração, confirmação (ativa Premium), cancelamento, estorno (volta a Basic), **payload da assinatura priorizando `PIX_COPIA_PLANO`** e integração com o webhook de pagamento | pytest |
| `test_painel_dono.py` | Testes do Trial/painel do dono (43): Teste Premium com validade (ativo/expirado/offline), `definir_trial`/`definir_plano_manual`, limpeza do `teste_ate` via PATCH, upsert de `usuarios` e `eh_dono()` | pytest |
| `test_perfil.py` | Testes do perfil (16): fallback JSONL, isolação por uid, **nuvem ganha do local**, `nome_exibicao`, fuso inválido → padrão, avatar e iniciais de bolinha | pytest |
| `test_github_client.py` | Testes do cliente GitHub (18): normalização de `dono/repo` (URL/.git), detecção de config por sessão, payload sem labels e erro amigável (404/401/403) — com mock de rede | pytest |
| `sessao_persist.py` | **Persistência de sessão no F5**: enfileira salvar/limpar e grava via ponte persistente (cookie + iframe `localStorage` → confirm) | **stdlib** |
| `test_sessao_persist.py` | Testes da ponte de escrita e do failover da sessão (8) | pytest |
| `test_ferramenta.py` | Testes da página ferramenta (12): UI/triagem | pytest |
| `ui_comum.py` | **Componentes comuns de UI**: sidebar (conta logada, tema), menu topo, rodapé com Termos/Privacidade, versão central (`VERSAO`, hoje v2.16.21) e helpers de configuração | streamlit |
| `roteador.py` | **Roteamento das páginas**: `PAGINAS` (Início, Triagem, Meu Plano, Dashboard, Integrações, Painel do Dono) com visibilidade por login/dono | streamlit |
| `test_pagbank.py` | Testes do PagBank (23): token/base/validade, payload do pedido (QR dinâmico, CPF, `notification_urls`, expiração), erros amigáveis e `webhook_url()` | pytest |
| `test_ui_comum.py` | Testes do `ui_comum` (12): versão e helpers de configuração | pytest |
| `telemetria.py` | **Telemetria de produto (PostHog)**: no-op total sem `POSTHOG_API_KEY` (ou falha), **sem PII/conteúdo do relato** no evento | **stdlib** |
| `test_telemetria.py` | Testes da telemetria (7): no-op sem chave, evento/`distinct_id`/propriedades com SDK fake (nunca rede) | pytest |
| `test_landing.py` | Testes da landing/Pages (26): HTML acessível, `canonical`/`og:url` no **domínio próprio `https://ai-bug-triage.com.br/`**, `sitemap.xml`/`robots.txt` com Sitemap, `CNAME` e badge `pytest-badge.json` | pytest |
| `test_legal.py` | Testes das páginas legais (5): Termos/Privacidade com WhatsApp de contato | pytest |
| `.streamlit/config.toml` | Tema e configurações visuais | streamlit |

## 3. Decisões de design

- **Motor local determinístico** (RF-10/RNF-01): garante funcionamento sem internet e resultado reprodutível, servindo de **base de confiança** mesmo se a IA falhar.
- **Fallback automático** (RNF-04): se a API de IA falhar ou não houver chave, a triagem segue com o motor local sem quebrar a experiência.
- **Reconciliação pelo maior vence** (RF-06): nenhum alerta grave é descartado pela concordância com o motor local; divergência é **explicitada** para revisão humana.
- **Transparência** (RNF-07): o relatório informa **qual motor** produziu a análise, permitindo auditoria.

## 4. Fluxo de processamento

0. **Roteamento multi-página** (`st.navigation`): `Início` é público; `Triagem`, `Meu Plano` e `Dashboard` fazem `auth_supabase.requer_login()` quando o Supabase está configurado. O **F5 mantém a sessão** via `sessao_persist.py` (cookie + ponte de escrita persistente); sem confirmação, o login reaparece com mensagem honesta. **Cobrança Pix ("nosso Stripe")**: o usuário assina o Premium → nasce uma `solicitacao_pagamento` `aguardando` com QR + copia-e-cola; paga no banco e clica **Já paguei**; o **responsável** (e-mail `ADMIN_EMAIL`) confirma no painel do Meu Plano → plano vira `pago`; estorno: o usuário solicita, o responsável devolve via Pix e marca estornado (volta a Basic).
1. Usuário informa a descrição do bug.
2. O app chama `guardrails.py` → se houver credencial/PII (token, chave, e-mail, senha numérica, telefone, CPF), o relato é **mascarado** e o usuário é avisado — nada sensível segue para os próximos passos.
3. `home.py` chama `triagem.py` → score local (léxico + negação) e sentimento.
4. Se houver chave `GEMINI_API_KEY`, `ia.py` enriquece com causa raiz/categoria; se falhar, **fallback** para o local. Se houver histórico persistido, **`rag.py`** recupera os top-k registros similares (BM25 híbrido + vetores) e `ia.py` responde também se o caso **já aconteceu** e **como foi resolvido**.
5. O **reconciliador** combina os resultados (maior vence) e marca divergência quando discordam.
6. Gera o relatório com severidade, fatores e **Gherkin**.
7. Usuário pode **exportar** (.md), abrir **Issue** no GitHub ou enviar ao **Jira**; histórico fica na tabela da sessão.
8. Cada triagem é **persistida** como snapshot fiel — **facade `persistencia.py`**: com
   `SUPABASE_URL` + `SUPABASE_ANON_KEY` configurados, grava no **Supabase** (`nuvem_supabase.py`);
   senão, no `data/historico.jsonl` (JSONL local, fuso `America/Sao_Paulo`). Se a nuvem falhar,
   **failover** automático para o arquivo local. A issue do Jira criada depois é vinculada ao
   último registro no backend ativo.

## 5. Infra de desenvolvimento com agentes (MCPs e skills)

O time (e o agente de código) desenvolvem com **MCPs de apoio** — nenhuma escrita de
produção acontece por eles: o MCP do Supabase é **read-only** e o do Render só faz GET.
O registro fica na config global do opencode (`~/.config/opencode/`); as pontes em si
são arquivos **do repo**.

| Ferramenta | Tipo | Papel | Segredo |
|---|---|---|---|
| `mcp_supabase.py` | MCP local (FastMCP, stdlib) | Leitura do Postgres do produto (tabelas, colunas, SELECT) pela role `mcp_readonly` — **nunca escreve** | role read-only no Supabase |
| semgrep MCP | MCP local | Varredura por regras (`p/security-audit`, `p/owasp-top-ten`) nos arquivos | `SEMGREP_SEND_METRICS=off` |
| Playwright MCP | MCP local | E2E e inspeção de UI | — |
| `mcp_render.py` | MCP local (ponte stdio, stdlib) | Serviço, deploys, logs, health e **só os nomes** das env vars do webhook, pela API REST do Render — **somente GET**, nunca cria, altera ou apaga. O valor de uma env nunca sai da ponte: ela devolve a chave | `RENDER_API_KEY` via `{env:...}`, lido do ambiente ou do `.env` (gitignored) |

Regras de higiene dessa camada:

- **Segredo por env, nunca inline**: a config referencia `{env:RENDER_API_KEY}` etc.; o valor vive no ambiente (`.zshrc`/secret do Render), não em arquivo versionado.
- **Dado de produção = leitura por MCP**: qualquer escrita passa pelo app (ou migration versionada), auditável no CHANGELOG.
- **No repo** ficam só skills e comandos próprios: `agent/skills/` (supabase, triagem, release, etc.) e `.opencode/command/` (`deploy.md`, `health.md`) — o ritual de release/CI do time.
- **Telegram de rede**: MCPs locais abrem rede só para os destinos que o agente escolhe (Render/Supabase oficial); o semgrep roda local com métricas desligadas.
