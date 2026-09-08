# RAG leve no histórico persistido (data/historico.jsonl).
#
# Arquitetura (sem banco vetorial — proporcional ao tamanho do projeto):
#   - Retrieval: similaridade Jaccard de tokens locais, 100% determinística e offline.
#   - Geração:   Gemini (ia.analisar_llm_rag) responde "já aconteceu? como resolvemos?"
#                usando o contexto recuperado.
#
# Nenhum dado é enviado além do próprio relato + os top-k registros similares.

import re

import ia

# Stopwords PT mínimas: filtram conectivos para a similaridade focar em termos úteis.
_STOPWORDS = {
    "a", "as", "ao", "aos", "com", "da", "das", "de", "do", "dos", "e", "é",
    "em", "na", "nas", "no", "nos", "o", "os", "para", "por", "que", "se",
    "um", "uma", "meu", "minha", "toda", "todo", "todas", "todos", "está",
    "estão", "mas", "como", "quando", "porque", "vai", "tentar",
    "depois", "tem", "ter", "ficou", "fazendo", "faz", "estava",
}


def _tokens(texto):
    """Conjunto de tokens relevantes do texto (minúsculas, sem stopwords)."""
    palavras = re.findall(r"\w+", (texto or "").lower())
    return {p for p in palavras if p not in _STOPWORDS and len(p) > 1}


def _jaccard(conjunto_a, conjunto_b):
    uniao = conjunto_a | conjunto_b
    if not uniao:
        return 0.0
    return len(conjunto_a & conjunto_b) / len(uniao)


def recuperar_similares(relato, registros, k=3):
    """Top-k registros do histórico mais parecidos com o relato (Jaccard de tokens)."""
    alvo = _tokens(relato)
    if not alvo or not registros:
        return []
    pontuados = []
    for reg in registros:
        texto = reg.get("descricao") or reg.get("resumo") or ""
        score = _jaccard(alvo, _tokens(texto))
        pontuados.append((score, reg))
    pontuados.sort(key=lambda par: -par[0])
    return [reg for _score, reg in pontuados[:k]]


def montar_contexto(similares):
    """Converte os registros recuperados em texto que vai no prompt do Gemini."""
    if not similares:
        return "Nenhuma triagem anterior recuperada para este relato."
    linhas = []
    for reg in similares:
        linhas.append(
            f"- [{reg.get('id', '?')}] {reg.get('resumo', '')} "
            f"(gravidade: {reg.get('gravidade', '—')}, score {reg.get('score', '—')}, "
            f"data {reg.get('data', '—')})"
        )
        if reg.get("resolucao"):
            linhas.append(f"   resolução registrada: {reg['resolucao']}")
    return "\n".join(linhas)


def analisar_com_rag(relato, registros, k=3, provedor=None):
    """Retrieval + geração. Retorna (dict | None, erro).

    Em caso de sucesso, dict contém o schema padrão da IA + campos do RAG:
    ja_aconteceu, resolucao_anterior, registros_similar (ids reais recuperados).
    """
    similares = recuperar_similares(relato, registros, k)
    contexto = montar_contexto(similares)
    resultado = None
    erro = None
    try:
        resultado, erro = ia.analisar_llm_rag(relato, contexto, provedor=provedor)
    except Exception as exc:  # nunca deixa o RAG derrubar o motor local
        return None, f"RAG: {type(exc).__name__}: {str(exc)[:120]}"
    if resultado is not None:
        resultado.setdefault("ja_aconteceu", False)
        resultado.setdefault("resolucao_anterior", "")
        # Confiável: marca os ids que DE FATO foram recuperados (retrieval local),
        # independente do que a IA listar como "registros_similar".
        resultado["registros_similar"] = [r.get("id", "?") for r in similares]
    return resultado, erro