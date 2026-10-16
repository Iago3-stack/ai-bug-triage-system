# Bug canônico: a que cluster de relato uma triagem pertence.
#
# Duas camadas, ambas offline e determinísticas:
#   1. exata  — texto normalizado idêntico (o caso dominante: a mesma fixture
#               submetida dezenas de vezes).
#   2. similar — tokens com expansão por sinônimos dos dois lados, Jaccard no
#               mesmo corte já medido do RAG.
#
# Reusa a máquina do RAG (`rag._tokens`/`_expandir`/`_jaccard`) em vez de
# recopiar: duas cópias da mesma regra divergem, e a divergência aparece como
# contagem errada, não como erro. De propósito NÃO chama `rag.recuperar_similares`
# — aquele caminho pode disparar embeddings/rede, e a gravação de uma triagem
# não pode depender de rede. A varredura aqui é linear sobre o histórico do
# tenant (já filtrado pela RLS por quem chama).

import unicodedata

import rag


def _chave_texto(texto: str) -> str:
    """Chave de agrupamento: minúsculas, sem acento, espaços normalizados."""
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFKD", (texto or "").lower())
        if not unicodedata.combining(c)
    )
    return " ".join(sem_acento.split())


def _texto_canonico(registro: dict) -> str:
    """Texto do relato por prioridade de campo.

    O app grava `descricao`; o webhook grava `relato`; registros antigos podem
    ter só `resumo`. Sem esse fallback, o webhook ficaria de fora da dedup.
    """
    return str(
        registro.get("descricao")
        or registro.get("relato")
        or registro.get("resumo")
        or ""
    )


def _mesmo(a: str, b: str) -> bool:
    """True se os dois textos são o mesmo relato (tokens expandidos, Jaccard)."""
    ta, tb = rag._expandir(rag._tokens(a)), rag._expandir(rag._tokens(b))
    if not ta or not tb:
        return False
    return rag._jaccard(ta, tb) >= rag._JACCARD_MESMO_RELATO


def _raiz(registro: dict) -> str:
    """Id canônico a que um registro pertence (legado sem bug_id = o próprio id)."""
    return registro.get("bug_id") or registro.get("id")


def identificar_canonico(relato: str, registros: list[dict]) -> dict:
    """A que cluster canônico o relato pertence, dentro de `registros`.

    Devolve `{"bug_id", "repeticoes", "primeiro_em"}`. `bug_id` é o id da
    triagem mais antiga do cluster, ou `None` quando não há match — o chamador
    então usa o id do próprio registro como raiz de um cluster novo.
    `repeticoes` conta quantos registros já estavam no cluster; `primeiro_em` é
    a data da raiz.
    """
    relato = (relato or "").strip()
    if not relato or not registros:
        return {"bug_id": None, "repeticoes": 0, "primeiro_em": ""}

    chave = _chave_texto(relato)
    melhor = None
    for reg in registros:  # camada 1 (exata), do mais antigo para o mais novo
        if _chave_texto(_texto_canonico(reg)) == chave:
            melhor = reg
            break
    if melhor is None:  # camada 2 (similaridade)
        for reg in registros:
            if _mesmo(relato, _texto_canonico(reg)):
                melhor = reg
                break
    if melhor is None:
        return {"bug_id": None, "repeticoes": 0, "primeiro_em": ""}

    bug_id = _raiz(melhor)
    repeticoes = sum(1 for r in registros if _raiz(r) == bug_id)
    raiz = next((r for r in registros if r.get("id") == bug_id), melhor)
    primeiro_em = str(raiz.get("data_hora") or raiz.get("data") or "")
    return {"bug_id": bug_id, "repeticoes": repeticoes, "primeiro_em": primeiro_em}


def linha_recorrencia(registro: dict) -> str:
    """Frase de recorrência para exibir; vazia quando o bug ainda é único."""
    n = int(registro.get("repeticoes") or 1)
    if n <= 1:
        return ""
    desde = str(registro.get("bug_primeiro_em") or "")[:10]
    sufixo = f" (primeiro em {desde})" if desde else ""
    return f"🧩 Bug recorrente: já reportado {n}×{sufixo}."
