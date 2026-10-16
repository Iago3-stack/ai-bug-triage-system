# Testes do servidor MCP (servidor_mcp.py).
#
# Só a LÓGICA pura é testada aqui — `nome_funcionalidade` e `montar_gherkin`.
# O SDK `mcp` fica fora de requirements*.txt de propósito (AGENTS.md), então
# este arquivo NÃO o importa: as três ferramentas do servidor são wrappers finos
# sobre `triagem.triar`/`adaptadores.estruturar`, ambos já cobertos por seus
# próprios testes. O handshake real do servidor é verificado à parte (ver
# docs/08-mcp.md).

import servidor_mcp

PW_TEXTO = """Teste: login
  › validar acesso com sucesso

Error: expect(received).toBeVisible()
"""
# A amostra acima tem "›" (marca de Playwright) e um nome de teste após ele.
# O nome extraído por `adaptadores.estruturar` é "validar acesso com sucesso".


def test_nome_funcionalidade_prefere_nome_do_teste():
    assert servidor_mcp.nome_funcionalidade("x", {"teste": "fluxo de login"}) == "fluxo de login"


def test_nome_funcionalidade_usa_requisicao_e_titulo():
    assert servidor_mcp.nome_funcionalidade("x", {"requisicao": "POST /login"}) == "POST /login"
    assert servidor_mcp.nome_funcionalidade("x", {"titulo": "Teste falhou: login"}) == "Teste falhou: login"


def test_nome_funcionalidade_sem_evidencia_usa_primeira_frase():
    relato = "O botão não responde. Depois a tela fica preta."
    assert servidor_mcp.nome_funcionalidade(relato, None) == "O botão não responde"


def test_nome_funcionalidade_vazio_vira_funcionalidade():
    assert servidor_mcp.nome_funcionalidade("", None) == "funcionalidade"
    assert servidor_mcp.nome_funcionalidade("   ", None) == "funcionalidade"


def test_nome_funcionalidade_trunca_em_80():
    relato = "a" * 120
    assert len(servidor_mcp.nome_funcionalidade(relato, None)) == 80


def test_montar_gherkin_gravidade_vazia_usa_lexico():
    import triagem

    relato = "O aplicativo trava e não consigo finalizar o pagamento"
    saida = servidor_mcp.montar_gherkin(relato)
    esperada = triagem.triar(relato)["gravidade"]
    assert saida["gravidade"] == esperada
    assert "Funcionalidade:" in saida["gherkin"]
    assert esperada in saida["gherkin"]
    assert "Dado que" in saida["gherkin"] and "Então" in saida["gherkin"]


def test_montar_gherkin_respeita_gravidade_dada():
    saida = servidor_mcp.montar_gherkin("qualquer relato", "CRÍTICA 🚨")
    assert saida["gravidade"] == "CRÍTICA 🚨"
    assert "CRÍTICA 🚨" in saida["gherkin"]


def test_montar_gherkin_usa_nome_do_teste_de_playwright():
    saida = servidor_mcp.montar_gherkin(PW_TEXTO)
    assert saida["gherkin"].startswith("Funcionalidade: validar acesso com sucesso")


def test_constantes_do_servidor():
    assert servidor_mcp.NOME_SERVIDOR == "ai-bug-triage"
    assert "read-only" in servidor_mcp.INSTRUCOES.lower() or "Read-only" in servidor_mcp.INSTRUCOES
