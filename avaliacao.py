"""Rótulo humano de severidade por triagem — o "ground truth" que faltava.

Por que: o único conjunto rotulado do projeto tinha 30 casos sintéticos, e o
motor semântico do v3.1.0 passou nele parecendo bom (+13 pontos) e foi revertido
no v3.2.0 depois de medido no histórico real. Sem rótulo em cima das triagens
reais, qualquer motor novo continua sendo julgado no escuro.

Como: o rótulo viaja dentro do `payload` (jsonb) da própria triagem, na chave
`avaliacao` — **sem migration e sem tabela nova** (Postgres jsonb aceita chave
nova; o PATCH reescreve o objeto inteiro, mesmo padrão de `registrar_resolucao`).
O rótulo é a severidade REAL do problema, não o texto: quem rotulou já sabe.

Leitura agregada (`carregar_rotulados`) é ferramenta do dono/admin: devolve os
textos para o harness `avaliar_lexico.py`; a UI do app só mostra contagem.
"""

from datetime import datetime, timezone
import unicodedata

import nuvem_supabase

ROTULOS = ("CRÍTICA", "MÉDIA", "NORMAL")

# A camada de IA usa 4 níveis (CRÍTICA/ALTA/MÉDIA/BAIXA) e o léxico 3
# (CRÍTICA/MÉDIA/NORMAL). O rótulo humano é sempre nas 3 canônicas.
# As chaves são SEM acento (entrada passa por NFKD), os valores são canônicos.
_ALIAS = {
    "CRITICA": "CRÍTICA", "ALTA": "CRÍTICA",
    "MEDIA": "MÉDIA",
    "NORMAL": "NORMAL", "BAIXA": "NORMAL",
}
_GRAVIDADE_PARA_ROTULO = {"CRÍTICA": "CRÍTICA", "MÉDIA": "MÉDIA", "NORMAL": "NORMAL"}


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalizar(rotulo: str) -> str:
    """'CRÍTICA 🚨' / 'alta' / 'BAIXA' -> 'CRÍTICA' / 'CRÍTICA' / 'NORMAL'.

    Aceita acento ou não (NFKD) e devolve '' quando não mapeia.
    """
    if not rotulo:
        return ""
    bruto = str(rotulo).split(" ")[0].strip().upper()
    sem_acento = "".join(c for c in unicodedata.normalize("NFKD", bruto) if not unicodedata.combining(c))
    return _ALIAS.get(sem_acento, "")


def registrar(registro_id: str, rotulo: str, comentario: str = "", autor: str = "") -> bool:
    """Grava o rótulo de severidade real no payload da triagem.

    True só se a triagem existir e o payload for reescrito com sucesso.
    Rótulo vazio/inválido ou triagem inexistente → False (não levanta).
    """
    canonico = normalizar(rotulo)
    if not registro_id or not canonico:
        return False
    try:
        doc = nuvem_supabase.requests.get(
            f"{nuvem_supabase._base_url()}/{nuvem_supabase._TABELA_PADRAO}",
            headers=nuvem_supabase._headers(),
            params={"select": "id,payload", "id": f"eq.{registro_id}", "limit": "1"},
            timeout=15,
        )
        doc.raise_for_status()
        docs = doc.json() or []
        if not docs:
            return False
        payload = dict(docs[0].get("payload") or {})
        payload["avaliacao"] = {
            "rotulo": canonico,
            "comentario": (comentario or "").strip()[:500],
            "em": _agora(),
            "autor": (autor or "").strip()[:120],
        }
        resp = nuvem_supabase.requests.patch(
            f"{nuvem_supabase._base_url()}/{nuvem_supabase._TABELA_PADRAO}",
            headers=nuvem_supabase._headers(),
            params={"id": f"eq.{registro_id}"},
            json={"payload": payload},
            timeout=15,
        )
        resp.raise_for_status()
        return True
    except Exception:
        return False


