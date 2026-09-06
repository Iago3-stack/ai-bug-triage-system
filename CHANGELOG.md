# Changelog

Todas as mudanças notáveis do **AI Bug Triage System** são registradas neste arquivo.

O formato é baseado no [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e segue o [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Não lançado]

### Corrigido
- **Credenciais do Jira não eram lidas do `.env`** — `jira_client` agora usa `_env_var()` (variável de ambiente com fallback no `.env`), mesmo padrão do `ia.py`; sem isso o `streamlit run` mostrava o opção "configurar no sidebar" mesmo com `.env` preenchida.
- **Botão "Exportar para Jira" sumia com o relatório** — o resultado da triagem agora fica em `st.session_state["resultado"]` e é renderizado **fora** do `if st.button(...)`; assim o rerun disparado pelo botão não apaga mais a tela e o envio ao Jira é processado corretamente (mesmo padrão que já resolvia o `link_button` do GitHub).
- **HTTP 400 ao exportar para o Jira com dados do sidebar** — a chave do projeto e o tipo de item digitados são normalizados (`strip` + chave em maiúsculas), evitando erro por espaço ou caixa errada (`kan` → `KAN`).

### Adicionado
- **Persistência do histórico (JSONL)** — nova `persistencia.py`: cada triagem vira um snapshot fiel em `data/historico.jsonl` (gitignored). Salva o que **de fato** rodou: com IA → relatório completo (causa raiz, passos, prioridade final, divergência); sem IA → só o léxico. Vincula depois a issue do Jira (ex.: `KAN-8`) e oferece seletor de data + download do relatório em Markdown.
- **Testes (7 novos)** da persistência. Total da suíte: **40 testes**.
- **Testes (4 novos)** para leitura de credenciais do `.env` (`_env_var`) e `configurado()`. Total da suíte: **31 testes**.
- **Exportação real para o Jira via API REST v3** (`jira_client.py`) — cria a issue do tipo **Bug** direto no projeto configurado (ex.: `iagoqa.atlassian.net`), com mapeamento automático da prioridade (NORMAL→Low … CRÍTICA→Highest) e descrição em formato ADF. Usa apenas a biblioteca padrão (`urllib`), sem novas dependências.
- **Configuração do Jira no sidebar** — e-mail, API Token (campo senha) e chave do projeto, gravados por sessão; botão "Salvar configuração" ativa a exportação sem necessidade de variável de ambiente.
- **Feedback de exportação** — sucesso mostra a issue criada com link direto `https://.../browse/CHAVE`; falha mostra o erro legível (HTTP, conexão ou credenciais ausentes).
- **Testes do cliente Jira (9)** — mapeamento de prioridade, montagem do payload ADF com a chave correta/`issuetype=Bug`/parágrafos, e falha amigável sem credenciais. Total da suíte: **27 testes**.

## [v1.1.0] - 2026-09-04

### Adicionado
- **Léxico de lentidão por raiz (regex)** — `\blent(?!es?\b)\w*` cobre todas as flexões (`lento`, `lenta`, `lentíssimo`, `lentamente`, `lentidão`...) sem enumerá-las; o lookahead exclui o falso positivo `lente/lentes`. Padrão compilado no módulo + normalização NFC.
- **Checkbox "🔮 Usar IA (Gemini)"** — análise por IA opcional por triagem; desmarcado, só o motor local roda (fallback e reconciliação preservados).
- **Testes unitários ampliados (12 → 18)** — cobrem severidade, negação, sentimento, determinismo, ausência de falso-positivo, padrão "não funciona" via `triar()`, flexões de lentidão, falso positivo `lente` e não dupla contagem de peso.
- **CI (GitHub Actions)** — roda `pytest` em todo push/PR na branch `main`, com badge "build passing" no README.

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
