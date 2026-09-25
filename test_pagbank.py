"""Testes do módulo PagBank (cobrança Pix automática via Orders API).

Nunca tocam a rede: requests.post/get são mockados. As envs de configuração
(PAGBANK_*) também são isoladas por monkeypatch.
"""
import pytest
import pix

import pagbank


def _configurar(monkeypatch):
    monkeypatch.setenv("PAGBANK_TOKEN", "tok-teste")
    monkeypatch.delenv("PAGBANK_API", raising=False)
    monkeypatch.delenv("PAGBANK_WEBHOOK_URL", raising=False)
    monkeypatch.delenv("PAGBANK_VALIDADE_HORAS", raising=False)


@pytest.fixture(autouse=True)
def _sem_env_local(monkeypatch):
    """Hermeticidade: config só via os.environ — o .env do desenvolvedor
    (ex.: PAGBANK_TOKEN/PAGBANK_API de sandbox local) não vaza para os testes."""
    monkeypatch.setattr(pix, "_ler_env", lambda nome: "")


def test_sem_token_nao_configurado(monkeypatch):
    monkeypatch.delenv("PAGBANK_TOKEN", raising=False)
    assert pagbank.configurado() is False


def test_configurado_com_token(monkeypatch):
    _configurar(monkeypatch)
    assert pagbank.configurado() is True
    assert pagbank.token() == "tok-teste"


def test_base_url_padrao_producao(monkeypatch):
    _configurar(monkeypatch)
    assert pagbank.base_url() == "https://api.pagseguro.com"


def test_base_url_sandbox(monkeypatch):
    _configurar(monkeypatch)
    monkeypatch.setenv("PAGBANK_API", "https://sandbox.api.pagseguro.com/")
    assert pagbank.base_url() == "https://sandbox.api.pagseguro.com"


def test_validade_padrao_24(monkeypatch):
    _configurar(monkeypatch)
    assert pagbank.validade_horas() == 24


def test_validade_custom(monkeypatch):
    _configurar(monkeypatch)
    monkeypatch.setenv("PAGBANK_VALIDADE_HORAS", "48")
    assert pagbank.validade_horas() == 48


def test_webhook_url_configurada(monkeypatch):
    _configurar(monkeypatch)
    monkeypatch.setenv("PAGBANK_WEBHOOK_URL", "https://x.onrender.com/webhook/pagamento")
    assert pagbank.webhook_url() == "https://x.onrender.com/webhook/pagamento"


class _Resposta:
    def __init__(self, status_code, dados):
        self.status_code = status_code
        self._dados = dados

    def json(self):
        return self._dados


def test_centavos():
    assert pagbank._centavos(19.99) == 1999
    assert pagbank._centavos(19) == 1900
    assert pagbank._centavos(0.5) == 50


def test_digitos():
    assert pagbank._digitos("123.456.789-09") == "12345678909"
    assert pagbank._digitos("") == ""


def test_cpf_valido():
    assert pagbank.cpf_valido("529.982.247-25") is True
    assert pagbank.cpf_valido("52998224725") is True
    assert pagbank.cpf_valido("12345678900") is False  # dígitos verificadores errados
    assert pagbank.cpf_valido("11111111111") is False  # dígitos repetidos
    assert pagbank.cpf_valido("123") is False
    assert pagbank.cpf_valido("") is False


def test_criar_cobranca_monta_pedido_correto(monkeypatch):
    _configurar(monkeypatch)
    monkeypatch.setenv("PAGBANK_WEBHOOK_URL", "https://x.onrender.com/webhook/pagamento")
    chamadas = {}

    def fake_post(url, headers, json, timeout):
        chamadas.update(url=url, headers=headers, json=json, timeout=timeout)
        return _Resposta(200, {
            "id": "ORDE_ABC",
            "reference_id": "cob-123",
            "charges": [{
                "id": "CHAR_1",
                "status": "WAITING",
                "qr_code": {"id": "QRCO_XYZ", "text": "0002010..."},
            }],
        })

    monkeypatch.setattr(pagbank.requests, "post", fake_post)
    resultado = pagbank.criar_cobranca(
        19.99, "cob-123", cpf="52998224725", nome="Jose da Silva", email="jose@test.com"
    )
    assert resultado == {"order_id": "ORDE_ABC", "qr_id": "QRCO_XYZ", "pix_copia": "0002010..."}
    assert chamadas["url"] == "https://api.pagseguro.com/orders"
    assert chamadas["headers"]["Authorization"] == "Bearer tok-teste"
    corpo = chamadas["json"]
    assert corpo["reference_id"] == "cob-123"
    assert corpo["customer"]["tax_id"] == "52998224725"
    assert "qr_codes" not in corpo  # formato atual usa charges[].payment_method.type = PIX
    charge = corpo["charges"][0]
    assert charge["amount"] == {"value": 1999, "currency": "BRL"}
    assert charge["payment_method"]["type"] == "PIX"
    assert charge["payment_method"]["pix"]["expiration_date"]
    assert "PAGBANK_WEBHOOK_URL" not in corpo["notification_urls"][0]  # usa a URL real
    assert corpo["notification_urls"] == ["https://x.onrender.com/webhook/pagamento"]
    assert corpo["items"][0]["unit_amount"] == 1999


