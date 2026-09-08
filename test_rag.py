# Testes unitários do RAG leve no histórico (rag.py)
# Roda com: pytest -v
# Confirma: tokenização, similaridade (Jaccard), recuperação top-k, montagem
# do contexto e orquestração (retrieval + geração) sem chave de API.

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