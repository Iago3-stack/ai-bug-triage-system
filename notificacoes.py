"""Notificações: alerta no Discord quando uma triagem é CRÍTICA/ALTA.

Objetivo: transformar o app em "monitor de QA" — o time recebe a mensagem no
canal sem abrir o app. Todas as funções são à prova de erro: uma falha de rede
ou webhook ausente NUNCA pode derrubar a triagem.
"""

import json
import os
import urllib.request

_SOPADRA = "***"


def _ler(nome: str) -> str:
    """Lê configuração com prioridade: st.secrets → os.environ → .env."""
    try:
        import streamlit as st

        v = st.secrets.get(nome)
        if v:
            return str(v).strip()
    except Exception:
        pass
    v = os.getenv(nome, "").strip()
    if v:
        return v
    return _ler_env(nome)


def _ler_env(nome: str) -> str:
    caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    try:
        with open(caminho, encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if linha.startswith(nome + "="):
                    return linha.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return ""


def webhook_discord() -> str:
    """URL do webhook do Discord configurada (vazia = recurso desligado)."""
    return _ler("DISCORD_WEBHOOK")


def _cor(prioridade: str) -> int:
    return 0xDC2626 if "CRÍTICA" in prioridade else 0xEA580C


def notificar_discord(prioridade_final: str, resumo: str, provedor: str | None = None) -> bool:
    """Envia alerta no Discord quando a prioridade for CRÍTICA/ALTA.

    Retorna True se enviou, False se não se aplica / sem webhook / falha.
    Nunca levanta exceção.
    """
    if not prioridade_final or not ("CRÍTICA" in prioridade_final or "ALTA" in prioridade_final):
        return False
    url = webhook_discord()
    if not url:
        return False
    try:
        payload = {
            "content": "🚨 **Nova triagem crítica detectada pelo AI Bug Triage System!**",
            "embeds": [
                {
                    "title": "Triagem " + prioridade_final,
                    "description": (resumo or "—")[:800],
                    "color": _cor(prioridade_final),
                    "fields": [
                        {"name": "🎯 Prioridade", "value": prioridade_final, "inline": True},
                        {
                            "name": "🧠 Motor",
                            "value": (provedor or "offline (léxico)")[:100],
                            "inline": True,
                        },
                    ],
                }
            ],
        }
        corpo = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=corpo,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 204
    except Exception:
        return False