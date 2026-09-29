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

## OpenCode 2 (2026-09-29) — decisão: **ficar no v1.18.3**
- **Não migrar agora.** Não há obrigação: o doc oficial de migração diz que o formato V1 continua suportado, que "não precisa reescrever nada" pra começar no v2 e que se algo suportado parar no v2 é **bug de compatibilidade**, não migração esperada. Projeto MIT com base de usuários enorme não forçaria break. Reavaliar só se: (a) o v1 parar de ganhar release, (b) precisarmos de feature exclusiva do v2 (Desktop, web/`opencode pair`, sessão compartilhada, extensão de IDE), ou (c) plugin que queremos usar só existir em v2.
- **O que quebraria se migrássemos:** os 2 plugins usam a API v1 e **não rodam no v2** — `vibeguard` (global, `file://`) e `gitsafe` (projeto, implícito). Mais 2 pontos: `permission.skill` pode não existir como ação no v2 (o v2 troca `permission` por array `permissions` com `shell`/`edit`/`subagent`/`websearch`) — **não confirmado**, é a incógnita a checar primeiro; e o v2 usa **um daemon único e persistente**, então a env do processo é capturada quando ele sobe e sobrevive a novos terminais — o 401 do `RENDER_API_KEY` (que já aconteceu aqui) fica **mais** provável de voltar.
- **Loss zero no resto:** não usamos `provider`, `compaction`, `logLevel`, `server`, `skills.paths`, `lsp` nem `CLAUDE.md` — todas as categorias de perda do v2 não nos atingem. MCPs, `agent/`, `command/`, `.opencode/skills/` e `experimental.mcp_timeout` seguem válidos nos dois.
- **Não existe side-by-side:** o instalador v2 **sobrescreve** `~/.opencode/bin/opencode` e as duas versões usam o comando `opencode`. Por isso existe o backup datado **`~/backups/opencode/v1-1.18.3-20260929/`** (binário + configs + os 2 plugins + `RESTAURAR.md` + `MANIFESTO.sha256`). Sem segredo copiado lá: a config tem só o placeholder `{env:RENDER_API_KEY}`. Verificar com `sha256sum -c MANIFESTO.sha256`.
- **`gitsafe.js` NÃO está no git** (nem ignorado, só solto) — é a única cópia em disco, e ele só carrega por auto-descoberta de pasta, sem aparecer em config nenhuma. Se parar de carregar, a proteção some **em silêncio**. Mitigação: o plugin agora grava heartbeat em `~/.config/opencode/.gitsafe-carregado` (`carregado_em`, `pid`, `versao`) ao carregar, e o comando **`/plugins`** audita guards + MCPs + env + integridade do backup. Rodar `/plugins` no início de sessão que for mexer em git ou segredos.
- **Lição de toolchain:** verificação passiva (arquivo presente) não prova que o código rodou. Para guarda de segurança, a prova tem que ser um artefato que o próprio guard produz ao rodar — senão o "funcionando" é só uma suposição que ninguém checa até o dia de precisar.

## Rótulo humano de severidade (v3.3.0)
- `avaliacao.py` grava `payload->avaliacao = {rotulo, comentario, em, autor}` via GET + PATCH (mesmo caminho do `registrar_resolucao`), **sem migration**. Rótulos canônicos: CRÍTICA / MÉDIA / NORMAL.
- O app mostra 4 botões; "Estava certa" usa a **prioridade reconciliada** (`payload->prioridade_final`), porque é o que o usuário viu. IA tem 4 níveis → `ALTA→CRÍTICA`, `BAIXA→NORMAL`.
- `carregar_rotulados()` é **ferramenta do dono/admin** (contém texto de relato de terceiros): a UI comum só mostra a contagem, nunca o texto.
- PostgREST **aceita** `payload->avaliacao->>rotulo=not.is.null` como filtro de servidor (validado na API real, só leitura) — usar isso, não varrer a tabela.
- Cobertura: 21 testes herméticos em `test_avaliacao.py` (mockam o REST).

