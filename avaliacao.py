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


def _linhas(limite: int = 1000, deslocamento: int = 0, apenas_rotuladas: bool = True) -> list[dict]:
    """Linhas com (ou sem) `payload->avaliacao->>rotulo`, filtradas no servidor.

    PostgREST aceita `payload->avaliacao->>rotulo` com `not.is.null` / `is.null`,
    então nunca varramos a tabela inteira. Ainda assim normalizamos e pulamos
    linha sem texto (pendente) ou sem rótulo canônico (rotulada): dado velho ou
    escrito à mão não entra na base.

    Devolve as DUAS previsões do app, porque elas respondem perguntas diferentes:
      gravidade  — o que o léxico (triagem.py) previu
      prioridade — o que o usuário viu (léxico x IA reconciliados em ferramenta.py)
    """
    resp = nuvem_supabase.requests.get(
        f"{nuvem_supabase._base_url()}/{nuvem_supabase._TABELA_PADRAO}",
        headers=nuvem_supabase._headers(),
        params={
            "select": "id,data_hora,payload",
            "payload->avaliacao->>rotulo": "not.is.null" if apenas_rotuladas else "is.null",
            "order": "data_hora.desc",
            "limit": str(limite),
            "offset": str(deslocamento),
        },
        timeout=20,
    )
    resp.raise_for_status()
    saida = []
    for linha in resp.json() or []:
        payload = linha.get("payload") or {}
        aval = payload.get("avaliacao") or {}
        rotulo = normalizar(aval.get("rotulo", ""))
        descricao = (payload.get("descricao") or "").strip()
        if not descricao:
            continue
        if apenas_rotuladas and not rotulo:
            continue
        linha_saida = {
            "id": linha.get("id", ""),
            "data_hora": linha.get("data_hora", ""),
            "descricao": descricao,
            "gravidade": _GRAVIDADE_PARA_ROTULO.get(
                (payload.get("gravidade") or "").split(" ")[0], ""
            ),
            "prioridade": normalizar(payload.get("prioridade_final") or "")
            or _GRAVIDADE_PARA_ROTULO.get(
                (payload.get("gravidade") or "").split(" ")[0], ""
            ),
        }
        if apenas_rotuladas:
            linha_saida.update({
                "rotulo": rotulo,
                "comentario": (aval.get("comentario") or "").strip(),
                "em": aval.get("em", ""),
                "autor": (aval.get("autor") or "").strip(),
            })
        saida.append(linha_saida)
    return saida


AUTOR_AGENTE = "agente"


def carregar_rotulados(limite: int = 1000, apenas_humanos: bool = True) -> list[dict]:
    """Triagens com rótulo humano (texto + rótulo). Vazio lista se a nuvem falhar.

    `apenas_humanos=True` (padrão) descarta os rótulos gravados com
    `autor=AUTOR_AGENTE`: o julgamento do agente não é ground truth, então não
    pode entrar na métrica de concordância nem na base exportável. Passe `False`
    para ver tudo, incluindo as pré-rotulagens do agente.
    """
    try:
        linhas = _linhas(limite, apenas_rotuladas=True)
    except Exception:
        return []
    if not apenas_humanos:
        return linhas
    return [linha for linha in linhas if linha.get("autor") != AUTOR_AGENTE]


def _chave_texto(texto: str) -> str:
    """Chave de agrupamento: minúsculas, sem acento, espaços normalizados."""
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFKD", (texto or "").lower())
        if not unicodedata.combining(c)
    )
    return " ".join(sem_acento.split())


def _agrupar(linhas: list[dict], limite: int, deslocamento: int, unicos: bool) -> list[dict]:
    """Agrupa por texto e pagina o resultado.

    Fica em uma função só porque a fila de pendentes e a de pré-rotulados
    precisam exatamente da mesma regra: duas cópias da mesma regra divergem, e a
    divergência aparece como contagem errada na métrica, não como erro.
    """
    if not unicos:
        return linhas[deslocamento:deslocamento + limite]
    vistos: dict[str, dict] = {}
    for linha in linhas:
        chave = _chave_texto(linha["descricao"])
        if chave in vistos:
            vistos[chave]["repeticoes"] += 1
            vistos[chave]["ids_irmaos"].append(linha["id"])
            continue
        item = dict(linha)
        item["repeticoes"] = 1
        item["ids_irmaos"] = [linha["id"]]
        vistos[chave] = item
    return list(vistos.values())[deslocamento:deslocamento + limite]


