"""Geração de QR Code Pix (BR Code) — 100% local, sem serviços externos.

Configuração (nunca commitada — Streamlit secrets, `.env` gitignored ou env):
    PIX_LINK    link de pagamento Pix com valor fixo (ex.: gerado no painel do
                provedor). Quando presente, o rodapé exibe um botão de
                pagamento no lugar do QR Code (QR estático não tem "finalidade
                de venda" e pode sofrer descontos).
    PIX_COPIA   copia-e-cola Pix oficial (EMV completo, ex.: emitido pelo banco)
    PIX_KEY     chave Pix (CPF, e-mail, celular ou chave aleatória) — usado
                somente quando PIX_COPIA não está presente
    PIX_NOME    nome do recebedor (máx. 25 caracteres — p/ payload montado por chave)
    PIX_CIDADE  cidade do recebedor (máx. 15 caracteres — p/ payload montado por chave)
    PIX_TXID    identificador opcional da transação (padrão: ***)

Prioridade de leitura (igual ao resto do app): st.secrets → os.environ → .env.
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


def _ler(nome: str) -> str:
    """Lê configuração com prioridade: st.secrets → os.environ → .env."""
    try:
        import streamlit as st

        v = st.secrets.get(nome)
        if v:
            return str(v).strip()
    except Exception:
        pass
    v = os.environ.get(nome, "").strip()
    if v:
        return v
    return _ler_env(nome)


def _ler_env(nome: str) -> str:
    """Lê uma chave do arquivo .env (apenas leitura, nunca commitado)."""
    caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    try:
        with open(caminho, encoding="utf-8") as f:
            for linha in f:
                lin = linha.strip()
                if not lin or lin.startswith("#") or "=" not in lin:
                    continue
                k, _, v = lin.partition("=")
                if k.strip() == nome:
                    return v.strip()
    except OSError:
        pass
    return ""


def configurado() -> bool:
    return bool(_copia() or _ler("PIX_KEY"))


def link_pagamento() -> str:
    """Retorna o link de pagamento Pix com valor fixo, se configurado."""
    return _ler("PIX_LINK")


def _copia() -> str:
    return _ler("PIX_COPIA")


def payload_configurado() -> str:
    """Retorna o copia-e-cola Pix se configurado; string vazia caso contrário.

    Prioriza PIX_COPIA (payload oficial emitido pelo banco); se ausente, monta
    o BR Code a partir de PIX_KEY.
    """
    copia = _copia()
    if copia:
        return copia
    chave = _ler("PIX_KEY")
    if not chave:
        return ""
    nome = _ler("PIX_NOME") or "Doacao"
    cidade = _ler("PIX_CIDADE") or "Sao Luis"
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