"""Cobrança Pix automática via API de Pedidos (Orders) do PagBank.

Transforma o "nosso Stripe" (confirmação manual) em checkout automático de
Pix: o app cria um pedido com QR Code dinâmico (valor, expiração e URL de
notificação) e o webhook (webhook.py -> /webhook/pagamento) confirma a
cobrança sozinho quando ela chega ao status ``PAID``.

Fluxo:
  1. pagbank.criar_cobranca(...)          -> pedido ORDE_* + QRCO_* + copia-e-cola
  2. cliente paga o QR/copia-e-cola no banco
  3. PagBank POSTa a notificação em PAGBANK_WEBHOOK_URL (evento de status)
  4. webhook.py consulta o pedido, vê PAID e chama pixbilling.confirmar_cobranca
     (idempotente) -> plano vira pago sem ação manual.

Config (st.secrets -> env -> .env, jamais commitada):
  PAGBANK_TOKEN           token de integração (PagBank: Integrações -> Gerar Token)
  PAGBANK_API             base da API (padrão: https://api.pagseguro.com;
                          sandbox: https://sandbox.api.pagseguro.com)
  PAGBANK_VALIDADE_HORAS  validade do QR Code em horas (padrão: 24)
  PAGBANK_WEBHOOK_URL     URL pública que o PagBank notifica (ex.: Render
                          https://ai-bug-triage-system-webhook.onrender.com/webhook/pagamento)

Segurança: o token nunca sai do secrets/.env; a confirmação do webhook é
reverificada consultando a API (estado real do pedido), logo não dá para
"forjar" um pagamento enviando um JSON falso.
"""
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pix
import requests

_BASE_PADRAO = "https://api.pagseguro.com"
_FUSO = ZoneInfo(os.environ.get("PERSISTENCIA_FUSO", "America/Sao_Paulo"))
_TIMEOUT = 20


class PagbankErro(RuntimeError):
    """Falha ao criar ou consultar um pedido no PagBank."""


def _ler(nome: str) -> str:
    """Lê configuração com prioridade: st.secrets → os.environ → .env (igual pix.py)."""
    return pix._ler(nome)


def token() -> str:
    return _ler("PAGBANK_TOKEN").strip()


def base_url() -> str:
    """URL base da API de Pedidos (sandbox via PAGBANK_API)."""
    return (_ler("PAGBANK_API").strip().rstrip("/") or _BASE_PADRAO)


def validade_horas() -> int:
    try:
        return max(1, int(float(_ler("PAGBANK_VALIDADE_HORAS"))))
    except (TypeError, ValueError):
        return 24


def configurado() -> bool:
    """PagBank ativo quando o token de integração está configurado."""
    return bool(token())


def webhook_url() -> str:
    """URL pública que o PagBank deve notificar (obrigatória p/ confirmação)."""
    return _ler("PAGBANK_WEBHOOK_URL").strip()


def _cabecalhos() -> dict:
    return {
        "Authorization": f"Bearer {token()}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _centavos(valor) -> int:
    return int(round(float(valor) * 100))


def _digitos(texto: str) -> str:
    return "".join(c for c in (texto or "") if c.isdigit())


def _expiracao_iso() -> str:
    """ISO-8601 UTC com offset (ex.: 2099-09-17T18:00:00-03:00) — válido por N horas."""
    d = datetime.now(_FUSO) + timedelta(hours=validade_horas())
    return d.replace(microsecond=0).isoformat()


def _erro_mensagem(dados: dict, status: int) -> str:
    """Extrai a mensagem de erro mais útil da resposta do PagBank."""
    mensagens = dados.get("error_messages") or []
    if isinstance(mensagens, list) and mensagens:
        detalhe = mensagens[0]
        if isinstance(detalhe, dict):
            codigo = detalhe.get("code", "")
            descricao = detalhe.get("description") or detalhe.get("message") or ""
            if descricao:
                return f"[{codigo}] {descricao}"
        return str(detalhe)
    return str(dados.get("message") or dados.get("error") or f"HTTP {status}")


def criar_cobranca(
    valor,
    reference_id: str,
    *,
    cpf: str = "",
    nome: str = "",
    email: str = "",
    notification_url: str = "",
):
    """Cria um pedido com QR Code Pix e devolve o copia-e-cola + metadados.

    Retorna dict: {"order_id", "qr_id", "pix_copia"}. Levanta ``PagbankErro``
    em qualquer falha (token ausente, URL ausente, HTTP/validação, timeout).
    O ``reference_id`` deve ser o id da cobrança interna (vira a nossa referência).
    """
    if not configurado():
        raise PagbankErro("PAGBANK_TOKEN não configurado")
    alvo = notification_url or webhook_url()
    if not alvo:
        raise PagbankErro(
            "URL de notificação ausente — configure PAGBANK_WEBHOOK_URL"
        )

    cliente = {}
    if nome:
        cliente["name"] = str(nome).strip()[:80]
    if email:
        cliente["email"] = str(email).strip()[:80]
    taxid = _digitos(cpf)[:14]
    if taxid:
        cliente["tax_id"] = taxid

    pedido = {
        "reference_id": reference_id,
        "items": [
            {
                "reference_id": "premium",
                "name": "AI Bug Triage System — Assinatura Premium (mensal)",
                "quantity": 1,
                "unit_amount": _centavos(valor),
            }
        ],
        "qr_codes": [
            {
                "amount": {"value": _centavos(valor)},
                "expiration_date": _expiracao_iso(),
            }
        ],
        "notification_urls": [alvo],
    }
    if cliente:
        pedido["customer"] = cliente

    try:
        resposta = requests.post(
            f"{base_url()}/orders", headers=_cabecalhos(), json=pedido, timeout=_TIMEOUT
        )
    except (requests.RequestException, OSError) as ex:
        raise PagbankErro(f"falha de rede: {ex}") from ex

    try:
        dados = resposta.json()
    except ValueError as ex:
        raise PagbankErro(
            f"resposta não-JSON do PagBank (HTTP {resposta.status_code})"
        ) from ex

    if resposta.status_code >= 400:
        raise PagbankErro(f"{_erro_mensagem(dados, resposta.status_code)}")

    qrs = dados.get("qr_codes") or dados.get("qr_code") or []
    if not qrs:
        raise PagbankErro("Pedido criado sem QR Code na resposta")
    primeiro = qrs[0] if isinstance(qrs, list) else qrs
    return {
        "order_id": dados.get("id"),
        "qr_id": primeiro.get("id"),
        "pix_copia": primeiro.get("text"),
    }


def consultar_pedido(order_id: str) -> dict:
    """Consulta o estado real de um pedido na API (para validar a notificação)."""
    if not configurado():
        raise PagbankErro("PAGBANK_TOKEN não configurado")
    try:
        resposta = requests.get(
            f"{base_url()}/orders/{order_id}", headers=_cabecalhos(), timeout=_TIMEOUT
        )
    except requests.RequestException as ex:
        raise PagbankErro(f"falha de rede: {ex}") from ex
    try:
        dados = resposta.json()
    except ValueError as ex:
        raise PagbankErro(
            f"resposta não-JSON do PagBank (HTTP {resposta.status_code})"
        ) from ex
    if resposta.status_code >= 400:
        raise PagbankErro(_erro_mensagem(dados, resposta.status_code))
    return dados


def pagamento_confirmado(pedido: dict) -> bool:
    """True quando alguma cobrança (charge) do pedido está com status PAID."""
    for charge in (pedido or {}).get("charges") or []:
        if charge.get("status") == "PAID":
            return True
    return False