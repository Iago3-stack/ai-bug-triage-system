import pytest
from datetime import datetime, timedelta, timezone


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


# --- Feedback pós-triagem --------------------------------------------------
def test_fb_deve_perguntar_sem_uid_nao_insiste():
    from secoes import ferramenta as f

    assert f._fb_deve_perguntar("") is False


def test_fb_deve_perguntar_nunca_avaliou(monkeypatch):
    from secoes import ferramenta as f

    monkeypatch.setattr(f, "_fb_ultimo_em", lambda uid: None)
    assert f._fb_deve_perguntar("uid1") is True


def test_fb_deve_perguntar_avaliou_recente_nao_insiste(monkeypatch):
    from secoes import ferramenta as f

    recente = datetime.now(timezone.utc).isoformat()
    monkeypatch.setattr(f, "_fb_ultimo_em", lambda uid: recente)
    assert f._fb_deve_perguntar("uid1") is False


def test_fb_deve_perguntar_avaliou_ha_semanas_insiste(monkeypatch):
    from secoes import ferramenta as f

    antigo = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    monkeypatch.setattr(f, "_fb_ultimo_em", lambda uid: antigo)
    assert f._fb_deve_perguntar("uid1") is True


def test_fb_deve_perguntar_leitura_falha_nao_quebra(monkeypatch):
    from secoes import ferramenta as f

    monkeypatch.setattr(f, "_fb_ultimo_em", lambda uid: (_ for _ in ()).throw(OSError("x")))
    # falha de leitura não quebra o fluxo e pergunta de novo (conservador, estilo 'falha suave')
    assert f._fb_deve_perguntar("uid1") is True


def test_fb_proxima_oportunidade_arredonda_para_cima(monkeypatch):
    from secoes import ferramenta as f

    rec_menos_1dia = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    monkeypatch.setattr(f, "_fb_ultimo_em", lambda uid: rec_menos_1dia)
    assert f._fb_proxima_oportunidade_em("uid1") == 2  # 2 dias restantes (janela de 3)

    ha_7dias = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    monkeypatch.setattr(f, "_fb_ultimo_em", lambda uid: ha_7dias)
    assert f._fb_proxima_oportunidade_em("uid1") == 0  # já pode

    monkeypatch.setattr(f, "_fb_ultimo_em", lambda uid: None)
    assert f._fb_proxima_oportunidade_em("uid1") is None

    monkeypatch.setattr(f, "_fb_ultimo_em", lambda uid: (_ for _ in ()).throw(OSError("x")))
    assert f._fb_proxima_oportunidade_em("uid1") is None


def test_feedback_ui_tem_chaves_frequencia_e_estado_obrigado():
    from pathlib import Path

    raiz = Path(__file__).resolve().parent
    ferra = (raiz / "secoes" / "ferramenta.py").read_text(encoding="utf-8")
    css = (raiz / "ui_tema.py").read_text(encoding="utf-8")
    assert 'key="fb_estrelas"' in ferra
    assert 'key="fb_comentario"' in ferra
    assert 'key="fb_enviar"' in ferra
    assert 'key="ex_feedback"' in ferra
    assert "fb_enviado_sessao" in ferra
    assert "_FB_DIAS = 3" in ferra
    # Widget fixo no fim da página (depois do histórico persistido), não só pós-triagem
    assert "    _ui_feedback()\n" in ferra
    assert ferra.find("    _ui_feedback()\n") > ferra.find("Histórico persistido")
    assert "_ui_feedback_pos_triagem" not in ferra
    # Duplicatas removidas: sessão e dashboard expander não existem mais na ferramenta
    assert "Histórico de triagens desta sessão" not in ferra
    assert "Dashboard de QA" not in ferra
    assert "ex_sessao" not in ferra and "ex_dashboard" not in ferra
    # Estado 'obrigado' discreto quando já avaliou (mantém a régua semanal)
    assert "_fb_agradecimento" in ferra and "fb-aviso" in ferra and "fb-aviso" in css
    assert "volta" in ferra and "obrigado" in ferra