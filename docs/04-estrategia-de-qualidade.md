# 04 — Estratégia de Qualidade

Processo de qualidade aplicado ao **AI Bug Triage System** — como o projeto é pensado, testado e mantido sob a ótica de **QA**.

## 1. O papel do QA aqui

O objetivo deste documento é mostrar que o app não foi apenas "escrito e publicado": ele foi **projetado com foco em qualidade**, pensando em **falso-positivo**, **determinismo**, **transparência** e **automação de validação** — os pilares do trabalho de um QA.

## 2. Pilares de qualidade

| Pilar | Implementação |
|---|---|
| **Determinismo** | Motor local 100% offline, mesma entrada → mesma saída (RNF-01) |
| **Controle de falso-positivo** | Palavras de vocabulário de teste (`erro`, `bug`...) não disparam severidade (RF-05) |
| **Cobertura de testes** | 106 testes `pytest` — motor (18), Jira (15), persistência (8), guardrails (14), dashboard (6), RAG (13), nuvem/Supabase (14), Pix (8) e IA (10) — cobrindo severidade, negação, sentimento, determinismo, exportação, fuso, PII, agregações de QA, recuperação do histórico, persistência em nuvem, registro de resolução (aprendizado do RAG), geração de QR Pix (EMV/CRC), fallback Gemini → Groq (open-weight) e seletor de provedor de IA (automático/forçado) |
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
- ~~**Persistência** do histórico~~ ✅ — snapshot fiel em `data/historico.jsonl` (JSONL local, gitignored): com IA grava o relatório completo; sem IA, só o léxico. Seletor de data + download em Markdown. *Futuro:* migrar para banco quando houver necessidade de consultas/agregações ou página por visitante.
- ~~**Guardrails de PII/credenciais**~~ ✅ — `guardrails.py` mascara tokens, chaves, e-mails, senhas numéricas, telefones e CPFs antes do envio a IA/Jira/GitHub/histórico (descoberto em teste real e validado com relato contendo os 4 tipos de dados).
- Ampliar ainda mais a **cobertura de testes** (novos cenários de negação, edge cases e guardrails).
