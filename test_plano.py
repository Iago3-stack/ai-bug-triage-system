import plano


def test_plano_padrao_free(monkeypatch):
    monkeypatch.delenv("PLANO", raising=False)
    assert plano.plano_atual() == "free"
    assert not plano.pago()


def test_plano_pago(monkeypatch):
    monkeypatch.setenv("PLANO", "pago")
    assert plano.plano_atual() == "pago"
    assert plano.pago()


def test_plano_desconhecido_vira_free(monkeypatch):
    monkeypatch.setenv("PLANO", "luxo")
    assert plano.plano_atual() == "free"
    assert not plano.pago()


def test_limite_historico_por_plano(monkeypatch):
    monkeypatch.setenv("PLANO", "free")
    assert plano.limite_historico_free() == 30
    monkeypatch.setenv("PLANO", "pago")
    assert plano.limite_historico_free() > 10**8


def test_tenant_padrao_global(monkeypatch):
    monkeypatch.delenv("TENANT_ID", raising=False)
    assert plano.tenant_atual() == "global"


def test_tenant_personalizado(monkeypatch):
    monkeypatch.setenv("TENANT_ID", "acme")
    assert plano.tenant_atual() == "acme"


def test_integrar_tenant_e_filtrar(monkeypatch):
    monkeypatch.setenv("TENANT_ID", "acme")
    reg = plano.integrar_tenant({"resumo": "bug"})
    assert reg["tenant_id"] == "acme"
    assert plano.dados_do_tenant(reg)
    monkeypatch.setenv("TENANT_ID", "outra")
    assert not plano.dados_do_tenant(reg)


def test_registro_antigo_sem_tenant_conta_global():
    assert plano.dados_do_tenant({"resumo": "antigo"})


def test_free_um_canal_prioriza_email(monkeypatch):
    monkeypatch.setenv("PLANO", "free")
    assert plano.aplicar_limite_canais(True, True) == (True, False)
    assert plano.aplicar_limite_canais(False, True) == (False, True)


def test_pago_multicanal(monkeypatch):
    monkeypatch.setenv("PLANO", "pago")
    assert plano.aplicar_limite_canais(True, True) == (True, True)
    assert plano.aplicar_limite_canais(False, True) == (False, True)