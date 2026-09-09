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
| `ia.py` | Análise por IA: causa raiz, categoria, passos — **seletor de provedor** (Automático → Gemini com fallback Groq `gpt-oss-120b`, forçado, ou **modelo próprio** via dict: Gemini custom ou OpenAI-compatível), expondo quem respondeu (`ULTIMO_PROVEDOR/MODELO`) | google-genai + groq + requests |
| `rag.py` | RAG leve no histórico: **retrieval local** (similaridade Jaccard, offline) + geração via `PROMPT_RAG` que responde "já aconteceu? como resolvemos?" — aprende com a resolução registrada | google-genai + `ia.py` |
| `jira_client.py` | Exportação Jira (REST v3): cria issues tipo `Tarefa`, prioridade mapeada | **stdlib apenas** |
| `persistencia.py` | Histórico persistido em `data/historico.jsonl` (JSONL, fuso Brasil) — **facade**: dispatches para o Supabase quando configurado, senão JSONL | **stdlib** (+ nuvem quando `nuvem_supabase` configura) |
| `nuvem_supabase.py` | Backend de persistência na nuvem via Supabase REST (Postgres): insert/select/update + vínculo da issue do Jira | requests |
| `guardrails.py` | Detecta/mascara credenciais e PII no relato (tokens, chaves, e-mails, senhas numéricas, telefones, CPFs) | **stdlib apenas** |
| `test_triagem.py` | Testes unitários do motor (18) | pytest |
| `test_jira_client.py` | Testes do cliente Jira (15) | pytest |
| `test_persistencia.py` | Testes da persistência (8): fuso, append, filtro por data, vínculo Jira | pytest |
| `test_guardrails.py` | Testes dos guardrails (14): detecção/máscara de PII e falso-positivo | pytest |
| `dashboard.py` | Dashboard de QA completo: KPIs + saúde da suíte (0–10), gauge de críticas, filtro por funcionalidade, top causas raiz (IA), score médio/dia, taxa + lista de divergências IA vs. léxico, provedor real na tabela (leitura do JSONL/cloud) | streamlit |
| `test_rag.py` | Testes do RAG (13): tokenização, Jaccard, recuperação top-k, contexto e orquestração sem chave | pytest |
| `test_dashboard.py` | Testes do dashboard (11): tabela recente (com/sem Jira), funcionalidades, falso-positivo, ordenação, provedor na coluna IA, taxa de divergência, top causas e saúde da suíte | pytest |
| `test_nuvem_supabase.py` | Testes do backend em nuvem (14): config, conversão linha↔doc, HTTP mockado, dispatch do facade e failover | pytest |
| `test_pix.py` | Testes do Pix (10): payload EMV, CRC-CCITT (`29B1`), precedência PIX_COPIA/link, chave e `chave_copia()` sem `+55` | pytest |
| `test_ia.py` | Testes da IA (16): dispatch de provedor (auto/Gemini/Groq/modelo próprio OpenAI-compatível e Gemini custom, com retry sem JSON mode), JSON esperado, fallback, `disponivel()` com modelo próprio e orquestração RAG | pytest |
| `.streamlit/config.toml` | Tema e configurações visuais | streamlit |

## 3. Decisões de design

- **Motor local determinístico** (RF-10/RNF-01): garante funcionamento sem internet e resultado reprodutível, servindo de **base de confiança** mesmo se a IA falhar.
- **Fallback automático** (RNF-04): se a API de IA falhar ou não houver chave, a triagem segue com o motor local sem quebrar a experiência.
- **Reconciliação pelo maior vence** (RF-06): nenhum alerta grave é descartado pela concordância com o motor local; divergência é **explicitada** para revisão humana.
- **Transparência** (RNF-07): o relatório informa **qual motor** produziu a análise, permitindo auditoria.

## 4. Fluxo de processamento

1. Usuário informa a descrição do bug.
2. `home.py` chama `guardrails.py` → se houver credencial/PII (token, chave, e-mail, senha numérica, telefone, CPF), o relato é **mascarado** e o usuário é avisado — nada sensível segue para os próximos passos.
3. `home.py` chama `triagem.py` → score local (léxico + negação) e sentimento.
4. Se houver chave `GEMINI_API_KEY`, `ia.py` enriquece com causa raiz/categoria; se falhar, **fallback** para o local. Se houver histórico persistido, **`rag.py`** recupera os top-k registros similares (Jaccard) e `ia.py` responde também se o caso **já aconteceu** e **como foi resolvido**.
5. O **reconciliador** combina os resultados (maior vence) e marca divergência quando discordam.
6. Gera o relatório com severidade, fatores e **Gherkin**.
7. Usuário pode **exportar** (.md), abrir **Issue** no GitHub ou enviar ao **Jira**; histórico fica na tabela da sessão.
8. Cada triagem é **persistida** como snapshot fiel — **facade `persistencia.py`**: com
   `SUPABASE_URL` + `SUPABASE_ANON_KEY` configurados, grava no **Supabase** (`nuvem_supabase.py`);
   senão, no `data/historico.jsonl` (JSONL local, fuso `America/Sao_Paulo`). Se a nuvem falhar,
   **failover** automático para o arquivo local. A issue do Jira criada depois é vinculada ao
   último registro no backend ativo.
