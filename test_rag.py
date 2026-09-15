# Testes unitários do RAG leve no histórico (rag.py)
# Roda com: pytest -v
# Confirma: tokenização, similaridade (Jaccard), recuperação top-k (BM25 +
# sinônimos + recência/resolução), rerank vetorial híbrido, montagem do
# contexto e orquestração (retrieval + geração) sem chave de API.
# O processo vetorial é testado com embeddings mockados — nunca toca a rede.

import pytest

import ia
import rag


# --- Tokenização -----------------------------------------------------
def test_tokens_remove_stopwords_e_palavras_curtas():
    assert "o" not in rag._tokens("o aplicativo crashou no login")
    assert "aplicativo" in rag._tokens("o aplicativo crashou no login")
    assert "login" in rag._tokens("o aplicativo crashou no login")


def test_tokens_texto_vazio_retorna_vazio():
    assert rag._tokens("") == set()
    assert rag._tokens(None) == set()


# --- Similaridade (Jaccard) -------------------------------------------
def test_jaccard_relatos_identicos_e_diferentes():
    a = {"crash", "login", "app"}
    identico = rag._jaccard(a, {"login", "app", "crash"})
    assert identico == pytest.approx(1.0)
    desconexo = rag._jaccard(a, {"cor", "fundo", "escura"})
    assert desconexo == 0.0


# --- Recuperação top-k -------------------------------------------------
def test_recuperar_similares_retorna_mais_parecido_primeiro():
    registros = [
        {"id": "b", "descricao": "a cor de fundo deveria ser mais escura"},
        {"id": "a", "descricao": "o app crasha sempre que tento fazer login"},
    ]
    resultado = rag.recuperar_similares(
        "o aplicativo deu crash quando fui fazer login", registros, k=1
    )
    assert len(resultado) == 1
    assert resultado[0]["id"] == "a"


def test_recuperar_similares_limita_k_e_ordena_por_score():
    relato = "botão de pagamento não responde"
    registros = [
        {"id": f"r{i}", "descricao": f"botão de pagamento quebrado {i}"} for i in range(10)
    ]
    resultado = rag.recuperar_similares(relato, registros, k=3)
    assert len(resultado) <= 3
    ids = [r["id"] for r in resultado]
    assert ids == sorted(ids)


def test_recuperar_vazio_sem_registros_ou_relato():
    assert rag.recuperar_similares("qualquer coisa", [], k=3) == []
    assert rag.recuperar_similares("", [{"descricao": "x"}], k=3) == []


# --- Sinônimos e BM25 -------------------------------------------------
def test_expandir_sinonimos_une_grupos():
    expandido = rag._expandir({"crash", "pagina"})
    assert "crashou" in expandido
    assert "travou" in expandido
    assert "tela" in expandido
    assert len(expandido) >= 2 + 2  # os originais + os do grupo


def test_sinonimos_aproximam_relatos():
    # relato usa "travou"; histórico usa "crashou" — o grupo aproxima os dois.
    registros = [
        {"id": "cor", "descricao": "a cor de fundo deveria ser mais escura"},
        {"id": "crash", "descricao": "o app crashou na hora do login"},
    ]
    resultado = rag.recuperar_similares(
        "o aplicativo travou ao fazer login", registros, k=1
    )
    assert resultado[0]["id"] == "crash"


def test_bm25_prefere_termo_mas_numera_mais_pontos():
    # fator de termo: mesmo número de ocorrências, mais tokens do relato = maior score.
    registros = [
        {"id": "u", "descricao": "erro ao salvar arquivo"},
        {"id": "d", "descricao": "erro ao salvar arquivo e a tela fecha"},
    ]
    resultado = rag.recuperar_similares("salvar arquivo erro", registros, k=1)
    assert resultado[0]["id"] == "u"


