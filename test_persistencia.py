import persistencia

# Caminho sobrescrevível por env (testes usam tmp_path e nunca tocam data/ real).


def _caminho_tmp(tmp_path, monkeypatch):
    arquivo = tmp_path / "hist.jsonl"
    monkeypatch.setenv("PERSISTENCIA_ARQUIVO", str(arquivo))
    return arquivo


def test_registrar_e_carregar(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    registro = persistencia.registrar_triagem({"resumo": "bug 1", "gravidade": "CRÍTICA 🚨", "score": -66.7})
    assert registro["id"]
    assert registro["data"]
    assert registro["data_hora"]
    registros = persistencia.carregar_registros()
    assert len(registros) == 1
    assert registros[0]["resumo"] == "bug 1"


def test_append_acumula_varias_triagens(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    persistencia.registrar_triagem({"resumo": "a"})
    persistencia.registrar_triagem({"resumo": "b"})
    persistencia.registrar_triagem({"resumo": "c"})
    assert len(persistencia.carregar_registros()) == 3


def test_registros_por_data_filtra(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    persistencia.registrar_triagem({"resumo": "hoje"})
    data_hoje = persistencia.carregar_registros()[0]["data"]
    assert len(persistencia.registros_por_data(data_hoje)) == 1
    assert persistencia.registros_por_data("2000-01-01") == []


def test_datas_disponiveis_sem_arquivo(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    assert persistencia.datas_disponiveis() == []


def test_registrar_exportacao_jira_vincula_ultimo(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    persistencia.registrar_triagem({"resumo": "primeira"})
    persistencia.registrar_triagem({"resumo": "segunda"})
    assert persistencia.registrar_exportacao_jira("KAN-9", "https://jira.x/9") is True
    registros = persistencia.carregar_registros()
    assert registros[-1]["jira_key"] == "KAN-9"
    assert registros[0].get("jira_key") is None


def test_registrar_exportacao_sem_registros(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    assert persistencia.registrar_exportacao_jira("KAN", "https://jira.x") is False


def test_excluir_antigos(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    persistencia.registrar_triagem({"resumo": "antiga"})
    persistencia.registrar_triagem({"resumo": "nova"})
    registros = persistencia.carregar_registros()
    registros[0]["data"] = "2020-01-01"
    persistencia._reescrever(registros)
    assert persistencia.excluir_antigos(90) == 1
    restantes = persistencia.carregar_registros()
    assert len(restantes) == 1
    assert restantes[0]["resumo"] == "nova"