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
| `home.py` | Interface web (Streamlit): cabeçalho, ferramenta, export, histórico e **rodapé de doação Pix via `st.iframe`** (components.html removido após 2026-06) | streamlit |
| `pix.py` | Gerador de pagamento Pix: payload EMV **COPIA-e-Coloca** com CRC-CCITT, QR Code PNG (base64), **link de pagamento** com valor fixo e chave com/sem `+55` (`chave`/`chave_copia`) | **stdlib apenas** + `qrcode` |
| `triagem.py` | Motor NLP **offline determinístico**: léxico PT + negações | **stdlib apenas** |
| `colar_falha.py` | **Pilar 1 de automação**: transforma a falha bruta colada (stack trace/log/mensagem) em **relato estruturado** (título, categoria na taxonomia da IA, módulo, versão, severidade prévia via `triagem`, erro principal, local do frame e passos) — 100% local; `estruturar_automatico` escolhe o extrator certo (adaptador → genérico) | **stdlib apenas** + `triagem` |
| `adaptadores.py` | **Pilar 2 de automação** — adapta a saída do **Playwright** (nome/erro de asserção do teste, Expected/Received, arquivo:linha; texto ou JSON do relator) e do **Postman/newman** (método+URL, **HTTP esperado × recebido**, asserção, erro do corpo JSON) para o relato estruturado; `None` → o parser genérico assume | **stdlib apenas** + `colar_falha` |
| `webhook.py` | **Pilar 3 de automação** — micro-servidor HTTP `POST /webhook/falha`: valida `evidencia` (max 200 KB), extrai via `colar_falha.estruturar_automatico`, monta o relato, com IA (`ia:true`/`WEBHOOK_IA`) e persistência (`WEBHOOK_PERSISTE`) opcionais; token `WEBHOOK_TOKEN`, `/health`, nunca levanta | **stdlib apenas** + `colar_falha` |
| `ia.py` | Análise por IA: causa raiz, categoria, passos — **seletor de provedor** (Automático → Gemini com fallback Groq `gpt-oss-120b`, forçado, ou **modelo próprio** via dict: Gemini custom ou OpenAI-compatível), expondo quem respondeu (`ULTIMO_PROVEDOR/MODELO`) | google-genai + groq + requests |
| `rag.py` | RAG híbrido no histórico: **retrieval BM25 com IDF** (sinônimos técnicos + ponderação por campo/recência/resolução, offline e determinístico) + **rerank vetorial** com embeddings Gemini (`text-embedding-004`) que cai silencioso para o lexical; geração via `PROMPT_RAG` que responde "já aconteceu? como resolvemos?" — aprende com a resolução registrada | google-genai + `ia.py` |
| `jira_client.py` | Exportação Jira (REST v3): cria issues tipo `Tarefa`, prioridade mapeada | **stdlib apenas** |
| `persistencia.py` | Histórico persistido em `data/historico.jsonl` (JSONL, fuso Brasil) — **facade**: dispatches para o Supabase quando configurado, senão JSONL | **stdlib** (+ nuvem quando `nuvem_supabase` configura) |
| `nuvem_supabase.py` | Backend de persistência na nuvem via Supabase REST (Postgres): insert/select/update + vínculo da issue do Jira + tabelas `planos_usuario` (plano por usuário + `teste_ate`), **`perfis_usuario` (perfil: nome/empresa/fuso/avatar)**, **`solicitacoes_pagamento` (cobranças Pix)** e **`usuarios` (contas: e-mail/último login — painel do dono)** | requests |
| `guardrails.py` | Detecta/mascara credenciais e PII no relato (tokens, chaves, e-mails, senhas numéricas, telefones, CPFs) | **stdlib apenas** |
| `test_triagem.py` | Testes unitários do motor (18) | pytest |
| `test_colar_falha.py` | Testes do Colar Falha (13): erro/local do traceback Python e Java, categorias, módulo, versão (ignora datas), severidade prévia, relato montado e robustez (nunca levanta) | pytest |
| `test_adaptadores.py` | Testes dos adaptadores Playwright/Postman (16): detecção de formato, extração de teste/asserção/Expected/Received/local, método+URL e **esperado × recebido** do Postman, erro do corpo JSON, fallback para o parser genérico, relato com "Ferramenta de origem"/"Requisição" e robustez | pytest |
| `test_webhook.py` | Testes do webhook de CI (21): payloads Playwright/Postman/livre, payload inválido, teto de 200 KB, token (ausente/ok/errado), IA/persistência por env e transporte HTTP real (servidor na porta 0): `/health`, POST `/webhook/falha`, 401/404/400 | pytest |
| `test_jira_client.py` | Testes do cliente Jira (15) | pytest |
| `test_persistencia.py` | Testes da persistência (14): fuso, append, filtro por data, vínculo Jira, tenant por usuário e **migração dos registros legados "global" → uid** | pytest |
| `test_guardrails.py` | Testes dos guardrails (18): detecção/máscara de PII e falso-positivo | pytest |
| `dashboard.py` | Dashboard de QA completo: KPIs + saúde da suíte (0–10), gauge de críticas, filtro por funcionalidade, top causas raiz (IA), score médio/dia, taxa + lista de divergências IA vs. léxico, provedor real na tabela (leitura do JSONL/cloud) | streamlit |
| `test_rag.py` | Testes do RAG (23): tokenização, Jaccard, BM25, sinônimos, recência/resolução, rerank vetorial híbrido com vetores mockados, contexto e orquestração sem chave | pytest |
| `test_dashboard.py` | Testes do dashboard (17): tabela recente (com/sem Jira), funcionalidades, falso-positivo, ordenação, provedor na coluna IA, taxa de divergência, top causas e saúde da suíte | pytest |
| `test_nuvem_supabase.py` | Testes do backend em nuvem (14): config, conversão linha↔doc, HTTP mockado, dispatch do facade e failover | pytest |
| `test_pix.py` | Testes do Pix (10): payload EMV, CRC-CCITT (`29B1`), precedência PIX_COPIA/link, chave e `chave_copia()` sem `+55` | pytest |
| `test_ia.py` | Testes da IA (36): dispatch de provedor (auto/Gemini/Groq/modelo próprio OpenAI-compatível e Gemini custom, com retry sem JSON mode), JSON esperado, fallback, mensagens de erro, `disponivel()` com modelo próprio, embeddings Gemini (normalização e fallback) e orquestração RAG | pytest |
| `auth_supabase.py` | **Autenticação (Supabase Auth/GoTrue via REST, stdlib)**: cadastro com confirmação de e-mail, login e logout — reusa `SUPABASE_URL`/`SUPABASE_ANON_KEY` | **stdlib** (+ requests) |
| `test_auth_supabase.py` | Testes de auth (29): parser de erros, cadastro/login/logout e isolação por sessão | pytest |
| `notificacoes.py` | **Alertas CRÍTICA/ALTA** (e-mail SMTP + Discord): override por usuário/sessão, testadores à prova de exceção, status real do envio e **`notificar_evento`** para avisos genéricos (pagamento/estorno) com template limpo, sem formato de triagem | **stdlib** |
| `test_notificacoes.py` | Testes de notificações (32): envio SMTP/Discord (mockado), override por sessão, erros amigáveis e **avisos genéricos de evento** (neutros, sem "Relato/Motor") | pytest |
| `plano.py` | **Planos Basic/Premium POR USUÁRIO**: plano salvo no banco (`planos_usuario`) e `tenant_id` = UID da conta logada (fallback: `PLANO`/`TENANT_ID` env). **Usuário logado com nuvem ativa SEMPRE vem do banco: sem linha = `free`** (novo usuário) — env legado só vale sem login/nuvem off | **stdlib** |
| `perfil.py` | **Perfil do usuário (Passo 5 SaaS)**: nome de exibição, empresa, fuso horário e avatar (base64 compacto) — nuvem (`perfis_usuario`) com fallback JSONL (`data/perfis.jsonl`); **nuvem ganha do local**, fuso inválido cai em América/São_Paulo e `nome_exibicao` (nome → empresa → parte do e-mail) | **stdlib** |
| `pixbilling.py` | **Cobrança própria ("nosso Stripe") — Passo 4 SaaS**: gera cobrança `aguardando` (QR + copia-e-cola via `pix.py`), confirmação manual ativa Premium, cancelamento, estorno (volta a Basic) e preço por env `PLANO_PRECO` (R$ 19,99/mês) — nuvem (`solicitacoes_pagamento`) com fallback JSONL. Payload da assinatura prioriza `PIX_COPIA_PLANO` → `PIX_COPIA` → padrão | **stdlib** + requests |
| `github_client.py` | **Issues no repositório do próprio usuário/empresa**: cada conta configura token (Issues: write) + `dono/repo` na sessão (⚙️ Configurações) e o app cria via `POST api.github.com/repos/{dono}/{repo}/issues` — sem labels (evita 422) e com mensagens amigáveis (404/401/403); nada de token em disco/banco | **stdlib** |
| `admin.py` | **Dono do app**: `email_logado()` (conta logada via `auth_supabase`) e `eh_dono()` — dono = e-mail igual ao env `ADMIN_EMAIL` | **stdlib** |
| `secoes/painel_dono.py` | **🛠️ Painel do Dono (Passo 6 SaaS)**: restrito a `ADMIN_EMAIL`, com métricas (contas/Basic/Premium/em teste), lista de contas (e-mail, perfil, plano, último login) e ações diretas — **Ativar Premium**, **Dar teste 7 dias** e **Voltar a Basic** | streamlit |
| `secoes/meu_plano.py` | **Página Meu Plano (SaaS)**: mostra o plano da conta logada, **checkout Premium via Pix** ("nosso Stripe": QR + copia-e-cola + "Já paguei"), **painel do responsável** (confirma/cancela pagamentos e processa estornos), suporte por WhatsApp, migração dos registros legados "global" → seu tenant e **checkout visível sempre que há cobrança aberta** (mesmo se o plano atual não for free) | streamlit |
| `test_plano.py` | Testes do plano (25): gating free×pago, filtro por `tenant_id`, plano por usuário (banco ganha do env), **novo usuário com nuvem ativa = Basic mesmo com env `PLANO=pago`**, fallbacks offline e upsert do plano | pytest |
| `test_pixbilling.py` | Testes da cobrança Pix (16): preço configurável, geração, confirmação (ativa Premium), cancelamento, estorno (volta a Basic) e **payload da assinatura priorizando `PIX_COPIA_PLANO`** | pytest |
| `test_painel_dono.py` | Testes do Trial/painel do dono (34): Teste Premium com validade (ativo/expirado/offline), `definir_trial`/`definir_plano_manual`, limpeza do `teste_ate` via PATCH, upsert de `usuarios` e `eh_dono()` | pytest |
| `test_perfil.py` | Testes do perfil (16): fallback JSONL, isolação por uid, **nuvem ganha do local**, `nome_exibicao`, fuso inválido → padrão, avatar e iniciais de bolinha | pytest |
| `test_github_client.py` | Testes do cliente GitHub (18): normalização de `dono/repo` (URL/.git), detecção de config por sessão, payload sem labels e erro amigável (404/401/403) — com mock de rede | pytest |
| `sessao_persist.py` | **Persistência de sessão no F5**: enfileira salvar/limpar e grava via ponte persistente (cookie + iframe `localStorage` → confirm) | **stdlib** |
| `test_sessao_persist.py` | Testes da ponte de escrita e do failover da sessão (8) | pytest |
| `test_ferramenta.py` | Testes da página ferramenta (3): UI/triagem | pytest |
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