def estado_de(registro_id: str) -> dict:
    """Rótulo salvo + prioridade final persistida (aquela que o usuário viu).

    {} quando a triagem não existe, a nuvem falha ou ainda não há rótulo.
    """
    vazio = {"rotulo": "", "comentario": "", "em": "", "prioridade": ""}
    if not registro_id:
        return dict(vazio)
    try:
        resp = nuvem_supabase.requests.get(
            f"{nuvem_supabase._base_url()}/{nuvem_supabase._TABELA_PADRAO}",
            headers=nuvem_supabase._headers(),
            params={"select": "payload", "id": f"eq.{registro_id}", "limit": "1"},
            timeout=15,
        )
        resp.raise_for_status()
        docs = resp.json() or []
        if not docs:
            return dict(vazio)
        payload = docs[0].get("payload") or {}
        aval = payload.get("avaliacao") or {}
        prioridade = normalizar(payload.get("prioridade_final") or payload.get("gravidade") or "")
        return {
            "rotulo": normalizar(aval.get("rotulo", "")),
            "comentario": (aval.get("comentario") or "").strip(),
            "em": aval.get("em", ""),
            "prioridade": prioridade,
        }
    except Exception:
        return dict(vazio)


def _linhas_rotuladas(limite: int = 1000) -> list[dict]:
    """Linhas com `payload->avaliacao->>rotulo` presente.

    O filtro é no servidor (PostgREST aceita a chave `payload->avaliacao->>rotulo`),
    então não varreram as triagens sem rótulo. Ainda assim normalizamos e pulamos
    linha sem texto/rótulo: dado velho ou escrito à mão não entra na base.
    """
    resp = nuvem_supabase.requests.get(
        f"{nuvem_supabase._base_url()}/{nuvem_supabase._TABELA_PADRAO}",
        headers=nuvem_supabase._headers(),
        params={
            "select": "id,data_hora,payload",
            "payload->avaliacao->>rotulo": "not.is.null",
            "order": "data_hora.desc",
            "limit": str(limite),
        },
        timeout=20,
    )
    resp.raise_for_status()
    saida = []
    for linha in resp.json() or []:
        payload = linha.get("payload") or {}
        aval = payload.get("avaliacao") or {}
        rotulo = normalizar(aval.get("rotulo", ""))
        if not rotulo:
            continue
        saida.append(
            {
                "id": linha.get("id", ""),
                "data_hora": linha.get("data_hora", ""),
                "descricao": (payload.get("descricao") or "").strip(),
                "gravidade": _GRAVIDADE_PARA_ROTULO.get(
                    (payload.get("gravidade") or "").split(" ")[0], ""
                ),
                "rotulo": rotulo,
                "comentario": (aval.get("comentario") or "").strip(),
                "em": aval.get("em", ""),
            }
        )
    return saida


def carregar_rotulados(limite: int = 1000) -> list[dict]:
    """Triagens com rótulo humano (texto + rótulo). Vazio lista se a nuvem falhar."""
    try:
        return [r for r in _linhas_rotuladas(limite) if r["descricao"]]
    except Exception:
        return []


def progresso() -> dict:
    """Contagem para a UI (sem texto de relato): total, rótuladas,pendentes."""
    vazio = {"total": 0, "rotuladas": 0, "pendentes": 0, "erro": False}
    try:
        resp = nuvem_supabase.requests.get(
            f"{nuvem_supabase._base_url()}/{nuvem_supabase._TABELA_PADRAO}",
            headers=nuvem_supabase._headers(),
            params={"select": "id", "limit": "1000"},
            timeout=20,
        )
        resp.raise_for_status()
        total = len(resp.json() or [])
    except Exception:
        return {**vazio, "total": 0, "rotuladas": 0, "pendentes": 0, "erro": True}
    rotuladas = len(_linhas_rotuladas())
    return {
        "total": total,
        "rotuladas": rotuladas,
        "pendentes": max(total - rotuladas, 0),
        "erro": False,
    }