def carregar_pendentes(limite: int = 50, deslocamento: int = 0, unicos: bool = True) -> list[dict]:
    """Triagens sem rótulo, com texto e a prioridade prevista (para rotular).

    Ordena da mais recente para a mais antiga. `deslocamento` pagina a fila.

    `unicos=True` (padrão) agrupa por texto: o histórico real é dominado por
    repetição (a mesma fixture de API aparece dezenas de vezes), e rotular cada
    cópia é esforço jogado fora — além de inflar a métrica, fazendo um único bug
    pesar várias vezes. Cada item ganha `repeticoes` (quantas linhas têm esse
    texto). A janela lida do servidor é maior que o pedido porque a deduplicação
    acontece depois da consulta.
    """
    try:
        janela = max(limite * 10, 200) if unicos else limite
        return _agrupar(_linhas(janela, 0, apenas_rotuladas=False), limite, deslocamento, unicos)
    except Exception:
        return []


def carregar_pre_rotulados(limite: int = 50, deslocamento: int = 0, unicos: bool = True) -> list[dict]:
    """Triagens rotuladas por AGENTE, para o dono conferir e promover.

    Mesma forma de `carregar_pendentes` (dedup por texto, `repeticoes`,
    `ids_irmaos`) e as mesmas duas previsões, mais `rotulo` — que aqui é a
    *sugestão* do agente, não ground truth.

    Estas linhas são justamente as que somem da tela: já têm `rotulo`, então não
    voltam para a fila de pendentes, e `carregar_rotulados` as descarta por
    autor, então não aparecem na concordância. Sem esta leitura o dono não tem
    onde conferir nem promover o que o agente sugeriu.
    """
    try:
        janela = max(limite * 10, 200) if unicos else limite
        linhas = [linha for linha in _linhas(janela, 0, apenas_rotuladas=True)
                  if linha.get("autor") == AUTOR_AGENTE]
        return _agrupar(linhas, limite, deslocamento, unicos)
    except Exception:
        return []


def registrar_varios(registro_ids: list[str], rotulo: str, comentario: str = "",
                     autor: str = "") -> int:
    """Rotula várias triagens de uma vez. Devolve quantas foram gravadas.

    O rótulo é propriedade do bug descrito, não da linha que o gravou: o mesmo
    relato repetido 20× no histórico recebe o mesmo rótulo nas 20. Chamar
    `registrar` em laço porque cada linha tem payload próprio (o PATCH do
    PostgREST substitui o jsonb inteiro, não dá para fazer numa tacada só).
    """
    return sum(1 for rid in registro_ids if registrar(rid, rotulo, comentario, autor))


def promover(registro_ids: list[str], rotulo: str, comentario: str = "", autor: str = "") -> int:
    """Promove pré-rotulagem do agente a rótulo HUMANO — é isso que a métrica conta.

    Exige identidade de leitor: sem `autor`, ou com `autor=AUTOR_AGENTE`, não
    promove e devolve 0. O motivo do filtro não é burocracia: promover com o
    autor do agente regravaria o mesmo rótulo de agente, e a tela passaria a
    dizer que algo foi revisado sem que ninguém o tivesse lido.
    """
    limpo = (autor or "").strip()
    if not limpo or limpo == AUTOR_AGENTE:
        return 0
    return registrar_varios(registro_ids, rotulo, comentario, limpo)


def base_para_csv() -> str:
    """Base rotulada em CSV (id, data, texto, léxico, prioridade vista, rótulo)."""
    import csv
    import io

    buf = io.StringIO()
    colunas = ["id", "data_hora", "descricao", "gravidade", "prioridade",
               "rotulo", "comentario", "em"]
    w = csv.DictWriter(buf, fieldnames=colunas, extrasaction="ignore")
    w.writeheader()
    for linha in carregar_rotulados():
        w.writerow(linha)
    return buf.getvalue()


def progresso() -> dict:
    """Contagem para a UI (sem texto de relato): total, humanas, pré, pendentes.

    `rotuladas` conta só o rótulo humano — o ground truth real. Os rótulos com
    `autor=AUTOR_AGENTE` vão em `pre_rotuladas` e NÃO contam como cobertura: só um
    leitor humano promove a pré-rotulagem, e é a métrica dele que mede o motor.
    """
    vazio = {"total": 0, "rotuladas": 0, "pre_rotuladas": 0, "pendentes": 0, "erro": False}
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
        return {**vazio, "erro": True}
    rotulados = _linhas(apenas_rotuladas=True)
    humanas = sum(1 for linha in rotulados if linha.get("autor") != AUTOR_AGENTE)
    pre = len(rotulados) - humanas
    return {
        "total": total,
        "rotuladas": humanas,
        "pre_rotuladas": pre,
        "pendentes": max(total - humanas - pre, 0),
        "erro": False,
    }
