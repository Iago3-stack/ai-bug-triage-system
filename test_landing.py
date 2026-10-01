"""Testes da landing standalone de marketing (web/landing/index.html).

A landing é um HTML estático publicado no GitHub Pages junto do badge de
testes (ci.yml). Estes testes garantem que ela continua apontando para as URLs
corretas do app e mantendo as tags de SEO — sem reescrever o arquivo inteiro.
"""
import json
import pathlib
import re

_RAIZ = pathlib.Path(__file__).resolve().parent
_HTML = (_RAIZ / "web" / "landing" / "index.html").read_text(encoding="utf-8")
_SITEMAP = (_RAIZ / "web" / "landing" / "sitemap.xml").read_text(encoding="utf-8")
_ROBOTS = (_RAIZ / "web" / "landing" / "robots.txt").read_text(encoding="utf-8")
_ARTIGO = (_RAIZ / "web" / "landing" / "artigos" / "triage-de-bugs-com-ia.html").read_text(encoding="utf-8")

APP_URL = "https://ai-bug-triage-system-d6vigycbjt4qxez2wrvsxf.streamlit.app/"
DOMINIO = "https://ai-bug-triage.com.br/"
PAGES_URL = DOMINIO
ARTIGO_URL = f"{PAGES_URL}artigos/triage-de-bugs-com-ia.html"


def _bloco_json_ld() -> dict:
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', _HTML, re.S)
    assert m, "bloco application/ld+json ausente"
    return json.loads(m.group(1))


def test_arquivo_existe_e_tem_title():
    assert _HTML.startswith("<!DOCTYPE html>")
    assert "AI Bug Triage System" in _HTML
    m = re.search(r"<title>(.*?)</title>", _HTML, re.S)
    assert m and "AI Bug Triage System" in m.group(1)


def test_meta_de_seo():
    assert 'name="description"' in _HTML
    assert 'name="robots" content="index, follow"' in _HTML
    assert f'rel="canonical" href="{DOMINIO}"' in _HTML
    assert 'property="og:title"' in _HTML and 'name="twitter:card"' in _HTML


def test_json_ld_valido_e_coerente():
    dados = _bloco_json_ld()
    assert dados["@type"] == "SoftwareApplication"
    assert dados["offers"]["priceCurrency"] == "BRL"
    assert float(dados["offers"]["price"]) == 19.99


def test_cta_aponta_para_o_app():
    # Todo CTA deve levar ao app (contagem ≥ 4: nav + hero + preço + cta-final).
    assert _HTML.count(f'href="{APP_URL}"') >= 4


def test_preco_exibido():
    assert "R$ 19,99" in _HTML
    assert "por mês" in _HTML
    assert "PIX" in _HTML


def test_pagamento_nao_promete_confirmacao_automatica():
    # A landing anunciava "PIX automático" e "confirmação automática" enquanto o
    # POST /orders do PagBank respondia 403 ACCESS_DENIED: a página pública
    # prometia uma cobrança automática que não existia. O teste cruza o
    # vocabulário de pagamento com "automátic" em vez de banir a palavra —
    # assim "Classificação automática da gravidade" (que é verdade) continua
    # livre e só a promessa falsa é barrada.
    #
    # A unidade de julgamento é a FRASE, não a linha: o twitter:description
    # junta "Triagem automática de bugs" a "Premium via PIX" no mesmo <meta>,
    # e uma única linha com as duas coisas acusaria a afirmação verdadeira.
    # Os <meta> entram como frases próprias porque são copy pública, visível em
    # resultado de busca, mas o conteúdo delas morre se as tags forem removidas.
    corpo = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", _HTML)
    visivel = re.sub(r"(?s)<[^>]+>", " ", corpo)
    metadados = re.findall(r'content="([^"]*)"', corpo)
    frases = re.split(r"(?<=[.!?])\s+", visivel)
    for meta in metadados:
        frases += re.split(r"(?<=[.!?])\s+", meta)

    pagamento = re.compile(r"pix|pagamento|cobran|assinatura|premium|renov", re.I)
    for frase in frases:
        if pagamento.search(frase):
            assert not re.search(r"autom[áa]tic", frase, re.I), (
                f"copy de pagamento promete automação: {frase.strip()[:120]}"
            )
    assert "PIX manual" in _HTML


def test_newsletter_avisa_consentimento_no_ponto_da_coleta():
    # LGPD art. 9º: transparência onde o dado é coletado. O aviso fica abaixo
    # do botão e cita as duas vontades separadamente — Termos e tratamento do
    # e-mail — porque consentir as duas num único clique enfraquece o
    # consentimento de marketing.
    assert "concorda com os" in _HTML
    assert "processamento do seu e-mail para envio de novidades" in _HTML


