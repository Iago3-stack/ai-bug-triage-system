"""Guardrails de entrada/saída: detecta e mascara credenciais/PII no relato.

Objetivo: impedir que tokens, chaves de API e e-mails digitados no relato do bug
vazem para o Gemini, o Jira, o GitHub ou o histórico persistido.
"""

import re

_PADROES: dict[str, re.Pattern] = {
    "token Atlassian": re.compile(r"ATATT3xFf[A-Za-z0-9_\-=:.]+"),
    "chave Gemini/Google (Shift)": re.compile(r"AQ\.Ab[A-Za-z0-9_\-\.]+"),
    "chave API Google": re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),
    "token OpenAI": re.compile(r"sk-[A-Za-z0-9]{20,}"),
    "token GitHub (clássico)": re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    "token GitHub (fine-grained)": re.compile(r"github_pat_[A-Za-z0-9_]{40,}"),
    "e-mail": re.compile(r"(?<![A-Za-z0-9])[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)+"),
    "senha (com números)": re.compile(r"\b(?:senha|pin)\b[:\s\-]*\d[\d\s.\-]{5,}"),
    "telefone": re.compile(r"\(?\d{2}\)?\s*\d{4,5}[-.\s]?\d{4}"),
    "CPF": re.compile(r"\d{3}\.?\d{3}\.?\d{3}[-.]?\d{2}"),
}

MANCER_ADOR = "***"


def detectar(texto: str) -> list[str]:
    """Retorna a lista ordenada de credenciais/PII encontradas (sem duplicatas)."""
    encontrados = []
    for nome, padrao in _PADROES.items():
        if padrao.search(texto or ""):
            encontrados.append(nome)
    return encontrados


def contem_credencial(texto: str) -> bool:
    return bool(detectar(texto))


def mascarar(texto: str, adorno: str = MANCER_ADOR) -> str:
    """Substitui cada ocorrência de credencial/PII pelo adorno."""
    resultado = texto or ""
    for padrao in _PADROES.values():
        resultado = padrao.sub(adorno, resultado)
    return resultado