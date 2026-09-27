# MEMORIA — ai-bug-triage-system

Memória de longo prazo do projeto. **Regra:** o agente deve ler este arquivo
antes de trabalhar (via skill `ai-bug-triage`) e ATUALIZÁ-LO no fim de cada
sessão com decisões novas. Fica no repositório (pode commitar).

## Deploy / stack
- App: Streamlit (Streamlit Cloud) + IA (Gemini/Groq) + Supabase (dados) + servidor webhook em Python stdlib no **Render** (`webhook.py`, porta 8000).
- Cadeia completa já configurada e consistente: `PAGBANK_TOKEN`, `PAGBANK_WEBHOOK_URL` (produção), `SUPABASE_ANON_KEY`, `SUPABASE_URL`, `WEBHOOK_TOKEN` — iguais em **Streamlit Secrets** e **Render env**.

## PagBank / Pix (estado atual)
- **Produção NÃO liberada**: `POST /orders` → `403 ACCESS_DENIED whitelist access required`. App opera em **fluxo manual** (Pix estático + botão "Já paguei" → confirmação no Painel do Dono → +30 dias). Funciona para pagamento real; sem mudança de código necessária após liberação.
- Homologação oficial **enviada** (formulário Pipefy `https://app.pipefy.com/public/form/2e56YZLK`). SLA ~4 dias úteis. Evidência: `~/Área de trabalho/homologacao_pagbank.txt`.
- Regras da API: `customer.email` **obrigatório** (guard em `pagbank.py`); e-mail do comprador **não pode ser igual** ao do vendedor (erro 40002). `PAGBANK_API` default = produção; local usa sandbox no `.env`.
- Pós-liberação: `POST /orders` deve voltar **201**. **Regenerar o token de produção** e trocar em Streamlit Secrets + Render (nunca colar o token novo no chat).

## Motor de triagem (léxico + semântico)
- `triagem.py` = léxico (contagem de palavras/emoções), **Basic 100% nele**; `semantico.py` = BERTabaporu ONNX int8 (embedding real, offline/determinístico).
- **Gate Premium:** `plano.pago()` (Premium + trial) chama `semantico.ensemble(descricao, triagem.triar(...))` — **média dos scores**, preservando sentimento/fatores do léxico. O semântico **nunca substitui** o léxico (medido: semântico sozinho é regressão).
- Medido em 30 relatos rotulados (`avaliar_motores.py`, 23 sem ambiguidade): léxico **60,9%** · semântico **39,1%** · ensemble **73,9%** estrito. Custo: 1ª carga ~4s, ~185ms/relato, 135MB 1x por instância Cloud.
- Modelo **não** está no repo (GitHub >100MB): **Release `modelo-semantico-v1`**, URL **fixada por tag** + **tamanho exato conferido** antes de instalar no cache (`~/.cache/abt/`); download truncado é apagado e o app fica no léxico. Ordem de resolução: `SEMANTICO_DIR` → `~/Documentos/semantico_nlp/modelo/onnx` (dev) → cache. Cache é efêmero no Streamlit Cloud.
- Deps: `onnxruntime`, `tokenizers`, `numpy`. Testes de `semantico.py` são **herméticos** (nunca rede/ONNX real).

## Supabase (banco real)
- Ref: `hwjmuqmgjfkxhpesxcsk` (projeto). Acesso read-only via role `mcp_readonly` (DSN em `PG_READONLY_DSN` no `.env`, gitignored).
- **Importante:** o pooler (Supavisor) exige o ref no usuário: `mcp_readonly.hwjmuqmgjfkxhpesxcsk`, porta 6543 (`aws-0-sa-east-1.pooler.supabase.com`). Direct connection usa IPv6 (evitar).
- Tabelas reais (schema): `usuarios`, `perfis_usuario`, `planos_usuario`, `solicitacoes_pagamento`, `triagens`, `feedbacks`.
- `planos_usuario` colunas: `uid`, `plano`, `atualizado_em`, `teste_ate`, `teste_auto`, `assinatura_ate` (NÃO tem coluna `id`).
- Consultas ao vivo: MCP `supabase` (ferramentas `db_list_tables`, `db_describe`, `db_query` read-only), servidor `mcp_supabase.py` (raiz).
- **SEGURANÇA (Rota B — FEITA/CONCLUÍDA):** REST roda com **service_role** (`SUPABASE_SERVICE_ROLE_KEY`; `nuvem_supabase._headers()` prefere service, fallback anon). `_config()`/anon continua só pro `/auth/v1`. Migração `migrations/fechar_anon_rest.sql` **aplicada** (SQL Editor): policies `anon` dropadas nas 6 tabelas; RLS segue ON (defesa em profundidade); role `mcp_readonly` com SELECT para diagnóstico. Validado (2026-09): anon SELECT → 0 linhas silencioso; anon INSERT → erro 42501 (não grava); service SELECT 200 nas 6 tabelas (app vivo); MCP `supabase` funcionando.
- App usa **Supabase Auth** (email/password, anon key em `/auth/v1`) — `auth.uid()` existe nas sessions, mas REST hoje não manda bearer do usuário (fica backend-only com service).

