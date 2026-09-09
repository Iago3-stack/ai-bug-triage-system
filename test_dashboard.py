import dashboard


def _registro(descricao, gravidade="MÉDIA ⚠️", usou_ia=False, divergente=None, **extra):
    reg = {
        "id": "abc",
        "data_hora": "2026-09-06T10:00:00-03:00",
        "data": "2026-09-06",
        "resumo": descricao[:100],
        "descricao": descricao,
        "gravidade": gravidade,
        "score": -1.5,
        "usou_ia": usou_ia,
    }
    if divergente is not None:
        reg["divergente"] = divergente
    reg.update(extra)
    return reg


def test_tabela_recente_sem_jira_key_nao_quebra():
    registros = [
        _registro("bug no login", "CRÍTICA 🚨", usou_ia=False),
        _registro("bug no pagamento", "MÉDIA ⚠️", usou_ia=True),
    ]
    tabela = dashboard.tabela_recente(registros)
    assert "Jira" in tabela.columns
    assert list(tabela["Jira"]) == ["—", "—"]
    assert list(tabela["IA"]) == ["não", "sim"]


def test_tabela_recente_com_jira_key():
    registros = [
        _registro("bug grave", "CRÍTICA 🚨", jira_key="QA-12", jira_url="https://..."),
    ]
    tabela = dashboard.tabela_recente(registros)
    assert list(tabela["Jira"]) == ["QA-12"]


def test_funcoes_afetadas_conta_uma_vez_por_registro():
    registros = [
        _registro("o login não funciona e o chat de suporte também não abre"),
        _registro("o pagamento falha na hora de confirmar"),
    ]
    contagem = dashboard.funcoes_afetadas(registros)
    assert contagem["Login/Conta"] == 1
    assert contagem["Chat/Suporte"] == 1
    assert contagem["Pagamento/Compra"] == 1


def test_funcoes_afetadas_ignora_registros_sem_feature():
    contagem = dashboard.funcoes_afetadas([_registro("o modo escuro não é aplicado")])
    assert sum(contagem.values()) == 0


def test_false_positivos_evitados_soma_apenas_normal_com_vocabulario_de_teste():
    registros = [
        _registro("encontrei um erro de digitação no rodapé", "NORMAL ✅"),
        _registro("achei um bug na página de login", "NORMAL ✅"),
        _registro("bug crítico no pagamento", "CRÍTICA 🚨"),
        _registro("tudo funcionando perfeitamente", "NORMAL ✅"),
    ]
    assert dashboard.false_positivos_evitados(registros) == 2


def test_contagem_por_ordena_por_gravidade():
    registros = [
        _registro("a", "NORMAL ✅"),
        _registro("b", "CRÍTICA 🚨"),
        _registro("c", "MÉDIA ⚠️"),
    ]
    df = dashboard._contagem_por(registros, "gravidade", dashboard._ORDEM_SEVERIDADE)
    assert list(df["gravidade"]) == ["CRÍTICA 🚨", "MÉDIA ⚠️", "NORMAL ✅"]
    assert list(df["quantidade"]) == [1, 1, 1]


def test_tabela_recente_mostra_provedor_ia():
    registros = [
        _registro("bug no login", usou_ia=True, provedor_ia="Groq", modelo_ia="openai/gpt-oss-120b"),
        _registro("bug no pagamento", usou_ia=True),
        _registro("bug no cadastro", usou_ia=False),
    ]
    tabela = dashboard.tabela_recente(registros)
    assert list(tabela["IA"]) == ["Groq", "sim", "não"]


def test_taxa_divergencia():
    registros = [
        _registro("a", usou_ia=True, divergente=True),
        _registro("b", usou_ia=True, divergente=False),
        _registro("c", usou_ia=True, divergente=True),
        _registro("d", usou_ia=False),
    ]
    assert dashboard.taxa_divergencia(registros) == 66.7
    assert dashboard.taxa_divergencia([_registro("x", usou_ia=False)]) is None


# --- Auditoria dos guardrails (credenciais/PII mascaradas) ---
def test_guardrails_auditoria_conta_por_tipo():
    registros = [
        _registro("a", sensiveis_mascarados=["e-mail", "CPF"]),
        _registro("b", sensiveis_mascarados=["e-mail"]),
        _registro("c", sensiveis_mascarados=[]),
        _registro("d"),
    ]
    contagem = dashboard.guardrails_auditoria(registros)
    assert contagem["e-mail"] == 2
    assert contagem["CPF"] == 1
    assert sum(contagem.values()) == 3


def test_guardrails_auditoria_registro_legado_string_avulsa():
    contagem = dashboard.guardrails_auditoria([_registro("a", sensiveis_mascarados="CPF")])
    assert contagem["CPF"] == 1


def test_guardrails_auditoria_vazia():
    assert sum(dashboard.guardrails_auditoria([]).values()) == 0


def test_tabela_recente_marca_linha_mascarada():
    registros = [
        _registro("a", sensiveis_mascarados=["e-mail"]),
        _registro("b", sensiveis_mascarados=[]),
        _registro("c"),
    ]
    tabela = dashboard.tabela_recente(registros)
    assert list(tabela["🔒"]) == ["sim", "—", "—"]


def test_top_causas_agrupa_e_limita_a_cinco():
    registros = [
        _registro("a", causa_raiz_ia="Servidor sobrecarregado"),
        _registro("b", causa_raiz_ia="servidor sobrecarregado"),
        _registro("c", causa_raiz_ia="Servidor   sobrecarregado"),
        _registro("d", causa_raiz_ia="Configuração errada"),
        _registro("e", causa_raiz_ia="Configuração errada"),
        _registro("f", causa_raiz_ia="Falha no banco"),
        _registro("g", causa_raiz_ia="Falha no banco"),
        _registro("h", causa_raiz_ia="Bug de rede"),
        _registro("i", causa_raiz_ia="Bug de rede"),
        _registro("j", causa_raiz_ia="Memória insuficiente"),
        _registro("k", causa_raiz_ia="Memória insuficiente"),
        _registro("l", causa_raiz_ia="Disco cheio"),
        _registro("m", causa_raiz_ia="Disco cheio"),
    ]
    df = dashboard.top_causas(registros)
    assert len(df) == 5
    assert df["quantidade"].max() == 3
    assert df.index[0] == "servidor sobrecarregado"
    assert dashboard.top_causas([_registro("z")]).empty


def test_tem_funcionalidade():
    assert dashboard._tem_funcionalidade({"descricao": "o login falhou"}, "Login/Conta")
    assert not dashboard._tem_funcionalidade({"descricao": "o modo escuro falhou"}, "Login/Conta")


def test_saude_suite_base_e_punicao_por_divergencia():
    regs = [_registro("x", gravidade="NORMAL ✅", usou_ia=False)]
    alto = dashboard.saude_suite(regs)
    regs_divergente = [
        _registro("a", gravidade="MÉDIA ⚠️", usou_ia=True, divergente=True, score=-4.0),
        _registro("b", gravidade="MÉDIA ⚠️", usou_ia=True, divergente=True, score=-4.0),
    ]
    baixo = dashboard.saude_suite(regs_divergente)
    assert 0.0 <= alto <= 10.0
    assert 0.0 <= baixo <= 10.0
    assert baixo < alto
    assert dashboard.saude_suite([]) == 0.0