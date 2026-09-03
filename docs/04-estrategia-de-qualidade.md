# 04 — Estratégia de Qualidade

Processo de qualidade aplicado ao **AI Bug Triage System** — como o projeto é pensado, testado e mantido sob a ótica de **QA**.

## 1. O papel do QA aqui

O objetivo deste documento é mostrar que o app não foi apenas "escrito e publicado": ele foi **projetado com foco em qualidade**, pensando em **falso-positivo**, **determinismo**, **transparência** e **automação de validação** — os pilares do trabalho de um QA.

## 2. Pilares de qualidade

| Pilar | Implementação |
|---|---|
| **Determinismo** | Motor local 100% offline, mesma entrada → mesma saída (RNF-01) |
| **Controle de falso-positivo** | Palavras de vocabulário de teste (`erro`, `bug`...) não disparam severidade (RF-05) |
| **Cobertura de testes** | 12 testes `pytest` cobrindo severidade, negação, sentimento e determinismo |
| **Automação (CI)** | GitHub Actions roda os testes a cada push → badge de qualidade |
| **Transparência** | Relatório informa o motor usado (auditoria) |
| **Robustez** | Fallback automático para o motor local quando a IA falha |

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

- Integração direta com a **API do Jira** (exportação nativa).
- **Persistência** do histórico em banco de dados (hoje em sessão).
- Ampliar a **cobertura de testes** (novos cenários de negação e edge cases).
