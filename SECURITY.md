# Política de Segurança

## Versões suportadas

| Versão | Suportada |
|---|---|
| 2.3.x (atual) | ✅ |
| 2.1.x (legado) | ❌ |
| 1.x (legado) | ❌ |
| 0.x (legado) | ❌ |

## Reportando uma vulnerabilidade

Se encontrar uma **vulnerabilidade de segurança**, por favor **não abra uma issue pública**. Reporte em privado:

- Envie e-mail ao mantenedor relatando o problema, **ou**
- Use a opção de *Security advisory* do repositório (na aba **Security**).

Inclua, se possível:
- Descrição do problema e impacto
- Passos para reproduzir
- Versão afetada e versão corrigida (se souber)

Responderemos o mais rápido possível. **Nunca** divulgue publicamente antes de o problema ser mitigado.

## Considerações de segurança do projeto

- O motor determinístico (`triagem.py`) roda **100% offline** sem expor dados a serviços externos.
- Quando a análise por IA (Gemini) está ativa, o texto do bug é enviado à API — **não use a triagem com dados sensíveis/confidenciais** sem anotar esse comportamento. O mesmo vale para o fallback Groq (`GROQ_API_KEY`).
- A chave `GEMINI_API_KEY` (e `GROQ_API_KEY`) **nunca** deve ser commitada: use `.env` (local) ou Secrets (Streamlit Cloud).

## 🔒 LGPD — Tratamento de dados pessoais

O tratamento de dados do projeto segue a **LGPD (Lei Geral de Proteção de Dados — Lei nº 13.709/2018)**:

- **Guardrails de entrada:** credenciais e dados pessoais digitados no relato do bug (e-mail, CPF, telefone, senha, chaves de API/tokens) são **detectados e mascarados automaticamente** (`***`) **antes** de qualquer processamento — nada sensível segue para a IA (Gemini/Groq), Jira, GitHub ou histórico persistido.
- **Minimização:** só o texto **mascarado** viaja para a LLM; o relato original permanece na tela/sessão do usuário e não é usado para identificá-lo nem para criar perfis.
- **Fins determinados:** a ferramenta não vende, compartilha ou usa dados pessoais para marketing; os relatos servem apenas à triagem técnica do próprio projeto.
- **Auditoria e transparência:** cada mascaramento é contabilizado no Dashboard (métrica **"Credenciais/PII mascaradas"** e expander **"Por que mascaramos?"**), e o aviso na tela explica o motivo de cada tipo mascarado.
- **Canais oficiais:** dúvidas, solicitações de titular e denúncias devem ser encaminhadas à **ANPD — Autoridade Nacional de Proteção de Dados**: <https://www.gov.br/anpd/pt-br>.

Agradecemos por ajudar a manter o projeto seguro! 🐞
