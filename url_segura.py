"""Validação anti-SSRF de URL — fonte única do repo.

Bloqueia esquemas fora de http/https e destinos que resolvam para endereços de
rede interna, loopback, link-local (inclui o metadata 169.254.169.254),
multicast, reservados ou não-globais. Não faz requisição: só resolve host e
inspeciona os endereços.

Dois níveis de permissão:

- ``url_segura(url)`` — o padrão, sem exceção: nenhum destino interno.
  Usado pelos webhooks de notificação (Discord/SMTP), que nunca precisam de
  rede privada.
- ``url_modelo_segura(url)`` — para a Base URL do modelo OpenAI-compatível
  trazido pelo usuário (Ollama/local). Só relaxa o ``loopback`` (127.0.0.1/::1)
  e **somente** com ``ALLOW_LOCAL_MODELS=1``; privado, link-local e metadata
  continuam bloqueados com a flag ligada. Default é negar: sem a flag, a cloud
  fecha sozinha e nenhum esquecimento abre a porta.

A validação acontece em dois momentos, e os dois importam:

- ao salvar o modelo na UI (erro cedo, antes de qualquer requisição);
- de novo antes do ``requests.post`` em ``ia.py`` — porque a resolução de DNS
  no salvar não vale para depois: um host público pode rebindar para IP privado
  entre os dois momentos.
"""

import ipaddress
import os
import socket
import urllib.parse

_resolver = socket.getaddrinfo


def loopback_de_modelo_permitido() -> bool:
    """True só com ``ALLOW_LOCAL_MODELS=1`` no ambiente (default: negar)."""
    return os.environ.get("ALLOW_LOCAL_MODELS", "").strip() == "1"


def url_segura(url: str | None, *, permitir_loopback: bool = False) -> bool:
    """Valida uma URL (anti-SSRF) sem tocar na rede.

    Retorna False para esquema não-http, host ausente, DNS inválido e qualquer
    endereço interno/privado. ``permitir_loopback=True`` deixa passar **apenas**
    loopback; link-local/metadata, privado, multicast e não-globais continuam
    bloqueados.
    """
    try:
        u = urllib.parse.urlparse((url or "").strip())
    except (ValueError, AttributeError):
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
        if permitir_loopback and ip.is_loopback:
            continue
        if (ip.is_loopback or ip.is_link_local or ip.is_private
                or ip.is_multicast or ip.is_reserved or ip.is_unspecified
                or not ip.is_global):
            return False
    return True


def url_modelo_segura(url: str | None) -> bool:
    """Base URL do modelo custom: público liberado, loopback só com a flag."""
    return url_segura(url, permitir_loopback=loopback_de_modelo_permitido())