## Benchmark local de embeddings (2026-09-27) — 2º candidato, resultado
- `avaliar_embeddings.py` (venv à parte em `/tmp/opencode/venv-embed`, **fora** do app; **venv e cache do modelo já foram apagados** — recriar com os 3 comandos no docstring do script) comparou `tardellirs/brazembed-pt-br` (BERT 12×768, mean pooling, MIT, 436MB fp32) com o léxico nos 30 casos de `casos_qa.py`.
- **Resultado:** léxico **96,7% / 95,7%** · protótipos (zero-shot) **53,3% / 43,5%** · 1-NN **66,7% / 60,9%** · logreg **56,7% / 47,8%** · tfidf+logreg **56,7% / 47,8%** · tfidf+centro **53,3% / 39,1%** (tolerante/estrito; os 4 últimos são leave-one-out, não comparáveis ao léxico).
- **Decisão: nenhum encoder entra no app.** O melhor modelo treinado (1-NN) fica 30 pontos abaixo do léxico, e o classificador simples sem transformer (tf-idf) é tão ruim quanto o transformer — ou seja, **o gargalo não é o modelo, é o dado**: 30 casos sintéticos, classe NORMAL com 4 exemplos.
- Mesma patologia do BERTabaporu, agora com mean pooling e treino em português: os 3 protótipos de severidade ficam quase equidistantes de qualquer entrada (margem top1−top2 média 0,058, máx 0,247) e o modelo superprediz CRÍTICA (16 de 30). **Severidade não é propriedade de similaridade semântica**, é impacto de negócio.
- Protótipos foram escritos pela *definição* de severidade antes de medir; não foram ajustados contra os 30 casos (isso daria número otimista na própria base).
- **Reaproveitar:** `casos_qa.py` virou a fonte única do ground truth (antes estava preso dentro de `avaliar_motores.py`, que exige onnxruntime). Quando houver 100+ rótulos reais (v3.3.0), é só rodar `avaliar_embeddings.py` de novo — sem mexer em código — para saber se um modelo treinado finalmente passa do léxico.

## Disco: material de experimento já removido (2026-09-27)
- Apagado: cache HF do **brazembed** (417MB) + venv do benchmark (1,3GB) + cache HF do **BERTabaporu** (1,1GB) + `model.onnx` fp32 (514MB) + `.venv` da exportação em `~/Documentos/semantico_nlp/` (1,3GB) = **~4,6GB liberados**.
- **Release `modelo-semantico-v1` removido do GitHub** (v3.4.0), motor `semantico.py` apagado do repo e **a pasta `~/Documentos/semantico_nlp/` deletada por completo** (o `model_int8.onnx` de 130MB era a última cópia do artefato). ⚠️ Consequência: recriar o ONNX exigiria re-baixar o BERTabaporu do HF e refazer a exportação + quantização int8 do zero. Não recomeçar esse experimento.
- O app não baixa nem cacheia modelo nenhum: é 100% léxico local (`triagem.py`), sem ONNX, sem `~/.cache/abt/`, sem dependência de rede.
- `~/.cache/huggingface/` foi removido; se for preciso re-exportar o ONNX, o `transformers` re-baixa o BERTabaporu do HF.

## Decisão: só léxico, evoluindo (v3.4.0)
- **Saem do repo:** `semantico.py`, `test_semantico.py`, `requirements-semantico.txt`, o Release `modelo-semantico-v1` e o `avaliar_motores.py` (léxico x semântico x ensemble).
- **Ficam:** `triagem.py` (o motor), **`avaliar_lexico.py`** (medição do léxico com score/fatores por erro + `--falhar-abaixo` como trava de regressão), `casos_qa.py` (ground truth) e `avaliar_embeddings.py` (evidência do benchmark negativo — só roda fora do app, sem dep no build).
- **Por quê:** dois experimentos, mesma conclusão. v3.1.0 (BERTabaporu) escalava bug cosmético; v3.3.0 (brazembed + classificadores) deu 43,5% estrito zero-shot e 60,9% no melhor caso treinado, contra **95,7% do léxico** — e o tf-idf **sem transformer** empatou, provando que o gargalo é o dado, não o modelo. Severidade é impacto de negócio, não similaridade semântica.
- **Como evoluir o léxico a partir de agora:** (1) rotular relatos reais pelo fluxo do v3.3.0, (2) `python3 avaliar_lexico.py` para ver os erros com o fator que disparou, (3) mexer em `triagem.py`, (4) rodar de novo + `pytest test_triagem.py` (tem 3 guardas de regressão) e `--falhar-abaixo 95`. Sem modelo, sem download, sem latência.
- **Não reabrir** a conversa de encoder sem 100+ rótulos reais medidos por esse mesmo harness.