## Testes / hermeticidade
- Nunca depender do `.env` do dev: fixtures autouse silenciam `pix._ler_env` em `test_pagbank.py`, `test_pixbilling.py`, `test_webhook.py`. PagBank "configurado" só via `os.environ`.
- Comandos: `.venv/bin/python -m pytest -q` e `.venv/bin/ruff check --select F --exclude .venv .` (suíte 600+).

## Segurança (não negligenciar)
- Nunca imprimir/logar/commitar: `PAGBANK_TOKEN`, `GEMINI_API_KEY`, `SUPABASE_*`, `.env`. Conferir `git status`/diff antes de `add`.
- Conversa exibe segredos como `__VG_...__` (plugin vibeguard). Segredo que já vazou → **rotacionar** (nunca apenas "ignorar").
- Ferramentas de diagnóstico (ex.: `verificar_pagbank.py`) sempre mascaradas.

## Config do opencode local (máquina do usuário)
- Plugins: `opencode-vibeguard` (local, `~/.config/opencode/vibeguard/`; redige email/uuid/ipv4 + regex `sk-`, `gh*`, `AKIA`) e **`gitsafe`** (`.opencode/plugin/gitsafe.js`, auto-descoberto): bloqueia `git add -f` e `git add`/`commit`/`push` de arquivos sensíveis (.env, tokens). Config global: `~/.config/opencode/opencode.jsonc`.
- MCP `supabase`: servidor local Python (`mcp_supabase.py`, read-only). Registrado no config **global**.
- Goodies do projeto: **comandos** `/testes`, `/qa`, `/health`, `/atualiza-memoria` e **subagente** `qa` (`.opencode/agent/qa.md`) que roda pytest+ruff.
- Skill do projeto: `.opencode/skills/ai-bug-triage/SKILL.md` + **skills oficiais do Supabase** em `~/.agents/skills/` (`supabase`, `supabase-postgres-best-practices`) — auto-carregadas.
- **Máquina:** `node` **v24.21.0** instalado sem sudo em `~/.local/node` + symlinks em `~/.local/bin` (no PATH) → `npx`/plugins npm funcionam agora. `psql` ainda não existe. `bun` está no `.zshrc`. Supermemory: descartado (binário local crasha/SIGILL; nuvem exigiria conta) → memória local = este arquivo.

## Pendências (follow-ups)
1. **PagBank**: aguardar resposta da homologação (~4 dias úteis). Ao liberar: revalidar `POST /orders` (201) + regenerar/trocar token de produção (sem colar no chat).
2. ~~**Rota B (segurança Supabase)**~~ ✅ concluída (chaves nos 3 ambientes, deploy no ar, `fechar_anon_rest.sql` aplicado, auditado).
3. `POSTHOG_API_KEY` ainda não no Secrets.
4. Remover monitor duplicado no instatus (precisa de `INSTATUS_API_KEY` ou ação manual no dashboard).
5. ~~Subir `model_int8.onnx` no bucket `modelos`~~ ✅ resolvido: **GitHub Release `modelo-semantico-v1`** (bucket do Supabase nem foi usado).
6. **Encoder do semântico (próximo sprint de qualidade)** — o BERTabaporu atual (`[CLS]` de MLM sem ajuste contrastivo) faz **39% estrito sozinho** (pior que o léxico, 61%); só rende como 2º sinal no ensemble (**73,9%**, 30 casos em `avaliar_motores.py`). Candidatos: `tardellirs/brazembed-pt-br`, `tardellirs/colibri-embed-ptbr`, `serafim-100m`, ou MiniLM pt-BR (~25–30MB int8) — **confirmar licença** antes de trocar.

## Rituais de fim de sessão
- Atualizar este `MEMORIA.md` (e a skill, se mudar convenção).
- Manter `skills/ai-bug-triage/SKILL.md` e este arquivo coerentes.