"""Notificações: alerta por e-mail (SMTP) ou Discord quando uma triagem é CRÍTICA/ALTA.

Objetivo: transformar o app em "monitor de QA" — o time recebe a mensagem no canal
sem abrir o app. Todas as funções são à prova de erro: uma falha de rede/credencial
ou canal não configurado NUNCA pode derrubar a triagem.
"""

import ipaddress
import json
import os
import smtplib
import socket
from email.message import EmailMessage
import urllib.parse
import urllib.request
import urllib.error

_SOPADRA = "***"

# O Discord (via Cloudflare) bloqueia o User-Agent padrão do urllib do Python
# ("Python-urllib/...") como bot — código 1010. Usando um header de navegador
# o webhook responde 204 normal.
_USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
               "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")

_resolver = socket.getaddrinfo


def _webhook_seguro(url: str | None) -> bool:
    """Valida uma URL de webhook (anti-SSRF) sem tocar na rede.

    Bloqueia esquemas fora de http/https e destinos que resolvam para endereços
    de rede interna, loopback, link-local (inclui o metadata 169.254.169.254),
    multicast, reservados ou não-globais. Não faz requisição: só resolve host e
    inspeciona os endereços.
    """
    try:
        u = urllib.parse.urlparse((url or "").strip())
    except Exception:
        return False
    if u.scheme not in ("http", "https") or not u.hostname:
        return False
    try:
        registros = _resolver(u.hostname, u.port or 443, proto=socket.IPPROTO_TCP)
    except (socket.gaierror, OSError, ValueError):
        return False
    for _af, _tipo, _proto, _canon, saida in registros:
        try:
            ip = ipaddress.ip_address(saida[0])
        except (ValueError, IndexError):
            return False
        if (ip.is_loopback or ip.is_link_local or ip.is_private
                or ip.is_multicast or ip.is_reserved or ip.is_unspecified
                or not ip.is_global):
            return False
    return True

# Override por sessão: cada usuário/visitante configura o SEU (webhook, e-mail,
# remetente/senha SMTP). Fica em st.session_state (por navegador/aba) no Streamlit;
# sem runtime do Streamlit (testes) cai num dict global. Nada é gravado em disco.
_CHAVE_OVERRIDE = "cfg_override_notif"
_SESSAO: dict[str, str] = {}


def _dados_override() -> dict:
    """Dicionário de override da sessão corrente (ou fallback p/ testes)."""
    try:
        import streamlit as st
        return st.session_state.setdefault(_CHAVE_OVERRIDE, {})
    except Exception:
        return _SESSAO


def set_config(**campos: str) -> None:
    """Sobrescreve (só nesta sessão do visitante) campos de configuração.

    Valores vazios removem o override do campo (volta a valer o config do dono).
    """
    dados = _dados_override()
    for k, v in campos.items():
        v = (v or "").strip()
        if v:
            dados[k] = v
        else:
            dados.pop(k, None)


def config_sessao() -> dict:
    """Snapshot dos overrides da sessão atual."""
    return dict(_dados_override())


def limpar_config_sessao() -> None:
    """Remove todos os overrides (volta ao config do dono: secrets/env/.env)."""
    _dados_override().clear()


def _ler(nome: str) -> str:
    """Lê configuração com prioridade: sessão → st.secrets → os.environ → .env."""
    v = _dados_override().get(nome)
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
    if not url or not _webhook_seguro(url):
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
            headers={"Content-Type": "application/json", "User-Agent": _USER_AGENT},
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


_ULTIMO_ERRO_EMAIL: str | None = None


def ultimo_erro_email() -> str:
    """Motivo detalhado da última falha de e-mail (para diagnóstico no app)."""
    return _ULTIMO_ERRO_EMAIL or ""


def _enviar_email(cfg: dict, para: str, assunto: str, corpo: str, corpo_html: str | None = None) -> bool:
    """Envia e-mail via SMTP. True se enviou; nunca levanta exceção."""
    global _ULTIMO_ERRO_EMAIL
    try:
        msg = EmailMessage()
        msg["Subject"] = assunto
        msg["From"] = cfg["user"]
        msg["To"] = para
        msg.set_content(corpo)
        if corpo_html:
            msg.add_alternative(corpo_html, subtype="html")
        with smtplib.SMTP(cfg["host"], cfg["porta"], timeout=10) as smtp:
            smtp.starttls()
            smtp.login(cfg["user"], cfg["senha"])
            smtp.send_message(msg)
        _ULTIMO_ERRO_EMAIL = None
        return True
    except Exception as e:
        _ULTIMO_ERRO_EMAIL = f"{type(e).__name__}: {str(e)[:160]}"
        return False


def enviar_email(para: str, assunto: str, corpo: str, corpo_html: str | None = None) -> bool:
    """Envia um e-mail transacional a QUALQUER destinatário (ex.: comprovante).

    Reutiliza a config SMTP dos secrets (.env/Streamlit Secrets). Diferente do
    `notificar_email`/`notificar_evento` (que sempre mandam para ALERTA_EMAIL_TO),
    aqui o destino é o próprio usuário. Nunca levanta exceção.
    """
    if not (para or "").strip() or not (assunto or "").strip() or not (corpo or "").strip():
        return False
    try:
        cfg = _smtp_config()
        if not cfg["user"] or not cfg["senha"]:
            return False
        return _enviar_email(cfg, para.strip(), assunto.strip(), corpo, corpo_html=corpo_html)
    except Exception:
        return False


def testar_discord() -> tuple[bool, str]:
    """Envia um teste ao webhook do Discord configurado. Nunca levanta exceção."""
    try:
        url = webhook_discord()
        if not url:
            return False, "Sem webhook do Discord configurado."
        if not _webhook_seguro(url):
            return False, "Webhook bloqueado (URL interna/privada não é permitida)."
        payload = {"content": "✅ Teste de notificação — AI Bug Triage System"}
        corpo = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=corpo,
            headers={"Content-Type": "application/json", "User-Agent": _USER_AGENT},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 204:
                return True, "Teste enviado ao Discord."
            return False, f"Resposta inesperada do Discord (HTTP {resp.status})."
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code} — {e.reason} (Discord recusou o webhook)."
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
        return False, f"Falha ao enviar o e-mail (SMTP): {ultimo_erro_email()}"
    except Exception as e:
        return False, f"Falha inesperada ao testar e-mail: {type(e).__name__}"


def notificar_evento(titulo: str, corpo: str) -> bool:
    """Envia um aviso GENÉRICO de evento (pagamento, estorno, conta, etc.).

    Diferente de notificar_email (template de triagem com "Relato/Motor"),
    esta função manda e-mail + Discord com o texto informado, sem formatação
    de triagem. Nunca levanta exceção. Config SMTP reutilizada.
    """
    ok = False
    corpo = (corpo or "").strip()
    titulo = (titulo or "Aviso").strip()
    if not corpo:
        return False
    try:
        cfg = _smtp_config()
        para = cfg["para"]
        if para and cfg["user"] and cfg["senha"]:
            ok = _enviar_email(cfg, para, f"💳 [AI Bug Triage] {titulo}", corpo) or ok
    except Exception:
        pass
    try:
        url = webhook_discord()
        if url and _webhook_seguro(url):
            payload = {
                "content": f"💳 **{titulo}**\n{corpo[:800]}",
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": _USER_AGENT},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                ok = (resp.status == 204) or ok
    except Exception:
        pass
    return ok


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