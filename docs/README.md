# 📚 Documentação de Engenharia de Software

Processo de engenharia e qualidade do **AI Bug Triage System**, documentado de forma escavável para mostrar o **raciocínio por trás do produto** (não só o código).

## Índice

| Doc | Conteúdo |
|---|---|
| [01 — Requisitos](01-requisitos.md) | Requisitos funcionais e não-funcionais, prioridades e decisões de contorno |
| [02 — Casos de Teste](02-casos-de-teste.md) | Matriz de casos em Gherkin + os testes automatizados (113 no total, incluindo Dashboard de QA completo, RAG, nuvem/Supabase, Pix e IA com fallback Groq) |
| [03 — Arquitetura e Fluxo](03-arquitetura.md) | Componentes, decisões de design e fluxo de processamento |
| [04 — Estratégia de Qualidade](04-estrategia-de-qualidade.md) | Pilares de QA, redução de risco e ciclo de melhoria |
| [05 — Persistência em Nuvem](05-persistencia-nuvem.md) | Supabase como backend opcional (secrets → `.env` → JSONL), passo a passo de ativação e limitações |
