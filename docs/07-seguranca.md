# 07 — Segurança (hardening de atendimento)

O app é **multiusuário** (cada conta tem seu token do GitHub, suas credenciais do Jira,
seu plano e seu histórico). A regra que guia tudo aqui: **zero confiança entre
usuários** — nada de segredo, override ou sessão compartilhado entre duas contas, nem
entre o app e o ambiente de teste.

## 1. Princípios

| Princípio | Como aparece no código |
|---|---|
| Segredo por sessão, nunca global | Config do Jira/GitHub num dict em `st.session_state`, passado por parâmetro — nada de mutar global de módulo |
| Sem estado compartilhado entre contextos | Dicionários "vazios" viram `ContextVar` (notificações, auth) |
| Comparação de segredo sem timing | Token do webhook com `hmac.compare_digest` |
| Falha fechada por padrão | `WEBHOOK_REQUIRE_TOKEN=1` rejeita payload sem token mesmo sem segredo configurado |
| Contêiner sem privilégio | `Dockerfile` roda como `appuser` (uid 10001) |
| Dado de produção só leitura no MCP | Role `mcp_readonly` no Supabase; escrita só pelo app/migrations |
| Segredo por env, nunca em arquivo | Configs de MCP usam `{env:RENDER_API_KEY}` etc.; `.env` e artefatos de homologação no `.gitignore` |

## 2. Segredos por sessão (Jira/GitHub)

- `jira_client.py` não guarda mais credencial em global de módulo. `configurar(...)`
  **devolve um dict** que a UI guarda em `st.session_state["jira_config"]`; todas as
  funções (`_headers`, `_montar_payload`, `criar_issue`) recebem `config=`.
- Semântica de `config` em `configurado(config)`: `None` = defaults de env/`.env`;
  `{}` = sessão limpa explicitamente (ignora env). Trocar/limpar credenciais na UI não
  vaza mais para o próximo usuário.
- Regressões presas em teste: `configurar` não vaza para globais, config por sessão
  ignora global, sessão limpa ignora secrets/env (`test_jira_client.py`).
- Token do GitHub segue o mesmo desenho (`github_client.py` recebe `config` da sessão).

## 3. Sem dicionário global (ContextVar)

`notificacoes.py` (overrides de e-mail/Discord) e `auth_supabase.py` (armário da conta
logada) usavam dict global de módulo — compartilhado entre sessões. Agora cada
contexto tem o seu via `contextvars.ContextVar` (default `None`), e o acesso a
`st.session_state` é **gateado por `streamlit.runtime.exists()`**.

> Nota de engenharia: no Streamlit moderno (1.64) acessar `st.session_state` fora do
> `streamlit run` (modo "bare", ex.: pytest) **não levanta erro** — devolve um dict
> compartilhado com aviso. Por isso o gate explícito de runtime, e não try/except.

Regressão: `test_override_nao_vaza_entre_contextos` sobe duas threads e prova que um
override não aparece na outra.

## 4. Webhook (porta pública)

- Token comparado em **tempo constante** (`hmac.compare_digest`), sem vazar por timing.
- `WEBHOOK_REQUIRE_TOKEN=1` = **fail-closed**: sem token configurado, todo payload sem
  `X-Webhook-Token` leva `401`.
- Em produção o `WEBHOOK_TOKEN` está definido no env do Render (ver
  [06 — Webhook](06-webhook.md#deploy-em-produção-render)); verificação viva: `POST`
  sem token → `401`, `/health` → `200`.
- A rota de pagamento **não confia no corpo**: consulta o estado real na API do PagBank
  antes de ativar o Premium (idempotente).

## 5. Rede e SSRF

- Webhooks do Discord passam por `_webhook_seguro` (bloqueia loopback/privado/
  link-local/multicast) antes de qualquer `urlopen`.
- Os `urlopen` "dinâmicos" do semgrep (`p/security-audit`) foram revisados: as URLs
  vêm de **config** (`JIRA_BASE_URL` de env, `api.github.com` com prefixo literal,
  webhook do Discord já guardado) —   nenhum host é controlado por input do usuário.
  Os achados são **informativos**, sem correção de código.

## 6. Dados e banco

- Tabelas do Supabase com **RLS**; a role do MCP (`mcp_readonly`) só lê (listas/describe/SELECT).
- Relatos passam pelo `guardrails.py` (token, chave, e-mail, senha numérica, telefone,
  CPF são mascarados antes de qualquer próximo passo do fluxo).
- Telemetria (PostHog) é no-op sem chave e **não leva PII nem conteúdo do relato**.

## 7. Auditoria estática (semgrep) e CI

- Varreduras feitas pelo **semgrep MCP**: `p/security-audit` (código: 5 achados
  informativos de urllib, revisados) e `p/owasp-top-ten` (supply-chain/CI).
- O CI (`.github/workflows/ci.yml`) roda **pytest + `pip-audit`** a cada push/PR; o
  `pip-audit` audita as versões **instaladas** e o `requirements.txt` já pina tudo com
  `==` (lockfile extra foi considerado desnecessário — decisão registrada).

### Dívida conhecida (opcional, não bloqueia)

- GitHub Actions com tag mutável (`@vN`) em vez de SHA imutável → endurecer com pin por SHA.
- `dependabot` sem cooldown → endurecer cooldown/alertas.

## 8. Onde mexer em cada tema

| Tema | Arquivo |
|---|---|
| Segredo por sessão | `jira_client.py`, `ui_comum.py`, `secoes/ferramenta.py`, `github_client.py` |
| Contexto sem global | `notificacoes.py`, `auth_supabase.py` |
| Token/tempo constante | `webhook.py` |
| Sem root | `Dockerfile` |
| Anti-SSRF / PII | `notificacoes.py`, `guardrails.py` |
| RLS / read-only | migrations, MCP `mcp_supabase.py` |