def test_criar_cobranca_sem_cpf_falha(monkeypatch):
    _configurar(monkeypatch)
    monkeypatch.setenv("PAGBANK_WEBHOOK_URL", "https://x.onrender.com/webhook/pagamento")
    with pytest.raises(pagbank.PagbankErro, match="CPF"):
        pagbank.criar_cobranca(19.99, "cob-123")


def test_criar_cobranca_cpf_invalido_falha(monkeypatch):
    _configurar(monkeypatch)
    monkeypatch.setenv("PAGBANK_WEBHOOK_URL", "https://x.onrender.com/webhook/pagamento")
    with pytest.raises(pagbank.PagbankErro, match="CPF"):
        pagbank.criar_cobranca(19.99, "cob-123", cpf="11111111111")


def test_criar_cobranca_sem_email_falha(monkeypatch):
    _configurar(monkeypatch)
    monkeypatch.setenv("PAGBANK_WEBHOOK_URL", "https://x.onrender.com/webhook/pagamento")
    with pytest.raises(pagbank.PagbankErro, match="E-mail"):
        pagbank.criar_cobranca(19.99, "cob-123", cpf="52998224725")


def test_criar_cobranca_lê_qr_top_level_como_fallback(monkeypatch):
    """Respostas que ainda trazem o campo antigo qr_codes seguem funcionando."""
    _configurar(monkeypatch)
    monkeypatch.setenv("PAGBANK_WEBHOOK_URL", "https://x.onrender.com/webhook/pagamento")

    def fake_post(url, headers, json, timeout):
        return _Resposta(200, {
            "id": "ORDE_ABC",
            "qr_codes": [{"id": "QRCO_LEGADO", "text": "0002010..."}],
        })

    monkeypatch.setattr(pagbank.requests, "post", fake_post)
    resultado = pagbank.criar_cobranca(19.99, "cob-123", cpf="52998224725", email="jose@test.com")
    assert resultado == {"order_id": "ORDE_ABC", "qr_id": "QRCO_LEGADO", "pix_copia": "0002010..."}


def test_criar_cobranca_sem_token_falha(monkeypatch):
    monkeypatch.delenv("PAGBANK_TOKEN", raising=False)
    with pytest.raises(pagbank.PagbankErro):
        pagbank.criar_cobranca(19.99, "cob-123")


def test_criar_cobranca_sem_notification_url_falha(monkeypatch):
    _configurar(monkeypatch)
    with pytest.raises(pagbank.PagbankErro):
        pagbank.criar_cobranca(19.99, "cob-123")


def test_criar_cobranca_erro_http(monkeypatch):
    _configurar(monkeypatch)
    monkeypatch.setenv("PAGBANK_WEBHOOK_URL", "https://x.onrender.com/webhook/pagamento")

    def fake_post(url, headers, json, timeout):
        return _Resposta(401, {"message": "unauthorized"})

    monkeypatch.setattr(pagbank.requests, "post", fake_post)
    with pytest.raises(pagbank.PagbankErro, match="unauthorized"):
        pagbank.criar_cobranca(19.99, "cob-123", cpf="52998224725", email="jose@test.com")


def test_criar_cobranca_erro_rede(monkeypatch):
    _configurar(monkeypatch)
    monkeypatch.setenv("PAGBANK_WEBHOOK_URL", "https://x.onrender.com/webhook/pagamento")

    def fake_post(url, headers, json, timeout):
        raise OSError("sem rede")

    monkeypatch.setattr(pagbank.requests, "post", fake_post)
    with pytest.raises(pagbank.PagbankErro):
        pagbank.criar_cobranca(19.99, "cob-123", cpf="52998224725")


def test_consultar_pedido_ok(monkeypatch):
    _configurar(monkeypatch)
    chamadas = {}

    def fake_get(url, headers, timeout):
        chamadas.update(url=url, headers=headers)
        return _Resposta(200, {"id": "ORDE_ABC", "charges": []})

    monkeypatch.setattr(pagbank.requests, "get", fake_get)
    dados = pagbank.consultar_pedido("ORDE_ABC")
    assert dados["id"] == "ORDE_ABC"
    assert chamadas["url"] == "https://api.pagseguro.com/orders/ORDE_ABC"
    assert chamadas["headers"]["Authorization"] == "Bearer tok-teste"


def test_consultar_pedido_erro(monkeypatch):
    _configurar(monkeypatch)

    def fake_get(url, headers, timeout):
        return _Resposta(404, {"error_messages": [{"code": "40010", "description": "order not found"}]})

    monkeypatch.setattr(pagbank.requests, "get", fake_get)
    with pytest.raises(pagbank.PagbankErro, match="order not found"):
        pagbank.consultar_pedido("ORDE_NAO_EXISTE")


def test_pagamento_confirmado_detecta_paid():
    pedido = {"charges": [{"id": "CHAR_1", "status": "WAITING"}, {"id": "CHAR_2", "status": "PAID"}]}
    assert pagbank.pagamento_confirmado(pedido) is True


def test_pagamento_nao_confirmado():
    pedido = {"charges": [{"id": "CHAR_1", "status": "WAITING"}]}
    assert pagbank.pagamento_confirmado(pedido) is False
    assert pagbank.pagamento_confirmado({}) is False