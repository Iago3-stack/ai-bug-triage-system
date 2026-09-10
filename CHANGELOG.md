# Changelog

Todas as mudanças notáveis do **AI Bug Triage System** são registradas neste arquivo.

O formato é baseado no [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e segue o [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Não lançado]

### Adicionado
- **⚙️ Configurações em modal (v2.5.6)** — as configurações saíram do expander do sidebar e viraram um **modal "⚙️ Configurações"** (`st.dialog`), aberto por um botão na sidebar: concentra **🎨 Tema** (claro/escuro com marcador ativo e outline), **🔑 Jira** (expander azul persistente com reconectar/credenciais) e **🔔 Notificações** (expander roxo). Tudo com estilos próprios dentro do dialog nos **dois temas** (fundo `#111721`, inputs escuros, expanders coloridos). Trocar o tema ou reconectar o Jira **mantém o modal aberto** (padrão flag + reabertura, já que `st.rerun()` fecharia o dialog).
- **🔔 Notificações configuráveis por usuário (v2.5.6)** — cada usuário/empresa configura o **seu** Discord/e-mail/SMTP **diretamente no modal, só nesta sessão**: preenche webhook, destinatário, remetente/app-password, host e porta → "💾 Salvar notificações (sessão)". O override fica em memória; **nada é gravado no disco**. Sem override, vale o config do dono (secrets/`.env`). Status em tempo real ("✅ configurado" / "❌ sem webhook"), botões **Testar Discord** e **Testar e-mail** (sem nunca interromper o app) e **"↩️ Limpar meu config"** (volta ao do dono). O status é re-renderizado após cada ação para refletir o estado pós-clique no mesmo run.
- **🛡️ Botões "Testar" nunca derrubam o app (v2.5.6)** — os testadores de canal são **à prova de exceção de ponta a ponta**: `SMTP_PORT` inválido ou fora do range (1-65535) cai no padrão `587` (config TOML/.env pode trazer texto), e qualquer falha inesperada vira mensagem amigável na tela com o **tipo da exceção** — em vez de derrubar o app no Cloud (onde o detalhe é redigido).

### Corrigido
- **🎨 Cores sólidas persistentes (v2.5.6)** — os botões de exportação e os títulos-chave mantêm a **cor sólida com ou sem hover**: "📥 Baixar relatório (.md)" e os downloads de histórico (verde-escuro `#065f46`), o "💾 Salvar resolução" e o "📋 Exportar para Jira" mantêm azul/verde fixo (o hover do Streamlit deixava tudo acinzentado/nativo); no escuro, os títulos dos expanders **"🔑 Jira"**, **"📁 Histórico persistido"**, **"📈 Dashboard de QA"** e **"➕ Adicionar modelo próprio"** também ficam com a cor viva fixa em vez de clarear no hover.
- **🌙 Fundo sólido nos títulos dos expanders no escuro (v2.5.6)** — o Streamlit pintava o título (summary) de **quase-branco quando o expander ficava aberto** e de **cinza translúcido no hover** (estilo herdado do tema claro), escondendo o texto branco/colorido. Agora o fundo do título é **solido escuro `#0d1117`** em todos os estados (colapsado, hover e aberto) — só a cor do texto continua viva (títulos-chave `/` perfis de cor).
- **🎨 Gradiente no botão Automático (v2.5.6)** — o card **"🔄 Automático (Gemini → Groq)"** trocou o fundo cinza-ardósia por um **gradiente azul→vermelho entre as cores das duas marcas** (`#2E7CF6` → `#f55036`, 135°), nos **dois temas** (claro e escuro) — passa a mesma ideia do "fallback Gemini→Groq" só de olhar; hover mantém o gradiente (apenas clareia).
- **🌙 Cores dos botões do histórico voltam no escuro (v2.5.6)** — a regra do chevron (que deixa os botões secundários transparentes no modo escuro) apagava o fundo dos botões **dentro de expanders**: agora **"⬇️ Exportar JSON / CSV"**, **"📥 Baixar relatório desta triagem (.md)"** voltam verde-escuro `#065f46` e o **"💾 Salvar resolução"** verde `#059669` no fundo escuro (mesmo princípio da restauração das cores do Gemini/Groq); o **"💾 Adicionar modelo"** também recupera o laranja `#f97316`.
- **🔑 Botão "Salvar configuração (sessão)" verde fixo (v2.5.6)** — no sub-expander Jira do **modal de Configurações**, o botão que salva as credenciais ganhou **verde fixo `#059669`** (texto branco) e **não muda no hover**, tanto no tema claro quanto no escuro (vencendo a regra escura do chevron, que o deixava transparente/cinza lá).
- **🔴 Mensagem de preenchimento em tom vermelho leve (v2.5.6)** — se faltar e-mail, token ou chave do projeto, a mensagem **"Preencha e-mail, token e chave do projeto."** agora aparece em `st.error`: caixa com **tom vermelho leve** (fundo translúcido vermelho) e texto vermelho-escuro, nos dois temas.
- **✨ Icons 100% emoji (v2.5.5)** — o **sparkle oficial do Gemini** (SVG) não renderizava como estrela no Cloud: foi removido do projeto e trocado pelo emoji **✨️** no pill do hero e no título "Análise por IA (Gemini)" do resultado (o ícone correto pra quem usa). A balança do rodapé também saía cortada ("quebrada" no topo) como SVG: agora é o emoji **⚖️** — o escudo continua só no LGPD. No hero, a pill do Streamlit troca o foguete pela coroa **👑** e a pill "NLP PT" mantém a lâmpada 💡.

### Adicionado
- **✨ Icons do rodapé e do hero (v2.5.4)** — o **sparkle oficial do Gemini** agora também aparece (tamanho maior) no herói animado ao lado do 🤖⚡ (antes só na pill); e o link **"Licença MIT"** trocou o escudo pela **balança da justiça ⚖️** — o escudo fica só para o **LGPD · Proteção de Dados**, que é onde faz sentido.
- **🔔 Status do alerta dentro do app (v2.5.3)** — após uma triagem **CRÍTICA/ALTA**, o app mostra verde/amarelo o resultado real do envio: "✉️ e-mail enviado ✅ / FALHOU ❌", "🔔 Discord enviado ✅ / FALHOU ❌" — ou o aviso "nenhum canal configurado" com o caminho para os Secrets. Funciona também na triagem só com o motor local (sem IA).
- **🔒 LGPD no rodapé e no SECURITY.md (v2.5.2)** — o rodapé do app ganhou o link padrão **"LGPD · Proteção de Dados"** para a **ANPD** (`gov.br/anpd`); o `SECURITY.md` agora tem seção dedicada à **LGPD (Lei 13.709/2018)**: guardrails que mascararem e-mail/CPF/telefone/senha/chaves antes de qualquer envio, minimização (só o texto mascarado vai pra LLM), auditoria no Dashboard e o canal oficial da ANPD para titular/denúncias.
- **✉️ Alerta por e-mail (SMTP/Gmail) (v2.5.1)** — mesmo alerta de CRÍTICA/ALTA agora também chega por **e-mail**: perfeito pra quem não quer criar conta de Discord. Config (secrets `.env`/Cloud): `ALERTA_EMAIL_TO` (destinatário), `SMTP_USER` + `SMTP_PASS` (Gmail: seu e-mail + **app password** do Google) — e opcionalmente `SMTP_HOST`/`SMTP_PORT` (padrão `smtp.gmail.com:587`). Sem config, fica silencioso e nunca interrompe a triagem.
- **🔔 Alerta no Discord (v2.5.0)** — nova camada de notificação: quando uma triagem resulta em **CRÍTICA 🚨 ou ALTA 🚨**, o app envia um embed automático pro canal (prioridade, resumo e motor — local/IA) via webhook. É o "monitor de QA" do roadmap: o time recebe a mensagem sem abrir o app. Para ativar, crie um webhook no Discord e configure o segredo `DISCORD_WEBHOOK` (Streamlit Cloud: Secrets; local: `.env`). Sem webhook/em falha de rede, a triagem segue normalmente — a notificação **nunca** derruba o fluxo.
- **🔒 Auditoria dos guardrails (v2.5.0)** — o Dashboard agora mostra quantas triagens tiveram **credencial/PII mascarada** (métrica + coluna "🔒" na tabela de recentes) e um expander **"Por que mascaramos?"** que explica o motivo de cada tipo (e-mail/LGPD, CPF/fraude, token/GitHub, senha...). No aviso do relato, o motivo também aparece ("...e-mail (dado pessoal (LGPD)). A informação sensível foi mascarada e não será enviada...").

### Corrigido
- **🎨 Cores "foscas" de volta à vida (v2.5.0)** — a restauração do seletor nativo (v2.3.0 → v2.4.0) deixou os widgets com a paleta padrão do Streamlit. O tema nativo foi **fixado no light com a paleta VIVA da v2.3.0**: `primaryColor #25D366`, fundos `#FFF`/`#F4F6F8` e texto `#1D1D1F` — botões/accent do Streamlit voltam ao verde-WhatsApp, sem mexer no tema claro/escuro próprio do app.
- **🌗 Tema claro "lavado" no Cloud** — o tema nativo do Streamlit ficava **travado no Dark** no navegador do usuário (a preferência fica salva por URL; como o menu "⋮" está oculto, não dá pra desfazer). Como o app força o fundo claro (`#fff`) enquanto o texto default do Streamlit ficava branco, o resultado era **branco sobre branco** (Contate-me, badge Linux Mint etc. quase invisíveis). Agora o tema nativo é **fixado em `light`** no `.streamlit/config.toml` e o CSS do app ganhou uma **blindagem de contraste** (texto de markdown, headings, captions, métricas e header com cores escuras no claro) — que o tema escuro do app (via `body:has`) continua sobrescrevendo, como sempre.
- **🌗 Tema escuro "sumia" sozinho** — o `session_state` do Streamlit é **perda a perder** quando o WebSocket cai (reconexão/sessão nova, comum no Community Cloud), e só ele guardava a escolha. Agora o tema também vai na **URL** (`?tema=escuro`): um iframe com JS lê o parâmetro da URL e aplica o marcador `data-st-tema` no cliente (determinístico — o `st.query_params` do primeiro run às vezes chega vazio), e o clique no seletor atualiza a URL. Resultado: recarregar, reconectar ou abrir outra aba **mantém o tema escolhido**; só um `?tema=claro`/remoção do parâmetro volta ao padrão.

### Adicionado
- **🌙 Tema próprio Claro/Escuro (v2.4.0)** — seletor **☀️ Claro / 🌙 Escuro** no topo do sidebar, com paleta **nossa** repintando todo o app por `body:has([data-st-tema="escuro"])`: cabeçalho, sidebar, cards, campos, expanders, métricas, blocos de código, badges e hcards do histórico oscurecem de verdade (sem depender do tema nativo, que só cobre a interface do Streamlit e destorcía textos do sidebar). O menu "⋮" nativo volta a ficar oculto para não misturar temas. Textos/cards com cor fixa inline ganharam classes (`.campo-tit`, `.prio-final`, `.hero-sub`, `.hcard`, `h1.nome-site`) para serem sobrescritos no escuro. `st.session_state["tema"]` (padrão: claro). **A escolha persiste na URL (`?tema=escuro`) a partir da v2.4.1; o tema claro ganhou blindagem de contraste e o nativo é fixado em `light` na v2.4.2.**

### Corrigido
- **🌓 Tema Claro/Escuro/Sistema do Streamlit restaurado** — o menu principal "⋮" voltou a ficar visível (`#MainMenu` deixou de ser ocultado no CSS) e o bloco `[theme]` custom do `.streamlit/config.toml` foi removido. No Streamlit 1.62, um tema custom único **remove por completo** os radios de tema do menu (a seção só é renderizada com 2+ temas disponíveis); sem o `[theme]`, o seletor **Use system setting / Light / Dark** reaparece no "⋮" e funciona (validado: troca de claro para escuro em tempo real). Nota: sem `[theme]`, os widgets nativos voltam à paleta padrão do Streamlit (o restante do app segue com cores próprias via CSS customizado).

### Adicionado
- **⚖️ Link "Licença MIT" no rodapé** — o item deixou de ser texto estático e passou a abrir o arquivo `LICENSE` do repositório (`/blob/main/LICENSE`), mantendo o mesmo estilo dos demais links do rodapé (Repositório, Documentação, Perfil).
- **✨ Símbolos das marcas de IA** — o seletor de provedor virou **cards simples** com um `st.button` nativo por opção e emoji dentro do card: **✨ Gemini**, **✴️ Groq**, 🔄 Automático e ⭐ modelos próprios. O **título "Análise por IA"** do resultado segue mostrando o **símbolo oficial** do Google Gemini (sparkle da gstatic) e o logotipo "groq" (Wikimedia Commons, PD-textlogo) de quem respondeu, e o **hero** do site mantém a pill com o ícone original. Helper `_svg_gemini()`/`_svg_groq()` reutilizáveis.
- **➕ Modelo próprio (traga sua API)** — botão no sidebar para **adicionar um modelo de qualquer provedor** dentro do app: OpenAI-compatível (OpenAI/DeepSeek/endpoint local — `base_url` + chave + modelo, com retry automático sem JSON mode para servidores que não suportam) ou **modelo Gemini custom** (ex.: tier pago) com chave própria ou a `GEMINI_API_KEY` existente. O modelo vira mais uma opção ⭐ no seletor de provedor e o relatório mostra quem respondeu. **A chave fica só na sessão** (`st.session_state`) — nunca é gravada em disco/histórico, e some no próximo reload.
- **📈 Dashboard de QA completo** — versão super completa (119 testes no total):
  - **🛡️ Card "Saúde da suíte" (0–10)** no topo — combina taxa de normais, score médio, penaliza divergência IA vs. motor e bonifica uso de IA e resoluções registradas (`saude_suite()`).
  - **Gauge de % de CRÍTICAS/ALTAS** — barra de progresso logo abaixo dos cards.
  - **Filtro global por funcionalidade** — selectbox filtra severidade, volume, score médio e últimas triagens por uma funcionalidade (login, pagamento, etc.).
  - **Evolução do score médio por dia** — nova série temporal ao lado do volume.
  - **Top causas raiz via IA** — agrupadas por similaridade de texto, com barra horizontal.
  - **Comparativo IA vs. motor turbinado** — taxa de divergência (%) + data table com as últimas 10 divergências (Gravidade local vs. IA vs. prioridade final).
  - **Coluna IA com o provedor real** — a tabela de últimas triagens mostra `Gemini`/`Groq`/`sim` (o snapshot agora persiste `provedor_ia` além de `modelo_ia`).
- **📋 Botão "copiar chave pix" dentro do card de doação** — abaixo do QR Code, em linha própria, com tramitação via iframe (`components.html`) para o JavaScript funcionar. O **QR code mantém a chave com `+55`** (payload EMV/CRC válido) e o **botão copia sem o `+55`** (`pix.chave_copia()`), porque os apps de banco reconhecem o número e completam o DDI sozinhos — padrão de mercado.
- **Símbolo oficial do Pix no botão de copiar** — o 📋 deu lugar ao losango teal do Banco Central (SVG inline, `_svg_pix()`), que agora aparece nas duas ações: "Pagar com Pix via link" e "copiar chave pix" (a troca do rótulo pós-cópia usa um `span`, preservando o ícone). O título do card também ganhou **🤝 na outra ponta** — "`[símbolo Pix]` Apoie este projeto `🤝`".

### Corrigido
- **Logotipo "groq" nunca renderizava no app** — o path do wordmark estava com números inválidos (separadores ausentes nas fronteiras de literais Python em `_GROQ_WORDMARK_PATHS`), o que fazia o navegador descartar o SVG em silêncio (hero, título e cards). Corrigido o path; o wordmark agora aparece em todo o app.
- **Cards-botão do seletor** — simplificados para **um `st.button` nativo por opção** (sem sobreposição nem metades coladas): o emoji fica dentro do próprio card (**✨ Gemini**, **✴️ Groq**) e a seleção usa outline no card ativo, eliminando corte e "trava" de clique.
- **viewBox do símbolo Pix** — bbox real medido nos paths (x 535..613, y 27..104, 78×77 com margem de 4): o losango saía cortado à esquerda e pequeno; agora preenche a área do ícone com margem uniforme.

## [v2.3.0] - 2026-09-08

### Adicionado
- **Seletor de provedor de IA** (Automático → Gemini + fallback Groq · só Gemini · só Groq) com checkbox "🔮 Usar IA para esta triagem". O relatório mostra **qual provedor/modelo respondeu** (ex.: `Gemini · gemini-3.5-flash` ou `Groq · openai/gpt-oss-120b`), e a escolha é propagada também no fluxo RAG.
- **Fallback Groq com `openai/gpt-oss-120b`** — sucessor recomendado do Llama 3.3 70B no Groq (Llama de chat foi aposentado do tier grátis em 08/2026). Chave `GROQ_API_KEY` no `.env`/Secrets; modelo sobrescrevível via `GROQ_MODELO`.
- **💡 RAG aprende com a resolução** — agora dá para **registrar como o bug foi resolvido** logo após a triagem (widget "Registrar resolução") ou editando qualquer registro no histórico persistido. A resolução entra no contexto recuperado pelo RAG (`rag.montar_contexto`), então, em triagens futuras similares, o Gemini responde **"como foi resolvido da última vez"** com a solução real de cada caso (também visível no expander de histórico).
- **`registrar_resolucao()`** no facade `persistencia.py` e no `nuvem_supabase.py` (fetch + PATCH por id no payload) — com failover automático pra JSONL local.

## [v2.2.0] - 2026-09-08

### Adicionado
- **☕ Seção de doação no rodapé** — card "Apoie este projeto" lado a lado com o CTA de estrela do GitHub, com **QR Code Pix (BR Code) gerado 100% local** (`pix.py`: payload EMV + CRC16-CCITT + PNG base64), configurável via `PIX_KEY`/`PIX_NOME`/`PIX_CIDADE`/`PIX_COPIA`/`PIX_LINK` (prioridade `st.secrets` → `os.environ` → `.env`) — sem intermediários, sem taxas. Se `PIX_LINK` estiver definido, exibe botão de pagamento com valor fixo no lugar do QR.
- **`test_pix.py`** — 6 testes 100% offline (estrutura EMV, CRC-CCITT com vetor conhecido `29B1`, prioridade PIX_COPIA, link de pagamento, precedência env/file e data-URI do QR). **96 testes no total** — CI continua verde.
- **Micro-polimento de UI** — rodapé em 2 colunas (estrela centralizado + Pix à direita), textos de apoio reescritos para evitar trocas indevidas por tradução automática e legenda do QR como apelo open source.

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
