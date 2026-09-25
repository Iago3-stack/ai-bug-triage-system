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

import notificacoes  # envio do comprovante (best-effort)

import nuvem_supabase
import pagbank
import telemetria
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
        "nome": (nome or "").strip(),
        "email": (email or "").strip(),
        "cpf": (cpf or "").strip(),
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


def regenerar_pagamento(doc: dict, cpf: str = "", nome: str = "", email: str = "") -> dict:
    """Tenta de novo gerar o QR dinâmico do PagBank NUMA cobrança já aberta.

    Não cria cobrança nova: reescreve no próprio documento os metadados do
    pedido (`pagbank_order_id`/`pagbank_qr_id`/`pix_copia_pagbank`) ou, em
    falha, o `pagbank_erro`. Usado no botão "tentar de novo" quando a primeira
    tentativa caiu no fallback manual (ex.: CPF faltando/erro da API).
    """
    nova = dict(doc)
    if pagbank.configurado():
        try:
            pago = pagbank.criar_cobranca(
                nova["valor"], nova["id"], cpf=cpf, nome=nome, email=email
            )
            nova["pagbank_order_id"] = pago["order_id"]
            nova["pagbank_qr_id"] = pago["qr_id"]
            nova["pix_copia_pagbank"] = pago["pix_copia"]
            nova.pop("pagbank_erro", None)
        except pagbank.PagbankErro as ex:
            nova["pagbank_erro"] = str(ex)
            nova.pop("pix_copia_pagbank", None)
            nova.pop("pagbank_order_id", None)
            nova.pop("pagbank_qr_id", None)
    if _usar_nuvem():
        nuvem_supabase.atualizar_cobranca(nova["id"], nova)
    else:
        _atualizar_local(nova)
    return nova


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
    """Admin confirma o pagamento -> plano vira pago no banco (+ comprovante).

    Este é o ÚNICO ponto por onde o pagamento vira "pago": tanto o webhook do
    PagBank (charge PAID) quanto a confirmação manual do dono passam por aqui.
    Por isso o comprovante é enviado aqui — garante que o assinante recebe o
    e-mail nos DOI situações, mesmo se a API do PagBank cair e a confirmação
    e-mail nos dois casos, mesmo se a API do PagBank cair e a confirmação
    for manual. O envio é best-effort e nunca quebra a confirmação.
    """
    doc = _buscar(doc_id)
    if not doc or doc.get("status") != _STATUS_ABERTO:
        return None
    atualizado = _transicao(doc, _STATUS_CONFIRMADO)
    plano.definir_plano_no_banco(doc["uid"], "pago")
    _enviar_comprovante(atualizado or doc)
    telemetria.capturar("pagamento_confirmado", usuario=doc.get("uid"), plano="pago")
    return atualizado


def _comprovante_html(nome: str, valor: str, data: str, pedido: str) -> str:
    """Corpo HTML do comprovante de pagamento (padrão visual simples)."""
    return f"""
<div style="font-family:Arial,Helvetica,sans-serif;max-width:560px;margin:0 auto;color:#111">
  <div style="background:#139c49;color:#fff;padding:18px 22px;border-radius:8px 8px 0 0">
    <div style="font-size:18px;font-weight:bold">✓ Comprovante de pagamento</div>
    <div style="opacity:.85;font-size:13px">Plano Premium — AI Bug Triage System</div>
  </div>
  <div style="border:1px solid #e2e8f0;border-top:none;border-radius:0 0 8px 8px;padding:22px">
    <p style="margin-top:0">Olá, <b>{nome}</b>,</p>
    <p>Recebemos a confirmação do seu pagamento. Seu acesso <b>Premium</b> já está liberado. 🎉</p>
    <table style="width:100%;border-collapse:collapse;margin:14px 0;font-size:14px">
      <tr><td style="padding:8px 10px;color:#555">Assinatura</td><td style="padding:8px 10px"><b>Premium</b></td></tr>
      <tr><td style="padding:8px 10px;color:#555;background:#f8fafc">Valor</td><td style="padding:8px 10px;background:#f8fafc"><b>{valor}</b>/mês</td></tr>
      <tr><td style="padding:8px 10px;color:#555">Forma de pagamento</td><td style="padding:8px 10px">PIX</td></tr>
      <tr><td style="padding:8px 10px;color:#555;background:#f8fafc">Data do pagamento</td><td style="padding:8px 10px;background:#f8fafc">{data}</td></tr>
      <tr><td style="padding:8px 10px;color:#555">Código do pedido</td><td style="padding:8px 10px">{pedido}</td></tr>
    </table>
    <p style="font-size:12px;color:#777;border-top:1px solid #e2e8f0;padding-top:12px">
      Este e-mail é um comprovante de pagamento e <b>não</b> é nota fiscal.<br>
      Para dúvidas, responda este e-mail ou fale com a gente pelo app.
    </p>
  </div>
</div>
"""


def _enviar_comprovante(doc: dict) -> bool:
    """Envia o comprovante de pagamento Premium ao assinante (best-effort).

    Usa o e-mail/nome gravados na cobrança. Se faltar e-mail ou o SMTP falhar,
    apenas retorna False — nunca interrompe a confirmação da cobrança.
    """
    email = (doc or {}).get("email") or ""
    if not email:
        return False
    try:
        nome = (doc.get("nome") or "").strip() or "assinante"
        valor = preco_texto()
        data = doc.get("atualizado_em") or doc.get("criado_em") or "—"
        pedido = (
            str(doc.get("pagbank_order_id") or "").strip()
            or f"cobrança {doc.get('id') or ''}"
        ).strip()
        assunto = "Comprovante de pagamento — Premium (AI Bug Triage)"
        corpo = (
            f"Olá, {nome},\n\n"
            "Recebemos a confirmação do seu pagamento do plano Premium. "
            "Seu acesso Premium já está liberado.\n\n"
            f"• Assinatura: Premium\n"
            f"• Valor: {valor}/mês\n"
            f"• Forma de pagamento: PIX\n"
            f"• Data do pagamento: {data}\n"
            f"• Código do pedido: {pedido}\n\n"
            "Este e-mail é um comprovante de pagamento e não é nota fiscal.\n"
            "Para dúvidas, responda este e-mail."
        )
        return bool(
            notificacoes.enviar_email(email, assunto, corpo, corpo_html=_comprovante_html(nome, valor, data, pedido))
        )
    except Exception:
        return False


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