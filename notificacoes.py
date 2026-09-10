"""Notificações: alerta por e-mail (SMTP) ou Discord quando uma triagem é CRÍTICA/ALTA.

Objetivo: transformar o app em "monitor de QA" — o time recebe a mensagem no canal
sem abrir o app. Todas as funções são à prova de erro: uma falha de rede/credencial
ou canal não configurado NUNCA pode derrubar a triagem.
"""

import json
import os
import smtplib
from email.message import EmailMessage
import urllib.request

_SOPADRA = "***"

# Override por sessão (cada usuário/empresa configura o seu): campos aqui têm
# prioridade sobre secrets/env/.env. Nada é gravado em disco — some no reload.
_SESSAO: dict[str, str] = {}


def set_config(**campos: str) -> None:
    """Sobrescreve (só nesta sessão) campos de configuração.

    Valores vazios removem o override do campo (volta a valer o config do dono).
    """
    for k, v in campos.items():
        v = (v or "").strip()
        if v:
            _SESSAO[k] = v
        else:
            _SESSAO.pop(k, None)


def config_sessao() -> dict:
    """Snapshot dos overrides da sessão atual."""
    return dict(_SESSAO)


def limpar_config_sessao() -> None:
    """Remove todos os overrides (volta ao config do dono: secrets/env/.env)."""
    _SESSAO.clear()


def _ler(nome: str) -> str:
    """Lê configuração com prioridade: sessão → st.secrets → os.environ → .env."""
    v = _SESSAO.get(nome)
    if v is not None:
        return str(v).strip()
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


def email_configurado() -> bool:
    """True se o e-mail está pronto (destinatário + remetente + senha SMTP)."""
    cfg = _smtp_config()
    return bool(cfg["para"] and cfg["user"] and cfg["senha"])


def discord_configurado() -> bool:
    """True se há webhook do Discord configurado."""
    return bool(webhook_discord())


def _merece_alerta(prioridade_final: str) -> bool:
    return bool(prioridade_final) and ("CRÍTICA" in prioridade_final or "ALTA" in prioridade_final)


def _cor(prioridade: str) -> int:
    return 0xDC2626 if "CRÍTICA" in prioridade else 0xEA580C


def notificar_discord(prioridade_final: str, resumo: str, provedor: str | None = None) -> bool:
    """Envia alerta no Discord quando a prioridade for CRÍTICA/ALTA.

    Retorna True se enviou, False se não se aplica / sem webhook / falha.
    Nunca levanta exceção.
    """
    if not _merece_alerta(prioridade_final):
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


def _smtp_config() -> dict:
    """Configuração SMTP (Gmail por padrão) — campos vazios = desligado."""
    try:
        _porta = int(str(_ler("SMTP_PORT") or "").strip())
        if not (1 <= _porta <= 65535):
            _porta = 587
    except (TypeError, ValueError):
        _porta = 587
    return {
        "para": _ler("ALERTA_EMAIL_TO"),
        "user": _ler("SMTP_USER"),
        "senha": _ler("SMTP_PASS"),
        "host": _ler("SMTP_HOST") or "smtp.gmail.com",
        "porta": _porta,
    }


def _enviar_email(cfg: dict, para: str, assunto: str, corpo: str) -> bool:
    """Envia e-mail via SMTP. True se enviou; nunca levanta exceção."""
    try:
        msg = EmailMessage()
        msg["Subject"] = assunto
        msg["From"] = cfg["user"]
        msg["To"] = para
        msg.set_content(corpo)
        with smtplib.SMTP(cfg["host"], cfg["porta"], timeout=10) as smtp:
            smtp.starttls()
            smtp.login(cfg["user"], cfg["senha"])
            smtp.send_message(msg)
        return True
    except Exception:
        return False


def testar_discord() -> tuple[bool, str]:
    """Envia um teste ao webhook do Discord configurado. Nunca levanta exceção."""
    try:
        url = webhook_discord()
        if not url:
            return False, "Sem webhook do Discord configurado."
        payload = {"content": "✅ Teste de notificação — AI Bug Triage System"}
        corpo = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=corpo,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 204:
                return True, "Teste enviado ao Discord."
            return False, f"Resposta inesperada do Discord (HTTP {resp.status})."
    except Exception as e:
        return False, f"Falha ao enviar: {type(e).__name__}"


def testar_email() -> tuple[bool, str]:
    """Envia um e-mail de teste pelo SMTP configurado. Nunca levanta exceção."""
    try:
        cfg = _smtp_config()
        if not (cfg["para"] and cfg["user"] and cfg["senha"]):
            return False, "E-mail não configurado (destinatário + usuário + senha SMTP)."
        if _enviar_email(
            cfg,
            cfg["para"],
            "🧪 [AI Bug Triage] Teste de notificação",
            "✅ Teste de notificação — AI Bug Triage System.\n\n"
            "Se você recebeu este e-mail, o canal de alertas está funcionando.",
        ):
            return True, "E-mail de teste enviado."
        return False, "Falha ao enviar o e-mail (SMTP)."
    except Exception as e:
        return False, f"Falha inesperada ao testar e-mail: {type(e).__name__}"


def notificar_email(prioridade_final: str, resumo: str, provedor: str | None = None) -> bool:
    """Envia e-mail (SMTP) quando a prioridade for CRÍTICA/ALTA.

    Config (secrets/.env): ALERTA_EMAIL_TO (destinatário), SMTP_USER + SMTP_PASS
    (para Gmail: seu e-mail + um "app password" do Google). SMTP_HOST/SMTP_PORT
    são opcionais (padrão smtp.gmail.com:587).
    Retorna True se enviou, False se não se aplica / sem config / falha.
    Nunca levanta exceção.
    """
    if not _merece_alerta(prioridade_final):
        return False
    cfg = _smtp_config()
    para = cfg["para"]
    if not para or not cfg["user"] or not cfg["senha"]:
        return False
    return _enviar_email(
        cfg,
        para,
        f"🚨 [AI Bug Triage] {prioridade_final} — {resumo[:60]}",
        "🚨 Uma triagem crítica foi detectada pelo AI Bug Triage System.\n\n"
        f"Prioridade final: {prioridade_final}\n"
        f"Relato: {(resumo or '—')[:800]}\n"
        f"Motor: {provedor or 'offline (léxico)'}\n\n"
        "Abra o app para ver a triagem completa.",
    )