import pytest


@pytest.fixture(scope="module")
def dados_relatorio():
    return {
        "descricao_limpa": "estou tentando baixar meus relatórios em pdf mas toda vez que aperto no botão baixar a página recarrega sozinha e me leva para outra guia",
        "relatorio": "# Relatório\n\n## Análise\n\n**Gravidade:** ALTA\n\nPassos para reproduzir:\n- clicar em baixar\n- ver a aba abrir",
        "gravidade": "ALTA",
        "prioridade_final": "ALTA",
        "polaridade": -0.5,
        "divergente": False,
        "resultado_llm": {
            "severidade": "alta",
            "categoria": "ux",
            "causa_raiz": "Botão de download não abre a página de forma esperada.",
            "passos_repro": ["Clicar em baixar PDF", "Observar nova aba"],
        },
        "provedor_ia": "Gemini",
        "modelo_ia": "gemini-3-pro",
    }


def test_gerar_pdf_relatorio_gera_pdf_valido(dados_relatorio):
    from secoes.ferramenta import FPDF, _gerar_pdf_relatorio

    if FPDF is None:
        pytest.skip("fpdf2 ausente neste ambiente")

    pdf_bytes = _gerar_pdf_relatorio(dados_relatorio)
    assert pdf_bytes[:4] == b"%PDF"
    assert len(pdf_bytes) > 1024


def test_gerar_pdf_relatorio_aceita_extras(dados_relatorio):
    from secoes.ferramenta import FPDF, _gerar_pdf_relatorio

    if FPDF is None:
        pytest.skip("fpdf2 ausente neste ambiente")

    pdf_bytes = _gerar_pdf_relatorio({"descricao_limpa": "bug de login"})
    assert pdf_bytes[:4] == b"%PDF"


def test_limpar_markdown_remove_marcacao():
    from secoes.ferramenta import _limpar_markdown

    texto = "## Título\n**negrito** e `código` e [link](https://x)"
    limpo = _limpar_markdown(texto)
    assert "Título" in limpo
    assert "negrito" in limpo and "**" not in limpo
    assert "código" in limpo
    assert "[link](" in limpo or "link" in limpo


def test_campo_relato_com_cara_de_terminal():
    """O campo de relato do usuário vira um terminal (barra + textarea mono verde),
    com o mesmo visual no claro e no escuro e SEM glow/hover."""
    from pathlib import Path

    raiz = Path(__file__).resolve().parent
    ferra = (raiz / "secoes" / "ferramenta.py").read_text(encoding="utf-8")
    css = (raiz / "ui_tema.py").read_text(encoding="utf-8")

    # Barra de janela do terminal logo acima do campo de relato
    assert 'class="term-cab"' in ferra
    assert "ai-bug-triage" in ferra
    assert 'class="marca-relato-term"' in ferra
    assert 'key="relato_entrada"' in ferra
    # O visual do textarea não muda nem no hover/focus/active (sem glow)
    assert "marca-relato-term" in css
    assert "textbox-shadow:none" not in css  # explicitly: box-shadow:none via !important
    assert "box-shadow:none !important" in css
    assert "hover" in css and ":focus" in css and ":active" in css


def test_botao_preencher_relato_cor_solida_nos_dois_temas():
    """'Preencher relato a partir da falha' tem verde sólido igual no hover/focus/active —
    penho nos dois temas, sem glow."""
    from pathlib import Path

    raiz = Path(__file__).resolve().parent
    css = (raiz / "ui_tema.py").read_text(encoding="utf-8")
    ferra = (raiz / "secoes" / "ferramenta.py").read_text(encoding="utf-8")

    assert 'class="marca-colar-btn"' in ferra
    assert 'key="btn_colar_falha"' in ferra
    bloco = css[css.find("marca-colar-btn") :]
    assert "background:#059669 !important; color:#ffffff !important; border:none !important" in bloco
    assert ":hover" in bloco and ":focus" in bloco and ":active" in bloco
    assert "box-shadow:none !important" in bloco