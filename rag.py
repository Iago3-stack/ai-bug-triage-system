# RAG híbrido no histórico persistido (data/historico.jsonl).
#
# Arquitetura (sem banco vetorial — proporcional ao tamanho do projeto):
#   - Retrieval processo A (offline determinístico): BM25 com IDF sobre o corpus,
#     texto ponderado por campo (resumo tem peso maior), expansão de sinônimos
#     técnicos e bônus de recência/resolução — nunca depende de rede.
#   - Retrieval processo B (vetorial, opcional): embeddings Gemini com cache em
#     RAM + data/embeddings.jsonl; rerank híbrido (0.6*cosseno + 0.4*BM25).
#     Cai silenciosamente para o processo A quando não há chave/rede.
#   - Geração:   Gemini (ia.analisar_llm_rag) responde "já aconteceu? como
#                resolvemos?" usando o contexto recuperado.
#
# Nenhum dado é enviado além do próprio relato + os top-k registros similares.

import json
import math
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone

import ia

# Stopwords PT mínimas: filtram conectivos para a similaridade focar em termos úteis.
_STOPWORDS = {
    "a", "as", "ao", "aos", "com", "da", "das", "de", "do", "dos", "e", "é",
    "em", "na", "nas", "no", "nos", "o", "os", "para", "por", "que", "se",
    "um", "uma", "meu", "minha", "toda", "todo", "todas", "todos", "está",
    "estão", "mas", "como", "quando", "porque", "vai", "tentar",
    "depois", "tem", "ter", "ficou", "fazendo", "faz", "estava",
}

# Sinônimos técnicos em PT-BR: mesmo grupo → mesmos termos na busca (expansão).
# Serve para relatos que usam "travou", "congelou", "crashou" atingirem o mesmo
# registro (ex.: atas escritas com outra palavra).
_GRUPOS_SINONIMOS = [
    {"crash", "crashou", "crasha", "travou", "trava", "congelou", "congela"},
    {"login", "logar", "autenticar", "autenticacao", "conta"},
    {"pagina", "tela", "page", "janela", "aba"},
    {"botao", "clicar", "clique", "clicou"},
    {"pagamento", "checkout", "pagar", "cobranca"},
    {"download", "baixar", "exportar", "exportacao", "pdf"},
    {"erro", "falha", "bug", "defeito", "falhou", "quebrado"},
    {"lento", "lenta", "performance", "demora", "lentidao", "travado"},
]

_ARQUIVO_VETORES = None  # resolvido em _garantir_vetores_disco() a partir do env
_VETORES = {}            # id -> lista (normalizada) — cache de sessão (memória)
_SEM_VETOR = set()       # ids que falharam (evita re-chamadas de rede na sessão)
_CARREGOU_DISCO = False
_VETOR_LIMITE_NOVOS = 300  # máx. de embeddings novos por consulta vetorial


def _garantir_vetores_disco():
    """Carrega vetores persistidos em data/embeddings.jsonl (best-effort)."""
    global _CARREGOU_DISCO, _ARQUIVO_VETORES
    if _CARREGOU_DISCO:
        return
    _CARREGOU_DISCO = True
    _ARQUIVO_VETORES = os.environ.get("RAG_VETORES_ARQUIVO") or os.path.join(
        "data", "embeddings.jsonl"
    )
    try:
        os.makedirs(os.path.dirname(_ARQUIVO_VETORES) or ".", exist_ok=True)
        if not os.path.exists(_ARQUIVO_VETORES):
            return
        with open(_ARQUIVO_VETORES, encoding="utf-8") as fh:
            for linha in fh:
                linha = linha.strip()
                if not linha:
                    continue
                dado = json.loads(linha)
                rid = dado.get("id")
                vetor = dado.get("vetor")
                if rid and isinstance(vetor, list):
                    _VETORES[rid] = vetor
    except Exception:
        pass


def _salvar_vetor_disco(rid, vetor):
    linha = json.dumps({"id": rid, "vetor": vetor})
    try:
        with open(_ARQUIVO_VETORES, "a", encoding="utf-8") as fh:
            fh.write(linha + "\n")
    except Exception:
        pass


def _tokens(texto):
    """Conjunto de tokens relevantes do texto (minúsculas, sem stopwords)."""
    palavras = re.findall(r"\w+", (texto or "").lower())
    return {p for p in palavras if p not in _STOPWORDS and len(p) > 1}


def _expandir(conjunto):
    """Expansão por sinônimos: se um token do grupo aparece, todos entram."""
    resultado = set(conjunto)
    for grupo in _GRUPOS_SINONIMOS:
        if conjunto & grupo:
            resultado |= grupo
    return resultado


def _texto_registro(reg):
    """Texto ponderado por campo: resumo tem mais peso que a descrição."""
    partes = []
    resumo = reg.get("resumo")
    if resumo:
        partes.append(str(resumo))
        partes.append(str(resumo))  # peso duplo para o resumo (mais confiável)
    descricao = reg.get("descricao")
    if descricao:
        partes.append(str(descricao))
    raiz = reg.get("causa_raiz")
    if raiz:
        partes.append(str(raiz))
    resolucao = reg.get("resolucao")
    if resolucao:
        partes.append(str(resolucao))
    return " ".join(partes)


def _jaccard(conjunto_a, conjunto_b):
    # Mantido por compatibilidade (era o ranking usado antes do BM25).
    uniao = conjunto_a | conjunto_b
    if not uniao:
        return 0.0
    return len(conjunto_a & conjunto_b) / len(uniao)


