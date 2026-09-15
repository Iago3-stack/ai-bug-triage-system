# 04 — Estratégia de Qualidade

Processo de qualidade aplicado ao **AI Bug Triage System** — como o projeto é pensado, testado e mantido sob a ótica de **QA**.

## 1. O papel do QA aqui

O objetivo deste documento é mostrar que o app não foi apenas "escrito e publicado": ele foi **projetado com foco em qualidade**, pensando em **falso-positivo**, **determinismo**, **transparência** e **automação de validação** — os pilares do trabalho de um QA.

## 2. Pilares de qualidade

| Pilar | Implementação |
|---|---|
| **Determinismo** | Motor local 100% offline, mesma entrada → mesma saída (RNF-01) |
| **Controle de falso-positivo** | Palavras de vocabulário de teste (`erro`, `bug`...) não disparam severidade (RF-05) |
| **Cobertura de testes** | **328 testes** `pytest` — motor (18), Jira (15), persistência (14), guardrails (18), dashboard (17), RAG (13), nuvem/Supabase (14), Pix (10), IA (32), Auth/Supabase (29), notificações (32), plano (25), cobrança Pix (16), perfil (16), **GitHub (18)**, **painel do dono (30: Teste Premium com validade via `teste_ate`, `definir_trial`/`definir_plano_manual`, limpeza do teste ao pagar via PATCH, upsert da tabela `usuarios` e `eh_dono`)**, persistência de sessão (8) e ferramenta (3) — cobrindo severidade, negação, sentimento, determinismo, exportação, fuso, PII, agregações de QA, recuperação do histórico, persistência em nuvem, registro de resolução (aprendizado do RAG), geração de QR Pix (EMV/CRC), fallback Gemini → Groq (open-weight), seletor de provedor de IA (automático/forçado), **modelo próprio** (OpenAI-compatível com retry sem JSON mode + Gemini custom com chave específica), **auth/Supabase** (cadastro/login/logout, isolação por sessão), **notificações** (e-mail SMTP + Discord com testadores à prova de exceção, **avisos genéricos de evento sem template de triagem**), **planos** (Basic/Premium com gating de recursos, **plano por usuário no banco**, **novo usuário com nuvem ativa sempre começa em Basic**, migração de registros legados "global" → uid e **Teste Premium que expira sozinho**), **cobrança Pix** ("nosso Stripe": geração de cobrança, confirmação que ativa Premium, cancelamento, estorno que volta a Basic, preço configurável e **payload da assinatura priorizando PIX_COPIA_PLANO**), **perfil do usuário** (nome/empresa/fuso/avatar com fallback JSONL, **nuvem ganha do local**, fuso inválido → padrão e iniciais para a bolinha), **GitHub por usuário** (criação de issues no repositório do próprio usuário via `api.github.com`, token/repo por sessão, normalização de URL e mensagens de erro amigáveis), **painel do dono** (Teste Premium com validade, registro automático de contas e ações de admin) e **persistência de sessão** (ponte cookie → iframe) |
| **Automação (CI)** | GitHub Actions roda os testes a cada push → badge de qualidade |
| **Transparência** | Relatório informa o motor usado (auditoria) |
| **Robustez** | Fallback automático para o motor local quando a IA falha |
| **Privacidade (Guardrails)** | Credenciais/PII (tokens, chaves, e-mails, senhas numéricas, telefones e CPFs) são detectadas e **mascaradas** antes do envio a IA/Jira/GitHub/histórico |

## 3. Como o processo QA reduz risco

- **Sem depender de rede**: o teste manual e a triagem inicial funcionam mesmo **offline** — importante em datacenter/ambientes restritos (motivo pelo qual o TextBlob/Google Translate foi removido).
- **Negações em PT-BR**: padrões como "não funciona", "não consigo" são detectados, evitando que o app leia um problema como elogio.
- **Decisão editorial do léxico**: "funciona" não entra no léxico positivo porque aparece dentro de negações — uma regra de QA que previne erro de classificação.

## 4. Ciclo de melhoria contínua

1. **Relatar** → bugs e sugestões entram via [issues](CONTRIBUTING.md) com templates.
2. **Testar** → novos cenários viram casos em `test_triagem.py` e na doc `02-casos-de-teste.md`.
3. **Validar** → CI roda os testes automaticamente.
4. **Versionar** → mudanças registradas no [CHANGELOG](../CHANGELOG.md).

## 5. Próximos passos (Roadmap de qualidade)

- ~~Integração direta com a **API do Jira**~~ ✅ — exportação nativa via `jira_client.py` (REST v3, tipo `Tarefa`).
- ~~**Persistência** do histórico~~ ✅ — snapshot fiel em `data/historico.jsonl` (JSONL local, gitignored): com IA grava o relatório completo; sem IA, só o léxico. Seletor de data + download em Markdown. *Backend Supabase disponível com failover automático.*
- ~~**Guardrails de PII/credenciais**~~ ✅ — `guardrails.py` mascara tokens, chaves, e-mails, senhas numéricas, telefones e CPFs antes do envio a IA/Jira/GitHub/histórico.
- ~~**Auth multi-tenant (Supabase)**~~ ✅ — cadastro com confirmação de e-mail, login e isolamento por `tenant_id`; sessão persiste no F5 (cookie + ponte).
- ~~**Alerta CRÍTICA/ALTA**~~ ✅ — notificação por e-mail (SMTP/Gmail) e Discord, com testadores à prova de exceção e status real do envio no app.
- ~~**Planos Basic/Premium**~~ ✅ — `PLANO=free|pago` com gating de recursos e `tenant_id` para isolamento por conta.
- ~~**Cobrança próprio via Pix ("nosso Stripe")**~~ ✅ — Premium a **R$ 19,99/mês** com checkout Pix (QR + copia-e-cola), confirmação manual do responsável, estorno controlado e suporte por WhatsApp — sem gateway, sem taxa.
- Ampliar ainda mais a **cobertura de testes** (edge cases, integrações).
- ~~**Dashboard de QA**~~ ✅ — saúde da suíte (0–10), gauge, filtro por funcionalidade, evolução do score/dia, top causas raiz (IA), divergências IA vs. léxico e provedor real — 100% local.
- ~~**RAG no histórico**~~ ✅ — retrieval Jaccard + geração; resposta "já aconteceu? como resolvemos?" com resolução registrada pelo usuário.