# --- Ponderação: recência e resolução ----------------------------------
def test_recencia_sobe_registro_recente():
    idade_90 = "2026-06-15T10:00:00"
    agora = "2026-09-15T10:00:00"
    registros = [
        {"id": "velha", "descricao": "erro ao abrir o arquivo", "data_hora": idade_90},
        {"id": "nova", "descricao": "erro ao abrir o arquivo", "data_hora": agora},
    ]
    resultado = rag.recuperar_similares("erro ao abrir o arquivo", registros, k=1)
    assert resultado[0]["id"] == "nova"


def test_resolucao_registrada_sobe_documento():
    reg1 = {"id": "sem", "descricao": "erro ao abrir o arquivo", "data": "2026-09-15"}
    reg2 = {"id": "com", "descricao": "erro ao abrir o arquivo", "data": "2026-09-15",
            "resolucao": "resolvido"}
    resultado = rag.recuperar_similares("erro ao abrir o arquivo", [reg1, reg2], k=1)
    assert resultado[0]["id"] == "com"


# --- Rerank vetorial híbrido -------------------------------------------
def _embedding_mock_semantico(texto):
    """Mock simples: vetor de 2 dims separando "app/aplicativo" de outras coisas."""
    lower = (texto or "").lower()
    if "app" in lower or "aplic" in lower:
        return [1.0, 0.0]
    return [0.0, 1.0]


@pytest.fixture
def ambiente_vetorial(tmp_path, monkeypatch):
    """Isola RAM/cache em disco e aponta o arquivo de vetores para um tmp."""
    rag._VETORES.clear()
    rag._SEM_VETOR.clear()
    rag._CARREGOU_DISCO = False
    rag._ARQUIVO_VETORES = None
    monkeypatch.setenv("RAG_VETORES_ARQUIVO", str(tmp_path / "embeddings.jsonl"))
    yield
    rag._VETORES.clear()
    rag._SEM_VETOR.clear()
    rag._CARREGOU_DISCO = False
    rag._ARQUIVO_VETORES = None


def test_vetor_habilita_hibrido_e_ia_embedding_retorna_cosseno(ambiente_vetorial, monkeypatch):
    # Processo B ligado: rerank híbrido desempata o BM25 e troca a ordem estável.
    monkeypatch.setattr(rag, "_vetores_ativos", lambda: True)
    monkeypatch.setattr(rag.ia, "embedding", _embedding_mock_semantico)
    registros = [
        {"id": "generic", "descricao": "módulo erro"},
        {"id": "app", "descricao": "app erro"},
    ]
    resultado = rag.recuperar_similares("erro aplicativo", registros, k=1)
    assert resultado[0]["id"] == "app"


def test_sem_vetores_cai_para_bm25_e_mantem_ordem_estavel(ambiente_vetorial, monkeypatch):
    # RAG_VETOR=off: nada de rede; empate BM25 → ordem original (estável).
    monkeypatch.setenv("RAG_VETOR", "off")
    registros = [
        {"id": "generic", "descricao": "módulo erro"},
        {"id": "app", "descricao": "app erro"},
    ]
    resultado = rag.recuperar_similares("erro aplicativo", registros, k=1)
    assert resultado[0]["id"] == "generic"  # ordem estável do empate


def test_vetor_falha_fallback_lexical(ambiente_vetorial, monkeypatch):
    # embedding indisponível → cossenos zerados → base continua o BM25.
    monkeypatch.setattr(rag, "_vetores_ativos", lambda: True)
    monkeypatch.setattr(rag.ia, "embedding", lambda texto: None)
    registros = [
        {"id": "generic", "descricao": "módulo erro"},
        {"id": "app", "descricao": "app erro"},
    ]
    resultado = rag.recuperar_similares("erro aplicativo", registros, k=1)
    assert resultado[0]["id"] in {"generic", "app"}
    assert len(resultado) == 1