def _bm25(termos_consulta, contador, idf, media_len, k1=1.5, b=0.75):
    """BM25 de um documento vs. os termos da consulta (soma de termo a termo)."""
    comprimento = sum(contador.values()) or 1
    denominador = k1 * (1 - b + b * comprimento / (media_len or 1))
    total = 0.0
    for termo in termos_consulta:
        freq = contador.get(termo, 0)
        if freq:
            total += idf.get(termo, 0.0) * freq * (k1 + 1) / (freq + denominador)
    return total


def _cosseno(u, v):
    """Cosseno entre vetores já normalizados (= produto interno)."""
    return sum(a * b for a, b in zip(u, v))


def _minmax(numeros):
    if not numeros:
        return numeros
    mn, mx = min(numeros), max(numeros)
    if mx == mn:
        return [0.0] * len(numeros)
    return [(x - mn) / (mx - mn) for x in numeros]


def _data_referencia(reg):
    """data_hora (ou data) do registro como datetime aware; None se ausente."""
    try:
        valor = reg.get("data_hora") or reg.get("data")
        if not valor:
            return None
        dt = datetime.fromisoformat(str(valor).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _fator_recencia(reg, agora=None):
    """Registros recentes sobem: 1/(1 + 0.02 * idade_em_dias)."""
    agora = agora or datetime.now(timezone.utc)
    ref = _data_referencia(reg)
    if ref is None:
        return 1.0
    idade_dias = max(0, (agora - ref).days)
    return 1.0 / (1.0 + 0.02 * idade_dias)


def _fator_importancia(reg):
    """Registros que já têm solução registrada sobem um pouco."""
    return 1.10 if reg.get("resolucao") else 1.0


def _vetores_ativos():
    """Habilita o rerank vetorial: env RAG_VETOR=on/off; auto = ligado fora de testes."""
    modo = os.environ.get("RAG_VETOR", "auto").strip().lower()
    if modo == "off":
        return False
    if modo == "on":
        return True
    return not ("pytest" in sys.modules)  # auto: em testes, nunca chama rede


def _vetor(texto):
    """Embedding do texto; None quando indisponível (rede/chave)."""
    return ia.embedding(texto)


def _recuperar_vetor_de(corpo, reg):
    """Vetor do registro com cache RAM/disco. Retorna (vetor|None, cache_hit)."""
    rid = reg.get("id")
    if rid in _VETORES:
        return _VETORES[rid], True
    if not rid or rid in _SEM_VETOR:
        return None, False
    vetor = _vetor(corpo)
    if vetor is None:
        _SEM_VETOR.add(rid)
        return None, False
    _VETORES[rid] = vetor
    _salvar_vetor_disco(rid, vetor)
    return vetor, False


def recuperar_similares(relato, registros, k=3):
    """Top-k registros do histórico mais parecidos com o relato (híbrido).

    Processo A (BM25 + sinônimos + recência/resolução) é sempre executado e
    nunca toca a rede. O processo B (embeddings Gemini) é somado quando
    disponível: 0.6*cosseno + 0.4*BM25(normalizados). Só os top-k voltam.
    """
    alvo = _tokens(relato)
    if not alvo or not registros:
        return []
    corpos = [_texto_registro(reg) for reg in registros]
    termos_consulta = _expandir(alvo)

    contadores = [Counter(_expandir(_tokens(corpo))) for corpo in corpos]
    n = len(registros)
    df = {t: sum(1 for c in contadores if c.get(t)) for t in termos_consulta}
    idf = {t: math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5)) for t in termos_consulta}
    media_len = sum(sum(c.values()) for c in contadores) / n
    bm = [_bm25(termos_consulta, c, idf, media_len) for c in contadores]

    cossenos = [0.0] * n
    teve_vetor = False
    if _vetores_ativos():
        vetor_consulta = _vetor(relato)
        if vetor_consulta:
            _garantir_vetores_disco()
            novos = 0
            for indice, reg in enumerate(registros):
                if novos >= _VETOR_LIMITE_NOVOS:
                    break
                vetor, cache_hit = _recuperar_vetor_de(corpos[indice], reg)
                if not cache_hit:
                    novos += 1  # tentativa nova de embedding (rede) não passa do limite
                if vetor is None:
                    continue
                cossenos[indice] = _cosseno(vetor_consulta, vetor)
                teve_vetor = True

    if teve_vetor:
        base = [
            0.6 * co + 0.4 * b
            for co, b in zip(_minmax(cossenos), _minmax(bm))
        ]
    else:
        base = bm

    # Ponderação pós-ranking: recente e com solução registrada sobem.
    base = [
        score * _fator_recencia(reg) * _fator_importancia(reg)
        for score, reg in zip(base, registros)
    ]

    pareado = sorted(zip(base, registros), key=lambda par: -par[0])
    return [reg for _score, reg in pareado[:k]]


def montar_contexto(similares):
    """Converte os registros recuperados em texto que vai no prompt do Gemini."""
    if not similares:
        return "Nenhuma triagem anterior recuperada para este relato."
    linhas = []
    for reg in similares:
        categoria = reg.get("categoria")
        sufixo = f", categoria: {categoria}" if categoria else ""
        linhas.append(
            f"- [{reg.get('id', '?')}] {reg.get('resumo', '')} "
            f"(gravidade: {reg.get('gravidade', '—')}, score {reg.get('score', '—')}, "
            f"data {reg.get('data', '—')}{sufixo})"
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