def test_action_do_formulario_nao_expoe_email_cru():
    # O FormSubmit gera um alias aleatório e o manda no e-mail de ATIVAÇÃO (o
    # próprio "Ativar Formulário"), não no painel depois. Enquanto o `action`
    # apontar para o e-mail cru, qualquer um que abrir o source da landing extrai
    # o endereço e spamma ele direto. Invariante: `action` sem "@".
    acao = re.search(r'action="([^"]+)"', _HTML).group(1)
    assert "@" not in acao, f"action expoe endereco de e-mail cru: {acao!r}"
    assert acao.startswith("https://formsubmit.co/")
    # e o alias sobreviveu à troca?
    assert re.fullmatch(r"[0-9a-f]{32}", acao.rsplit("/", 1)[-1]), acao


def test_formulario_nao_desliga_o_captcha():
    # O reCAPTCHA do FormSubmit vem ligado por padrão; o único valor documentado
    # de `_captcha` é "false", ou seja, a linha existe só para desligar. A
    # documentação deles avisa que desligar sujeita o formulário às limitações
    # que aplicam de vez em quando para filtrar bot — o que pode descartar
    # inscrição legítima em silêncio. Linha presente = captcha desligado.
    assert 'name="_captcha" value="false"' not in _HTML
    # O honeypot continua como segunda camada, sem depender de terceiro.
    assert 'name="_honey"' in _HTML


def test_link_inline_em_texto_tem_sublinhado():
    # WCAG 1.4.1: cor sozinha não pode ser o único indício de que algo é link.
    # A regra global `a { text-decoration: none }` deixava o aviso de
    # consentimento — justamente onde a pessoa precisa enxergar que está
    # concordando — com um link verde sem sublinhado. O :not(.btn) mantém CTA,
    # nav e rodapé como estão.
    assert "p a:not(.btn) { text-decoration: underline; }" in _HTML


def test_newsletter_descreve_o_descadastro_que_existe():
    # O formulário só entrega o endereço no e-mail do responsável: não há lista,
    # nem ferramenta de envio, e portanto nenhum botão de descadastro — esse
    # header vem de quem envia (RFC 2369/8058), não do FormSubmit. A página
    # diz "responder este e-mail" porque é o caminho que existe. Banir aqui o
    # "um clique" impede que a volta da frase fácilaga a versão antiga.
    assert "responder este e-mail" in _HTML
    assert "Cancele quando quiser" not in _HTML
    proibido = re.compile(r"um clique|clique para cancelar|descadastrar em", re.I)
    visivel = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", _HTML)
    assert not proibido.search(visivel), "promete descadastro que o relay nao faz"


def test_links_legais():
    # Deep-link para a página Legal: aponta para a RAIZ com ?pag=legal (o
    # Streamlit Cloud derruba subrotas como /legal na primeira carga).
    assert f"{APP_URL}?pag=legal&amp;aba=termos" in _HTML
    assert "Termos &amp; Privacidade" in _HTML
    # Links de Termos e Privacidade unificados em um só (a página tem as abas).
    assert '<a href="https://ai-bug-triage-system-d6vigycbjt4qxez2wrvsxf.streamlit.app/legal?aba=privacidade"' not in _HTML


def test_badge_de_testes_do_pages():
    assert "pytest-badge.json" in _HTML
    assert "img.shields.io/endpoint" in _HTML


def test_faq_e_passos_presentes():
    assert 'id="como-funciona"' in _HTML
    assert 'id="recursos"' in _HTML
    assert 'id="precos"' in _HTML
    assert 'id="faq"' in _HTML
    assert _HTML.count("<details") >= 4


def test_sem_erros_clssicos_de_css():
    # Evita regressões tipo "let(--x)" que quebram o gradiente.
    assert "let(--" not in _HTML
    assert "var(--verde)" in _HTML


def test_robots_txt_aponta_sitemap():
    assert "User-agent: *" in _ROBOTS
    assert "Allow: /" in _ROBOTS
    assert f"Sitemap: {PAGES_URL}sitemap.xml" in _ROBOTS


def test_sitemap_xml_valido_e_com_url_principal():
    assert '<?xml version="1.0" encoding="UTF-8"?>' in _SITEMAP
    assert "http://www.sitemaps.org/schemas/sitemap/0.9" in _SITEMAP
    assert f"<loc>{PAGES_URL}</loc>" in _SITEMAP
    assert f"<loc>{ARTIGO_URL}</loc>" in _SITEMAP


