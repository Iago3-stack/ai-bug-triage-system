# Política de Segurança

## Versões suportadas

| Versão | Suportada |
|---|---|
| 1.x (atual) | ✅ |
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
- Quando a análise por IA (Gemini) está ativa, o texto do bug é enviado à API — **não use a triagem com dados sensíveis/confidenciais** sem anotar esse comportamento.
- A chave `GEMINI_API_KEY` **nunca** deve ser commitada: use `.env` (local) ou Secrets (Streamlit Cloud).

Agradecemos por ajudar a manter o projeto seguro! 🐞
