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


# ─── Passo 3: plano por usuário (banco) + tenant = usuário logado ─────────────

def _mock_login(monkeypatch, uid="u-abc"):
    """Simula um usuário logado (uid) sem depender do Supabase real."""
    monkeypatch.setattr(plano, "uid_logado", lambda: uid)


def test_plano_do_banco_ganha_do_env(monkeypatch):
    monkeypatch.setenv("PLANO", "free")
    _mock_login(monkeypatch)
    monkeypatch.setattr(plano, "plano_no_banco", lambda uid: "pago")
    assert plano.plano_atual() == "pago"
    assert plano.pago()


def test_plano_sem_linha_no_banco_cai_no_env(monkeypatch):
    monkeypatch.setenv("PLANO", "free")
    _mock_login(monkeypatch)
    monkeypatch.setattr(plano, "plano_no_banco", lambda uid: None)
    assert plano.plano_atual() == "free"
    assert not plano.pago()


def test_plano_do_banco_invalido_cai_no_env(monkeypatch):
    monkeypatch.setenv("PLANO", "free")
    _mock_login(monkeypatch)
    monkeypatch.setattr(plano, "plano_no_banco", lambda uid: "luxo")
    assert plano.plano_atual() == "free"


def test_plano_sem_login_usa_env(monkeypatch):
    monkeypatch.setenv("PLANO", "pago")
    monkeypatch.setattr(plano, "uid_logado", lambda: None)
    assert plano.plano_atual() == "pago"


def test_plano_no_banco_usa_env_se_nao_logado(monkeypatch):
    monkeypatch.delenv("PLANO", raising=False)
    monkeypatch.setattr(plano, "uid_logado", lambda: None)
    assert plano.plano_atual() == "free"


def test_tenant_atual_usa_uid_do_usuario(monkeypatch):
    monkeypatch.setenv("TENANT_ID", "acme")
    _mock_login(monkeypatch, uid="u-xyz")
    assert plano.tenant_atual() == "u-xyz"
    reg = plano.integrar_tenant({"resumo": "bug"})
    assert reg["tenant_id"] == "u-xyz"
    assert plano.dados_do_tenant(reg)


def test_tenant_sem_login_vira_global(monkeypatch):
    monkeypatch.delenv("TENANT_ID", raising=False)
    monkeypatch.setattr(plano, "uid_logado", lambda: None)
    assert plano.tenant_atual() == "global"


def test_usuario_nao_ve_dados_de_outro_tenant(monkeypatch):
    _mock_login(monkeypatch, uid="u-um")
    assert not plano.dados_do_tenant({"tenant_id": "u-dois"})
    assert plano.dados_do_tenant({"tenant_id": "u-um"})


def test_definir_plano_no_banco_delega_upsert(monkeypatch):
    gravado = {}
    _mock_login(monkeypatch, uid="u-abc")

    def _falso(uid, plano):
        gravado[uid] = plano
        return True

    monkeypatch.setattr(plano, "nuvem_supabase", type("NS", (), {
        "gravar_plano_banco": _falso,
        "carregar_plano_banco": lambda uid: None,
    }))
    assert plano.definir_plano_no_banco("u-abc", "pago")
    assert gravado == {"u-abc": "pago"}
    # valor inválido vira free
    assert plano.definir_plano_no_banco("u-abc", "luxo")
    assert gravado["u-abc"] == "free"


def test_definir_plano_offline_nao_levanta(monkeypatch):
    _mock_login(monkeypatch, uid="u-abc")

    class Falso:
        @staticmethod
        def gravar_plano_banco(uid, plano):
            raise RuntimeError("offline")

    monkeypatch.setattr(plano, "nuvem_supabase", Falso)
    assert plano.definir_plano_no_banco("u-abc", "pago") is False


def test_plano_no_banco_offline_cai_no_env(monkeypatch):
    monkeypatch.setenv("PLANO", "free")
    _mock_login(monkeypatch)

    class Falso:
        @staticmethod
        def carregar_plano_banco(uid):
            raise RuntimeError("offline")

    monkeypatch.setattr(plano, "nuvem_supabase", Falso)
    assert plano.plano_atual() == "free"


# ─── Passo 4: usuário novo (nuvem ativa, sem linha) começa SEMPRE em free ──

def _mock_nuvem_ativa(monkeypatch, ativa=True):
    monkeypatch.setattr(plano, "nuvem_supabase", type("NS", (), {
        "disponivel": lambda: ativa,
        "carregar_plano_banco": lambda uid: None,
    }))


def test_usuario_novo_sem_linha_comeca_free_mesmo_com_plano_pago_env(monkeypatch):
    monkeypatch.setenv("PLANO", "pago")
    _mock_login(monkeypatch)
    _mock_nuvem_ativa(monkeypatch, ativa=True)
    assert plano.plano_atual() == "free"
    assert not plano.pago()


def test_usuario_novo_sem_linha_env_free_tambem_free(monkeypatch):
    monkeypatch.setenv("PLANO", "free")
    _mock_login(monkeypatch)
    _mock_nuvem_ativa(monkeypatch, ativa=True)
    assert plano.plano_atual() == "free"


def test_usuario_novo_env_ignorado_mas_plano_do_banco_ganha(monkeypatch):
    monkeypatch.setenv("PLANO", "free")
    _mock_login(monkeypatch)
    monkeypatch.setattr(plano.nuvem_supabase, "disponivel", lambda: True)
    monkeypatch.setattr(plano.nuvem_supabase, "carregar_plano_banco", lambda uid: "pago")
    assert plano.plano_atual() == "pago"


def test_usuario_com_nuvem_off_mantem_env_legado(monkeypatch):
    monkeypatch.setenv("PLANO", "pago")
    _mock_login(monkeypatch)
    _mock_nuvem_ativa(monkeypatch, ativa=False)
    assert plano.plano_atual() == "pago"