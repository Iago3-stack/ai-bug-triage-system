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

## Motor de triagem (100% léxico desde v3.2.0)
- `triagem.py` = **motor único do app** (Basic e Premium), local/deterministico/instantâneo. Não há mais download de modelo nem gate por plano.
- **v3.1.0 (motor semático BERTabaporu no Premium) foi revertido no v3.2.0.** Lição: no corpus de 30 casos ele parecia ganhar (+13 pts), mas no histórico real (38 textos únicos) só escalava bug cosmético para MÉDIA, com zero resgates. **Lição maior: corpus pequeno e não representativo engana — medir sempre nos dados reais também.**
- Por que o semântico falhou: usa só o `[CLS]` de um MLM sem ajuste contrastivo → o vetor não discrimina severidade (similaridade máx. praticamente igual nos acertos e nos erros, distribuições sobrepostas) → nenhum threshold OOD resolve. Precisaria de um encoder de sentence-embeddings com mean pooling (MiniLM/brazembed) **e** de 100+ casos rotulados.
- **Gate para qualquer motor novo entrar em produção:** bater o léxico no corpus de 30 (`avaliar_motores.py`) **e** no teste de texto real (concordância com a gravidade já gravada, que vem da camada de IA/Gemini — hoje o léxico concorda em 37/38).
- Experimento fica no repo, fora do app: `semantico.py`, `avaliar_motores.py`, `test_semantico.py`, `requirements-semantico.txt` (rode `pip install -r requirements-semantico.txt`). Modelo no GitHub Release `modelo-semantico-v1` (URL fixada por tag + tamanho conferido).
- **Corpus de avaliação:** 30 relatos rotulados em `~/Documentos/relatos-teste-dashboard-qa.md` (23 sem ambiguidade; "ALTA"→CRÍTICA). Léxico v3.2.0: **96,7% tolerante / 95,7% estrito** (era 66,7%/60,9%). Erro restante Known: #30 (`página em branco` = -1,95, rótulo CRÍTICA) — não forçado de propósito.
- Ground truth real **não existe** ainda: `feedbacks` tem 4 linhas de estrelas (satisfação, não severidade). Para avançar com qualidade de triagem, o passo certo é rotular 100+ relatos.

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

## Rótulo humano de severidade (v3.3.0)
- `avaliacao.py` grava `payload->avaliacao = {rotulo, comentario, em, autor}` via GET + PATCH (mesmo caminho do `registrar_resolucao`), **sem migration**. Rótulos canônicos: CRÍTICA / MÉDIA / NORMAL.
- O app mostra 4 botões; "Estava certa" usa a **prioridade reconciliada** (`payload->prioridade_final`), porque é o que o usuário viu. IA tem 4 níveis → `ALTA→CRÍTICA`, `BAIXA→NORMAL`.
- `carregar_rotulados()` é **ferramenta do dono/admin** (contém texto de relato de terceiros): a UI comum só mostra a contagem, nunca o texto.
- PostgREST **aceita** `payload->avaliacao->>rotulo=not.is.null` como filtro de servidor (validado na API real, só leitura) — usar isso, não varrer a tabela.
- Cobertura: 21 testes herméticos em `test_avaliacao.py` (mockam o REST).

## Benchmark local de embeddings (2026-09-27) — 2º candidato, resultado
- `avaliar_embeddings.py` (venv à parte em `/tmp/opencode/venv-embed`, **fora** do app) comparou `tardellirs/brazembed-pt-br` (BERT 12×768, mean pooling, MIT, 436MB fp32) com o léxico nos 30 casos de `casos_qa.py`.
- **Resultado:** léxico **96,7% / 95,7%** · protótipos (zero-shot) **53,3% / 43,5%** · 1-NN **66,7% / 60,9%** · logreg **56,7% / 47,8%** · tfidf+logreg **56,7% / 47,8%** · tfidf+centro **53,3% / 39,1%** (tolerante/estrito; os 4 últimos são leave-one-out, não comparáveis ao léxico).
- **Decisão: nenhum encoder entra no app.** O melhor modelo treinado (1-NN) fica 30 pontos abaixo do léxico, e o classificador simples sem transformer (tf-idf) é tão ruim quanto o transformer — ou seja, **o gargalo não é o modelo, é o dado**: 30 casos sintéticos, classe NORMAL com 4 exemplos.
- Mesma patologia do BERTabaporu, agora com mean pooling e treino em português: os 3 protótipos de severidade ficam quase equidistantes de qualquer entrada (margem top1−top2 média 0,058, máx 0,247) e o modelo superprediz CRÍTICA (16 de 30). **Severidade não é propriedade de similaridade semântica**, é impacto de negócio.
- Protótipos foram escritos pela *definição* de severidade antes de medir; não foram ajustados contra os 30 casos (isso daria número otimista na própria base).
- **Reaproveitar:** `casos_qa.py` virou a fonte única do ground truth (antes estava preso dentro de `avaliar_motores.py`, que exige onnxruntime). Quando houver 100+ rótulos reais (v3.3.0), é só rodar `avaliar_embeddings.py` de novo — sem mexer em código — para saber se um modelo treinado finalmente passa do léxico.

## Pendências (follow-ups)
1. **PagBank**: aguardar resposta da homologação (~4 dias úteis). Ao liberar: revalidar `POST /orders` (201) + regenerar/trocar token de produção (sem colar no chat).
2. ~~**Rota B (segurança Supabase)**~~ ✅ concluída (chaves nos 3 ambientes, deploy no ar, `fechar_anon_rest.sql` aplicado, auditado).
3. `POSTHOG_API_KEY` ainda não no Secrets.
4. Remover monitor duplicado no instatus (precisa de `INSTATUS_API_KEY` ou ação manual no dashboard).
5. ~~Subir `model_int8.onnx` no bucket `modelos`~~ ✅ resolvido: **GitHub Release `modelo-semantico-v1`** (bucket do Supabase nem foi usado).
6. ~~**Encoder do semântico**~~ ✅ **descartado no benchmark local (2026-09-27)**: `brazembed-pt-br` (o 2º candidato) deu 43,5% estrito zero-shot e 60,9% com 1-NN, contra 95,7% do léxico — e tf-idf sem transformer deu o mesmo. Só reabrir a conversa com **100+ rótulos reais**, e medir com `avaliar_embeddings.py`.
7. **Rotular 100+ relatos** — é o bloqueio de qualquer ganho de qualidade em triagem: o corpus de 30 é pequeno e não representativo do histórico (que é dominado por fixture de teste). O fluxo de rótulo por triagem (**v3.3.0**, `avaliacao.py`) existe para isso: `payload->avaliacao` + `carregar_rotulados()` para o dono/admin medir.

## Rituais de fim de sessão
- Atualizar este `MEMORIA.md` (e a skill, se mudar convenção).
- Manter `skills/ai-bug-triage/SKILL.md` e este arquivo coerentes.