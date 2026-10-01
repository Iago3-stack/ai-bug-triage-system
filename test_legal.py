"""Testes dos helpers da página Legal (Termos e Privacidade/LGPD)."""
import streamlit as st

from secoes import legal


def test_contato_whatsapp_sem_numero(monkeypatch):
    monkeypatch.delenv("WHATSAPP_NUMERO", raising=False)
    assert legal._contato_whatsapp("mensagem") == ""


def test_contato_whatsapp_gera_link(monkeypatch):
    monkeypatch.setenv("WHATSAPP_NUMERO", "5511999999999")
    link = legal._contato_whatsapp("Olá! LGPD")
    assert link.startswith("https://wa.me/5511999999999?text=")
    assert "LGPD" in link


def test_contato_whatsapp_ignora_mais(monkeypatch):
    monkeypatch.setenv("WHATSAPP_NUMERO", "+5511999999999")
    link = legal._contato_whatsapp("oi")
    assert link.startswith("https://wa.me/5511999999999?text=")


def test_aba_da_url_cai_em_termos_quando_sem_parametro(monkeypatch):
    class _QueryFalha:
        def get(self, *args, **kwargs):
            raise RuntimeError("sem streamlit runtime")

    monkeypatch.setattr(st, "query_params", _QueryFalha())
    assert legal._aba_da_url() == "termos"


def test_aba_da_url_privacidade_quando_pedida(monkeypatch):
    class _Query:
        def get(self, nome, padrao=None):
            return "privacidade" if nome == "aba" else padrao

    monkeypatch.setattr(st, "query_params", _Query())
    assert legal._aba_da_url() == "privacidade"


def test_politica_declara_o_operador_internacional(monkeypatch):
    # O formulário da landing entrega o e-mail ao FormSubmit, que fica fora do
    # Brasil. A política listava Streamlit, Supabase, Render e PagBank, e omitia
    # justamente o operador que recebe o dado do visitante — a omissão é o que
    # o art. 9º proíbe. O teste renderiza a página e procura no texto emitido,
    # não no fonte, para garantir que o card existe de fato na tela.
    escritos = []
    monkeypatch.setattr(st, "markdown", lambda texto, *a, **k: escritos.append(texto))
    monkeypatch.delenv("WHATSAPP_NUMERO", raising=False)
    monkeypatch.delenv("ADMIN_EMAIL", raising=False)

    legal._privacidade()

    pagina = " ".join(escritos).lower()
    assert "formsubmit" in pagina
    assert "transferência internacional" in pagina or "transferencia internacional" in pagina
    # O reCAPTCHA (Google) entra no caminho quando o captcha do FormSubmit está
    # ligado — e ele vê o comportamento de quem preenche, não o e-mail. Sem
    # esse card, a política declararia um operador e omiria o outro.
    assert "recaptcha" in pagina
