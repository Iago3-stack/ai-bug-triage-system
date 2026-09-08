"""Geração de QR Code Pix (BR Code) — 100% local, sem serviços externos.

Configuração (via variáveis de ambiente / Streamlit secrets — nunca no repo):
    PIX_KEY    chave Pix (CPF, e-mail, celular ou chave aleatória)
    PIX_NOME   nome do recebedor (máx. 25 caracteres)
    PIX_CIDADE cidade do recebedor (máx. 15 caracteres)
    PIX_TXID   identificador opcional da transação (padrão: ***)
"""

import base64
import io
import os

import qrcode

_CRC16_TABLE = None


def _build_crc16_table() -> list[int]:
    global _CRC16_TABLE
    if _CRC16_TABLE is None:
        table = []
        for i in range(256):
            crc = (i << 8) & 0xFFFF
            for _ in range(8):
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
            table.append(crc)
        _CRC16_TABLE = table
    return _CRC16_TABLE


def crc16_ccitt(texto: str) -> str:
    """CRC16-CCITT (polinômio 0x1021) — obrigatório no fim do payload Pix."""
    crc = 0xFFFF
    for byte in texto.encode("utf-8"):
        crc = ((crc << 8) ^ _build_crc16_table()[((crc >> 8) ^ byte) & 0xFF]) & 0xFFFF
    return f"{crc:04X}"


def _tlv(ident: str, valor: str) -> str:
    """Empacota um campo EMV (identificador + comprimento + valor)."""
    if not valor:
        return ""
    return f"{ident}{len(valor.encode('utf-8')):02d}{valor}"


def montar_payload(chave: str, nome: str, cidade: str, txid: str = "***") -> str:
    """Monta o payload estático Pix (BR Code/EMV) a partir da chave."""
    if not chave:
        rise = "PIX_KEY não configurada"
        raise ValueError(rise)
    nome = nome.strip()[:25]
    cidade = cidade.strip()[:15]
    txid = (txid or "***").strip()[:25] or "***"

    merchant_account = _tlv("00", "br.gov.bcb.pix") + _tlv("01", chave)
    payload = _tlv("00", "01")
    payload += _tlv("26", merchant_account)
    payload += _tlv("52", "0000")
    payload += _tlv("53", "986")
    payload += _tlv("58", "BR")
    payload += _tlv("59", nome)
    payload += _tlv("60", cidade)
    payload += _tlv("62", _tlv("05", txid))

    payload += "6304"
    return payload + crc16_ccitt(payload)


def configurado() -> bool:
    return bool(os.environ.get("PIX_KEY", "").strip())


def payload_configurado() -> str:
    """Retorna o copia-e-cola Pix se configurado; string vazia caso contrário."""
    chave = os.environ.get("PIX_KEY", "").strip()
    if not chave:
        return ""
    nome = os.environ.get("PIX_NOME", "Doacao")
    cidade = os.environ.get("PIX_CIDADE", "Sao Luis")
    return montar_payload(chave, nome, cidade)


def qrcode_png_base64(payload: str) -> str:
    """Gera o QR Code em data-URI (imagem PNG base64) para exibir direto no app."""
    qr = qrcode.QRCode(border=2, box_size=10)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"