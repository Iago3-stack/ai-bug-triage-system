import dedup


def _reg(id_, **campos):
    base = {"id": id_, "bug_id": id_}
    base.update(campos)
    return base


def test_exato_herda_bug_id():
    registros = [_reg("a1", descricao="App crasha no login")]
    r = dedup.identificar_canonico("app crasha no login", registros)
    assert r["bug_id"] == "a1"
    assert r["repeticoes"] == 1


def test_parafrase_com_sinonimo_colapsa():
    registros = [_reg("a1", descricao="o app travou no login")]
    r = dedup.identificar_canonico("o app congelou no login", registros)
    assert r["bug_id"] == "a1"


def test_parecido_mas_distinto_nao_colapsa():
    registros = [_reg("a1", descricao="o botao de salvar nao funciona")]
    r = dedup.identificar_canonico("o botao de exportar nao funciona", registros)
    assert r["bug_id"] is None


def test_sem_historico_retorna_none():
    assert dedup.identificar_canonico("qualquer coisa", [])["bug_id"] is None
    assert dedup.identificar_canonico("", [_reg("a1", descricao="x")])["bug_id"] is None


def test_webhook_usa_relato():
    registros = [_reg("w1", relato="Timeout ao salvar o cadastro")]
    r = dedup.identificar_canonico("timeout ao salvar o cadastro", registros)
    assert r["bug_id"] == "w1"


def test_registro_legado_sem_bug_id_vira_raiz():
    registros = [{"id": "leg1", "descricao": "erro de banco ao salvar o cadastro"}]
    r = dedup.identificar_canonico("erro de banco ao salvar o cadastro", registros)
    assert r["bug_id"] == "leg1"


def test_conta_membros_do_cluster_e_primeiro_em():
    registros = [
        _reg("a1", descricao="App crasha no login", data_hora="2026-10-01T10:00:00-03:00"),
        _reg("a2", bug_id="a1", descricao="App crasha no login"),
    ]
    r = dedup.identificar_canonico("app crasha no login", registros)
    assert r["bug_id"] == "a1"
    assert r["repeticoes"] == 2
    assert r["primeiro_em"].startswith("2026-10-01")


def test_linha_recorrencia_unico_e_vazia():
    assert dedup.linha_recorrencia({"bug_id": "a1", "repeticoes": 1}) == ""


def test_linha_recorrencia_descreve_recorrente():
    texto = dedup.linha_recorrencia(
        {"bug_id": "a1", "repeticoes": 3, "bug_primeiro_em": "2026-10-01T10:00:00-03:00"}
    )
    assert "3" in texto
    assert "2026-10-01" in texto
