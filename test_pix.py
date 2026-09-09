import re

import pix


def test_montar_payload_estrutura_emv():
    payload = pix.montar_payload("EMAIL@pix.com", "Iago Nunes", "Sao Luis", "DOACAO001")
    assert payload.startswith("000201")
    assert "br.gov.bcb.pix" in payload
    assert payload[-8:-4] == "6304"
    assert payload[-4:] == pix.crc16_ccitt(payload[:-4])


def test_crc16_ccitt_valor_conhecido():
    assert pix.crc16_ccitt("123456789") == "29B1"


def test_configurado_e_payload_configurado(monkeypatch):
    monkeypatch.setattr(pix, "_ler_env", lambda nome: "")  # isola o .env local
    monkeypatch.delenv("PIX_COPIA", raising=False)
    monkeypatch.delenv("PIX_KEY", raising=False)
    monkeypatch.delenv("PIX_NOME", raising=False)
    monkeypatch.delenv("PIX_CIDADE", raising=False)
    assert not pix.configurado()
    assert pix.payload_configurado() == ""


def test_configurado_com_chave(monkeypatch):
    monkeypatch.setattr(pix, "_ler_env", lambda nome: "")
    monkeypatch.setenv("PIX_KEY", "11999999999")
    monkeypatch.setenv("PIX_NOME", "Iago Nunes de Araujo")
    monkeypatch.setenv("PIX_CIDADE", "Sao Luis")
    assert pix.configurado()
    payload = pix.payload_configurado()
    assert payload.startswith("00020126")
    assert payload[-4:] == pix.crc16_ccitt(payload[:-4])


def test_ler_preferencia_env_sobre_env_file(monkeypatch):
    monkeypatch.setattr(pix, "_ler_env", lambda nome: "do-arquivo")
    monkeypatch.setenv("PIX_KEY", "os-environ-manda")
    assert pix._ler("PIX_KEY") == "os-environ-manda"


def test_copia_e_cola_tem_prioridade(monkeypatch):
    monkeypatch.setenv("PIX_COPIA", "000201269A10014br.gov.bcb.pix0104+551123456789")
    monkeypatch.setenv("PIX_KEY", "outra-chave")
    assert pix.configurado()
    assert pix.payload_configurado().startswith("00020126")


def test_link_pagamento(monkeypatch):
    monkeypatch.delenv("PIX_LINK", raising=False)
    assert pix.link_pagamento() == ""
    monkeypatch.setenv("PIX_LINK", "https://pag.ae/abc123")
    assert pix.link_pagamento().startswith("https://")


def test_chave_exposta_para_copiar(monkeypatch):
    monkeypatch.setattr(pix, "_ler_env", lambda nome: "")
    monkeypatch.delenv("PIX_KEY", raising=False)
    assert pix.chave() == ""
    monkeypatch.setenv("PIX_KEY", "+5598985914235")
    assert pix.chave() == "+5598985914235"


def test_qrcode_png_base64_gera_data_uri(monkeypatch):
    monkeypatch.setenv("PIX_KEY", "11999999999")
    payload = pix.payload_configurado()
    data_uri = pix.qrcode_png_base64(payload)
    assert data_uri.startswith("data:image/png;base64,")
    assert len(re.sub(r"^data:image/png;base64,", "", data_uri)) > 100