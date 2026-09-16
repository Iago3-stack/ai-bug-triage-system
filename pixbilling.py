"""Módulo de pagamento próprio ("nosso Stripe") — cobrança 100% Pix, sem gateway.

Passo 4 do caminho SaaS: cliente escolhe Premium, o app gera uma cobrança
(solicitação de pagamento) com QR Pix + copia-e-cola; ao pagar, marca "Já
paguei" e o dono da conta confirma manualmente — o plano passa a "pago".

Fluxo:
  1. gerar_cobranca(uid)         -> document {id, uid, valor, status:'aguardando'}
  2. cliente paga o Pix (QR/copia-e-cola) e clica "Já paguei"
  3. admin confirma (confirmar_cobranca) -> plano vira pago no banco
  4. estorno: cliente solicita, admin devolve via Pix e marca estornado

Valores/regras (ajustáveis por env):
  PLANO_PRECO   valor mensal do Premium (padrão: 19.99)
  PIX_*         reuso do pix.py (chave/QR/copia-e-cola)

Ambos os caminhos seguem a dinâmica "Pix + confirmação manual" — sem taxa,
personalizado e com ciclo de estorno controlado pelo dono.
"""
import json
import os
import pathlib
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

import nuvem_supabase
import pagbank
import pix
import plano

_RAIZ = pathlib.Path(__file__).resolve().parent
_ARQUIVO_COBRANCAS = _RAIZ / "data" / "cobrancas.jsonl"
_FUSO = ZoneInfo(os.environ.get("PERSISTENCIA_FUSO", "America/Sao_Paulo"))

_STATUS_ABERTO = "aguardando"
_STATUS_CONFIRMADO = "confirmado"
_STATUS_CANCELADO = "cancelado"
_STATUS_ESTORNO = "estorno"
_STATUS_ESTORNADO = "estornado"
_VALIDOS = (_STATUS_ABERTO, _STATUS_CONFIRMADO, _STATUS_CANCELADO, _STATUS_ESTORNO, _STATUS_ESTORNADO)


def preco() -> float | int:
    """Valor mensal do Premium (padrão R$ 19,99). Aceita vírgula ou ponto no env."""
    try:
        return float(str(os.environ.get("PLANO_PRECO", "19.99")).replace(",", "."))
    except (TypeError, ValueError):
        return 19.99


def preco_texto() -> str:
    v = preco()
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _usar_nuvem() -> bool:
    """Nuvem ativa quando configurada; JSONL local é o fallback (testes/offline)."""
    if os.environ.get("PIXBILLING_BACKEND") == "jsonl":
        return False
    if os.environ.get("PIXBILLING_ARQUIVO"):
        return False
    return nuvem_supabase.disponivel()


def _caminho() -> pathlib.Path:
    return pathlib.Path(os.environ.get("PIXBILLING_ARQUIVO", str(_ARQUIVO_COBRANCAS)))


def _agora() -> str:
    return datetime.now(_FUSO).strftime("%Y-%m-%dT%H:%M:%S%z")


def _ler_jsonl() -> list[dict]:
    caminho = _caminho()
    if not caminho.exists():
        return []
    with caminho.open(encoding="utf-8") as f:
        return [json.loads(linha) for linha in f if linha.strip()]


def _salvar_jsonl(doc: dict) -> dict:
    caminho = _caminho()
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("a", encoding="utf-8") as f:
        f.write(json.dumps(doc, ensure_ascii=False, sort_keys=True) + "\n")
    return doc


def _escrever_jsonl(docs: list[dict]) -> None:
    caminho = _caminho()
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(".jsonl.tmp")
    with temporario.open("w", encoding="utf-8") as f:
        for doc in docs:
            f.write(json.dumps(doc, ensure_ascii=False, sort_keys=True) + "\n")
    temporario.replace(caminho)


def _todas_local() -> list[dict]:
    return _ler_jsonl()


def _todas_nuvem() -> list[dict]:
    return nuvem_supabase.carregar_cobrancas() or []


def _persistir_nuvem(doc: dict) -> bool:
    return nuvem_supabase.gravar_cobranca(doc)


def _atualizar_local(nova: dict) -> None:
    docs = _todas_local()
    for i, doc in enumerate(docs):
        if doc.get("id") == nova.get("id"):
            docs[i] = nova
            break
    else:
        docs.append(nova)
    _escrever_jsonl(docs)


def gerar_cobranca(uid: str, cpf: str = "", nome: str = "", email: str = "") -> dict:
    """Cria uma cobrança 'aguardando' para o usuário. Retorna o documento.

    Quando o PagBank está configurado (PAGBANK_TOKEN), a cobrança ganha um
    QR Code **dinâmico** na hora (pedido na API de Pedidos) e o pagamento é
    confirmado automaticamente pelo webhook; senão, mantém o fluxo manual
    atual (Pix estático + "Já paguei"). A falha do PagBank nunca derruba a
    geração — cai no fluxo manual como fallback.
    """
    doc = {
        "id": "cob-" + uuid.uuid4().hex[:10],
        "uid": uid,
        "valor": preco(),
        "status": _STATUS_ABERTO,
        "criado_em": _agora(),
        "atualizado_em": _agora(),
    }
    if pagbank.configurado():
        try:
            pago = pagbank.criar_cobranca(
                doc["valor"], doc["id"], cpf=cpf, nome=nome, email=email
            )
            doc["pagbank_order_id"] = pago["order_id"]
            doc["pagbank_qr_id"] = pago["qr_id"]
            doc["pix_copia_pagbank"] = pago["pix_copia"]
        except pagbank.PagbankErro as ex:
            doc["pagbank_erro"] = str(ex)
    if _usar_nuvem():
        return doc if _persistir_nuvem(doc) else doc
    return _salvar_jsonl(doc)


