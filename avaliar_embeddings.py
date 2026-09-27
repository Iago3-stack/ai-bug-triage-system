#!/usr/bin/env python3
"""Benchmark LOCAL de embeddings/classificadores contra os 30 relatos rotulados.

Compara o léxico de produção (zero-shot) com o `tardellirs/brazembed-pt-br`
(BERT português, mean pooling) e com classificadores simples, nos mesmos casos
e com as mesmas métricas de `avaliar_motores.py` (via `casos_qa.py`).

Estratégias
    léxico        triagem.triar — referência de produção, não treina nada
    protótipos    brazembed + cosseno contra 4 frases por severidade (zero-shot)
    1-NN          brazembed + vizinho mais próximo (usa rótulo de 1 exemplo)
    logreg        brazembed + regressão logística (C=1.0, precisa de treino)
    tfidf+logreg  só n-gramas de palavra, sem transformer (classificador simples)
    tfidf+centro  TF-IDF + centroide mais próximo, cosseno (classificador simples)

⚠️ Comparabilidade: só `léxico` e `protótipos` NÃO treinam nestes casos — são os
únicos comparáveis entre si. Os outros quatro são leave-one-out: o número vale
para "um modelo treinado com 22 exemplos", e não para "pronto para produção".
Com 30 casos sintéticos, nenhum número abaixo aprova um motor sozinho.

Uso (venv separado — não instalar no .venv do app):
    python3 -m venv /tmp/opencode/venv-embed
    /tmp/opencode/venv-embed/bin/pip install torch --index-url https://download.pytorch.org/whl/cpu
    /tmp/opencode/venv-embed/bin/pip install sentence-transformers scikit-learn
    /tmp/opencode/venv-embed/bin/python avaliar_embeddings.py --detalhe
"""

import argparse
import unicodedata

import numpy as np

import triagem
from casos_qa import CASOS, N_CASOS, N_ESTRITOS

MODELO = "tardellirs/brazembed-pt-br"
ROTULOS = ("CRÍTICA", "MÉDIA", "NORMAL")

# Únicas comparáveis ao léxico (nada aqui olha os rótulos dos 30 casos).
ZERO_SHOT = ("léxico", "protótipos")

# Frases escritas a partir da DEFINIÇÃO de severidade (impacto no cliente), não
# a partir dos 30 casos. Se fossem copiadas dos casos, a métrica seria otimista
# na mesma base e não provaria nada.
PROTOTIPOS = {
    "CRÍTICA": [
        "falha grave que impede o usuário de usar o serviço",
        "o aplicativo crasha e a pessoa perde o trabalho, sem conseguir continuar",
        "problema crítico que derruba o sistema e causa perda de dados",
        "erro que deixa o serviço indisponível para todos os usuários",
    ],
    "MÉDIA": [
        "problema que atrapalha o uso, mas a pessoa ainda consegue fazer o trabalho",
        "funcionalidade com defeito que exige um contorno para ser usada",
        "o sistema fica lento ou instável, com impacto parcial no trabalho",
        "erro em uma parte do aplicativo, sem impedir o uso principal",
    ],
    "NORMAL": [
        "detalhe cosmético que só afeta a aparência, sem impacto no uso",
        "erro de digitação em um texto, sem consequência para a pessoa",
        "ajuste pequeno de apresentação que ninguém precisa para trabalhar",
        "sugestão de melhoria, sem defeito que atrapalhe o usuário",
    ],
}

_MODELO_CARREGADO = None


# --- texto -------------------------------------------------------------------
def chave(texto: str) -> str:
    """Minúsculas sem acento: o BERT PT é "cased", então maiúscula vira outro token."""
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFKD", texto.lower())
        if not unicodedata.combining(c)
    )
    return " ".join(sem_acento.split())


def _unitario(v: np.ndarray) -> np.ndarray:
    return v / (np.linalg.norm(v, axis=-1, keepdims=True) + 1e-9)


