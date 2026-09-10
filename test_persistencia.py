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


def test_timestamp_usa_fuso_local_brasil(tmp_path, monkeypatch):
    from datetime import datetime
    _caminho_tmp(tmp_path, monkeypatch)
    registro = persistencia.registrar_triagem({"resumo": "fuso"})
    agora_local = datetime.now(persistencia._FUSO)
    # o data_hora deve trazer o offset -03:00 (Brasília) e bater com a hora local
    assert registro["data_hora"].endswith("-03:00")
    assert registro["data_hora"][11:13] == agora_local.strftime("%H")


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


def test_tenant_isola_dados(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    monkeypatch.setenv("TENANT_ID", "acme")
    persistencia.registrar_triagem({"resumo": "bug acme"})
    monkeypatch.setenv("TENANT_ID", "global")
    persistencia.registrar_triagem({"resumo": "bug global"})
    monkeypatch.setenv("TENANT_ID", "acme")
    regs = persistencia.carregar_registros()
    assert len(regs) == 1
    assert regs[0]["resumo"] == "bug acme"
    data = regs[0]["data"]
    assert len(persistencia.registros_por_data(data)) == 1
    assert persistencia.datas_disponiveis() == [data]


def test_tenant_grava_campo_no_registro(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    monkeypatch.setenv("TENANT_ID", "acme")
    registro = persistencia.registrar_triagem({"resumo": "x"})
    assert registro["tenant_id"] == "acme"


def test_registro_antigo_sem_tenant_vale_como_global(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    persistencia._salvar_jsonl({"resumo": "pré-SaaS"})  # sem tenant_id
    monkeypatch.setenv("TENANT_ID", "global")
    assert len(persistencia.carregar_registros()) == 1
    monkeypatch.setenv("TENANT_ID", "outra")
    assert persistencia.carregar_registros() == []