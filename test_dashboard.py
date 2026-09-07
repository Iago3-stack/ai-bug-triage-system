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