def test_artigo_existe_e_tem_seo():
    """Página de conteúdo: meta de SEO, canonical próprio e robots indexável."""
    assert _ARTIGO.startswith("<!DOCTYPE html>")
    assert "<title>" in _ARTIGO
    assert 'name="description"' in _ARTIGO
    assert 'name="robots" content="index, follow"' in _ARTIGO
    assert ARTIGO_URL in _ARTIGO  # canonical + og:url apontam para si mesma


def test_artigo_json_ld_completo():
    """Article + BreadcrumbList + FAQPage válidos e coerentes entre si."""
    blocos = re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', _ARTIGO, re.S
    )
    tipos = [json.loads(b)["@type"] for b in blocos]
    assert tipos == ["Article", "BreadcrumbList", "FAQPage"]
    artigo = json.loads(blocos[0])
    assert artigo["@type"] == "Article"
    assert artigo["mainEntityOfPage"] == ARTIGO_URL
    assert "triage de bugs" in artigo["headline"].lower()
    faq = json.loads(blocos[2])
    assert faq["@type"] == "FAQPage"
    assert len(faq["mainEntity"]) == 6


def test_artigo_tem_conteudo_para_pesquisa():
    """Palavras-chave long-tail presentes no corpo (conteúdo, não só meta)."""
    corpo = _ARTIGO.lower()
    for alvo in ("triage de bugs", "triagem manual", "severidade", "componente",
                 "proposta de correção", "relatório em pdf", "checklist", "qa"):
        assert alvo in corpo, f"artigo deveria conter: {alvo}"


def test_index_links_para_o_artigo():
    """A landing referencia o artigo via caminho relativo (Pages) e no sitemap
    a URL canônica absoluta — o Google descobre o artigo pela home."""
    assert "/artigos/triage-de-bugs-com-ia.html" in _HTML


def test_terminal_demo_no_hero():
    """Telinha de terminal: barra de tráfego, linhas digitadas e cursor piscando."""
    assert 'id="term-linhas"' in _HTML
    assert "ai-bug-triage — zsh" in _HTML
    # Bolinhas verde / amarela / vermelha
    assert "#FF5F57" in _HTML and "#FEBC2E" in _HTML and "#28C840" in _HTML
    # O texto digitado aparece no HTML (conteúdo real, não imagem)
    assert "ai-triage relatos/pagamento_falhou.txt" in _HTML
    assert "CRÍTICA" in _HTML
    # Sempre digita em loop (sem trava de prefers-reduced-motion)
    assert "setTimeout(escrever" in _HTML
    assert "aria-label" in _HTML


def test_selo_de_qualidade_nos_passos():
    """Cada passo do 'Como funciona' carrega um selo de qualidade."""
    selos = re.findall(r'class="selo-passo">([^<]+)<', _HTML)
    assert len(selos) == 3, f"esperado 3 selos, obtido {len(selos)}: {selos}"
    for esperado in ("Testabilidade", "Tempo real", "Rastreável"):
        assert esperado in selos, f"selo '{esperado}' ausente"


def test_preview_teste_agora_presente():
    """Seção interativa 'Teste agora': campo, botão, chips e honestidade."""
    assert 'id="teste-agora"' in _HTML
    assert 'id="preview-bug"' in _HTML and 'id="preview-btn"' in _HTML
    assert 'id="preview-resultado"' in _HTML
    assert 'aria-live="polite"' in _HTML
    # Chips prontos para clicar (exemplos reais do produto)
    assert 'data-preview-exemplo' in _HTML
    assert "💳 PIX / erro 500" in _HTML
    # Aviso de que é uma prévia ilustrativa (sem prometer IA real no navegador)
    assert "Prévia ilustrativa" in _HTML
    assert "grátis no cadastro" in _HTML


def test_preview_eh_100_local_sem_api():
    """A preview não deve expor chave nem chamar backend: só heurística local."""
    assert "CAUSAS" in _HTML
    assert "function severidade" in _HTML and "function componente" in _HTML
    assert "normalize('NFD')" in _HTML
    # Nenhuma chave de API embutida na landing
    assert "api.key" not in _HTML and "AIza" not in _HTML and "Bearer " not in _HTML


def test_contador_triagens_no_hero():
    """Contador de triagens: lê stats.json local (dados reais) e não vaza chave."""
    assert 'id="contador-triagens"' in _HTML
    assert 'id="ct-total"' in _HTML and 'id="ct-hoje"' in _HTML
    assert 'fetch(\'stats.json\')' in _HTML
    assert "relatos já triados no sistema" in _HTML
    assert "número real, atualizado diariamente" in _HTML
    # Esconde até carregar (sem número falso pulando na visita)
    assert "display: none" in _HTML
    # Falha silenciosa: .catch sem quebrar a página
    assert ".catch(function () {});" in _HTML