def cobrancas_do_uid(uid: str) -> list[dict]:
    """Cobranças do usuário, mais recentes primeiro."""
    docs = _todas_nuvem() if _usar_nuvem() else _todas_local()
    do_uid = [d for d in docs if (d.get("uid") or "").lower() == (uid or "").lower()]
    return sorted(do_uid, key=lambda d: d.get("criado_em", ""), reverse=True)


def pendentes() -> list[dict]:
    """Cobranças aguardando confirmação (painel do admin). Mais recentes primeiro."""
    docs = _todas_nuvem() if _usar_nuvem() else _todas_local()
    abertas = [d for d in docs if d.get("status") == _STATUS_ABERTO]
    return sorted(abertas, key=lambda d: d.get("criado_em", ""), reverse=True)


def estornos() -> list[dict]:
    """Pedidos de estorno aguardando devolução (painel do admin)."""
    docs = _todas_nuvem() if _usar_nuvem() else _todas_local()
    pedidos = [d for d in docs if d.get("status") == _STATUS_ESTORNO]
    return sorted(pedidos, key=lambda d: d.get("criado_em", ""), reverse=True)


def _buscar(doc_id: str) -> dict | None:
    for d in (_todas_nuvem() if _usar_nuvem() else _todas_local()):
        if d.get("id") == doc_id:
            return d
    return None


def buscar_cobranca(doc_id: str) -> dict | None:
    """Busca pública de uma cobrança pelo id (usada pelo webhook de pagamento)."""
    return _buscar(doc_id)


def _transicao(doc: dict, novo_status: str, extra: dict | None = None) -> dict:
    novo = dict(doc)
    novo["status"] = novo_status
    novo["atualizado_em"] = _agora()
    if extra:
        novo.update(extra)
    if _usar_nuvem():
        nuvem_supabase.atualizar_cobranca(doc["id"], novo)
    else:
        _atualizar_local(novo)
    return novo


def confirmar_cobranca(doc_id: str) -> dict | None:
    """Admin confirma o pagamento -> plano vira pago no banco."""
    doc = _buscar(doc_id)
    if not doc or doc.get("status") != _STATUS_ABERTO:
        return None
    atualizado = _transicao(doc, _STATUS_CONFIRMADO)
    plano.definir_plano_no_banco(doc["uid"], "pago")
    return atualizado


def cancelar_cobranca(doc_id: str) -> dict | None:
    """Admin cancela uma cobrança ainda não paga (mantém plano atual)."""
    doc = _buscar(doc_id)
    if not doc or doc.get("status") != _STATUS_ABERTO:
        return None
    return _transicao(doc, _STATUS_CANCELADO)


def solicitar_estorno(doc_id: str, motivo: str = "") -> dict | None:
    """Cliente pede devolução de um pagamento confirmado."""
    doc = _buscar(doc_id)
    if not doc or doc.get("status") != _STATUS_CONFIRMADO:
        return None
    return _transicao(doc, _STATUS_ESTORNO, {"motivo": motivo})


def estornar(doc_id: str, motivo: str = "") -> dict | None:
    """Admin devolve via Pix e marca o pedido como estornado -> volta a Basic."""
    doc = _buscar(doc_id)
    if not doc or doc.get("status") != _STATUS_ESTORNO:
        return None
    atualizado = _transicao(doc, _STATUS_ESTORNADO, {"motivo": motivo})
    plano.definir_plano_no_banco(doc["uid"], "free")
    return atualizado


def status_rotulo(status: str) -> str:
    return {
        _STATUS_ABERTO: "Aguardando pagamento",
        _STATUS_CONFIRMADO: "Pago",
        _STATUS_CANCELADO: "Cancelado",
        _STATUS_ESTORNO: "Estorno solicitado",
        _STATUS_ESTORNADO: "Estornado",
    }.get(status, status)


def payload_pix(valor: float | None = None) -> str:
    """Copia-e-cola Pix DA ASSINATURA (Premium).

    Prioridade:
      1. PIX_COPIA_PLANO  — código fixo gerado no seu banco (ex.: Itaú/PagSeguro),
                            já carrega o valor da assinatura embutido;
      2. PIX_COPIA        — copia-e-cola geral configurado (doação/reusa);
      3. payload padrão   — montado da PIX_KEY (sem valor embutido).
    """
    dedicado = pix._ler("PIX_COPIA_PLANO")
    if dedicado:
        return dedicado
    geral = pix._ler("PIX_COPIA")
    if geral:
        return geral
    try:
        return pix.payload_configurado()
    except Exception:
        return ""


def pix_da_cobranca(cobranca: dict) -> str:
    """Copia-e-cola a exibir para a cobrança: o QR dinâmico do PagBank, se
    existir; senão cai no Pix estático/manual da assinatura."""
    dinâmico = (cobranca or {}).get("pix_copia_pagbank")
    if dinâmico:
        return dinâmico
    return payload_pix((cobranca or {}).get("valor"))