# Changelog

Todas as mudanças notáveis do **AI Bug Triage System** são registradas neste arquivo.

O formato é baseado no [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e segue o [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [v2.15.8] - 2026-09-16

### Alterado
- **🎁 Texto do Teste Premium (página Meu Plano)** — badge e frase agora dizem **"Teste Premium 7 dias"**: *"Você está no Teste Premium 7 dias — acesso completo liberado até esta data expirar. Depois disso, a conta volta ao Basic."*

## [v2.15.7] - 2026-09-15

### Corrigido
- **🔍 Título do card SEO agora é `<div>` em vez de `<h2>`** — o Streamlit sobrescreve/sanitiza a cor de `<h2>`, e foi por isso que o branco nunca pegava; o masthead ("Conheça o plano") usa `<div>` e funciona. O título passou a `<div role="heading">` branco (mesmo mecanismo que já dá certo).

## [v2.15.6] - 2026-09-15

### Corrigido
- **🔍 Título do card SEO em branco garantido** — cor `#ffffff!important` no `<h2>` (imune ao CSS do Streamlit que estava apagando o texto) + barra em gradiente abaixo do título, deixando a palavra-chave bem visível nos dois temas.

## [v2.15.5] - 2026-09-15

### Corrigido
- **🔍 Card SEO da Início mais visível e honesto** — título maior (25px, peso 900, com borda e sombra de texto para destacar no card) e a frase "sistema gratuito" corrigida: agora diz que o **Basic é grátis para começar** (o sistema tem plano Premium), sem prometer que tudo é gratuito.

## [v2.15.4] - 2026-09-15

### Adicionado
- **🔍 SEO na página Início** — bloco fixo no topo do conteúdo com título e descrição ricos em palavras-chave ("triagem de bugs com IA", "QA", "teste de software", "Gherkin", "JIRA/GitHub", "Gemini/Groq"). O Google indexa Streamlit apps via renderização server-side, então esse texto em `<h2>`/`<p>` passa a ser o que os buscadores capturam; aumenta as chances de aparecer em buscas como **"triagem de bug IA"** e **"QA"**.

### Alterado
- **🔎 Título da página (aba) com palavra-chave na frente** — `set_page_config` agora usa **"Triagem de bugs com IA para QA | Iago Nunes - AI Bug Triage System"** (ex-metabrado "Iago Nunes | IA & QA Portfolio"), que é o `<title>` que o Google mostra e lê primeiro.

## [v2.15.3] - 2026-09-15

### Adicionado
- **📸 Foto de perfil no celular** — o upload agora aceita **HEIC/HEIF** (iPhone) com recado amigável se o decodificador não estiver instalado, e ganhou um botão **câmera** (`st.camera_input`) para bater foto ou escolher da galeria direto no aparelho.
- **📦 Quadrado em "Meu Plano"** — as seções "Dados da sua conta", "Plano da conta", "Painel do responsável" e "Suporte" foram agrupadas dentro de uma caixa (borda arredondada, adapta ao tema claro/escuro).

### Alterado
- **💬 Botão do WhatsApp colado ao texto** — em "Fale direto com a gente pelo WhatsApp.", o botão (símbolo verde + "WhatsApp") agora aparece logo em seguida à frase, em vez de empurrado para a direita da página.

## [v2.15.2] - 2026-09-16

### Corrigido
- **🎨 Cores sólidas nos botões do Painel do Administrador, sem hover, nos dois temas** — cada ação com sua cor fixa: ⭐ **Ativar Premium** verde, 🎁 **Dar teste 7 dias** âmbar, 🔓 **Voltar a Basic** cinza-ardósia. Estilo via marcadores `marca-dono-*`; o hover não muda a cor (padrão já usado nos botões de plano).

## [v2.15.1] - 2026-09-16

### Adicionado
- **🎁 6º badge na página Início — "Teste Premium 7 dias grátis"**: a fileira de recursos (Triagem NLP, Causas raiz, RAG, Alertas, Histórico) agora destaca também o **teste de 7 dias do Premium**, iluminado para qualquer plano. Cosmético (sem mudança de lógica).

## [v2.15.0] - 2026-09-15

### Adicionado
- **🛰️ Pilar 3 de automação — webhook de CI** (`webhook.py`): micro-servidor HTTP **100% stdlib** que recebe `POST /webhook/falha` com a evidência de uma execução que falhou (GitHub Actions, GitLab, cron do newman/Playwright...) e responde com o **relato já estruturado** (Playwright/Postman/Pilar 1 + relato em markdown). Proteção opcional por `WEBHOOK_TOKEN` (header `X-Webhook-Token`), IA opcional (`ia:true`/`WEBHOOK_IA=1`, `analisar_llm`), persistência opcional (`WEBHOOK_PERSISTE=1`), teto de 200 KB, `/health`, e nunca derruba (erros viram campos `aviso_*`). Roda fora do Streamlit: `python webhook.py --porta 8080`. 21 testes (**400 no total**, todos offline, incluindo transporte HTTP real na porta 0).
- **🤖 Action "CI - Reportar Falha ao Webhook"** (`.github/workflows/ci-falhas.yml`): quando o workflow **"CI - Testes (pytest)"** falha, monta a evidência (workflow/run/commit/jobs/passos que falharam) e envia `POST` para o secret `WEBHOOK_URL` (com `WEBHOOK_TOKEN` se houver). Sem `WEBHOOK_URL` configurada, apenas avisa e pula.
- **📄 `docs/06-webhook.md`** — guia do webhook: payload, resposta, envs e setup da action.

## [v2.14.0] - 2026-09-15

### Adicionado
- **📋📮 Pilar 2 de automação — adaptadores Playwright / Postman·newman** (`adaptadores.py`): a mesma caixa "📋 Colar falha bruta" agora **reconhece a saída dessas ferramentas** e extrai o relato com o léxico próprio de cada uma. **Playwright**: nome do teste, erro de asserção (`Error: expect(...)`), **Expected/Received** e arquivo:linha (texto do terminal ou JSON do relator). **Postman/newman**: método + URL, **HTTP status esperado × recebido**, detalhe da asserção e **erro do corpo JSON**. O relato ganha as linhas **"Ferramenta de origem"** e **"Requisição"**. Se a evidência não bater com nenhum formato, o parser genérico (Pilar 1) assume — 100% local e determinístico. 16 testes novos (**379 no total**, todos offline).

### Corrigido
- **🔍 Alertas agora revelam o motivo real do e-mail falho** — `notificacoes.py` guarda o último erro SMTP (`_ULTIMO_ERRO_EMAIL`/`ultimo_erro_email()`), `_enviar_email` captura `TipoErro: msg`, **"✉️ Testar e-mail"** e o alerta no painel mostram o detalhe exato (ex.: `SMTPAuthenticationError: (535...)`, timeout, porta errada) em vez de só "FALHOU ❌". +1 teste (**33 de notificações**).

## [v2.13.0] - 2026-09-15

### Adicionado
- **📋 Pilar 1 de automação — "Colar falha"** (`colar_falha.py`): na página Ferramenta, um expander **"📋 Colar falha bruta: preencher o relato automaticamente"** — cole um **stack trace, log de erro ou a mensagem do usuário** e o app extrai **título, categoria (na mesma taxonomia da IA), módulo, versão, severidade prévia (via motor local), erro principal, local do frame e passos para reproduzir**, preenchendo o relato na caixa de triagem para você revisar. 100% local e determinístico (não gasta token de LLM, funciona sem internet); reconhece traces **Python, Java, JS/TS, C#/.NET, Go e Ruby** e ignora datas ("2026.09") na detecção de versão. 13 testes novos (**362 no total**, todos offline).

### Corrigido
- **Painel do Administrador explora o 400 PGRST204** — quando "🎁 Dar teste 7 dias" falha por a coluna `teste_ate` não estar no schema cache do PostgREST, o app agora mostra o passo-a-passo exato (rodar o `alter table ... teste_ate timestamptz;` + `NOTIFY pgrst, 'reload schema';` no SQL Editor), em vez de "Falha (offline/Supabase)". Novo probe `nuvem_supabase.teste_disponivel()` confirma se o PostgREST enxerga a coluna (só rodado no caminho de erro, para não adicionar latência). 3 testes novos no painel (**362 no total**). Nenhuma ação manual: já validado contra o projeto real (o teste 7 dias passou a gravar `teste_ate` na nuvem).

## [v2.12.0] - 2026-09-15

### Adicionado
- **🧠 RAG híbrido (retrieval evoluído — Passo A do plano de IA)** — o histórico consultado pelo Gemini deixa de usar Jaccard simples e passa a usar **BM25 com IDF sobre o corpus**, com o texto de cada registro **ponderado por campo** (resumo tem peso duplo, depois descrição, causa raiz e resolução), **expansão de sinônimos técnicos** em PT-BR (crash/travou/congelou, login/autenticar, página/tela, botão/clicar, pagamento/checkout, download/baixar, erro/falha, lento/performance…) e **ponderação por recência** (`1/(1+0.02×idade_dias)`) e **resolução registrada** (×1.10). Tudo offline e determinístico; os antigos `_tokens`/`_jaccard` foram mantidos.
- **🔎 Rerank vetorial híbrido (Passo B)** — por padrão fora dos testes (`RAG_VETOR=auto/on/off`), embeddings Gemini (`text-embedding-004`) buscam os candidatos do BM25 e **reordenam** com `0.6×cosseno + 0.4×BM25` (normalizados). Vetores ficam em cache de RAM + `data/embeddings.jsonl` (tabela de visto, sem banco vetorial), com limite de 300 embeddings novos por consulta; se não há chave/rede, o RAG **cai silencioso** para o lexical — nunca quebra o app.
- **Citações honestas no prompt** — o `PROMPT_RAG` agora manda o Gemini citar **apenas** os ids que aparecem no histórico recuperado e **sinalizar caso novo** (sem nenhum registro parecido, não inventa: `ja_aconteceu=false` e `registros_similar=[]`). O contexto recuperado também inclui a **categoria** do registro quando existe.
- **UI** — caption do RAG na ferramenta atualizada ("retrieval híbrido local — BM25 + vetores, sinônimos e recência"; nada é enviado além do relato e dos registros similares). 14 testes novos (**346 no total**, todos offline — vetores mockados).

### Observações
- O RAG continua **Premium** (plano free consulta o LLM direto, sem histórico) — a mudança torna a análise dos assinantes muito mais precisa, não muda o gating.
- **Nenhuma ação manual necessária** no Supabase. Se quiser vetores desde o 1º dia, deixe `GEMINI_API_KEY` configurada (já usada pelo LLM) e remova/ignore a variável `RAG_VETOR=off`; o cache de vetores é populado automaticamente nas primeiras triagens.

## [v2.11.0] - 2026-09-15

### Adicionado
- **🛠️ Painel do Dono (Passo 6 SaaS)** — página **restrita ao dono** (`ADMIN_EMAIL`): o dono vê o app inteiro no modo "astra", sem precisar cruzar tabelas no Supabase. A página antiga não é listada para mais ninguém e aparece como uma página própria no menu do dono.
- **Métricas gerais** — cards com total de contas, Premium, em teste e Basic + aviso de pagamentos aguardando e estornos pendentes (tratados no painel do responsável dentro de Meu Plano).
- **Lista de contas** — para cada conta (com nome/perfil e último login): botões **⭐ Ativar Premium**, **🎁 Dar teste 7 dias** e **🔓 Voltar a Basic**. As ações valem de imediato no plano do usuário.
- **📇 Registro automático de contas** — nova tabela `usuarios` (uid, email, criado_em, ultimo_login): a cada login/renovação a conta é anotada (best-effort, nunca quebra o login). Sem ela, o painel simplesmente não tem contas a listar.
- **🎁 Teste Premium com validade** — nova coluna `teste_ate` em `planos_usuario`: o teste conta como Premium até a data expirar (então volta a Basic sozinho). O usuário em teste vê "🎁 Teste Premium" no Meu Plano; pagar (ou o dono voltar a Basic) encerra o teste.
- **Módulos** — `admin.py` (`email_logado`/`eh_dono`), `secoes/painel_dono.py` e helpers em `nuvem_supabase.py`/`plano.py` (`teste_premium_restante`, `definir_trial`, `definir_plano_manual`, `carregar_usuarios`/`carregar_todos_planos`/`carregar_todos_perfis`); 34 testes novos (**332 no total**).

### Corrigido
- **Painel não quebra se a coluna/tabela ainda não existe no Supabase** — o 400 do PostgREST ao selecionar `teste_ate` (ALTER TABLE pendente) derrubava a página inteira. Agora o painel carrega **cada fonte isolada** (usuários, planos, perfis, cobranças) — a que falhar vira lista vazia e as demais seguem; `carregar_todos_planos` refaz o select **sem** `teste_ate` quando a coluna não existe, `carregar_teste_banco` vira `None` no erro e o PATCH de limpeza do teste é best-effort (o plano é salvo mesmo se a coluna faltar). O painel funciona já; o eixo de testes só liga depois do SQL rodado.

### Observações
- **Ação necessária:** rode no SQL Editor do Supabase as duas instruções do cabeçalho de `nuvem_supabase.py` — criar a tabela `usuarios` (3 policies anon) e `alter table planos_usuario add column if not exists teste_ate timestamptz;`.
- Configure `ADMIN_EMAIL` (secrets da Cloud) para ativar o painel — sem ele, ninguém é dono e o pedido não aparece.

## [v2.10.0] - 2026-09-15

### Adicionado
- **🐙 Issues no repositório do próprio usuário/empresa** — no modal ⚙️ Configurações, cada conta configura um **Personal Access Token** (escopo **Issues: write** — fine-grained ou clássico `repo`/`public_repo`) e um **repositório `dono/repo`**. A partir daí o botão da triagem passa de "link que abre o repo do dev" para **criar a issue de verdade na SUA conta** via `POST https://api.github.com/repos/{dono}/{repo}/issues` (URL correta da API — a página `github.com/.../issues` não cria nada). A issue chega com título, relatório em Markdown e o **link direto** de volta.
- **Sem labels obrigatórios** — diferente do exemplo inicial (que quebra com 422 quando a label `bug`/`ai-triaged` não existe no repo de destino), a issue é criada sem labels para funcionar em qualquer repositório.
- **Segurança**: token e repositório ficam **só na sessão** (`st.session_state`), nunca em disco nem no banco — cada visitante tem o seu e não há vazamento entre contas (o banco tem políticas anon permissivas). Sem config, o botão mantém o comportamento antigo (abre o repo da ferramenta) com aviso de como configurar.
- **Módulo `github_client.py`** — `normalizar_repo` (aceita URL completa, `.git`, espaços), `configurado` (exige token + `dono/repo`) e `criar_issue` com mensagens amigáveis para 401/403/404; 18 testes novos (**298 no total**).

## [v2.9.0] - 2026-09-15

### Adicionado
- **👤 Perfil do usuário (Passo 5 SaaS)** — bolinha no topo (canto superior, acima do chip do e-mail) com **foto** ou **iniciais** em gradiente; clique abre um **modal** (`@st.dialog`) para editar nome de exibição, empresa/cargo, **fuso horário** e **avatar** (upload JPG/PNG/WebP redimensionado para 160px via Pillow). Salvo na nuvem (tabela nova `perfis_usuario`) com fallback JSONL local (`data/perfis.jsonl`).
- **Chip mostra nome E e-mail** — quando o nome é preenchido, o chip exibe `👤 Nome` com o e-mail logo abaixo; sem nome, mantém apenas o e-mail.
- **Relatório PDF assinado** — o relatório de triagem agora grava o **nome do perfil** em "Relatório gerado por …" (sem perfil, omite a linha).
- **Módulo `perfil.py`** — `carregar`/`salvar` (nuvem → JSONL), `nome_exibicao` (nome → empresa → parte do e-mail), validação de fuso (inválido cai em América/São_Paulo) e iniciais da bolinha; `pillow` entrou no `requirements.txt`; 16 testes novos (**280 no total**).

### Observações
- **Ação necessária:** crie a tabela `perfis_usuario` no SQL Editor do Supabase (script no cabeçalho de `nuvem_supabase.py`) — há 3 policies anon (insert/select/update), igual às demais tabelas.
- A foto é armazenada como **base64 compacto** na própria tabela (sem bucket do Supabase), então o mesmo perfil vale na Cloud e no app local — sem infra extra.

## [v2.8.1] - 2026-09-15

### Corrigido
- **Novo cadastro já nascia Premium** — usuário logado com nuvem ativa e sem linha no banco agora **sempre começa em Basic** (`free`); o env legado `PLANO` só vale offline/sem login. Isso também corrigia o **QR/copia-e-cola nunca aparecer**: o checkout só era mostrado quando o plano era `free`, e como todos "eram" Premium, o fluxo de assinatura ficava inacessível.
- **Checkout agora aparece sempre que há cobrança aberta** — independentemente do plano atual, se existe um pedido `aguardando` o QR + copia-e-cola + "Já paguei" ficam visíveis.
- **E-mail de pagamento com template de triagem** — criada `notificar_evento()` (e-mail + Discord **neutros**, sem "Relato:/Motor:"); o aviso ao responsável (nova cobrança, "Já paguei", estorno) usa essa função.

### Adicionado
- **`PIX_COPIA_PLANO`** — o payload da assinatura agora **prioriza** um copia-e-cola dedicado (ex.: código fixo gerado no seu Itaú, que já carrega o valor R$ 19,99 embutido); depois `PIX_COPIA` (doação geral) e por fim o payload padrão da chave.
- 9 testes novos (novo usuário = Basic mesmo com env `PLANO=pago`, payload `PIX_COPIA_PLANO`, avisos genéricos de evento) — **264 no total**.

## [v2.8.0] - 2026-09-15

### Adicionado
- **💳 Cobrança própria via Pix ("nosso Stripe" — Passo 4)** — o Premium passa a ser **R$ 19,99/mês** com pagamento 100% Pix, sem gateway nem taxa: o usuário assina, o app gera uma cobrança `aguardando` com **QR Pix + copia-e-cola**, o usuário paga no banco e clica **"✅ Já paguei"**; o **responsável** (e-mail configurado em `ADMIN_EMAIL`) confirma no painel do Meu Plano e o plano vira `pago`. Estorno controlado: o usuário solicita, o responsável devolve o valor via Pix e marca o pedido como `estornado` (o plano volta a Basic). Tudo persistent em `solicitacoes_pagamento` no Supabase (com fallback JSONL local em `data/cobrancas.jsonl`).
- **🎛️ Painel do responsável no Meu Plano** — fila de pagamentos aguardando confirmação (com botões confirmar/cancelar) e lista de estornos solicitados (com botão "marcar como devolvido"). Dispara avisos por e-mail/Discord (`notificacoes.py`) quando algo exige ação.
- **💬 Suporte por WhatsApp** — link direto (`wa.me`) configurável por env `WHATSAPP_NUMERO`, zero custo, para dúvidas sobre plano, pagamento e estorno.
- **Módulo `pixbilling.py`** — preço configurável por env `PLANO_PRECO` (padrão `19.99`), geração de cobrança, confirmação (ativa Premium no banco), cancelamento e ciclo de estorno; 13 testes novos.

## [v2.7.0] - 2026-09-14

### Adicionado
- **💼 Página "Meu Plano" (SaaS — Passo 3)** — a página mostra o plano **da conta logada** (Basic ou Premium), traz um comparativo Basic × Premium, um bloco de auto-atendimento para escolher o plano (salvo no banco `planos_usuario` no Supabase; sem Stripe ainda, que fica para o Passo 4) e o botão de migração que **reivindica os registros legados "global"** (pré-isolamento) para o seu usuário.
- **Plano por usuário no banco** — `plano.py` agora resolve o plano na ordem: (1) conta logada → tabela `planos_usuario` no Supabase via upsert; (2) fallback `PLANO` (env), usado offline/em testes. O `tenant_id` dos novos registros passa a ser o **UID da conta logada**, isolando dados entre usuários.
- **Migração de registros legados** — `migrar_tenant_global(uid)` e `contar_legados_globais()` reetiquetam os registros antigos com tenant `global`/"sem tenant" para o usuário que reivindicar (nuvem primeiro, senão JSONL local).

### Corrigido
- **"Sombra"/fantasma do login e do expander de histórico** — a ponte de sessão era (des)montada a cada run, causando churn no DOM do Streamlit e artefatos repetidos (ex.: "Histórico persistido" 3× e sombra do formulário na tela de login). A ponte agora é **sempre montada** (comando `ocioso` quando não há pendência) e o JS ignora os runs intermediários.
- **Sair agora é realmente definitivo** — além de limpar a sessão, o botão Sair **revoga o token no Supabase** (`sair_da_conta`) e o guard impede um re-login automático na mesma sessão; resposta assertiva e instantânea.
- **Login com layout prioritário** — o formulário (e-mail/senha) sempre fica acima das colunas de informação, mesmo em telas baixas.

### Alterado
- **Template de "Meu Plano" atualizado no Início** — o aviso de que o plano era por "variável de ambiente no deploy" virou "plano **por usuário** (página 💼 Meu Plano)".

## [v2.6.26] - 2026-09-14

### Adicionado
- **📄 Download do relatório em PDF** — exportação em PDF nativo (A4) com `fpdf2` e fontes DejaVu embutidas, além do Markdown já existente.

### Corrigido
- **F5/Ctrl+R deslogava (cauda longa)** — a escrita da sessão agora é uma **pendência enfileirada** (`sessao_persist.salvar/limpar` só marcam o que falta gravar) e uma **ponte persistente** renderizada em todos os runs do `home.py` mantém o componente vivo até o iframe **confirmar** a escrita. Antes, o `salvar()` renderizava dentro da ação de login seguida de `st.rerun()`, e o rerun descartava a árvore antes de o payload chegar ao `localStorage`/cookie — a sessão "apanhava" a pista e vinha vazia no reload.
- **IA: resposta JSON truncada do Gemini quebrava a análise** — `_reparar_json_truncado()` fecha strings/arrays/chaves cortados e só então propaga o erro; a triagem não perde a causa raiz.
- **Dashboard: `NaN` em divergente quebrava a máscara** — `convergente/divergente` tolerando NaN; erro de "modelo não encontrado" separado do fluxo.
- **Recarregar sem sessão agora é honesto** — em vez de deslogar em silêncio, o app mostra "Sua sessão expirou ou foi perdida ao recarregar a página. Faça login novamente."

### Alterado
- **✏️ Modelo próprio renomeável e editável** — depois de adicionar, dá para renomear o modelo (ex.: "mini2") e ajustar a configuração; a lista de provedores ⭐ reflete o nome novo.
- **Erros do provedor traduzidos para pt-BR amigável** — 503/429/chave inválida viram mensagens úteis em vez de rastreio.
- **Rótulo/placeholder da API Key do modelo próprio** — avisa que sem chave usa a `GEMINI_API_KEY` do Sistema, com exemplo `AQ.Ab...`, e reforça que a sua chave fica só na sessão.

### Corrigido
- **Erro 429 "email rate limit exceeded" no cadastro (v2.6.25)** — a resposta `over_email_send_rate_limit` do Supabase agora é traduzida corretamente: avisa que o limite de e-mails de confirmação foi atingido (aguardar até 1h ou configurar SMTP próprio), em vez da mensagem genérica de "muitas tentativas".
- **Botão "⚙️ Configurações" não abria o dialog (v2.6.24)** — `abrir_configuracoes()` só *definia* a função do dialog interno mas nunca a chamava; o clique simplesmente não fazia nada. Agora o dialog é invocado no final da função.
- **Botão ">>" (recolher sidebar) oculto no desktop (v2.6.23)** — com a sidebar forçada aberta em ≥769px (v2.6.20), o botão de recolher vira controle morto. Agora ele é escondido via `display: none` no desktop; no mobile (hambúrguer overlay) continua visível e funcional.
- **Card CTA com fundo vazando para a página inteira (v2.6.22)** — o seletor `:has(.marca-cta)` pintava todos os blocos-ancestrais que continham o card ("página toda envolvida nas cores"). Agora o fundo é aplicado **somente ao bloco do container border** (o único cujo filho é o leiaute do card), via seletor com negação de filhos fora do card.
- **Aviso "st.rerun() within a callback is a no-op" (v2.6.22)** — os botões do CTA chamavam `st.switch_page` dentro do `on_click` (callback), o que gerava o aviso. Trocado para o padrão `if st.button(...): st.switch_page(...)` (fluxo principal).

### Corrigido
- **Botões de volta para dentro do card CTA (v2.6.21)** — os botões "Ir para a Ferramenta" e "Ver Dashboard de QA" voltaram para dentro do card escuro do Início, agora como `st.button` + `st.switch_page` (navegação nativa; sem as âncoras que fugiam do iframe) e com os mesmos gradientes de antes (vermelho/verde).

### Corrigido
- **Sidebar "aparece e some" no desktop (v2.6.20)** — em larguras ~768-820px o Streamlit 1.62 flutua entre o modo desktop e o modo hambúrguer e o sidebar colapsa sozinho. Agora ≥769px o sidebar fica **forçado aberto** (300px fixos, sem transição de colapso). <769px segue o modo hambúrguer (celular inalterado).

### Corrigido
- **CTA do Início: sidebar "sumia" ao clicar nos botões (v2.6.19)** — os botões eram âncoras cruas (`<a href="/dashboard?tema=…">`) que **fugiam do iframe** do Cloud: em caminho externo, o app respondia `303 → auth` e renderizava página vazia sem sidebar ("tenta aparecer e some"). Troquei por `st.page_link` nativo (navegação SPA que permanece dentro do app; tema preservado via session_state). Validado: clique mantém sidebar aberta e leva à tela de login.
- **Import circular (v2.6.19)** — `secoes/inicio` passou a importar `roteador`, que já importava `inicio`; movido para dentro de `render()` (lazy).

### Corrigido
- **Login: erro 429 traduzido (v2.6.18)** — o Supabase Auth devolve 429 (rate limit OU "Email signups are disabled for this project") com corpo usando `msg`/`error_code` (não `error_description`). O parser agora lê esses campos e mostra mensagem clara: "Cadastro por e-mail está desativado… ative 'Enable email signups'" ou "Muitas tentativas… aguarde ~1 minuto". Antes caía em "Falha inesperada (código 429)" sem explicação.

### Corrigido
- **Sidebar que "sumia" (v2.6.17)** — o Streamlit 1.62 mantém o botão de recolher/expandir a sidebar (`stSidebarCollapseButton`) com `visibility: hidden` no CSS padrão. Se a sidebar recolhia (re-render ou no iframe do Community Cloud), não havia **como expandi-la de volta** — resultado: "a sidebar apareceu com a setinha e sumiu". Agora esse botão é forçado sempre visível (`visibility: visible !important`), e o seletor que escondia o menu principal foi trocado de `#MainMenu` (genérico, antigo) para `[data-testid="stMainMenuButton"]` (mais preciso). Comportamento preservado: desktop abre com a sidebar expandida; ≤767px a sidebar recolhe e o menu hambúrguer assume (como no celular, que já funcionava).

### Adicionado
- **🔐 Login real (Supabase Auth) — passo 2 do SaaS (v2.6.16)** — novo módulo `auth_supabase.py` (GoTrue via REST, sem dependências novas; reusa as credenciais `SUPABASE_URL`/`SUPABASE_ANON_KEY` da persistência). Fluxos de **cadastro** (com confirmação de e-mail) e **login** (e-mail + senha, token na sessão), com mensagens amigáveis em pt-BR (credenciais inválidas, e-mail não confirmado, e-mail já cadastrado). Nova página `secoes/login.py`: **Início continua público**, enquanto **Ferramenta e Dashboard exigem login** quando o Supabase está configurado. Sem configuração (ex.: ambiente local sem secrets), o app permanece integralmente aberto — comportamento anterior. Sidebar ganhou **status de usuário** (👤 e-mail + botão "Sair") quando logado, ou aviso "Faça login" quando não. 17 testes novos (187 no total, todos verdes). **Validação real do fluxo de login fica para depois do deploy** (o Supabase local não tem credenciais). Antes de publicar: manter `SUPABASE_URL`/`SUPABASE_ANON_KEY` e habilitar Authentication -> Providers -> Email no painel.

### Adicionado
- **📖 Guia do Dashboard unificado (v2.6.15)** — removido o expander duplicado ("📖 Como ler este dashboard") da página Dashboard; como o `render_dashboard` já exibia o guia completo lá dentro (e é reutilizado na página **Ferramenta**), o expander foi **renomeado para "📖 Como ler este Dashboard — Guia Completo"** e virou o único lugar do guia nas duas páginas. Na página Dashboard agora há **1 único expander de guia** (além de "Por que mascaramos?").

### Adicionado
- **🎯 Botões do CTA dentro do card (v2.6.14)** — os links "🚀 Ir para a Ferramenta" e "📈 Ver Dashboard de QA" foram **embutidos no card "🤖 Pronto para triar bugs?"** (hoje um bloco único via `st.html`), com **cores de destaque** estilo Gemini/Groq: vermelho-rosa (`#e11d48→#db2777`) e verde-água (`#0d9488→#25D366`). No desktop ficam **lado a lado dentro do card**; no mobile empilham sozinhos (flex-wrap) sem vazar. A navegação é **na mesma aba**, preservando o tema (`/triagem?tema=escuro`). Bônus técnico: `st.html` não reescreve os links com `target="_blank"` como o markdown faz.

### Adicionado
- **🐙 Ícone do GitHub nos botões "Dar estrela" (v2.6.13)** — os botões **"Dar estrela no GitHub"** (sidebar e rodapé) agora exibem o **ícone oficial do GitHub (octocat)** ao lado do texto, o mesmo já usado nas colunas "Repositório" e "Perfil" do rodapé. No sidebar o botão virou flex com ícone centralizado à esquerda do texto.

### Adicionado
- **🔘 Botões do CTA lado a lado (v2.6.12)** — no card "🤖 Pronto para triar bugs?", os links **"🚀 Ir para a Ferramenta"** e **"📈 Ver Dashboard de QA"** ficam agora **emparelhados na mesma linha** (2 colunas) em vez de um embaixo do outro. No mobile, em telas estreitas, voltam a empilhar automaticamente (cada um em largura total) para não apertar o texto.

### Adicionado
- **🗂️ App multi-página via `st.navigation` (v2.6.11)** — o app deixou de ser um `home.py` monolítico e virou um **roteador de páginas**: `Início` (default), `Triagem de Bugs` e `Dashboard QA`, com menu nativo na sidebar e URLs próprias (`/inicio`, `/triagem`, `/dashboard`). O código foi fatiado em módulos comuns (`ui_tema.py` — tema claro/escuro + CSS global + bootstrap; `ui_comum.py` — versão, Pix, modal de configurações, sidebar e rodapé) e páginas (`secoes/inicio.py`, `secoes/ferramenta.py`, `secoes/dashboard_pagina.py`). Zero mudança visual/estrutural: masthead, hero, Sobre Mim, CTA ("Ir para a Ferramenta" / "Ver Dashboard de QA" agora via `st.page_link`) e dashboard idênticos em desktop e mobile, nos dois temas. (Passo 1 do caminho SaaS: próximo vem **login** e o plano vindo da assinatura.)

### Adicionado
- **📚 Gemini → RAG no hero (v2.6.10)** — no card animado, a pill "✨️ Gemini" virou **"📚 RAG"** (roxo) e o marquee trocou `Gemini` por `RAG` ("QA • IA • NLP • RAG • Streamlit • Python • Linux").

### Adicionado
- **📱 Sidebar de volta no mobile (v2.6.9)** — em telas < 768 px a barra nativa do Streamlit **reaparece** (com o hambúrguer) e o masthead desce para logo abaixo dela (sem margem negativa). Antes o header ficava oculto em qualquer largura e o menu da sidebar era inalcançável no celular. No desktop nada muda (header continua oculto, masthead no topo).

### Adicionado
- **✏️ Copy do subtítulo da ferramenta (v2.6.8)** — novo texto de valor: "Triagem automática de bugs com NLP + IA: técnico, emocional e com plano de ação em segundos." (antes: "Esta ferramenta demonstra o uso de NLP para automatizar..."). Mais direto e orientado a benefício.

### Adicionado
- **📐 "Sobre Mim" full-width (v2.6.7)** — removidas as colunas `esq, centro` que deixavam um vão à esquerda; o card agora ocupa **100% da largura** e fica **rentre ao divisor e ao título "🤖 Agente de Triagem e Documentação de Bugs 2026"** (gap 27 px, sem espaços laterais, sem overflow no mobile).

### Adicionado
- **➡️ Hero full-width (v2.6.6)** — o card do hero deixou de ter `max-width: 640px` e agora **ocupa 100% da largura da coluna/da tela**: no desktop acompanha as bordas (rentre à linha de cima do cabeçalho) e no celular se ajusta à largura da tela sem vazamento horizontal (validado em 390 px).

### Adicionado
- **🦸 Card do perfil → Hero no cabeçalho (v2.6.5)** — o card "🚀 Construo automação de QA... / 📍 São Luís" foi **removido** (conteúdo já citado no Sobre Mim e no hero) e o **hero animado "QA Automation + IA"** passou a ocupar o lugar dele, ao lado direito, logo abaixo dos nome. O cabeçalho ficou: foto (esquerda) + nome + hero.

### Adicionado
- **🧩 Card "Sobre Mim" ampliado (v2.6.4)** — o conteúdo do antigo card da UNIASSELVI foi **integrado ao card "Sobre Mim"** numa seção "🎓 Formação &amp; Stack", com **menção explícita ao SaaS** (planos Basic/Premium por variável de ambiente, RAG, comparativo IA×local, multi-canal). O card único agora é um bloco de perfil completo. A linha divisória ficou **entre o card e o título "🤖 Agente de Triagem e Documentação de Bugs 2026"**.

### Adicionado
- **🧹 Cabeçalho reorganizado + animação removida (v2.6.3)** — a animação de digitação ("Bem-vindo ao meu site! / Informações sobre mim e meus projetos / QA+IA no Lab Hack28") e a imagem-cápsula foram **removidas**. O card "🚀 Construo automação de QA com IA... / 📍 São Luís" subiu para o **lado direito, logo abaixo do nome**, formando um cabeçalho de perfil compacto; a foto permanece à esquerda.

### Adicionado
- **🏷️ Planos renomeados: Grátis → Basic e Pago → Premium (v2.6.2)** — toda a copy visível do app (badge do masthead, frases, tabela "💼 Comparar planos — Basic × Premium" e captions do histórico/dashboard) agora usa **Basic × Premium**. Os nomes internos (`PLANO = "free"|"pago"`, `plano.pago()`) e o env de deploy seguem intactos — só o discurso comercial mudou.

### Adicionado
- **🧭 Masthead mais alto e colado no topo (v2.6.1)** — a barra nativa do Streamlit (`stHeader`) é ocultada e o card "Conheça o plano" sobe para **6px do topo**, preenchendo o espaço antes vazio, com card **mais alto** (padding 30px/34px, título 26px, textos 16px). O alinhamento é igual nos **dois temas** (`margin-top` negativo por tema para compensar containers zero-altura). O conteúdo seguinte (cabeçalho) não colide.

### Adicionado
- **💼 Masthead "Conheça o plano" (v2.6.0)** — card fixo acima do nome do site ("rodapé superior"): badge do plano atual (**🔓 Grátis** / **⭐ Pago**, lido de `PLANO`), frase-resumo, pills dos recursos bloqueados/liberados e expander **"💼 Comparar planos — Grátis × Pago"** com a tabela completa por plano (IA/LLM, RAG, causas raiz, comparativo IA×local, histórico, canais de alerta). O card fica visível ao visitante em qualquer tema e sumariza de forma explícita o que cada plano libera.

### Adicionado
- **⚙️ Configurações em modal (v2.5.6)** — as configurações saíram do expander do sidebar e viraram um **modal "⚙️ Configurações"** (`st.dialog`), aberto por um botão na sidebar: concentra **🎨 Tema** (claro/escuro com marcador ativo e outline), **🔑 Jira** (expander azul persistente com reconectar/credenciais) e **🔔 Notificações** (expander roxo). Tudo com estilos próprios dentro do dialog nos **dois temas** (fundo `#111721`, inputs escuros, expanders coloridos). Trocar o tema ou reconectar o Jira **mantém o modal aberto** (padrão flag + reabertura, já que `st.rerun()` fecharia o dialog).
- **🔔 Notificações configuráveis por usuário (v2.5.6)** — cada usuário/empresa configura o **seu** Discord/e-mail/SMTP **diretamente no modal, só nesta sessão**: preenche webhook, destinatário, remetente/app-password, host e porta → "💾 Salvar notificações (sessão)". O override fica em memória; **nada é gravado no disco**. Sem override, vale o config do dono (secrets/`.env`). Status em tempo real ("✅ configurado" / "❌ sem webhook"), botões **Testar Discord** e **Testar e-mail** (sem nunca interromper o app) e **"↩️ Limpar meu config"** (volta ao do dono). O status é re-renderizado após cada ação para refletir o estado pós-clique no mesmo run.
- **🛡️ Botões "Testar" nunca derrubam o app (v2.5.6)** — os testadores de canal são **à prova de exceção de ponta a ponta**: `SMTP_PORT` inválido ou fora do range (1-65535) cai no padrão `587` (config TOML/.env pode trazer texto), e qualquer falha inesperada vira mensagem amigável na tela com o **tipo da exceção** — em vez de derrubar o app no Cloud (onde o detalhe é redigido).
- **🖥️ Modal de Configurações em largura total (v2.5.6)** — o modal agora abre em **até 1280px** (`width="large"`), aproveitando melhor a tela; os campos do **Jira** e das **Notificações** foram organizados em **grade de 2 colunas** dentro da largura nova (webhook/e-mail, usuário/senha, host/porta lado a lado).
- **🎨 Corpo dos expanders do modal com fundo próprio (v2.5.6)** — o conteúdo aberto de **cada expander** (Jira/Notificações) ganhou **fundo de destaque nos dois temas**, então os campos aparecem de cara (sem depender do hover da borda): no **claro**, tom azul `rgba(0,82,204,.07)` no Jira / roxo `rgba(124,58,237,.07)` no Notificações com borda suave colorida; no **escuro**, fundo **`#0d1523` (Jira)** / **`#141021` (Notificações)** sobre base `#0b1018` — ainda mais escuro que o corpo do modal —, texto claro `#d7dbe0` e bordas `#1e3a5f`/`#3b2f5a` — eliminando as cores nativas claras que "predominavam" dentro do modal escuro.
- **🎨 Botões do modal com cor sólida por intenção (v2.5.6)** — no expander de **Notificações** do modal, os 4 botões têm **cor sólida fixa nos dois temas** (texto branco, sem oscilação no hover): **"💾 Salvar notificações (sessão)" verde `#059669`** (confirmação), **"🔔 Testar Discord" azul `#2563eb`**, **"✉️ Testar e-mail" roxo `#7c3aed`** e **"↩️ Limpar meu config" cinza-ardósia `#475569`** — cada um com a cor da sua intenção. O botão **"⚙️ Configurações" da sidebar** também virou sólido roxo `#7c3aed` nos dois temas (via `type="primary"` + regra no `stBaseButton-primary`), destacando que abre o modal.
- **📊 Seção "Status" do modal destacada (v2.5.6)** — o bloco de status das notificações ganhou leitura clara **nos dois temas**: no **claro**, o título "Status" e os nomes dos canais ficam **grafite sólido** (não mais esbranquiçados) e o estado aparece colorido (verde `#059669` em "✅ configurado" / âmbar `#b45309` em "❌ ..."); no **escuro**, o título fica **branco destacado**, as linhas claras `#d7dbe0`/`#f1f5f9` e os estados em tons vivos `#34d399`/`#fbbf24` — fora das cores pálidas do tema.
- **🩷 Títulos do modal com cor de destaque no escuro (v2.5.6)** — o nome do modal **"⚙️ Configurações"** e o rótulo **"🎨 Tema"** deixaram de ficar esbranquiçados `#e2e8f0` no modo escuro: ganharam cores vivas — progresso **roxo `#a78bfa`** no título e **azul `#3b82f6`** no "Tema" (no claro seguem grafite, já legíveis).
- **💳 Planos SaaS e isolamento por tenant (v2.5.6)** — base pronta pra monetização sem billing ainda: `PLANO=free|pago` (padrão **free**) liga/desliga recursos e `TENANT_ID` prepara a segmentação por empresa. **Plano free**: histórico/dashboard **resumidos às últimas 30 triagens**, **RAG desligado**, **1 canal de alerta** (prioriza e-mail) e deep-analysis do Dashboard oculto (causas raiz via IA + comparativo IA×local) — com aviso "🔓 Plano grátis" na interface. **Plano pago**: histórico e Dashboard **completos**, **RAG ligado** (o LLM consulta casos similares do histórico) e **multi-canal** de alerta (e-mail **e** Discord quando ambos configurados). Todo registro persistido passa a carregar `tenant_id` (padrão `global`; registros antigos sem o campo continuam valendo como globais) e as leituras **filtram pelo tenant atual** — a arquitetura já entende isolamento por empresa quando houver contas.

### Corrigido
- **👥 Override de Notificações verdadeiramente por visitante (v2.5.6)** — antes o override ficava num **global do módulo** compartilhado: no Cloud, o e-mail/webhook que o **visitante A** cadastrava valia também para o **visitante B** na mesma instância (até o app reiniciar). Agora o override vive em **`st.session_state`** (`cfg_override_notif`) — **cada navegador/aba tem o seu**, isolado dos demais; só um "Limpar meu config" na própria sessão apaga, e nada é gravado em disco (sem runtime do Streamlit/testes cai num fallback global).
- **🔒 Campos do modal não vazam os secrets do dono (v2.5.6)** — antes, os campos de **Notificações** (webhook, e-mail de destino, usuário, **senha/App Password SMTP**, host e porta) vinham **pré-preenchidos com o config resolvido** (secrets/.env) e a "máscara" do campo de senha só escondia visualmente (o valor continuava no DOM). Qualquer visitante no Cloud abria o modal e lia os dados do dono (F12). Agora os campos **nascem vazios** e só mostram o que **a própria sessão** digitou (override): os valores reais continuam nos Secrets e são usados **silenciosamente** no envio — placeholders explicam ("o do dono fica em Secrets"). Campo vazio = volta ao config do dono.
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
