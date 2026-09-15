import pytest

from colar_falha import (
    _detectar_categoria,
    _detectar_modulo,
    _extrair_arquivo_linha,
    _extrair_erro,
    _extrair_versao,
    estruturar,
    montar_relato,
)

TRACEBACK = """Traceback (most recent call last):
  File "/app/secoes/ferramenta.py", line 312, in render
    resultado = triar(descricao_bug)
  File "/app/triagem.py", line 121, in triar
    return _analisar_lexico(texto)
TypeError: 'NoneType' object is not subscriptable (v2.12.0)"""


def test_extrair_erro_pega_nome_e_detalhe():
    assert _extrair_erro(TRACEBACK) == "TypeError: 'NoneType' object is not subscriptable"


def test_extrair_erro_none_sem_excecao():
    assert _extrair_erro("o botão de salvar não responde") is None


def test_arquivo_linha_usa_frame_mais_interno():
    assert _extrair_arquivo_linha(TRACEBACK) == "triagem.py:121"


def test_detectar_categoria_por_keywords():
    assert _detectar_categoria("demora muito e fica travando") == "performance"
    assert _detectar_categoria("não consigo fazer login, senha não aceita") == "seguranca"
    assert _detectar_categoria("botão de baixar o relatório não funciona") == "funcionalidade"
    assert _detectar_categoria("a cor do fundo da página está quebrada") == "design"
    assert _detectar_categoria("qualquer coisa aleatória") == "outro"


def test_detectar_modulo():
    assert _detectar_modulo("falha ao tentar pagar com pix") == "pagamento"
    assert _detectar_modulo("erro de login e senha") == "login"
    assert _detectar_modulo("não consigo baixar o pdf") == "exportacao"
    assert _detectar_modulo("issue no github não abre") == "integracao"
    assert _detectar_modulo("xpto") is None


def test_extrair_versao():
    assert _extrair_versao("erro na versão 2.12.0 do app") == "v2.12.0"
    assert _extrair_versao("v1.3 valida") == "v1.3"
    assert _extrair_versao("nada de versão aqui") is None
    assert _extrair_versao("ano 2026.09 é data") is None


def test_estruturar_traceback_python():
    e = estruturar(TRACEBACK)
    assert e["linguagem"] == "Python"
    assert e["erro"].startswith("TypeError:")
    assert e["severidade"] in ("ALTA 🚨", "CRÍTICA 🚨", "MÉDIA ⚠️")
    assert e["versao"] == "v2.12.0"
    assert "Erro `TypeError`" in e["titulo"]
    assert len(e["passos_repro"]) >= 2


def test_estruturar_texto_solto():
    e = estruturar("Estou tentando pagar e o botão não responde, estou muito frustrado!")
    assert e["categoria"] == "funcionalidade"
    assert e["modulo"] == "pagamento"
    assert e["erro"] is None
    assert "frustrado" in e["descricao"]


def test_estruturar_evidencia_vazia():
    e = estruturar("   ")
    assert e["titulo"] and e["erro"] is None


def test_montar_relato_inclui_secoes():
    relato = montar_relato(TRACEBACK)
    assert "**Título:**" in relato
    assert "**Descrição:**" in relato
    assert "**Categoria:**" in relato
    assert "**Passos para reproduzir:**" in relato
    assert "TypeError" in relato
    assert "**Linguagem detectada:** Python" in relato


def test_montar_relato_sem_estrutura_pre_calculada():
    relato = montar_relato("o sistema está demorando demais e caiu com timeout 504")
    assert "versão da falha" not in relato
    assert "**Categoria:** performance" in relato


def test_detecta_linguagem_java():
    e = estruturar("com.example.login.LoginActivity: java.lang.NullPointerException")
    assert e["linguagem"] == "Java"


def test_nunca_levanta_excecao():
    assert montar_relato(None)
    assert estruturar("**#**")["titulo"]