## Tela de rotulamento no painel do dono (v3.5.0)
- **Onde:** `secoes/painel_dono.py` → `_secao_rotulagem()` (chamada no fim de `render()`, só depois do gate `admin.eh_dono()`), com `_metricas_de_concordancia()`, `_registrar_grupo()`, `_campo_atalho()` e `_cartao()`.
- **Fila:** `avaliacao.carregar_pendentes(limite, deslocamento, unicos=True)` — filtra no servidor (`payload->avaliacao->>rotulo=is.null`) e **dedup por texto** (`_chave_texto()`: minúsculas, sem acento, espaços normalizados). Cada item traz `repeticoes` e `ids_irmaos`.
- **Regra de produto:** o rótulo é do **bug**, não da linha. Um clique grava todas as cópias (`registrar_varios` faz GET+PATCH por linha, porque o PATCH do PostgREST substitui o jsonb inteiro e não dá para fazer em uma tacada).
- **Atalhos:** `1`=CRÍTICA, `2`=MÉDIA, `3`=NORMAL, `0`=pular, via `st.text_input(max_chars=1, on_change=...)` — não existe `st.keyboard` no Streamlit 1.64.
- **Métrica:** por **texto único**, nunca por linha (senão a fixture que aparece 20× pesa mais que todo o resto). Mostra léxico × rótulo, prioridade vista × rótulo, e a contagem de quantas vezes a reconciliação deixou a prioridade **mais severa** que o léxico — é o indicador do `max(sev_local, sev_ia)` em `secoes/ferramenta.py:669` estar inflando CRÍTICA.
- **Identidade do autor:** `admin.email_logado()` (fonte única de verdade, mesma de `eh_dono()`) — não replicar a leitura de `auth_supabase.sessao()` nem importar o `_fb_identidade()` privado de `ferramenta.py`.
- **Export:** `avaliacao.base_para_csv()` + `st.download_button` para análise fora do app.
- **Testado** com `streamlit.testing.v1.AppTest` (mock de `nuvem_supabase.requests`): render sem exceção, dedup exibindo `×2`, matriz de confusão correta, 1 clique → 2 PATCH (`id=eq.a`, `id=eq.b`) e atalhos `2`/`0`/`x` com o efeito esperado. 9 testes herméticos novos (706 no total).

### Correções de tema da tela (v3.5.1)
- **Regra da casa para cor:** nunca `style="color:#xxx"` inline em painel. Vai para `ui_tema.py` como classe, com variante por tema. A tela de rotulagem nasceu com `#e2e8f0`/`#94a3b8` fixos e o texto ficou invisível no tema claro — erro já cometido antes no app, não repetir.
- **Botão sem hover:** o `:hover`/`:active`/`:focus` **repete a mesma cor de fundo** do estado normal e zera `filter`/`box-shadow`. Só isso desliga o hover nativo do Streamlit (o `.marca-jira` é o exemplo canônico).
- **Marcador precisa estar DENTRO da coluna:** o CSS casa por `[data-testid="stColumn"]:has(.marca-rot-*)`, então a `_marca()` tem de sair dentro do `with coluna:`. Fora dela a regra não pega e o botão volta ao estilo nativo **sem nenhum erro** — falha silenciosa.
- **Contraste:** tons -600 com texto branco reprovam em WCAG AA (`#d97706` 3,19:1, `#059669` 3,77:1). Usar os -700 (`#b45309` 5,02:1, `#047857` 5,48:1, `#dc2626` 4,83:1, `#475569` 7,58:1). `test_contraste()` em `test_painel_dono.py` trava isso.
- **Armadilha do `with`:** ao converter `coluna.button(...)` para `with coluna:`, conferir a indentação do `st.rerun()` que vem logo abaixo — dentro do `with` ele vira incondicional e trava a página em loop de rerun. O teste de render com `AppTest` pegou isso; `pytest` puro não pega.

## Pendências (follow-ups)
1. **PagBank**: aguardar resposta da homologação (~4 dias úteis). Ao liberar: revalidar `POST /orders` (201) + regenerar/trocar token de produção (sem colar no chat).
2. ~~**Rota B (segurança Supabase)**~~ ✅ concluída (chaves nos 3 ambientes, deploy no ar, `fechar_anon_rest.sql` aplicado, auditado).
3. `POSTHOG_API_KEY` ainda não no Secrets.
4. Remover monitor duplicado no instatus (precisa de `INSTATUS_API_KEY` ou ação manual no dashboard).
5. ~~Subir `model_int8.onnx` no bucket `modelos`~~ ✅ resolvido: **GitHub Release `modelo-semantico-v1`** (bucket do Supabase nem foi usado).
6. ~~**Encoder do semântico**~~ ✅ **descartado no benchmark local (2026-09-27)**: `brazembed-pt-br` (o 2º candidato) deu 43,5% estrito zero-shot e 60,9% com 1-NN, contra 95,7% do léxico — e tf-idf sem transformer deu o mesmo. Só reabrir a conversa com **100+ rótulos reais**, e medir com `avaliar_embeddings.py`.
7. **Rotular 100+ relatos** — é o bloqueio de qualquer ganho de qualidade em triagem: o corpus de 30 é pequeno e não representativo do histórico (que é dominado por fixture de teste). A tela do **v3.5.0** é o instrumento: 🛠️ Painel do Administrador → 🏷️ Rótulo de severidade. Começar por ela e deixar rodando; a base exporta em CSV.
8. **Auditar a reconciliação "o mais grave vence"** (`secoes/ferramenta.py:669`, `max(sev_local, sev_ia)`) — ainda não medido. A tela do v3.5.0 dá o indicador de graça: a métrica "prioridade vista × rótulo" vs "léxico × rótulo" já separa o dano do léxico do dano da IA.

## Rituais de fim de sessão
- Atualizar este `MEMORIA.md` (e a skill, se mudar convenção).
- Manter `skills/ai-bug-triage/SKILL.md` e este arquivo coerentes.