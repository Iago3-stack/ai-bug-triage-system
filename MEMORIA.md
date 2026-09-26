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

## Supabase (banco real)
- Ref: `hwjmuqmgjfkxhpesxcsk` (projeto). Acesso read-only via role `mcp_readonly` (DSN em `PG_READONLY_DSN` no `.env`, gitignored).
- **Importante:** o pooler (Supavisor) exige o ref no usuário: `mcp_readonly.hwjmuqmgjfkxhpesxcsk`, porta 6543 (`aws-0-sa-east-1.pooler.supabase.com`). Direct connection usa IPv6 (evitar).
- Tabelas reais (schema): `usuarios`, `perfis_usuario`, `planos_usuario`, `solicitacoes_pagamento`, `triagens`, `feedbacks`.
- `planos_usuario` colunas: `uid`, `plano`, `atualizado_em`, `teste_ate`, `teste_auto`, `assinatura_ate` (NÃO tem coluna `id`).
- Consultas ao vivo: MCP `supabase` (ferramentas `db_list_tables`, `db_describe`, `db_query` read-only), servidor `mcp_supabase.py` (raiz).
- **SEGURANÇA (Rota B — implementada no código):** REST roda com **service_role** (`SUPABASE_SERVICE_ROLE_KEY`; `nuvem_supabase._headers()` prefere service, fallback anon). `_config()`/anon continua só pro `/auth/v1`. Pendente: configurar a service key em **Local (.env) + Streamlit Secrets + Render env**, **deployar**, e aplicar `migrations/fechar_anon_rest.sql` (drop policies anon das 6 tabelas; mantém `mcp_readonly` com SELECT). Não aplicar antes de ter a service key rodando em produção.
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
2. **Rota B (segurança Supabase)**: pegar `SUPABASE_SERVICE_ROLE_KEY` (Settings → API Keys) e configurar em **.env local, Streamlit Secrets e Render env**; commit+push (deploy Render/Streamlit); aplicar `migrations/fechar_anon_rest.sql` no SQL Editor; conferir `pg_policies` com 0 policies anon e MCP `supabase` seguindo funcionando.
3. `POSTHOG_API_KEY` ainda não no Secrets.
4. Remover monitor duplicado no instatus.
5. Subir `model_int8.onnx` + `tokenizer.json` no bucket `modelos`.

## Rituais de fim de sessão
- Atualizar este `MEMORIA.md` (e a skill, se mudar convenção).
- Manter `skills/ai-bug-triage/SKILL.md` e este arquivo coerentes.