# AGENTS.md — AI Bug Triage System

Contexto para agentes que trabalham neste repo. Só entra aqui o que **não** dá
para inferir lendo os arquivos em 30 segundos.

## O que é

App Streamlit que classifica bugs por severidade. Motor **100% léxico local**
(`triagem.py`, stdlib puro), com reconciliação opcional por IA (`ia.py`).
Site público: `ai-bug-triage.com.br`. Repo **público** — nada de segredo aqui.

## Comandos

Ambiente virtual é `.venv` (na raiz, gitignored). Instale sempre por ele:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest -q                        # suíte completa
.venv/bin/pytest test_triagem.py -v        # um módulo
.venv/bin/streamlit run home.py            # app
.venv/bin/python webhook.py --porta 8080 --host 0.0.0.0
.venv/bin/python triagem.py                # motor sem UI, sem chave
```

Sem `pyproject.toml` e sem `[tool.pytest]`/`[tool.ruff]`: **pytest roda na raiz
e pega `test_*.py` automaticamente**; ruff não tem config, é invocado com flags
explícitas. `ruff` **não está em nenhum requirements** — se um comando precisar
dele e não achar, instale à parte, não adicione aos requirements sem querer.

## Ordem do CI (e por que importa)

`pip-audit` → `pytest` → `semgrep` → badge. O `ci.yml` explica o motivo na
íntegra: **o semgrep vem depois do pytest de propósito** — se o gate de segurança
falhasse primeiro, o `junit.xml` não existiria, o badge cairia no fallback
"erro no CI" e o `ci-falhas.yml` reportaria uma falha de testes que não
aconteceu. Não reordene esses dois passos.

O badge é gerado com `if: always()` em todos os passos pós-pytest, para
refletir o resultado real mesmo com job vermelho.

**Semgrep** (`.semgrep/segredo-tempo-constante.yaml`) roda com
`--config .semgrep/ --error --metrics=off`. Consequência: **só a nossa regra
roda** — o `--config` aponta para a pasta, então as regras default do Semgrep
**nunca** executam aqui. É decisão deliberada (privacidade, sem egress no
build). Não troque por `--config auto` sem falar com o dono: `auto` exige
métricas ligadas e busca no registry.

`semgrep` está **fora** de `requirements*.txt` de propósito: é ferramenta de
análise, não dependência do app nem de teste, e não deve entrar no build do
Streamlit Cloud. Versão pinada no workflow, não em requirements.

## Versionamento — duas fontes que precisam andar juntas

1. `VERSAO` em `ui_comum.py` (~linha 24) — o que o app exibe no rodapé.
2. `CHANGELOG.md` — Keep a Changelog, pt-BR.

Toda entrada do CHANGELOG cita a **contagem de testes** daquela versão. Se você
mudou a suíte, atualize o número. O CHANGELOG é denso e explicativo (o padrão
do repo é descrever *o defeito*, não só a correção) — manter esse tom.

## Arquitetura que não é óbvia pelo nome

- `home.py` = entrypoint. Carrega o `.env`   **à mão** (parser próprio, imitando
  `CHAVE=valor`; sem python-dotenv) **antes** de importar o resto, e só aplica
  se a variável ainda não existir no ambiente. No Streamlit Cloud não há `.env`,
  então isso é no-op e valem os Secrets.
- `roteador.py` registra 7 páginas via `st.navigation`, todas em `secoes/`.
  `painel_dono` só entra na lista para quem passa em `admin.eh_dono()` — não é
  só esconder a página, é omitir do roteador.
- `webhook.py` = micro-serviço HTTP **100% stdlib** que escuta em
  `127.0.0.1` (não expõe). Teto de payload `MAX_BYTES`, valida `Content-Length`
  antes de ler.
- Tema: `.streamlit/config.toml` trava o tema **nativo** em `light` de propósito
  (o app faz dark/light no CSS próprio, via seletor no sidebar). Não é esquecimento.
- `web/landing/` é site estático separado do app e é publicado pelo **mesmo**
  workflow de CI que o badge.

## Testes

- **Não existe `conftest.py`** e não há fixtures compartilhadas: cada `test_*.py`
  monta o que precisa (monkeypatch de env é o padrão).
- **O CHANGELOG afirma que há testes de integração via `AppTest` do Streamlit.
  Não há.** `AppTest` aparece num comentário do `home.py` e no CHANGELOG, e em
  mais nenhum lugar. Os testes de UI importam a função e testam a lógica isolada
  (com `types.SimpleNamespace` no lugar de um file uploader, Pillow para
  imagens). **Não tente rodar `AppTest` esperando que os testes existam.**
- Ambientes externos são mockados por `monkeypatch` (`urlopen`, clients HTTP).
  `requests` e `urllib` usados em produção **todos** têm `timeout` — vale
  manter, é o padrão do repo (55 de 55 no momento).

## Segurança

- Segredo **nunca** no repo. Local: `.env` (gitignored). Nuvem: Settings →
  Secrets do Streamlit Cloud.
- Comparação de token/chave é **tempo-constante** (`hmac.compare_digest` /
  `secrets.compare_digest`). `==` é vetor de timing (CWE-208) e é o que a
  regra do Semgrep bloqueia. `WEBHOOK_REQUIRE_TOKEN` desliga a exigência — é o
  nome do token que ele lê.
- `homologacao_pagbank.txt` e `verif_pagbank.txt` contêm PII/CPF de teste e
  estão no `.gitignore` **de propósito**. Não remova do ignore, não commite.
- O `.gitignore` ignora `*.csv` e `data/` — cuidado: o histórico de triagens e
  a base rotulada vivem nessa área. Se precisar versionar um CSV de dados,
  é uma decisão explícita do dono, não um `git add -f` automático.

## Deploy

- Push na `main` dispara: CI (testes + badge + landing) e **auto-deploy do
  webhook no Render** (serviço `ai-bug-triage-system-webhook`).
- `docker-image.yml` **só** roda em `release: published` (ou dispatch manual) —
  publicar a imagem não é parte do push normal.
- `stats-triagens.yml` é cron (`12 */6 * * *`) e escreve `stats.json` no Pages.
  O `ci.yml` faz `curl` do `stats.json` **já publicado** antes de publicar o
  badge, justamente para um deploy de CI não apagar o contador. Se mexer na
  ordem de publicação, preserve esse `curl`.
- Branch protection exige o status check `test` — pushes falham no gate até a
  run concluir.
- Auto-merge do Dependabot existe (`auto-merge-dependabot.yml`, por label).

## OpenCode (config local, não versionada)

`.opencode/` e `.claude/` são **untracked por decisão** — são config de agente
do dono, não artefatos do projeto. Não as adicione ao git. `opencode.json`
(raiz, versionado) só registra o MCP `supabase` com caminho absoluto para
`.venv/bin/python` + `mcp_supabase.py`.

Comandos locais em `.opencode/command/`: `health`, `testes`, `qa`, `deploy`,
`atualiza-memoria`, `guardas`. O OpenCode lê essa pasta **na subida do
processo** — arquivo novo só aparece depois de reiniciar o cliente.

Skills de terceiros (`.claude/skills/`, `skills-lock.json`) são **não
versionadas** e rastreadas por hash no lock. Não commitar; o lock existe pra
deteção de drift.