def test_cache_vetores_evita_rechamada(ambiente_vetorial, monkeypatch):
    chamadas = []

    def _embedding_contada(texto):
        chamadas.append(texto)
        return _embedding_mock_semantico(texto)

    monkeypatch.setattr(rag, "_vetores_ativos", lambda: True)
    monkeypatch.setattr(rag.ia, "embedding", _embedding_contada)
    registros = [
        {"id": "app", "descricao": "app erro"},
        {"id": "generic", "descricao": "módulo erro"},
    ]
    rag.recuperar_similares("erro aplicativo", registros, k=1)
    primeira = len(chamadas)
    apos_cache = rag.recuperar_similares("erro aplicativo", registros, k=1)
    assert apos_cache[0]["id"] == "app"
    # query embutida de novo, mas documentos vêm do cache (memória/disco).
    assert len(chamadas) == primeira + 1


# --- Contexto para o prompt --------------------------------------------
def test_montar_contexto_inclui_id_resumo_e_gravidade():
    contexto = rag.montar_contexto([
        {"id": "20260906_123456", "resumo": "crash ao fazer login",
         "gravidade": "CRÍTICA 🚨", "data": "2026-09-06"}
    ])
    assert "20260906_123456" in contexto
    assert "crash ao fazer login" in contexto
    assert "CRÍTICA" in contexto


def test_montar_contexto_inclui_resolucao_quando_registrada():
    # O Gemini só consegue responder "como foi resolvido" se a resolução
    # estiver no contexto recuperado — esse é o coração do aprendizado.
    contexto = rag.montar_contexto([
        {"id": "abc", "resumo": "crash no login",
         "resolucao": "rollback da versão 1.2.0 corrigiu o crash"}
    ])
    assert "resolução registrada" in contexto
    assert "rollback da versão 1.2.0" in contexto


def test_montar_contexto_omite_resolucao_quando_nao_existe():
    contexto = rag.montar_contexto([
        {"id": "abc", "resumo": "crash no login"}
    ])
    assert "resolução registrada" not in contexto


def test_montar_contexto_inclui_categoria_quando_existe():
    contexto = rag.montar_contexto([
        {"id": "abc", "resumo": "crash no login", "categoria": "funcionalidade"}
    ])
    assert "funcionalidade" in contexto


def test_montar_contexto_vazio_avisa():
    assert "Nenhuma" in rag.montar_contexto([])


# --- Orquestração (retrieval + geração) --------------------------------
def test_analisar_com_rag_sem_chave_retorna_erro(monkeypatch):
    monkeypatch.setattr(ia, "_chave", lambda nome: None)
    resultado, erro = rag.analisar_com_rag(
        "um relato de login", [{"id": "x", "descricao": "login"}]
    )
    assert resultado is None
    assert "não configurada" in erro


def test_analisar_com_rag_atributo_ausente_nao_derruba(monkeypatch):
    # Caso real da Streamlit Cloud: se o ia.py deployado estiver desatualizado e
    # faltar 'analisar_llm_rag', o RAG não pode derrubar o motor local.
    monkeypatch.delattr(rag.ia, "analisar_llm_rag", raising=False)
    resultado, erro = rag.analisar_com_rag(
        "login falhou de novo", [{"id": "x", "descricao": "login falhou"}]
    )
    assert resultado is None
    assert "AttributeError" in erro or "has no attribute" in erro


def test_analisar_com_rag_marca_ids_recuperados(monkeypatch):
    monkeypatch.setattr(ia, "_chave", lambda: "chave-falsa")
    monkeypatch.setattr(
        ia, "analisar_llm_rag",
        lambda relato, contexto, provedor=None: (
            {"severidade": "alta", "categoria": "funcionalidade",
             "causa_raiz": "x", "passos_repro": ["1"], "resumo_tecnico": "y"}, None
        ),
    )
    registros = [{"id": "zz1", "descricao": "login falha sempre"}]
    resultado, erro = rag.analisar_com_rag("login falhou de novo", registros)
    assert erro is None
    assert resultado["ja_aconteceu"] is False
    assert resultado["registros_similar"] == ["zz1"]