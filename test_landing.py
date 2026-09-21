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


def test_links_legais():
    assert f"{APP_URL}legal?aba=termos" in _HTML
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
    assert len(faq["mainEntity"]) == 4


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


def test_logo_do_app_na_navegacao():
    assert (_RAIZ / "web" / "landing" / "logo7_robo.png").exists()
    assert 'src="logo7_robo.png"' in _HTML
    assert 'alt="Logo do AI Bug Triage System"' in _HTML