def _matriz(frases: list[str]) -> np.ndarray:
    """Embeddings normalizados (cosseno = produto interno)."""
    global _MODELO_CARREGADO
    from sentence_transformers import SentenceTransformer

    if _MODELO_CARREGADO is None:
        print(f"→ baixando/carregando {MODELO} (1ª vez baixa ~436MB)...", flush=True)
        _MODELO_CARREGADO = SentenceTransformer(MODELO)
    return _unitario(
        _MODELO_CARREGADO.encode(frases, batch_size=16, convert_to_numpy=True,
                                 show_progress_bar=False)
    )


# --- métricas (idênticas às do avaliar_motores.py) ---------------------------
def medir(previsoes: list[str]) -> tuple[int, int]:
    """(acertos tolerantes nos 30, acertos estritos nos 23 sem ambiguidade)."""
    tol = sum(1 for p, (_, esp) in zip(previsoes, CASOS) if p in esp)
    est = sum(1 for p, (_, esp) in zip(previsoes, CASOS) if len(esp) == 1 and p in esp)
    return tol, est


# --- estratégias zero-shot ---------------------------------------------------
def prever_lexico() -> list[str]:
    return [triagem.triar(t)["gravidade"].split(" ")[0] for t, _ in CASOS]


def _centro_de_vetores(vets: np.ndarray) -> np.ndarray:
    return vets.mean(axis=0) / (np.linalg.norm(vets.mean(axis=0)) + 1e-9)


def prever_prototipos(vetores: np.ndarray) -> list[str]:
    centros = {
        rotulo: _centro_de_vetores(_matriz([chave(f) for f in frases]))
        for rotulo, frases in PROTOTIPOS.items()
    }
    previsoes = []
    for i in range(N_CASOS):
        sims = {r: float(vetores[i] @ c) for r, c in centros.items()}
        previsoes.append(max(sims, key=sims.get))
    return previsoes


# --- estratégias treinadas (leave-one-out) ----------------------------------
def _prevê_com_treino(treino: list[tuple], entradas: list, fit) -> list[str]:
    """fit(treino, entrada_do_alvo) -> rótulo. LOO nos estritos; ambíguos usam os 23.

    `treino` é a lista de (entrada, rótulo) dos 23 casos estritos; `entradas` tem
    a entrada de cada um dos 30 casos, na ordem de `CASOS`. A exclusão é por
    POSIÇÃO dentro de `treino` (nunca por texto), para não vazar um caso idêntico
    que por acaso se repita.
    """
    estritos = [i for i, (_, esp) in enumerate(CASOS) if len(esp) == 1]
    ambiguos = [i for i, (_, esp) in enumerate(CASOS) if len(esp) > 1]
    previsoes: list[str] = [""] * N_CASOS
    for posicao, caso in enumerate(estritos):
        sem_o_caso = [par for j, par in enumerate(treino) if j != posicao]
        previsoes[caso] = fit(sem_o_caso, entradas[caso])
    for caso in ambiguos:
        previsoes[caso] = fit(treino, entradas[caso])
    return previsoes


def _fit_1nn(treino: list[tuple], alvo: np.ndarray) -> str:
    entradas = np.array([v for v, _ in treino])
    rotulos = [r for _, r in treino]
    return rotulos[int(np.argmax(entradas @ alvo))]


def _fit_logreg(treino: list[tuple], alvo: np.ndarray) -> str:
    from sklearn.linear_model import LogisticRegression

    clf = LogisticRegression(max_iter=2000, C=1.0)
    clf.fit(np.array([v for v, _ in treino]), [r for _, r in treino])
    return str(clf.predict(alvo[None, :])[0])


def _fit_tfidf_logreg(treino: list[tuple], alvo: str) -> str:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression

    # TF-IDF refeito a cada fold: o vocabulário do teste não pode vazar.
    vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
    matriz = vec.fit_transform([t for t, _ in treino])
    clf = LogisticRegression(max_iter=2000, C=1.0)
    clf.fit(matriz, [r for _, r in treino])
    return str(clf.predict(vec.transform([alvo]))[0])


