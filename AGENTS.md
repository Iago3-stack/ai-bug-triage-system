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
.venv/bin/python scripts/checar_scroll_legal.py   # check no browser (app precisa estar no ar)
```

Sem `pyproject.toml` e sem `[tool.pytest]`/`[tool.ruff]`: **pytest roda na raiz
e pega `test_*.py` automaticamente**; ruff não tem config, é invocado com flags
explícitas. `ruff` **não está em nenhum requirements** — se um comando precisar
dele e não achar, instale à parte, não adicione aos requirements sem querer.
Mesma regra para `playwright` (usado por `scripts/checar_scroll_legal.py`):
fica **fora** de `requirements*.txt`, porque o `pytest` roda a cada push e
depender de browser de verdade em todo push seria caro e instável.

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
- `webhook.py` = micro-serviço HTTP **100% stdlib** que em produção escuta em
  **`0.0.0.0:8080`**, exposto de propósito — é o endpoint público do PagBank.
  Só `criar_servidor()` amarra em `127.0.0.1`, e quem o chama é **apenas
  `test_webhook.py`**; o caminho de produção é `principal()`, cujo default já é
  `0.0.0.0` (travado em `test_interpretar_args_defaults`).
- **As duas rotas `/webhook/*` têm teto de `MAX_BYTES` e timeout de socket** — o
  teto é `Content-Length` antes de ler, e o 413 fecha a conexão em vez de
  deixar lixo no socket com keep-alive.
- **`/webhook/pagamento` autentica pelo `x-authenticity-token` do próprio
  PagBank**, não por `X-Webhook-Token`. A assinatura oficial é
  `SHA256(token_da_conta + "-" + corpo_cru)` em hex. Não existe header
  customizado configurável na conta do PagBank, então `X-Webhook-Token` — que
  protege `/webhook/falha` — **não serviria** aqui. O hash é sobre os **bytes
  crus**: reserializar o JSON parseado muda o espaçamento e a validação falha
  sempre. Sem `PAGBANK_TOKEN` a rota fica aberta, a menos que
  `WEBHOOK_REQUIRE_TOKEN=1` feche. Continua sendo defesa em profundidade: mesmo
  com corpo forjado, nada é confirmado sem a consulta server-side na API.
- O endpoint é público, **sem rate limiting**. O que fecha o abuso hoje é a
  assinatura + o fato de a confirmação ir sempre à API do PagBank.
- **Ressalva sobre `Assinaturas` (recorrente):** a doc pública diz
  `x-authenticity-token`, mas há relatos no fórum do PagBank de receber
  `X-Payload-Signature` (RSA, via `GET /public-keys`) em produção e nunca em
  homologação — em URLs `api.assinaturas.pagseguro.com`. A rota atual valida o
  header documentado. **Se a recorrência for ativada, confirmar o header real em
  produção antes de confiar que a validação está ativa** — assinatura sempre
  inválida é o sintoma, e o fallback atual é rota aberta.
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

## UI no browser — o teste que quase mentiu

O bug do `_rolar_topo` (v3.5.3) jogava quem rolasse a Legal de volta ao topo a
cada 400ms. **Duas rodadas de teste automatizado disseram que não havia bug**,
porque as duas mediram no lugar errado. As regras que saíram disso:

1. **Arme o observador antes — e no lugar certo — em relação ao observado.**
   Aqui isso significou rolar com `page.mouse.wheel`, que emite `WheelEvent`
   real. Atribuir `el.scrollTop` por JS **não** dispara `wheel`/`keydown`, e o
   `_rolar_topo` só libera o timer no primeiro gesto: um robô programático nunca
   gera gesto, então mede um usuário que não existe e acusa uma puxada que
   ninguém sente.
2. **Nunca encerre a medição no primeiro acerto.** O teste que "confirmou a
   ausência de bug" fazia `break` no primeiro `scrollTop != 0` — ou seja,
   parava no primeiro zero, que era o próprio sintoma mascarado.
3. **Julgue a forma, não o ponto.** O defeito era um padrão no tempo (dente-de-
   serra de 400ms). Nenhuma asserção de valor único pega oscilação: grave pares
   `[tempo, scrollTop]`.
4. **Série vazia não é "nenhuma jogada".** Ausência de evidência não é evidência
   de ausência. `scripts/checar_scroll_legal.py` tem piso de amostras e devolve
   `INCONCLUSIVO` (exit 1) abaixo dele — sem isso, uma sonda que nem rodou dá
   verde falso. Foi exatamente o que aconteceu na primeira versão dele.

Armadilhas deste app, para não reprovar a sonda errada:

- O alvo é o **botão** `⚖️ Termos & Privacidade` do menu (`st.switch_page` — é o
  caminho que chama o `_rolar_topo`). Existe um `<a href="/legal">` no rodapé com
  texto quase igual e é o caminho **errado**: full page load, sem `_rolar_topo`,
  e redirecionado para `/` em servidor frio.
- A rota inicial é `/inicio`, não `/`. E o deep link externo `/?pag=legal`
  depende de `st.query_params` sobreviver ao cold-start, o que **não** se
  reproduz no servidor local — por isso o check usa o botão, não o deep link.
- O scroll é `[data-testid="stMain"]`, não `window` nem `documentElement`.
- Meça em 1366x768: em 800x600 o conteúdo da Legal cabe e o defeito some sozinho.
- sobra uma janela de armar de ~1s (o iframe do `components.html` monta depois,
  e o `sobe()` inicial pode rodar antes do listener de gesto existir). **Uma**
  jogada ali é tolerada e reportada; a puxada sustentada não é.

O check roda **fora do `pytest`** e foi verificado nos dois lados: falha com o
bug (12 jogadas, exit 1) e passa com a correção (3/3, exit 0). Os 2 testes de
`test_ui_comum.py` travam a *estrutura* do JS; só o browser prende o
*comportamento*.

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

`.opencode/`, `.claude/`, `agent/`, `mcp_render.py`, `skills-lock.json` e
`opencode.json` são **config de agente do dono**, não artefatos do projeto — estão
no `.gitignore` e não devem ser adicionados ao git. `opencode.json` só registra o
MCP `supabase` com caminho absoluto para `.venv/bin/python` + `mcp_supabase.py`,
o que não vale para mais ninguém. `mcp_supabase.py` **é** versionado (ponte
read-only, útil a quem mexe no repo); `mcp_render.py` não.

Comandos locais em `.opencode/command/`: `health`, `testes`, `qa`, `deploy`,
`atualiza-memoria`, `guardas`. O OpenCode lê essa pasta **na subida do
processo** — arquivo novo só aparece depois de reiniciar o cliente.

Skills de terceiros (`.claude/skills/`, `skills-lock.json`) são **não
versionadas** e rastreadas por hash no lock. Não commitar; o lock existe pra
deteção de drift.