def test_contador_so_faz_fetch_local():
    """Fetches da landing: apenas stats.json local + endpoints públicos do instatus.

    Endpoints externos permitidos: summary.json (estado geral) e
    v3/components.json (estado por componente) da página pública de status
    (URL fixa do serviço, CORS aberto, sem chave nenhuma) — garante que NENHUM
    outro fetch externo entre. Vale para a index e para o artigo.
    """
    ocorrencias = re.findall(r"fetch\(\s*['\"]([^'\"]+)['\"]", _HTML)
    assert ocorrencias == [
        "stats.json",
        "https://ai-bug-triage.instatus.com/summary.json",
        "https://ai-bug-triage.instatus.com/v3/components.json",
    ], f"fetch inesperado: {ocorrencias}"
    artigo = re.findall(r"fetch\(\s*['\"]([^'\"]+)['\"]", _ARTIGO)
    assert artigo == [
        "https://ai-bug-triage.instatus.com/summary.json",
        "https://ai-bug-triage.instatus.com/v3/components.json",
    ], f"fetch inesperado no artigo: {artigo}"
    # Badge por componente: só acessa componentes.json e mostra nome+estado por comp
    assert "v3/components.json" in _HTML and 'id="rotulo-detalhe"' in _HTML
    assert "OPERATIONAL" in _HTML


def test_metricas_do_produto_presentes():
    """Seção 'Números do produto': cards reais (stats.json) + fatos da oferta."""
    assert 'id="numeros"' in _HTML
    assert 'id="num-ia"' in _HTML and 'id="num-critica"' in _HTML and 'id="num-tempo"' in _HTML
    assert 'id="card-tempo"' in _HTML
    assert "Números do produto, não estimativa" in _HTML
    # Faxos da oferta (fatos, não estatísticas)
    for fato in ("7 dias grátis", "Sem cartão de crédito", "Sem fidelidade", "Relatório em PDF"):
        assert fato in _HTML, f"fato ausente: {fato}"
    # Oculta até carregar; esconde card de tempo enquanto não há medição
    assert "cardTempo.style.display = 'none'" in _HTML
    assert "seccao.style.display = 'grid'" in _HTML


def test_workflow_stats_existe():
    """Job de estatísticas: cron diário, secrets por referência, deploy com fallback."""
    wf = (_RAIZ / ".github" / "workflows" / "stats-triagens.yml").read_text(encoding="utf-8")
    assert "cron: '12 */6 * * *'" in wf
    assert "workflow_dispatch" in wf
    # Só usa secrets por referência — nunca valores literais
    assert "${{ secrets.SUPABASE_URL }}" in wf
    assert "${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}" in wf
    # Fallback: se o badge vivo não estiver disponível, não derruba o deploy
    assert "exit 0" in wf
    assert "actions/deploy-pages" in wf
    assert "America/Sao_Paulo" in wf


def test_workflow_stats_calcula_metricas_reais():
    """As métricas do stats.json saem dos dados reais (payload), com paginação."""
    wf = (_RAIZ / ".github" / "workflows" / "stats-triagens.yml").read_text(encoding="utf-8")

    def dentro(bloco, token):
        i = wf.find(bloco)
        return i >= 0 and wf.find(token, i, i + len(bloco)) >= 0

    # Lê payloads paginados (Range header) — nunca perde linhas por limite
    assert '"Range"' in wf and "inicio + 199" in wf
    # Métricas reais calculadas dos dados
    assert '"total"' in wf and '"com_ia"' in wf and '"critica"' in wf
    assert '"tempo_medio_ms"' in wf
    # Percentuais não são inventados: saem de contagens reais
    assert 'get("usou_ia")' in wf
    assert 'startswith("CRÍTICA")' in wf
    assert 'get("duracao_ms")' in wf
    # tempo só vira média com >= 3 medições; abaixo, fica null (card oculto)
    assert "if tempo_n >= 3 else None" in wf
    assert '"tempo_n": tempo_n' in wf


def test_ci_preserva_stats_json():
    """O deploy do CI não pode apagar o stats.json: preserva o que está no ar."""
    ci = (_RAIZ / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "curl -sf" in ci
    assert "-o badge/stats.json" in ci
    # Sem quebra: se ainda não existe, o contador simplesmente fica oculto
    assert "stats.json ainda não existe" in ci


def test_logo_do_app_na_navegacao():
    assert (_RAIZ / "web" / "landing" / "logo7_robo.png").exists()
    assert 'src="logo7_robo.png"' in _HTML
    assert 'alt="Logo do AI Bug Triage System"' in _HTML