def _fit_tfidf_centro(treino: list[tuple], alvo: str) -> str:
    from sklearn.feature_extraction.text import TfidfVectorizer

    # TF-IDF (norm='l2' é o padrão) + centroide de classe normalizado.
    # Espresso/denso explícito: a média de matriz esparsa devolve np.matrix e o
    # sklearn 1.9 recusa np.matrix em normalize().
    vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
    matriz = vec.fit_transform([t for t, _ in treino])
    alvo_v = np.asarray(vec.transform([alvo]).todense()).ravel()
    melhor, pontuacao = "", -2.0
    for rotulo in ROTULOS:
        linhas = [j for j, (_, r) in enumerate(treino) if r == rotulo]
        if not linhas:
            continue
        centro = np.asarray(matriz[linhas].mean(axis=0)).ravel()
        norma = np.linalg.norm(centro)
        if norma > 0:
            centro = centro / norma
        sim = float(alvo_v @ centro)
        if sim > pontuacao:
            melhor, pontuacao = rotulo, sim
    return melhor


# --- relatório --------------------------------------------------------------
def main(detalhe: bool) -> None:
    print(f"Ground truth: {N_CASOS} casos ({N_ESTRITOS} sem ambiguidade) via casos_qa.py")
    print(f"Modelo: {MODELO}\n")

    textos = [chave(t) for t, _ in CASOS]
    vetores = _matriz(textos)

    previsoes: dict[str, list[str]] = {
        "léxico": prever_lexico(),
        "protótipos": prever_prototipos(vetores),
    }

    treino_vet = [(vetores[i], next(iter(CASOS[i][1])))
                  for i in range(N_CASOS) if len(CASOS[i][1]) == 1]
    previsoes["1-NN"] = _prevê_com_treino(treino_vet, list(vetores), _fit_1nn)
    previsoes["logreg"] = _prevê_com_treino(treino_vet, list(vetores), _fit_logreg)

    treino_txt = [(textos[i], next(iter(CASOS[i][1])))
                  for i in range(N_CASOS) if len(CASOS[i][1]) == 1]
    previsoes["tfidf+logreg"] = _prevê_com_treino(treino_txt, textos, _fit_tfidf_logreg)
    previsoes["tfidf+centro"] = _prevê_com_treino(treino_txt, textos, _fit_tfidf_centro)

    print(f"\n{'estratégia':<14}{'tolerante (30)':<20}{'estrito (23)':<20}treina nos casos?")
    print("-" * 76)
    for nome, prev in previsoes.items():
        tol, est = medir(prev)
        treina = "NÃO (zero-shot)" if nome in ZERO_SHOT else "sim (LOO, 22 exemplos)"
        print(f"{nome:<14}{f'{tol}/{N_CASOS} ({tol/N_CASOS:5.1%})':<20}"
              f"{f'{est}/{N_ESTRITOS} ({est/N_ESTRITOS:5.1%})':<20}{treina}")

    if detalhe:
        for nome, prev in previsoes.items():
            erros = [(i, texto, pp, esp)
                     for i, ((texto, esp), pp) in enumerate(zip(CASOS, prev), start=1)
                     if pp not in esp]
            if not erros:
                continue
            print(f"\n{nome} — {len(erros)} erro(s):")
            for i, texto, pp, esp in erros:
                print(f"  {i:>2}. prev={pp:<8} esp={'/'.join(sorted(esp)):<18} {texto[:62]}")

    print("\n⚠️ Comparáveis entre si: léxico x protótipos (nenhum dos dois treina "
          "nestes casos).")
    print("   1-NN, logreg, tfidf+logreg e tfidf+centro são leave-one-out: medem "
          "modelo treinado com 22 exemplos,")
    print("   não generalize para produção. Base de 30 casos sintéticos: use para "
          "descartar candidato, não para aprovar.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--detalhe", action="store_true", help="lista os erros")
    main(ap.parse_args().detalhe)
