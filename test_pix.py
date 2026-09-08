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


def test_configurado_e_payload_configurado():
    assert not pix.configurado()
    assert pix.payload_configurado() == ""


def test_configurado_com_chave(monkeypatch):
    monkeypatch.setenv("PIX_KEY", "11999999999")
    monkeypatch.setenv("PIX_NOME", "Iago Nunes de Araujo")
    monkeypatch.setenv("PIX_CIDADE", "Sao Luis")
    assert pix.configurado()
    payload = pix.payload_configurado()
    assert payload.startswith("00020126")
    assert payload[-4:] == pix.crc16_ccitt(payload[:-4])


def test_qrcode_png_base64_gera_data_uri(monkeypatch):
    monkeypatch.setenv("PIX_KEY", "11999999999")
    payload = pix.payload_configurado()
    data_uri = pix.qrcode_png_base64(payload)
    assert data_uri.startswith("data:image/png;base64,")
    assert len(re.sub(r"^data:image/png;base64,", "", data_uri)) > 100