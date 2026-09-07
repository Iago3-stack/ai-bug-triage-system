# Changelog

Todas as mudanças notáveis do **AI Bug Triage System** são registradas neste arquivo.

O formato é baseado no [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e segue o [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Não lançado]

### Adicionado
- **💡 RAG aprende com a resolução** — agora dá para **registrar como o bug foi resolvido** logo após a triagem (widget "Registrar resolução") ou editando qualquer registro no histórico persistido. A resolução entra no contexto recuperado pelo RAG (`rag.montar_contexto`), então, em triagens futuras similares, o Gemini responde **"como foi resolvido da última vez"** com a solução real de cada caso (também visível no expander de histórico).
- **`registrar_resolucao()`** no facade `persistencia.py` e no `nuvem_supabase.py` (fetch + PATCH por id no payload) — com failover automático pra JSONL local.

## [v2.1.0] - 2026-09-07

### Adicionado
- **☁️ Persistência em nuvem (Supabase)** — o histórico agora pode viver num **Postgres na nuvem** em vez do disco efêmero da Cloud. Novo módulo `nuvem_supabase.py` (REST: insert/select/update + vínculo Jira) e `persistencia.py` virou **facade**: se `SUPABASE_URL` + `SUPABASE_ANON_KEY` estiverem configurados (secrets → `.env` → `os.environ`), grava na nuvem; senão, segue no JSONL local. `PERSISTENCIA_BACKEND=jsonl` força o modo local. O expander do histórico mostra **qual** backend está ativo.
- **`test_nuvem_supabase.py`** — 10 testes 100% offline (config, conversão linha↔doc, HTTP mockado, dispatch do facade e failover). **82 testes no total** — CI continua verde inclusive sem credenciais.

## [v2.0.0] - 2026-09-07

> 🎉 **Marco do produto:** com o **RAG no histórico**, o MVP fechou **10/10** no roadmap. O `AI Bug Triage System` sai de ferramenta pessoal e vira um **produto de triagem com "memória"** — a IA aprende com as triagens passadas e responde "isso já aconteceu? como resolvemos?". A visão rumo a um **SaaS/CRM de QA** (persistência em nuvem, login, notificações, webhook) agora é a fase seguinte (ver README).

### Adicionado
- **📚 RAG no histórico (retrieval + geração)** — o Gemini agora consulta as triagens passadas persidadas e responde **"isso já aconteceu? como resolvemos?"**. Novo módulo `rag.py` com **retrieval local por similaridade Jaccard** (100% determinístico e offline — nada de banco vetorial, proporcional ao projeto) + geração via `ia.analisar_llm_rag` com o campo `PROMPT_RAG`. O relatório ganhou a seção "📚 Histórico consultado (RAG)" (já aconteceu? / registros similares / resolução anterior) e os campos `rag_*` entram no snapshot JSONL.
- **`test_rag.py`** — 10 testes: tokenização (stopwords), similaridade Jaccard, recuperação top-k, montagem do contexto e orquestração sem chave. **71 testes no total** — roadmap do MVP **10/10 concluído** 🎉.

### Corrigido
- **App não pode cair por erro da camada IA/RAG (Streamlit Cloud)** — a Cloud reportava `AttributeError` redigido na chamada do RAG. Blindagem em 2 camadas: `rag.analisar_com_rag` envolve a chamada à IA em `try/except` (retorna `(None, erro)` se o `ia.py` deployado estiver desatualizado) e `home.py` envolve todo o bloco de IA/RAG em `try/except`, salvando o **traceback real no expander "🔧 Diagnóstico interno (IA/RAG)"** (sem redação) e mantendo o motor local no controle. Inclui health check `hasattr(ia, "analisar_llm_rag")` para detectar deploy desatualizado.

## [v1.3.0] - 2026-09-07

### Adicionado
- **📈 Dashboard de QA** — visão geral do histórico persistido em `data/historico.jsonl`: KPIs (total, CRÍTICAs/Altas, MÉDIAS, normais, score médio), **distribuição de severidade**, **volume por dia**, **funcionalidades mais afetadas** (categorização 100% offline) e **comparativo IA vs. motor local** (divergências). Novo módulo `dashboard.py` + expander "📈 Dashboard de QA" no fim do app. A análise é 100% local — nada é enviado para fora.
- **`seed_historico.py`** — reproduz os 30 relatos de teste (32 registros, um duplicado) usando o mesmo motor do app (`triagem.triar`) e popula o `data/historico.jsonl` local com timestamps espalhados em 4 dias — permite desenvolver/testar o Dashboard sem depender da Cloud (arquivo gitignored).
- **Rodapé de crédito no app** — "© v1.3.0 Iago Nunes de Araújo · repo · licença MIT" fixado no fim da página: a autoria aparece em runtime, mesmo se o app for forkado.
- **`AUTORIA.md`** — manifesto de origem/autoria com as provas públicas (commits, releases, CHANGELOG, CI) e exemplos de como dar crédito; linkado no README.
- **Guardrails ampliados (senha/telefone/CPF)** — além de tokens, chaves e e-mails, agora detecta e mascara **senha numérica** (`senha 4323454321`), **telefone** e **CPF** digitados no relato. Descoberto em teste real: a senha numérica passava mascarando apenas o e-mail e ia para a IA. (61 testes no total)

### Corrigido
- **KeyError `jira_key` no Dashboard (Cloud)** — registros persistidos sem exportação para o Jira não tinham a coluna `jira_key` e a tabela de últimas triagens quebrava. A montagem agora tolera a ausência (mostra `—`) e foi extraída para a função `tabela_recente()` pura, com testes de regressão (com e sem `jira_key`).

## [v1.2.1] - 2026-09-06

### Corrigido
- **Teste do guardrails dependia do `.env` local** — `test_detectar_token_atlassian` usava o token real do ambiente, que só existe na sua máquina; no CI (sem `.env`) o token ficava vazio e o teste falhava (49/50). Agora usa token sintético no padrão `ATATT3xFfG...`, deixando o **CI verde**.

## [v1.2.0] - 2026-09-06

### Corrigido
- **Credenciais do Jira não eram lidas do `.env`** — `jira_client` agora usa `_env_var()` (variável de ambiente com fallback no `.env`), mesmo padrão do `ia.py`; sem isso o `streamlit run` mostrava o opção "configurar no sidebar" mesmo com `.env` preenchida.
- **Botão "Exportar para Jira" sumia com o relatório** — o resultado da triagem agora fica em `st.session_state["resultado"]` e é renderizado **fora** do `if st.button(...)`; assim o rerun disparado pelo botão não apaga mais a tela e o envio ao Jira é processado corretamente (mesmo padrão que já resolvia o `link_button` do GitHub).
- **HTTP 400 ao exportar para o Jira com dados do sidebar** — a chave do projeto e o tipo de item digitados são normalizados (`strip` + chave em maiúsculas), evitando erro por espaço ou caixa errada (`kan` → `KAN`).
- **Fuso horário do histórico** — `persistencia.py` usa `ZoneInfo("America/Sao_Paulo")` em vez de `astimezone()`; no servidor da Streamlit Cloud (UTC) a hora caía 3h à frente. Agora o `data_hora` sai sempre no fuso local brasileiro (`-03:00`).
- **Tipo de item padrão `Bug` → `Tarefa`** — o projeto de template Kanban (ex.: `KAN`) não aceita `Bug` e devolvia HTTP 400 enganoso ("projeto não existe"). O default agora é `Tarefa`, compatível; o placeholder do sidebar também foi atualizado.

### Alterado
- **Spinner da IA acolhedor** — o texto durante a análise por IA agora é "🔮 A IA está analisando sua triagem — pode levar um pouco..." (sem prazo fixo que gerava ansiedade).
- **Configuração do Jira recolhida por padrão** — o expander "🔑 Jira — configurar exportação" do sidebar começa fechado, deixando a interface mais limpa para quem usa `.env`/Secrets.

### Adicionado
- **Guardrails de entrada/saída (PII/credenciais)** — novo `guardrails.py`: detecta e **mascara** tokens Atlassian, chaves Gemini/Google/OpenAI, tokens GitHub e e-mails digitados no relato. Se detectar, o texto sensível nunca vai para o Gemini, o Jira, o GitHub nem o histórico — só o aviso "máscara aplicada" aparece. Testes (9 novos). Total da suíte: **50 testes**.
- **Persistência do histórico (JSONL)** — nova `persistencia.py`: cada triagem vira um snapshot fiel em `data/historico.jsonl` (gitignored). Salva o que **de fato** rodou: com IA → relatório completo (causa raiz, passos, prioridade final, divergência); sem IA → só o léxico. Vincula depois a issue do Jira (ex.: `KAN-8`) e oferece seletor de data + download do relatório em Markdown.
- **Testes (7 novos)** da persistência. Total da suíte: **40 testes**.
- **Testes (4 novos)** para leitura de credenciais do `.env` (`_env_var`) e `configurado()`. Total da suíte: **31 testes**.
- **Teste do fuso** (`test_timestamp_usa_fuso_local_brasil`) — trava o `-03:00` na persistência (regressão do bug de hora UTC).
- **Exportação real para o Jira via API REST v3** (`jira_client.py`) — cria a issue do tipo **Tarefa** direto no projeto configurado (ex.: `iagoqa.atlassian.net`), com mapeamento automático da prioridade (NORMAL→Low … CRÍTICA→Highest) e descrição em formato ADF. Usa apenas a biblioteca padrão (`urllib`), sem novas dependências.
- **Configuração do Jira no sidebar** — e-mail, API Token (campo senha) e chave do projeto, gravados por sessão; botão "Salvar configuração" ativa a exportação sem necessidade de variável de ambiente.
- **Feedback de exportação** — sucesso mostra a issue criada com link direto `https://.../browse/CHAVE`; falha mostra o erro legível (HTTP, conexão ou credenciais ausentes).
- **Testes do cliente Jira (9)** — mapeamento de prioridade, montagem do payload ADF com a chave correta/`issuetype=Tarefa`/parágrafos, e falha amigável sem credenciais. Total da suíte: **27 testes**.

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
