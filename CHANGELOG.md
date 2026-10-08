# Changelog

Todas as mudanças notáveis do **AI Bug Triage System** são registradas neste arquivo.

O formato é baseado no [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e segue o [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [v3.6.0] - 2026-10-08

### Alterado
- **A análise por IA passa a ser do Premium, e o Teste de 7 dias é a porta de experimentação.** Antes, o Basic chamava o LLM com o mesmo motor do Premium: o custo por triagem não tinha contrapartida e o teste não significava nada. Agora o Basic roda só o motor léxico local — offline, determinístico e sem custo — e a IA (Gemini/Groq e modelo próprio) fica atrás de `plano.pago()`, que já cobre a assinatura e o Teste Premium vigente (`plano_atual`). O gate tem **duas camadas independentes**: para o free, o checkbox e o seletor de provedor somem e dão lugar a um aviso de upsell; e `_pode_usar_ia()` reconfere o plano no ponto exato onde o LLM é chamado, de modo que uma UI que vaze não gasta cota. Resultados de IA **já persistidos** continuam visíveis no histórico — o que muda é não haver chamada nova.
- **As tabelas de comparação (Início e Meu Plano), as pills do hero, a frase de plano e os cards de preço da landing diziam que "Triagem NLP + IA" era liberada no Basic e, na linha seguinte, que "Análises de IA" eram Premium** — a contradição estava dentro da mesma tabela. A linha virou uma só: *IA (Gemini/Groq) — causa raiz, passos e comparativo IA×local*, `—` no Basic e `liberado` no Premium.

### Corrigido
- **A landing prometia triagem com IA "grátis no cadastro".** A prévia do navegador é heurística local — é o que o próprio teste garante —, mas a nota ao lado vendia IA gratuita. Agora ela diz que a triagem acontece no app, grátis no cadastro, e que a análise por IA está liberada nos 7 dias de teste Premium.

### Observações
- **819 testes**, 5 a mais que os 814 da v3.5.9, todos passando. Os novos cobrem o gate (`_pode_usar_ia`): free bloqueia mesmo com o checkbox marcado, pago libera, pago com o checkbox desmarcado não chama, trial vigente conta como pago e trial expirado volta a bloquear; e um teste de contrato garante que o gate está no site da chamada do LLM, não só na UI.
- **A segunda camada é a que importa.** O teste do trial não mocka `plano.pago()`: ele monta o caminho real de `plano_atual()` (login + banco + `_teste_em_vigor`), porque é o que garante que os 7 dias grátis continuam abrindo a IA sem tocar no gate.

## [v3.5.9] - 2026-10-05

### Adicionado
- **Tela "🤖 Pré-rotulados pelo agente" no Painel do Dono, com promoção a ground truth.** A v3.5.8 separou o rótulo de agente da métrica, e a consequência esperada de uma separação é que o rótulo de agente fica invisível: ele tem `rotulo`, então não volta para a fila de pendentes, e `carregar_rotulados` o descarta por `autor`, então não aparece na concordância. Não existia lugar nenhum onde a sugestão pudesse ser conferida — o agente podia rotular, a tela não mostrava, e a linha ficava fora da métrica sem caminho para entrar. Agora `avaliacao.carregar_pre_rotulados()` lê as linhas com `autor="agente"` com a mesma forma da fila (dedup por texto, `repeticoes`, `ids_irmaos`), e cada grupo mostra a sugestão do agente, o léxico e o que o usuário viu, com os três botões de severidade. O clique **regrava o mesmo rótulo com `autor` do dono logado** (`avaliacao.promover()`) — é isso que promove a linha a ground truth e a faz entrar na métrica. O guard de `promover()` recusa promover sem identidade de leitor e recusa `autor="agente"`: regravar com o autor do agente deixaria a linha fora da métrica e a tela diria que algo foi revisado sem ninguém ter lido. A fila de pendentes virou `_bloco_fila()` justamente para o `return` de "fila vazia" não engolir a tela nova.
- Dedup e paginação das duas filas passam por uma função só (`_agrupar`): o rótulo é do bug, não da linha, e duas cópias da mesma regra divergem em silêncio, aparecendo como contagem errada em vez de erro.

### Corrigido
- **"Ver mais →" não paginava nada na fila de rotulagem.** Os botões escreviam `_rot_offset` no `session_state`, mas `carregar_pendentes()` era chamado só com `limite` — nunca com `deslocamento`. O offset era gravado e nunca lido, então o clique redesenhava exatamente a mesma primeira página, e o defeito era indistinguível de "não há mais nada". O mesmo valia para a sondagem que decide se o botão aparece: ela contava sempre a partir do começo, então oferecia "Ver mais" em página cheia sem ter o que mostrar. O mesmo no-op estava em "⏭️ Pular" e na tecla **0** — esta última era a pior, porque a caption e o `help` do campo anunciavam "0 pular"; agora os três avançam o offset da sessão, e "Voltar ao início" (que só aparecia quando o offset era lido, ou seja, nunca) volta a ter a função que o nome promete.
- **O título da fila sumiu no próprio dia em que a tela nova entrou.** "#### Fila para rotular" ficava na mesma função que agora também chama a seção de pré-rotulados; ao extrair a fila para `_bloco_fila()`, o título ficou para trás e os cards passaram a aparecer sem landmark, lendo como preâmbulo da tela de agente.
- **Promover sem digitar nada apagava a justificativa do agente.** A tela mostra sugestão, léxico e o que o usuário viu — mas não o comentário que o agente gravou. Confirmar sem escrever nada sobrescrevia o campo em branco, e não havia outro lugar onde a justificativa da sugestão aparecesse. O comentário digitado tem precedência; vazio preserva o do agente.
- **Promover o último item de uma página intermediária sumia com a seção.** O botão de voltar era desenhado depois do `return` de lista vazia, então quem promovesse no fim da página 4 perdia a forma de voltar sem nenhum aviso. Agora ele é desenhado antes do `return`, nas duas filas.

### Observações
- **784 testes**, 23 a mais que os 761 da v3.5.8, todos passando. São 20 funções novas: 11 no backend (14 casos — uma é parametrizada com 4 autores) e 9 de contrato de UI. Cobrem o filtro por `autor`, a descida do filtro para o PostgREST, a exclusão de texto já rotulado na mão, dedup, paginação, queda sem nuvem, a promoção (grupo, autor aparado, lista vazia, id inexistente) e a recusa nos quatro casos de autor; na UI, que as duas filas são chamadas na mesma seção, que o `return` de fila vazia não engole a tela nova nem o botão de voltar, que a tela nova não usa cor inline e diz que não conta na métrica, que a promoção passa pelo guard, que a fila conserva título e offset, e que o `0` do teclado avança o mesmo que o botão.
- **A leitura de pré-rotulados faz duas consultas, não uma.** A segunda é a dos rótulos humanos, e ela não é redundante: a métrica deduplica por texto guardando a linha mais recente, então oferecer de novo um texto que o dono já rotulou na mão deixa o clique competindo com o rótulo que ele mesmo escreveu — e, se a linha pré-rotulada for mais velha, o clique é ignorado e o toast ainda afirma que a linha passou a contar. Filtrar esse caso é o que mantém "promover" querendo dizer uma coisa só.
- **O filtro de `autor` desce para o PostgREST e é reconferido em Python.** No servidor, porque a janela de leitura é contada sobre todas as linhas rotuladas e vem ordenada por `data_hora.desc`: filtrando depois, as linhas de agente mais antigas caem pela cauda e a seção esvazia sem aviso, enquanto a legenda acima dela continua anunciando quantas faltam. Em Python, porque é o que os testes observam (o REST é mockado e ignora `params`) e porque um servidor que responde 200 sem filtrar não pode virar fonte de verdade do ground truth.
- **Verificado contra o dado real, não só no mock.** A leitura devolveu os 27 grupos / 51 linhas que a rotulagem assistida gravou (14 `CRÍTICA`, 7 `MÉDIA`, 6 `NORMAL`), e o guard se recusou nos dois casos sem leitor humano. A tela foi renderizada num Streamlit local contra o banco, com a paginação percorrida até o fim (5+5+5+5+5+2 = 27), as cores dos botões medidas no `getComputedStyle` e o console sem erro. Os testes unitários mockam o REST; a forma do payload no Supabase é o que o `jsonb` realmente devolve, e isso só a leitura real confirma.
- **A promoção é o único caminho para a métrica.** Um rótulo de agente corrigido com outro rótulo é o mesmo PATCH: mesmo `payload.avaliacao`, campo `autor` trocado. Nada é copiado para outra tabela, então não há como um rótulo de agente entrar na concordância sem passar por `promover()`.

## [v3.5.8] - 2026-10-04

### Corrigido
- **A métrica de concordância somaria qualquer rótulo como se fosse humano.** A premissa de `carregar_rotulados` é medir o léxico contra o julgamento de quem lê o relato, mas nada no código exigia que o rótulo tivesse vindo de gente: bastava existir `payload.avaliacao.rotulo`. Com uma rotulagem assistida no horizonte, um lote marcado automaticamente entraria na conta e faria o motor ser medido contra a própria saída — inflando a concordância. Agora o rótulo carrega `autor`, `carregar_rotulados(apenas_humanos=True)` descarta os de `autor="agente"` (a métrica e o CSV exportado contam só humano), e `progresso()` separa **com rótulo humano** de **pré-rotuladas por agente**: estas últimas aparecem na legenda do Painel do Dono como pendentes de revisão, não como cobertura.

### Observações
- **761 testes**, 2 a mais que os 759 da v3.5.7, todos passando. Um trava que o rótulo de `autor="agente"` fica fora de `carregar_rotulados` por padrão e volta com `apenas_humanos=False`; o outro, que `progresso()` conta o agente em `pre_rotuladas` sem inflar `rotuladas`.
- **A separação é preventiva.** Não há rótulo de `autor="agente"` nas triagens atuais; o campo existe para que uma rotulagem assistida futura não contamine a métrica. Enquanto isso não acontece, `pre_rotuladas` é 0 e a tela não muda.

## [v3.5.7] - 2026-10-03

### Corrigido
- **O alerta por e-mail nunca era enviado quando o relato tinha mais de uma linha.** O assunto era montado com o início do relato cru (`resumo[:60]`) direto no header `Subject`, e o `email.message` recusa header com quebra de linha (RFC 5322) — levanta `ValueError: Header values may not contain linefeed or carriage return characters`. Como a evidência de teste chega multi-linha (saída de Newman/Playwright), o assunto carregava o `\n` do relato e o envio falhava **sempre** que a prioridade era CRÍTICA/ALTA; o Discord seguia funcionando porque manda no corpo, não em header. O sintoma aparecia na tela como `✉️ e-mail FALHOU ❌` com o `ValueError` ao lado, e ficava invisível enquanto as triagens não passavam do gatilho de alerta. Agora todo valor de header passa por uma função que achata CR/LF antes de montar a mensagem, e o assunto deriva do relato já achatado.
- **Os passos da IA saíam numerados em dobro ("1. 1. ...").** O relatório e a tela já numeram os passos, mas quando o modelo devolvia a lista com a própria numeração (`"1. Enviar..."`) o resultado virava `1. 1. Enviar...`. A normalização passou a remover numeração/bullet do início de cada passo logo após a resposta do LLM, num único ponto (`ia._normalizar_dados`), valendo tanto para a análise pura quanto para a com RAG. Número que faz parte do texto (ex.: `2FA`, `3 itens`) é preservado — só sai o que é separador (`1.`/`2)`, `3º`, `-`).

### Observações
- **759 testes**, 4 a mais que os 755 da v3.5.6, todos passando, e `ruff` sem achados. Os 4 novos travam os dois defeitos: o assunto multi-linha não quebra o envio e continua legível, e a limpeza dos passos remove numeração/bullet sem tocar em número no meio do texto.
- **Verificado com o dado que reproduziu.** O caso que falhava foi uma rodada do Newman com prioridade CRÍTICA cujo relato começa com várias linhas (`newman\n\nAI Bug Triage — ...`); o teste usa esse mesmo formato.

## [v3.5.6] - 2026-10-03

### Corrigido
- **O RAG afirmava "já aconteceu" sem nenhuma evidência.** `ja_aconteceu` era deixado a critério da IA, que decidia pelo que enxergava no contexto — e o contexto é a lista de registros recuperados. Medido: três registros idênticos, salvos com 8 minutos de diferença, sem severidade e sem resolução, fazeram a IA responder "já aconteceu: SIM" para um bug que nunca tinha acontecido. Duas causas, ambas agora fechadas em `rag.py`: (a) registro **sem severidade nunca foi triado**, então serve como histórico de uma submissão que ninguém analisou — passou a ser descartado antes de contar; (b) **cópias do mesmo relato** contavam como ocorrências distintas — cópias colapsam por Jaccard ≥ 0.85, e registro idêntico ao relato de agora também não prova recorrência. Sem evidência, `ja_aconteceu` é `False` por definição: a pergunta é "isso já aconteceu?", e uma cópia do texto de agora não responde nada. O que a IA lista em `registros_similar` nunca passou, e segue assim.
- **Um relatório de teste do Playwright perdia a causa ao virar relato.** A linha `Received:` **só aparece quando o elemento existe com outro texto**. Quando ele não existe — que é o caso mais comum de selector errado — a saída traz `Locator:` e um `Error:` com o motivo, e o parser ficava com `recebido: None`. Resultado medido: "senha rejeitada" e "typo no seletor" produziam registros **idênticos**, mesmo com causas opostas. Agora o motivo real é lido da segunda linha `Error:` (a primeira é só o header `expect(...) failed`, e pegá-la era o erro anterior) e o `locator` vai para o relato e para os passos de reprodução. `recebido` continua `None` quando não existe valor recebido — a ausência é informação, e preencher com o motivo seria fabricar dado.
- **Uma rodada do Newman com N asserções quebradas virava um relato só, em silêncio.** O parser usava `search` no bloco de falhas, que devolve a primeira ocorrência e descarta o resto. Numa execução real com 4 asserções quebradas, 3 sumiram do registro — entre elas o `HTTP 500` com `TimeoutError` de banco, o único defeito de servidor da rodada. Perda de dado sem nenhum aviso: o relato dizia ter uma falha e não tinha. Agora todas as falhas são preservadas, cada uma com requisição, método, URL, status e detalhe, e o texto do relato diz quantas foram e quais são as demais.
- **O nome do teste|reportado vinha com lixo do reporter.** O reporter `list` desce o título com o separador de desenho da caixa (`──────────`) e com a duração da asserção (`(4.0s)`) colados; ambos iam para o título e para o nome do teste no relato.
- **A "resolução" exibida podia ser um resumo da IA sem caso de origem.** A seção de histórico mostrava `resolucao_anterior`, texto que a IA escrevia a partir do contexto — não a resolução gravada no caso. Com mais de um registro similar, não dava para saber de qual caso a resolução veio, nem se veio de algum; e o texto na tela não era o que estava no banco — era paráfrase da IA, não o texto gravado. Agora a resolução exibida é a **gravada no caso**, verbatim, com `id` e data ao lado, e entre os casos com resolução vale o mais recente (o mais provável de refletir a correção vigente). Sem nenhum caso com resolução registrada, a IA não preenche mais nada — aparece "nenhum caso parecido tem resolução registrada" em vez de um texto sem procedência.

### Observações
- **755 testes**, 14 a mais que os 741 da v3.5.5, todos passando. Os 12 primeiros são de regressão sobre **saída real de execução**, não string montada à mão: Playwright 1.62.0 com Chromium e Newman 6.2.2, capturadas de uma rodada de verdade contra servidor local e scrubadas para `/app` no fixture. Cobrem o motivo real do Playwright, a extração de `locator`, o nome do teste sem traços nem duração, dois defeitos diferentes não virando o mesmo registro, e as 4 asserções do Newman preservadas com método/URL/status. Os 6 do RAG cobrem o caso medido das três cópias, registro não triado, relato distinto triado (que **deve** sustentar recorrência), o id que a IA inventa não passando, a resolução sair verbatim do caso mais recente e a fonte trazer a data. Dois deles foram endurecidos junto: o caso triado agora exige a resolução verbatim do banco, e o caso sem resolução registrada exige que o texto da IA seja descartado.
- **Verificado por execução, não por leitura.** Os três formatos de falha do Playwright e as quatro asserções do Newman foram reproduzidos localmente; a saída do parser foi conferida campo a campo antes de escrever o teste. A versão do Playwright 1.62 é relevante: `element(s) not found` no lugar de `Received:` foi a mudança de formato que motivou a correção.
- **Nada mudou no contrato dos adaptadores.** `estruturar_playwright` e `estruturar_postman` continuam devolvendo um dict — `colar_falha.py`, `secoes/integracao.py` e `webhook.py` dependem disso. As falhas novas do Newman entram em `falhas` e `total_falhas`, e as do Playwright em `locator`, `motivo_falha` e `timeout`.
- **Escopo desta versão.** O `v3.5.6` consolida três PRs anteriores sem versão — a remoção do inventário local de agente do `AGENTS.md` (#19) e as duas correções de RAG e adapters (#20 e #21) — e registra no `AGENTS.md` as duas invariantes de RAG que o código sozinho não deixa óbvias: recorrência só com evidência, resolução exibida sempre vinda do registro.

## [v3.5.5] - 2026-10-01

### Segurança
- **`/webhook/pagamento` era pública e sem autenticação nenhuma.** O endpoint público do PagBank respondia **antes** de qualquer checagem: não exigia token, não tinha teto de payload e não tinha timeout de socket. A primeira leitura dos logs do Render acotou o risco — **zero POST em `/webhook/pagamento` entre 29/09 e 01/10**, só health checks — e o `403 ACCESS_DENIED` (whitelist) mantinha a cobrança automática desligada, então o caminho nunca exercitou. Risco latente, não ativo; corrigido agora, antes da whitelist cair.
- **A autenticação correta não é `X-Webhook-Token`.** A conta do PagBank **não permite header customizado** — os documentados são `x-authenticity-token`, `x-product-origin` e `x-product-id` —, então o token que protege `/webhook/falha` jamais chegaria nessa rota. A doc oficial define a assinatura como `SHA256(token_da_conta + "-" + payload_cru)` em hex, comparada em tempo constante (`hmac.compare_digest`, para não cair na regra CWE-208 do Semgrep do repo). O hash é calculado sobre os **bytes crus** do corpo: reserializar o JSON parseado muda o espaçamento e a validação falha sempre, que é o erro que a própria doc deles avisa e que já gera thread de "signature mismatch" no fórum deles.
- **Teto de payload e timeout de socket nas duas rotas.** `MAX_BYTES` valida `Content-Length` antes de ler e agora vale também para `/webhook/pagamento`; o `413` **fecha a conexão** em vez de responder e deixar o corpo não drenado sujar o socket sob keep-alive (o sintoma aparecia como `Exception occurred during processing of request` no log do servidor durante os testes). `TratadorWebhook.timeout = 30` impede que uma conexão fique aberta indefinidamente esperando corpo que não vem.
- **`.env` estava em modo `664`** — legível por qualquer usuário da máquina. Agora `600`. O arquivo é gitignored e não tem segredo hardcoded, então a exposição era local e curta, mas o custo do conserto é zero.

### Corrigido
- **`AGENTS.md` descrevia a rota de pagamento pelo comportamento antigo** e afirmava que `MAX_BYTES` valia só para `/webhook/falha`, tornando invisível a #1 da auditoria. Reescrito com o mecanismo real, o motivo de `X-Webhook-Token` não servir ali, e a armadilha do corpo cru.
- **O procedimento local de rotação de credenciais ensinava a passar o segredo como argumento de tool** (`cred-rotate RENDER_API_KEY <novo-valor>`) — exatamente o que o próprio procedimento proíbe dez linhas acima, porque o valor de argumento fica persistido em texto plano no banco do OpenCode. O comando estava também errado de fato: `cred-rotate` exige só o nome da variável e lê o valor de stdin ou de prompt sem eco, então a forma documentada abortava com erro de uso.

### Observações
- **741 testes**, 11 a mais que os 730 da v3.5.4, todos passando, e `semgrep` com 0 achados. Os 9 novos travam o que a auditoria apontou e o modo de falha que a doc do PagBank descreve: assinatura válida aceita, inválida em `401`, ausente em `401`, corpo adulterado reaproveitando assinatura alheia em `401`, `X-Webhook-Token` **não** abrindo a rota, hex em caixa alta aceito, teto de payload em `413`, rota aberta sem `PAGBANK_TOKEN` e falha fechada com `WEBHOOK_REQUIRE_TOKEN=1`, e `timeout` do tratador, mais 2 de keep-alive (401 não corrompe a conexão seguinte). O teste do corpo cru manda JSON com espaçamento não canônico de propósito — se alguém passar a reserializar o dict antes de hashear, ele quebra.
- **Ressalva herdada da doc do PagBank:** em webhooks de **Assinaturas** (recorrente) há relatos no fórum deles de receber `X-Payload-Signature` com chave pública RSA via `GET /public-keys`, em produção e nunca em homologação, em URLs `api.assinaturas.pagseguro.com` — o que não bate com o `x-authenticity-token` documentado. A rota valida o header documentado. **Se a recorrência for ativada, confirmar o header real em produção antes de supor que a validação está pegando**: assinatura sempre inválida é o sintoma, e o fallback de hoje é rota aberta.
- **O formato do corpo da notificação segue sob dúvida.** `analisar_pagamento` lê `reference_id` do topo do dict, que é o formato de **Assinaturas**; a notificação de **Pedidos** devolve `notificationCode`/`notificationType` e não traz `reference_id`. Não foi corrigido aqui — é mudança de contrato com a API, e a evidência real só aparece quando a whitelist cair e um pagamento de teste chegar. O que se sabe hoje: a confirmação **nunca** vem do corpo, sempre de `consultar_pedido` server-side.

## [v3.5.4] - 2026-10-01

### Corrigido
- **A landing anunciava um PIX automático que não existe.** Três trechos diziam que a confirmação e a ativação chegavam sozinhas. O que roda em produção é Pix estático + "Já paguei" + confirmação à mão no Painel do Dono — o `POST /orders` do PagBank responde `403 ACCESS_DENIED` (whitelist), então o caminho automático nunca funcionou e a página anunciava um produto que o código não faz. A landing passou a descrever o fluxo manual e a atribuir a ativação ao dono. Três frases são travadas por teste em `test_landing.py`, que analisa **frase a frase** em vez do HTML inteiro, para não reprovar meta tag legítima como "Triagem automática".
- **O consentimento da newsletter não era pedido no ponto da coleta, e "Cancele quando quiser" prometia um clique que não existe** — não há lista, não há `List-Unsubscribe`, o descadastro é responder o e-mail. A linha agora diz isso textualmente, e o link inline do consentimento ganhou sublinhado via `p a:not(.btn)`, que antes só existia no texto das regras.
- **A política declarava 1 operador internacional onde há 2.** Ao religar o captcha o Google entrou no caminho dos dados e a Legal só nomeava o FormSubmit. O card agora separa os papéis: o **FormSubmit** leva o e-mail, o **reCAPTCHA** leva o comportamento de quem preenche (IP, navegador, interações) e **não recebe o e-mail**, com esse dado processado nos **Estados Unidos** e o Google na função de operador contratado desde 2026-04-02. O hedge anterior ("não informamos o país porque o serviço não publica") vale para o FormSubmit, cujo país não é verificável, e estava indevidamente estendido ao reCAPTCHA, onde o país é verificável.
- **`AGENTS.md` descrevia o fixture de teste como se fosse produção.** O arquivo afirmava que o `webhook.py` escuta em `127.0.0.1` e "não expõe". Esse `127.0.0.1` vinha de `criar_servidor()`, função que **apenas `test_webhook.py` chama**; o caminho de produção é `principal()`, cujo default já é `0.0.0.0:8080` (travado em `test_interpretar_args_defaults`). O mesmo bullet ainda apresentava `MAX_BYTES` como teto geral: vale só para `/webhook/falha`; `/webhook/pagamento` responde **antes** da checagem de token e não tem teto. Como o `AGENTS.md` é a fonte de contexto de quem mexe no repo, a descrição errada tornava invisível a #1 da auditoria.
- **`docs/03-arquitetura.md` descrevia o Render MCP como remoto** (`https://mcp.render.com/mcp`). Hoje é ponte stdio local, somente GET, que devolve o **nome** das env vars e nunca o valor. Tabela e parágrafo de higiene reescritos, incluindo de onde a chave é lida.

### Segurança
- **O formulário da newsletter estava sem captcha e com o e-mail cru no `action` — desde 19/09.** A linha `<input name="_captcha" value="false">` desligava o reCAPTCHA, que no FormSubmit **vem ligado por padrão** e cujo único valor documentado é `false`: a linha existia só para desligar. Além do spam, a documentação deles avisa que desligar sujeita o formulário às "technical limitations which we impose from time to time to filter out bots", o que pode **descartar inscrição legítima em silêncio** — problema de correção, não só de ruído. O alias aleatório que substitui o e-mail no `action` foi aplicado: ele chega no e-mail de *Ativar Formulário*, não no painel depois. `test_landing.py` trava o invariante (`action` sem `@`) e foi verificado pelo lado negativo — reintroduzir e-mail cru faz a suíte falhar.

### Observações
- **730 testes**, 7 a mais que os 723 da v3.5.3, todos passando: 3 de promessa de pagamento, 3 de copy/consentimento/descadastro da newsletter, 1 de sublinhado do link inline, 1 do `action` sem e-mail cru e 1 do captcha não estar desligado. Nenhuma mudança no app em execução — só landing, Legal, documentação e os testes que a protegem.
- **Verificado no browser antes de fechar a versão.** O `_captcha=false` fora do source não prova que o reCAPTCHA está ativo, porque o widget é injetado no submit e não existe no HTML servido. Submetendo o formulário ao vivo pelo navegador, o FormSubmit respondeu `Almost There — Please help us fight spam by clicking the box below`, com o widget real do Google carregado (dois iframes em `google.com/recaptcha/api2/anchor` e `/bframe`, o div `.g-recaptcha`, `api.js` e o locale `recaptcha__pt_br.js`). **O captcha está ativo**, confirmado por observação, não por inferência. A entrega do alias também foi observada: duas submissões chegaram na caixa do dono, com o `Reference` do formulário e o parágrafo "Someone just submitted your form on https://ai-bug-triage.com.br".
- **O FormSubmit também notifica o dono a cada envio**, o que só ficou visível na submissão real: o remetente nunca é o do visitante. Serve de alerta de spam sem precisar de lista — mas o aviso chega **em inglês** ("Someone just submitted your form on …"), com o e-mail do visitante numa tabela. O texto do formulário, esse, está em português.

## [v3.5.3] - 2026-09-29

### Corrigido
- **Rolar a página Legal jogava de volta ao topo a cada 400ms** — o conserto do "a Legal abria no fim" (o `st.switch_page` preserva a posição de rolagem) foi implementado com `setInterval(400ms)` repetindo 12 vezes, ou seja, 4,8 segundos em que o timer reatribuía `scrollTop=0` sem olhar se alguém já estava rolando. Quem abria a página e começava a ler recebia uma leve puxada de volta ao topo a cada 400ms — uma dente-de-serra de 180px/180px/180px... — e só normalizava quando o intervalo morria. O sintoma era pior que o defeito que o código existia para corrigir. Agora o loop cede no primeiro gesto do usuário (`wheel`, `touchstart`, `keydown` e `mousedown` marcam `livre` e cancelam o reagendamento) e o passo virou `setTimeout(60ms)`, encurtando a janela de ~4,8s para ~720ms — o suficiente para cobrir a reaplicação de rolagem do Streamlit na montagem. Medido no browser a 1366x768: a dente-de-serra sumiu (0 puxadas em 10s de rolagem contínua, do início ao fim da página) **e** a página continua abrindo no topo (62/62 amostras em `scrollTop=0` quando ninguém rola) — corrigir a briga com a pessoa não pode reintroduzir o defeito original.
- **2 testes de contrato do JS do rodapé** em `test_ui_comum.py` travando o modo de falha silencioso: o primeiro exige os quatro eventos de gesto e proíbe a volta do `setInterval` fixo; o segundo garante que o `scrollTop=0` continua no script, para o "abre no fim" não voltar junto. **723 testes**, todos passando.

## [v3.5.2] - 2026-09-28

### Corrigido
- **Links externos de "Termos & Privacidade" abriam o Início do app** — a landing e o rodapé da status page apontavam para `legal?aba=termos`, mas o Streamlit Cloud, na primeira carga, redireciona qualquer subrota (`/legal`, `/triagem`) para a raiz `/`: quem clicava caía na página principal, não nos Termos. Os links agora apontam para a **raiz com `?pag=legal&aba=termos|privacidade`** (que sobrevive ao cold-start), e o `home.py` navega sozinho via `st.switch_page` para a página Legal já na aba pedida — mesmo caminho confiável dos botões do rodapé internos. O rodapé da status page ganhou link de **Privacidade** separado do de Termos, e a página de status como um todo manteve o `language: pt` e o `publicEmail`.

### Adicionado
- **Deep-link externo para subpáginas** — parâmetro `?pag=legal` na raiz do app, com helper `ui_comum._aba_para_deep_link` e 5 testes de contrato do helper em `test_ui_comum.py` (aba pedida, padrão `termos`, lista de abas e página fora do contrato); a navegação em si usa `_ir_para_legal`, o mesmo caminho dos botões do rodapé. A landing (`index.html` e o artigo) e o rodapé da status page usam o novo formato.
- **716 testes** na suíte (5 a mais: deep-link termos/privacidade/padrão/lista/outras páginas em `test_ui_comum.py`), todos passando.

## [v3.5.1] - 2026-09-27

### Corrigido
- **Texto da tela de rótulo sumia no tema claro** — os cards e a linha de cabeçalho da fila nasceram com cor clara fixa (`#e2e8f0`, `#94a3b8`, `#cbd5e1`), pensada só para o tema escuro: no tema claro o texto ficava quase branco sobre fundo branco, com cara de "brilho por cima". As cores foram para `ui_tema._ROTULAGEM_CSS`, em classe (`.rot-cartao`, `.rot-topo`, `.rot-nota`) com variante por tema, seguindo a convenção do resto do app (`body:has([data-st-tema="escuro"])`) em vez de `style="..."` inline no painel.
- **Botões da fila com hover colorido no tema escuro** — os 4 botões de severidade herdavam o hover nativo do Streamlit, que troca a cor ao passar o mouse. Agora são sólidos em ambos os temas e o `:hover`/`:active`/`:focus` repete a mesma cor de fundo (é o truque que o app já usa em `.marca-jira`). Cores escolhidas por contraste: os tons que o app usa em outros botões **reprovam** em WCAG AA com texto branco (`#d97706` = 3,19:1 e `#059669` = 3,77:1), então foram para as variantes escuras `#b45309` (5,02:1) e `#047857` (5,48:1). Também knocking out `filter`/`box-shadow` no hover, e o export de CSV e a paginação receberam o mesmo tratamento.
- **Loop infinito de rerun na fila (achado no teste de render)** — o `st.rerun()` do botão "Pular" tinha entrado dentro do `with` da coluna e passava a rodar a cada item, a cada render, travando a página. A marca de CSS também estava sendo emitida fora da coluna, o que faria a regra `stColumn:has(.marca-rot-*)` não casar e o botão voltar ao estilo nativo sem nenhum erro aparente. Ambos fixados: o `st.rerun()` saiu do `with` e a marca passou a ser emitida dentro da coluna. O defeito só apareceu **renderizando o painel de verdade** — a suíte não reproduz render do Streamlit (nada aqui usa `AppTest`), e o que ela cobra é a estrutura do fonte.
- **5 testes de contrato de tema** em `test_painel_dono.py` travando os três defeitos: cor fixa no card, ausência de variante escura nas classes e botão que volta a mudar de cor no hover — mais um teste que garante que toda `marca-rot-*` usada no painel exista no CSS (o modo de falha silencioso) e um que valida o contraste AA das cores de botão. 711 testes, todos passando.

## [v3.5.0] - 2026-09-27

### Adicionado
- **Tela de rotulamento no painel do dono (v3.5.0)** — o gargalo do projeto deixou de ser o modelo e passou a ser o dado: os 30 casos do corpus são sintéticos (texto de QA, não relato de cliente), e foi por isso que um motor ruim passou na métrica e quase foi para produção. Agora o dono tem uma fila de triagens reais para rotular, e a métrica passa a medir o léxico contra julgamento humano de verdade. Um clique grava o rótulo no `payload->avaliacao` de todas as cópias daquele texto, com atalhos **1** CRÍTICA / **2** MÉDIA / **3** NORMAL / **0** pular e campo para o motivo da escolha.
- **Deduplicação por texto na fila** — o histórico real é dominado por repetição (uma única fixture de teste de API aparece 20 vezes), então rotular linha a linha desperdiça esforço e, pior, infla a métrica: um bug só passaria a pesar mais que todos os outros juntos. A fila agrupa por texto normalizado (minúsculas, sem acento, espaços colapsados) e mostra `×20 no histórico`; o rótulo é propriedade do bug, não da linha que o gravou.
- **Métrica de concordância léxico × seu rótulo** — quantos textos o léxico acertou e quantos o usuário *enxergou*, lado a lado, mais uma matriz de confusão (linhas = o que o léxico previu, colunas = o seu rótulo). As duas colunas existem porque a tela mostra `prioridade_final` (léxico x IA reconciliados) e não a saída crua do léxico: são coisas diferentes e é justamente a diferença entre elas que revela se a reconciliação "o mais grave vence" está empurrando tudo para CRÍTICA. A métrica conta por **texto único**, não por linha, pelo mesmo motivo da dedup.
- **`avaliacao.carregar_pendentes()`** — listagem server-side das triagens sem rótulo (`payload->avaliacao->>rotulo=is.null`, paginada), devolvendo texto, `gravidade` (léxico) e `prioridade` (o que o usuário viu).
- **`avaliacao.registrar_varios()`** — grava o mesmo rótulo em várias linhas de uma vez, devolvendo quantas foram gravadas.
- **Export da base rotulada em CSV** (`avaliacao.base_para_csv()`) — a base sai com `id, data_hora, descricao, gravidade, prioridade, rotulo, comentario, em`, pronta para análise fora do app.
- **9 testes** para a fila (filtro `is.null`, dedup ignorando caixa/acento, descarte de linha sem texto, paginação, gravação em grupo com falha parcial, CSV, `prioridade` vista) — total de 706 testes, todos passando.

## [v3.4.0] - 2026-09-27

### Removido
- **Experimento de NLP semântico sai do repositório (v3.4.0)** — decisão: **ficar só com o léxico, evoluindo**. O motor (`semantico.py`), seus 19 testes e o `requirements-semantico.txt` foram apagados, junto com o Release `modelo-semantico-v1` (135MB). O `avaliar_motores.py` (léxico x semântico x ensemble) virou **`avaliar_lexico.py`**, que mede só o léxico — que é o instrumento de trabalho para evoluí-lo: mostra o acerto por severidade prevista e, para cada erro, o **score e os fatores que dispararam** (é assim que se descobre que o caso #30 para em -1,95 por causa do padrão "página em branco"). Ganhou `--falhar-abaixo PCT`, que sai com código 1 se o acerto estrito cair abaixo do limite — dá para usar como trava ao mexer em `triagem.py`. Nenhuma mudança de comportamento no app: o semântico já estava fora desde o v3.2.0.

### Adicionado
- **Benchmark local de embeddings + classificador simples (experimento, sem mudança no app)** — `avaliar_embeddings.py` roda **fora** do app (venv própria em `/tmp/opencode/venv-embed`, sem tocar no `.venv` nem no `requirements.txt`) e compara o `tardellirs/brazembed-pt-br` (BERT 12×768, mean pooling, MIT) com o léxico nos mesmos 30 casos e mesmas métricas de sempre. **Resultado:** léxico **96,7% / 95,7%** · protótipos (zero-shot) **53,3% / 43,5%** · 1-NN **66,7% / 60,9%** · logreg **56,7% / 47,8%** · TF-IDF+logreg **56,7% / 47,8%** · TF-IDF+centroide **53,3% / 39,1%** (tolerante/estrito; os últimos 4 em leave-one-out, logo não comparáveis ao léxico). **Nenhum encoder entra no app:** o melhor modelo treinado fica 30 pontos abaixo do léxico e o classificador **sem transformer** empata com o transformer — o gargalo é o dado (30 casos sintéticos, classe NORMAL com 4 exemplos), não o modelo. Confirmada a mesma patologia do v3.1.0 mesmo com mean pooling e treino em português: os protótipos de severidade ficam quase equidistantes de qualquer entrada (margem top1−top2 média 0,058) e o modelo superprediz CRÍTICA (16/30) — **severidade é impacto de negócio, não similaridade semântica**.
- **`casos_qa.py` como fonte única do ground truth** — os 30 casos rotulados e as regras de métrica saíram de dentro de `avaliar_motores.py` (que exige `onnxruntime` só para importar) para um módulo próprio, agora importável por qualquer harness. `avaliar_motores.py` passa a importar de lá — resultado idêntico (léxico 29/30 e 22/23, sem mudança de comportamento). 36 testes travam os invariantes do corpus (30 casos, 23 estritos, rótulos canônicos, textos únicos, 3 classes no treino, ambiguidade sempre entre níveis adjacentes).

## [v3.3.0] - 2026-09-27

### Adicionado
- **Rótulo humano de severidade por triagem (v3.3.0)** 🏷️ — novo `avaliacao.py` + expander "🏷️ Avaliar a severidade real" logo abaixo do relatório de cada triagem. **Por quê:** o único conjunto rotulado do projeto são 30 casos sintéticos de QA, e foi exatamente porque eles não representavam a realidade que o motor semântico do v3.1.0 passou na métrica e ia para produção — a auditoria do histórico real mostrou que ele só escalava bug cosmético. Sem rótulo de severidade real não existe como medir nenhum motor. **Como funciona:** 4 botões (✅ Estava certa · 🚨 Era CRÍTICA · ⚠️ Era MÉDIA · ✅ Era NORMAL) + comentário opcional; grava em `payload->avaliacao = {rotulo, comentario, em, autor}` via GET + PATCH, **sem migration** e sem escrita anônima (mesmo caminho já provado do "registrar resolução"). "Estava certa" usa a **prioridade reconciliada que o usuário viu** (léxico x IA, persistida em `payload->prioridade_final`), não a palpite bruto. A IA usa 4 níveis (CRÍTICA/ALTA/MÉDIA/BAIXA) e o léxico 3, então `ALTA → CRÍTICA` e `BAIXA → NORMAL` são normalizados para as 3 canônicas. A UI mostra só a **contagem** de rótulos (nunca o texto de outro cliente) e só rotula quando a triagem foi para a nuvem. `carregar_rotulados()` é ferramenta do dono/admin para medir motores e filtra no servidor (`payload->avaliacao->>rotulo`), sem varrer todas as triagens. 21 testes herméticos novos (mockam o REST, nenhuma chamada de rede).

## [v3.2.0] - 2026-09-27

### Corrigido
- **Premium volta a ser 100% léxico — o motor semântico saiu do app (v3.2.0)** 🎯 — o experimento de NLP semântico do v3.1.0 foi **medido no histórico real** (38 textos únicos em `triagens`) e **não se sustentou**: o ensemble divergia da gravidade já gravada (que vem da camada de IA/Gemini) em **8 de 39** textos, e **todos os 7 flips eram `NORMAL → MÉDIA` em bug cosmético** ("erro de digitação no rodapé" ×4, "erro de digitação no texto do botão", um `Traceback` colado, um `TypeError`) — **zero resgates**. A causa: o BERTabaporu pega só o `[CLS]` de um MLM sem ajuste contrastivo, então o vetor não discrimina severidade — a similaridade máxima é praticamente a mesma nos textos que ele acerta e nos que ele erra (mediana 0.925 vs 0.918 no corpus; distribuições **sobrepostas** nos 38 textos reais), e nenhum threshold separa "digitação no rodapé" de "app crasha". Na prática o motor só somava um empurrão fixo de gravidade. O ganho de +13 pontos que ele mostrava no corpus de 30 casos vinha do **léxico errar 6 bugs médios óbvios**, não de understanding semântico. **Sai do app:** gate semântico, download de 135MB, ~4s de 1ª carga, ~185ms/relato, `onnxruntime`/`tokenizers` do build de produção. **Ficam no repo:** `semantico.py`, `avaliar_motores.py`, `test_semantico.py` e `requirements-semantico.txt` como experimento documentado (`pip install -r requirements-semantico.txt`), pronto para um encoder de sentence-embeddings (MiniLM/brazembed) só entrar em produção se bater o léxico no corpus **e** no texto real.

### Adicionado
- **Léxico com 10 padrões novos — acerto de 66,7% → 96,7% (v3.2.0)** — os 10 erros do léxico no corpus de 30 relatos foram analisados e **8 deles davam score 0.0** (o léxico nem disparava): lacuna de vocabulário, não de lógica. Entraram padrões **gerais de classe de bug** (não frases do corpus), cada um somando uma vez como os demais: instalação/atualização que não conclui, busca/consulta que não devolve resultado, notificação/push que não chega, registro/linha duplicada, renderização (conteúdo cortado, logo cortada, margem errada), saída em branco (página/arquivo em branco), raiz "demor\*" (latência), conexão que cai no meio da operação, cobrança "cobra a mais" no presente (o léxico só pegava "cobrou a mais", no passado) e cálculo fiscal/financeiro errado (restrito a imposto/fatura/boleto/cobrança/parcela). **"fecha sozinho" subiu de -1.8 para -2.0** (app morre no meio da tarefa = gravidade de crash). Pesos calibrados para não estourar: "extremamente lento… tudo demora" e "o valor fica errado" no carrinho **continuam MÉDIA** (eram as 2 regressões que a 1ª versão dos padrões tinha criado), e "erro de digitação" continua **NORMAL**. Resultado no corpus de 30: **29/30 (96,7%) tolerante e 22/23 (95,7%) estrito** — acima do ensemble (80%/73,9%), sem modelo, sem download, sem latência. **Zero mudança de severidade** nos 38 textos reais do histórico (antes × depois), e 12 testes novos, incluindo 3 de guarda contra regressão.

## [v3.1.0] - 2026-09-27

> ⚠️ **Superado pelo v3.2.0:** o motor semântico e o ensemble ficarão fora do app (medido no histórico real, o semântico só escalava bug cosmético). O código do experimento permanece no repositório.

### Adicionado
- **Motor de triagem semântico no Premium (v3.1.0)** — novo `semantico.py` no app: embeddings reais do BERTabaporu (ONNX int8, 100% offline e determinístico) que **complementam o léxico** (`triagem.py`) entendendo contexto em vez de só contar palavras. **Gate:** só `plano.pago()` (Premium + trial) usa o semântico; Basic segue 100% no léxico, igual hoje. **Hospedagem do modelo:** o `model_int8.onnx` (135MB) não cabe no repo (GitHub limita 100MB/arquivo) — foi para o **GitHub Release `modelo-semantico-v1`**, e o app baixa na 1ª execução e cacheia em `~/.cache/abt/`; em dev usa a pasta local se existir. **Fallback:** se o download ou a carga falhar, o app **continua no léxico** sem quebrar (nada de erro visível). Deps novas: `onnxruntime`, `tokenizers`, `numpy`. 13 testes herméticos novos.
- **Harness de métrica dos motores (v3.1.0)** — `avaliar_motores.py` roda os **30 relatos rotulados** do corpus de teste do Dashboard de QA (23 sem ambiguidade; "ALTA" da legenda → CRÍTICA) e compara léxico × semântico × ensemble. Resultado medido: **léxico 60.9% estrito · semântico sozinho 39.1% · ensemble 73.9%**.
- **Premium usa ENSEMBLE (léxico + semântico), não só o semântico (v3.1.0)** — a métrica mostrou que o semântico sozinho (que pega só o `[CLS]` de um MLM sem ajuste contrastivo) é **regressão** em relação ao léxico; somado ao léxico (média dos scores) ganha **+13 pontos** de acerto. O Premium passou a chamar `semantico.ensemble()`, que preserva o sentimento/fatores do léxico e soma o fator semântico. *(later reverted in v3.2.0)*

### Corrigido
- **Download do modelo passa a ser verificado (v3.1.0)** — a URL do Release estava em `releases/latest/download/`, que passa a apontar para o **último** release (um release novo do app trocaria o modelo em produção sem querer) e o download aceitava arquivo truncado. Agora a URL é **fixada por tag** (`releases/download/modelo-semantico-v1/...`) e cada arquivo só é instalado no cache se o **tamanho bater exatamente** com o do Release (`model_int8.onnx` 135.328.214 B · `tokenizer.json` 1.519.999 B); download parcial/corrompido é apagado junto com o `.part` e o app fica no léxico. Fallback testado agora pelo caminho real (sem `onnxruntime`), não só com mock.

### Corrigido (v3.0.x)
- **Sidebar volta a recolher no desktop (v3.0.1)** — revertida a "sidebar fixa" (v2.6.20/v2.6.23) que travava o painel aberto com 300px fixos, sem botão de recolher. **Causa raiz** (rastreada no git): o Streamlit esconde o botão `stSidebarCollapseButton` com `visibility:hidden` por padrão; se a sidebar recolhia (janela estreita ~768-820px, re-render ou iframe do Cloud), não havia como expandir de volta — daí "a sidebar não abre". O antídoto do v2.6.17 (botão sempre visível) já resolvia o travamento; o v2.6.20 foi uma apelação que substituiu o bug pelo incômodo da barra eternamente aberta. Agora: botão recolher/expandir sempre visível + `initial_sidebar_state="expanded"` (desktop abre expandida, como antes) e o comportamento nativo recolhível de volta.
- **Chevron (`<<`/`>>`) da sidebar no tema escuro (v3.0.2)** — o ícone Material (span/ligadura de fonte, não é svg) vinha `rgba(29,29,31,.6)` (quase preto) sobre o fundo `#0f1217`; agora o botão `stSidebarCollapseButton` (recolher, `<<`) e o `stExpandSidebarButton` (expandir, `>>`) são pintados de **vermelho** (`#f87171`). Além disso, a **caixinha de hover** do botão (cinza padrão do Streamlit) agora fica **vermelha**, com o chevron **branco** por contraste. No tema claro continuou como estava (já era visível).

## [v3.0.0] - 2026-09-19

### Adicionado
- **Release principal 3.0** 🎉 — marca a maturidade do app como portfólio de produto SaaS de QA.
- **Logo oficial do Postman** na página Integração — SVG real (simple-icons, `#FF6C37`) via `<img>` base64, mesmo método dos ícones de contato que renderizam no app (o `<svg>` inline não aparecia em ambiente restrito).
- **Botões da tela de login/cadastro com cores sólidas e SEM hover nos dois temas:**
  - 🚪 **Entrar** — verde sólido (`#059669`).
  - ✨ **Criar conta grátis** — gradiente Google de 4 cores.
  - 🔑 **Esqueceu a senha?** — vermelho sólido (`#dc2626`).
  - 📧 **Reenviar confirmação** — azul sólido (`#2563eb`).
  - **Enviar link de recuperação / Reenviar link de confirmação** — verde sólido.
  - **Voltar** e **🏠 Voltar ao Início** — verdes sólidos com mesmo tamanho dos principais.
  - O CSS abandonou o seletor antigo (`stVerticalBlock:has(> stElementContainer)`) que **não casava** com a estrutura real do Streamlit e deixava o fundo branco com hover cinza; agora usa o padrão comprovado **`stColumn:has(.marca-x)`**, com os marcadores dentro das mesmas colunas dos botões.

### Alterado
- **Página Início:** o card **"Triagem de bugs com IA para QA"** subiu para o topo (primeira impressão do app) e o masthead **"Conheça o plano"** desceu para logo acima da **tabela comparativa** — o visitante lê a proposta antes e vê a comparação de planos logo em seguida.
- **README:** screenshot do app atualizado (nova captura 1920×1080) + cache-buster `?v=202609` na URL da imagem para o GitHub mostrar a versão nova.

### Corrigido
- **Botões "Voltar ao Início", "Enviar link de recuperação" e "Voltar" ficavam brancos com hover cinza** — mesma falha do seletor `:has(>)`; corrigidos pelo padrão `stColumn:has` (ver acima).

## [v2.16.21] - 2026-09-18

### Alterado
- **Textos do pagamento sem jargão** — mensagens da confirmação de cobrança (webhook) mais claras e amigáveis para o assinante.

## [v2.16.20] - 2026-09-18

### Alterado
- **Troca de senha com feedback verdadeiro:** mensagens distintas para senha **igual à atual**, **fraca/conhecida** ou que **não atende os requisitos** (`auth_supabase.definir_senha`), com testes cobrindo cada caso (`test_auth_supabase.py`).

## [v2.16.19] - 2026-09-18

### Corrigido
- **"Defina sua nova senha" não gravava a senha** (a senha antiga continuava valendo): a troca usava `POST /user`, mas o GoTrue altera o usuário via **`PUT /user`** (`POST` não existe → 405 e a senha nunca era salva). `auth_supabase.definir_senha` agora usa `PUT`. Como a sessão vem do fluxo de recuperação, não são exigidos `current_password` nem reautenticação.
- **Erro vermelho "link expirado/inválido" ao recarregar a página (F5) após concluir o reset:** o link de uso único re-processado gritava erro mesmo com o usuário já logado (sessão restaurada). Agora, **sessão ativa ⇒ link marcado como consumido e tratamento silencioso** (`_link_ja_usado`).

## [v2.16.17] - 2026-09-17

### Adicionado
- **Comprovante de pagamento Premium por e-mail.** Ao confirmar o pagamento, o assinante recebe no e-mail um comprovante padrão (nome, valor, PIX, data, código do pedido + aviso de que não é nota fiscal).
  - O envio acontece dentro de `confirmar_cobranca` — **o único ponto onde o plano vira "pago"** — então vale tanto para o webhook automático do PagBank (charge PAID) quanto para a **confirmação manual** do dono (ex.: quando a API cai).
  - Reutiliza o SMTP já configurado (secrets); é **best-effort** (falha no envio nunca quebra a confirmação).
  - A cobrança agora guarda `nome`/`email`/`cpf` do assinante (usados no comprovante).
  - Nova função pública `notificacoes.enviar_email(para, assunto, corpo, corpo_html)` para e-mails transacionais a qualquer destinatário.

## [v2.16.15] - 2026-09-17

### Adicionado
- **Ponte para link no formato fragmento (`#access_token=...`):** quando o projeto Supabase usa "Flow Type" implícito, o link do e-mail de recuperação/confirmação traz o token no fragmento (`#`), que o Streamlit não lê. Um componente JS reescreve a URL (fragmento → query) e recarrega; o Python monta a sessão via `GET /auth/v1/user` (`auth_supabase.usuario_por_token`) e segue o fluxo normal (signup = logar, recovery = formulário de nova senha).

### Corrigido
- Link de recuperação continuava abrindo só o Início mesmo com query=token_hash: agora o app também processa quando o `access_token` vem explícito na URL.

## [v2.16.14] - 2026-09-17

### Corrigido
- **Link de recuperação/confirmação abrindo só o Início (sem agir):** o `st.query_params.get("type")` retorna **lista** em Streamlit novo; o filtro anterior rejeitava a lista e o app ignorava o link. Extração agora aceita lista/valor único.
- **Formulário "Defina sua nova senha" levado para o TOPO da página** — antes ficava abaixo de todo o conteúdo do Início (era fácil achar que "só abriu a home").

## [v2.16.13] - 2026-09-17

### Adicionado
- **"Esqueceu a senha?"** na tela de login — botão abaixo do formulário abre um mini-formulário de e-mail e dispara o e-mail de recuperação via `POST /auth/v1/recover` (Supabase/GoTrue). Anti-enumeração: a resposta é a mesma existindo ou não a conta.
- **"Reenviar confirmação"** na tela de login — reenvia o e-mail de confirmação de cadastro via `POST /auth/v1/resend` (type=signup) para quem não confirmou o 1º e-mail; conta já confirmada recebe aviso amigável.
- **Conclusão do fluxo de recuperação:** ao abrir o link `?token_hash=...&type=recovery` vindo do e-mail, o app troca o hash por uma sessão (`POST /auth/v1/verify`) e exibe um formulário para **definir a nova senha** (troca via `POST /auth/v1/user`). Com isso o cadastro e a recuperação usam o mesmo padrão de link (query param, compatível com o Streamlit).
- E-mails transacionais agora cobrem recuperação de senha + confirmação reenviável (a confirmação inicial já existia).

### Detalhes técnicos
- `auth_supabase.py`: novas funções `recuperar_senha(email)`, `reenviar_confirmacao(email)`, `recuperar_via_link(token_hash)` e `definir_senha(nova, access_token)`; validador de e-mail isolado `_valida_email`.
- `secoes/login.py`: botões "🔑 Esqueceu a senha?" / "📧 Reenviar confirmação" abaixo do formulário, com formulário de e-mail condicional (modo em `st.session_state["_auth_modo"]`) e "Voltar".
- `home.py`: `_processar_link_email()` passa a tratar `type=signup` e `type=recovery`; formulário de nova senha renderizado no fim da página (flag `_definir_nova_senha`).
- `test_auth_supabase.py`: +13 testes.
- Requisito no painel do Supabase: template "Reset Password" apontando para o app (Site URL já configurado para o link de cadastro).

## [v2.16.12] - 2026-09-17

### Alterado
- **Card "⚖️ Legal" unificado** — os botões "📜 Termos de Uso" e "🛡️ Privacidade / LGPD" viraram um único botão **"⚖️ Termos & Privacidade"** (verde `#25D366`), já que ambos levavam à MESMA página `/legal` (Termos e Privacidade são abas da mesma página; a aba aberta é a escolhida por padrão = Termos). Colunas passaram de `[1.6,1,1]` para `[1.6,1]` e o CSS `.marca-legal` agora pinta 1 botão (removida a regra do `nth-child(3)` azul). No mobile fica mais enxuto.
- **Landing: footer unificado** — os dois links "Termos de Uso" e "Privacidade" viraram **"Termos & Privacidade"** (apontando para a mesma página com a aba Termos).

## [v2.16.11] - 2026-09-17

### Alterado
- **Logo oficial na navegação da landing** — o quadrado verde com "A" no cabeçalho virou a logo do app (`logo7_robo.svg`, a mesma usada no app via data URI), publicada em `web/landing/` junto da página. Teste novo garante a presença do arquivo e do `<img>`.

## [v2.16.10] - 2026-09-17

### Adicionado
- **SEO da landing: `sitemap.xml` + `robots.txt`** — novos arquivos em `web/landing/` publicados no GitHub Pages junto da landing (ci.yml copia a pasta inteira agora). `robots.txt` permite a indexação e aponta o `sitemap.xml`, que lista a URL principal — acelera a descoberta da página pelo Google e facilita o envio via Search Console.

## [v2.16.9] - 2026-09-17

### Adicionado
- **Landing de marketing standalone (desacoplada do app)** — página estática `web/landing/index.html` publicada no GitHub Pages (`https://iago3-stack.github.io/ai-bug-triage-system/`) junto do badge de testes, no deploy já existente do `ci.yml`. É um HTML único e autocontido (SEO + JSON-LD `SoftwareApplication` + CSS/JS embutidos) com: hero + CTA para o app, "Como funciona" (3 passos), recursos, card de preços (Premium R$ 19,99/mês via PIX), FAQ e rodapé com Termos/Privacidade/badge dinâmico de testes. Todo CTA aponta para o app real (`streamlit.app`), mantendo o produto sem marketing dentro dele. Testes de sanidade: `test_landing.py`.

## [v2.16.8] - 2026-09-17

### Alterado
- **Rodapé "⚖️ Legal" reorganizado no mesmo leiaute do card "🤖 Pronto para triar bugs?"** — agora é um `st.container(border=True)` com colunas: título à esquerda e os dois botões à direita (`st.button` + `st.switch_page`), com CSS próprio (`.marca-legal`) no mesmo gradiente escuro e cores sólidas (verde `#25D366` / azul `#2E7CF6`). No mobile as colunas empilham sozinhas, então os botões ficam DENTRO do card (fim do vazamento) — validado no Playwright (390×844): `overflow-x = 0` e ambos os botões contidos.

### Corrigido
- **Página Legal agora abre no TOPO de verdade** — o scroll-to-top anterior usava `st.iframe(..., height=0)`, mas `height=0` é inválido no Streamlit 1.62 (`StreamlitInvalidHeightError`) e o `except` engolia a exceção: o script nunca rodava. Trocado por `streamlit.components.v1.html(height=0)`, que executa e tem acesso same-origin ao `window.parent`; o script zera o `scrollTop` do `[data-testid="stMain"]` (com loop curto de reforço). Validado: 2328 → 0 ao navegar do rodapé.
- **Troca de aba pelo rodapé** — a aba escolhida passa por `session_state` + um nonce na `key` do `st.tabs` (o `default` só vale na criação do widget). Validado: "Termos" abre a aba Termos e "Privacidade" abre a aba Privacidade, ambas no topo.

## [v2.16.7] - 2026-09-17

### Alterado
- **Responsivo mobile no rodapé "⚖️ Legal"** — o botão "Privacidade / LGPD" vaza pra fora do card em telas estreitas (texto quebra em duas linhas). Media query `@media (max-width:760px)`: aumenta a margem negativa e reduz padding/fonte dos botões; validado no Playwright (420×800): os dois botões ficam dentro do painel arredondado.

### Adicionado
- **Página Legal sempre abre no topo** — `st.switch_page` preservava a posição do scroll do navegador (aparecia já embaixo no rodapé). Um iframe invisível (st.iframe, JS igual-origem) roda `window.parent.scrollTo(0,0)` ao renderizar a página.

## [v2.16.6] - 2026-09-17

### Corrigido
- **📜 Rodapé "⚖️ Legal": cores sólidas não aplicavam nos botões** — os seletores dependiam do marcador `.rodape-legal-bg` ser irmão da linha de colunas, mas o Streamlit envolve as colunas num `stLayoutWrapper` (confirmado no DOM real com Playwright), então nenhum `~` casava e valia o estilo padrão. Agora o styling mira direto a classe que o `key` do widget gera no `stElementContainer`: `.st-key-rodape_termos` (verde `#25D366`/texto `#022c0e`) e `.st-key-rodape_privacidade` (azul `#2E7CF6`/branco), com `:hover`/`:active`/`:focus` fixados na MESMA cor (ambos os temas). Validado no navegador: a regra vence o hover nativo e nada muda ao passar o mouse.

## [v2.16.5] - 2026-09-17

### Corrigido
- **📜 Rodapé "⚖️ Legal": o app exibia o HTML cru como bloco de código (com o botão de copiar) e a faixa escura sumia na v2.16.4** — ao interpolar o CSS gerado (regras quebradas em várias linhas no nível de indentação 0), o bloco misturava linhas com indentação e quebrava o reconhecimento de HTML do markdown, virando "code block". Agora `_menu_legal()` monta o `<style>`/`<div>` em Python com **todas as linhas na coluna 0** (comprovado: zero linhas ≥4 espaços), então sempre renderiza como HTML. O painel escuro com os botões verdes/azuis sólidos e sem hover volta a aparecer nos dois temas.

## [v2.16.4] - 2026-09-17

### Corrigido
- **📜 Rodapé "⚖️ Legal": hover branco nas versões v2.16.2/v2.16.3** — o seletor CSS estava ancorado em `stMarkdownContainer`, mas no DOM o marcador fica dentro de um `stElementContainer`, então as regras nunca eram aplicadas (o visual sólido sumia e o hover padrão do tema aparecia). Agora a âncora usa `[data-testid="stElementContainer"]:has(...)` como os outros botões do app (ferramenta/integração) e cobre as duas formas de o Streamlit montar a linha de colunas. Cores **sólidas** verdes/azuis e **sem hover** em ambos os temas.

## [v2.16.3] - 2026-09-16

### Alterado
- **📜 Rodapé "⚖️ Legal" integrado ao card** — os botões "Termos de Uso" e "Privacidade / LGPD" agora ficam sobre um painel escuro com o mesmo gradiente do rodapé (parecem parte do bloco). Cores **sólidas** (verde #25D366 / azul #2E7CF6) e **sem hover**, idênticas no tema claro e escuro.

## [v2.16.2] - 2026-09-16

### Adicionado
- **⚖️ Página Legal** (nova aba no menu: "Termos & Privacidade") — **Termos de Uso** e **Política de Privacidade (LGPD)** em linguagem simples, com transparência de que o projeto é de **pessoa física (sem CNPJ e sem emissão de nota fiscal/NFS-e)**, quais dados são coletados (e-mail, CPF/nome só na assinatura, conteúdo da triagem), o papel dos guardrails que **mascaram CPF/e-mail/token antes de qualquer envio**, compartilhamento restrito à infraestrutura (Streamlit Cloud, Supabase, Render, PagBank) e os **direitos do titular** (art. 18 da LGPD) com canal de contato (WhatsApp/e-mail).

### Alterado
- **📜 Rodapé** — o link solto de "LGPD · Proteção de Dados" (que só apontava para o site da ANPD) saiu do iframe; em seu lugar, uma linha **"⚖️ Legal"** com botões reais **"📜 Termos de Uso"** e **"🛡️ Privacidade / LGPD"** que abrem as páginas internas (a referência à ANPD continua, mas dentro da página de Privacidade).
- Página Legal é **pública** (acessível sem login), como Início e Integração.

## [v2.16.1] - 2026-09-16

### Corrigido
- **💳 Pix PagBank usando o formato atual da API de Pedidos** — a criação da cobrança usava o antigo `qr_codes` (depreciado) e deixava o `customer` sem CPF; agora envia `charges[].payment_method.type = "PIX"` com `payment_method.pix.expiration_date` e lê o copia-e-cola de `charges[].qr_code.text` (com fallback para o formato antigo). Esse era o motivo de a cobrança cair no fluxo manual em produção.
- **🧾 CPF obrigatório e validado** — a API exige `customer.tax_id`; o campo "CPF do titular" virou obrigatório no "Assinar Premium" (com validação dos 11 dígitos e dígitos verificadores via `pagbank.cpf_valido`), evitando a chamada fadada ao erro.

### Adicionado
- **🔄 Nova tentativa do Pix PagBank** — quando a cobrança pendente falhou no PagBank, o Meu Plano mostra a **mensagem real do erro** (`pagbank_erro`) e um botão "Gerar Pix PagBank de novo" que regenera o QR dinâmico na **mesma cobrança** (`pixbilling.regenerar_pagamento`), sem duplicar.

## [v2.16.0] - 2026-09-16

### Adicionado
- **⚙️ Checkout automático de Pix via PagBank** (`pagbank.py`) — a assinatura do Premium agora pode criar um pedido com **QR Code dinâmico** na API de Pedidos (Orders): valor, expiração e URL de notificação. Cobra apenas **Pix entre chaves (0%)** passa a valer como gateway próprio, sem confirmação manual.
- **🔔 Webhook `/webhook/pagamento`** (Render) — recebe a notificação do PagBank, **consulta o estado real do pedido na API** (não confia no corpo do webhook) e, confirmando o status `PAID`, ativa o Premium **automaticamente** e de forma idempotente.
- **📊 Meu Plano** — campo de CPF/nome do titular (opcional) ao assinar, exibição do copia-e-cola dinâmico do PagBank e avisos de confirmação automática na página.

### Alterado
- `pixbilling.gerar_cobranca` ganhou o fluxo PagBank com **fallback**: se o PagBank não estiver configurado (ou a API falhar), a cobrança cai no caminho manual atual (Pix estático + "Já paguei"), sem derrubar o app.

### Configuração (secrets da Cloud + env da Render, jamais no repositório)
- `PAGBANK_TOKEN` — token de integração (Integrações → Gerar Token, chegou no e-mail).
- `PAGBANK_WEBHOOK_URL` — ex.: `https://ai-bug-triage-system-webhook.onrender.com/webhook/pagamento`.
- Opcionais: `PAGBANK_API` (sandbox `https://sandbox.api.pagseguro.com`), `PAGBANK_VALIDADE_HORAS` (padrão 24h).

## [v2.15.21] - 2026-09-16

### Alterado
- **📌 Barra superior nativa do Streamlit de volta no desktop** — antes ela ficava oculta no computador (só aparecia no celular para o hambúrguer). Agora volta a aparecer no notebook/desktop, mantendo a barra de navegação personalizada do topo como navegação principal.

## [v2.15.20] - 2026-09-16

### Alterado
- **📋 Ferramenta — texto do "Colar falha bruta" legível** — a explicação ("Cole um stack trace, log, a mensagem do usuário…") saiu do texto de legenda apagado e virou um **card branco com letras escuras**, com destaques em verde-escuro.
- **🎯 Botões de exemplo em cor sólida** — "🎯 Exemplo Playwright" verde (#16a34a), "🎯 Exemplo Postman" laranja (#ea580c) e "🧹 Limpar" cinza (#64748b), sem mudança de cor no hover (mantém a mesma cor sólida).

## [v2.15.19] - 2026-09-16

### Alterado
- **🔍 Cards "Extraído automaticamente:" legíveis na Integração** — os valores extraídos (Título, Arquivo, Esperado, Severidade prévia, etc.) saíram do fundo translúcido claro e agora ficam em **card branco com texto escuro**, borda/cor por ferramenta (verde Playwright, âmbar Postman) e a **severidade colorida** conforme o caso (vermelho p/ CRÍTICA/ALTA, âmbar p/ MÉDIA). Acabou o "efeito luz" que sumia com o texto.

## [v2.15.18] - 2026-09-16

### Alterado
- **⚫ Texto escuro sobre card claro na Integração** — os cartões dos 3 passos da ponte e a caixa "💡 Não tem Playwright ou Postman instalados?" passaram a usar fundo branco com letras escuras (slate/preto), títulos coloridos e chips dos botões de exemplo em verde/âmbar — legível de ponta a ponta, sem texto apagado.

## [v2.15.17] - 2026-09-16

### Alterado
- **🔆 Contraste extra na página Integração** — o badge "✨ Extraído automaticamente:" agora tem fundo sólido (verde no Playwright e âmbar no Postman) com texto escuro e maior. A caixa "💡 Não tem Playwright ou Postman instalados?" ficou mais legível: texto e título mais claros e os botões de exemplo em destaque.

## [v2.15.16] - 2026-09-16

### Alterado
- **🔌 Vitrine da página Integração repagina da** — os 3 passos da ponte ("Rode o teste → Cole a falha aqui → App estrutura e analisa") agora ficam dentro de um card único com borda, títulos em verde/âmbar/roxo e textos mais legíveis. Os cartões "✨ Extraído automaticamente" (Playwright e Postman) ficaram mais visíveis: nome dos campos colorido + valores em branco-forte e maior.
- **🎨 Botões com gradiente por ferramenta** — "🚀 Testar isso na Ferramenta" do Playwright usa gradiente verde (marca Playwright), o do Postman usa laranja (marca Postman) e o botão "🔍 Ir para a Ferramenta de Triagem" usa azul. Ao passar o mouse, clareiam e sobem levemente.

## [v2.15.15] - 2026-09-16

### Adicionado
- **🔌 Integração no menu do topo (desktop)** — a navegação do computador usa a barra do topo (a sidebar nativa fica fechada/estática no PC e só abre no celular), e o botão "🔌 Integração" não tinha entrado lá. Agora aparece no topo, logo ao lado de "🔍 Triagem de Bugs", igual ao menu lateral.

## [v2.15.14] - 2026-09-16

### Corrigido
- **⛑️ App não trava mais com "This page cannot be called directly"** — sessões iniciadas numa versão anterior (a lista de páginas mudou após deploy) deixavam a navegação dessincronizada e o `pg.run()` da `home.py` levantava `StreamlitAPIException`, travando o app numa tela de erro. Agora, quando isso acontece, o app redireciona uma vez para o **Início** e a navegação recomeça limpa — sem tela de erro, sem precisar matar manualmente a sessão.

## [v2.15.13] - 2026-09-16

### Adicionado
- **🔌 Nova página "Integração" (Playwright & Postman)** — vitrine/tutorial que explica a ponte entre as ferramentas e o app: como funciona, o que é extraído de cada saída (com exemplo real de cada uma e o resultado da extração ao vivo) e botões que levam direto à Ferramenta já com o campo preenchido. Disponível no menu da sidebar; o Painel do Administrador continua só para o dono.

### Evoluído
- **📋 Expander "Colar falha bruta"** agora tem os botões **🎯 Exemplo Playwright**, **🎯 Exemplo Postman** (preenchem o campo com uma falha realista — sem precisar ter as ferramentas instaladas) e **🧹 Limpar**. Depois é só clicar em "✨ Preencher relato a partir da falha" e executar a triagem, como antes.

## [v2.15.12] - 2026-09-16

### Alterado
- **🔍 Card SEO da Início menciona Playwright e Postman** — o texto agora deixa claro que o app reconhece a saída de testes **Playwright** e **Postman·newman** (método + URL e HTTP esperado × recebido), reforçando a integração e as palavras-chave de automação de QA.

## [v2.15.11] - 2026-09-16

### Corrigido
- **📱 Tabela do "Comparar planos" no celular** — o conteúdo passava da borda do expander; agora o corpo do expander rola horizontalmente quando a tela é estreita, mantendo a borda e os dois temas intactos.

## [v2.15.10] - 2026-09-16

### Adicionado
- **📖 Expander "📖 Como ler este Dashboard — Guia Completo" com cor** — mesmo estilo roxo (`marca-dashboard`) dos demais expanders do Dashboard, legível nos dois temas e sem mudança no hover.

## [v2.15.9] - 2026-09-16

### Adicionado
- **🎨 Expanders "📋 Colar falha bruta" e "💼 Comparar planos — Basic × Premium" agora com cor sólida (sem hover, legível nos dois temas)** — título em verde/Colar falha e dourado/Comparar planos, com borda e fundo suave combinando; no escuro usam tons claros fixos (hover não troca a cor).
- **🌈 Linha em gradiente acima dos cards** — Painel do Administrador, Dashboard de QA e o masthead da Início agora têm a mesma linha verde→azul→roxo que as demais seções já tinham, unificando a identidade visual da página.

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
