# Changelog

Todas as mudanças notáveis do **AI Bug Triage System** são registradas neste arquivo.

O formato é baseado no [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e segue o [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Não lançado]

### Adicionado
- Testes unitários do motor de triagem (`pytest`) — 12 testes cobrindo severidade, negação, sentimento, determinismo e ausência de falso-positivo.
- **CI (GitHub Actions)** — robozinho que roda `pytest` a cada push/PR na branch `main`, com badge "build passing" no README.
- **Léxico de lentidão por raiz (regex)** — `\blent(?!es?\b)\w*` cobre todas as flexões (`lento`, `lenta`, `lentíssimo`, `lentamente`, `lentidão`...) sem enumerá-las; o lookahead exclui o falso positivo `lente/lentes`. Padrão compilado no módulo + normalização NFC.
- **Checkbox "🔮 Usar IA (Gemini)"** — análise por IA opcional por triagem; desmarcado, só o motor local roda (fallback e reconciliação preservados).
- **Testes ampliados (12 → 18)** — incluem cobertura de `triar()` para o padrão "não funciona", flexões de lentidão, ausência de falso positivo `lente` e não dupla contagem de peso.

## [v1.0.0] - 2026-08-27

### Adicionado
- **Motor NLP offline** (léxico PT + detecção de negação) — 100% determinístico e sem dependência de API para a triagem inicial.
- **Análise de causa raiz via Google Gemini** — JSON estruturado com fallback automático entre modelos.
- **Prioridade reconciliada** entre os dois motores — a regra do "maior vence" evita que alerta grave seja ignorado, sinalizando divergência para revisão humana.
- **Relatório Gherkin** (`Dado/Quando/Então`) pronto para copiar no Jira ou GitHub Issues.
- **Exportação** do relatório (Markdown), abertura de Issue no GitHub e envio ao Jira (configurável).
- **Histórico de sessão** em tabela com opção de limpar.
- **Interface web** com identidade visual própria (Streamlit).
- **Dockerfile** + publicação de imagem no **GHCR** (GitHub Container Registry).

### Publicado
- App no **Streamlit Cloud**: [ai-bug-triage-system](https://ai-bug-triage-system-d6vigycbjt4qxez2wrvsxf.streamlit.app/).

<!--
### Corrigido
Modelos de verbete para mudanças que corrigem um bug.

### Alterado
Modelos de verbete para mudanças que alteram funcionalidades existentes.

### Removido
Modelos de verbete para mudanças que removem funcionalidades existentes.
-->
