# Testes do Painel do Dono (v2.11.0): Teste Premium com validade, tabela
# `usuarios` e ações de admin. Roda com: pytest -v

from datetime import datetime, timedelta, timezone

import pytest

import admin
import plano
import nuvem_supabase


# ─── plano: Teste Premium com validade ────────────────────────────────────────

def _mock_nuvem_trial(monkeypatch, teste_ate=None, plano_b="free", ativa=True):
    """Máquina fake da nuvem com suporte a teste_ate."""
    class NS:
        @staticmethod
        def disponivel():
            return ativa

        @staticmethod
        def carregar_plano_banco(uid):
            return plano_b

        @staticmethod
        def carregar_teste_banco(uid):
            if teste_ate is _OFFLINE:
                raise RuntimeError("offline")
            return teste_ate

        @staticmethod
        def gravar_teste_banco(uid, ate_iso):
            registros_trial["ate"] = ate_iso
            return True

        @staticmethod
        def gravar_plano_banco(uid, plano_novo, clear_teste=False):
            registros_trial["plano"] = plano_novo
            registros_trial["clear"] = clear_teste
            return True

    registros_trial.clear()
    monkeypatch.setattr(plano, "nuvem_supabase", NS)
    return registros_trial


registros_trial = {}
_OFFLINE = object()


def test_teste_premium_restante_delega_para_nuvem(monkeypatch):
    monkeypatch.setattr(plano, "nuvem_supabase", type("NS", (), {
        "carregar_teste_banco": lambda uid: "2026-10-01T00:00:00+00:00",
    }))
    assert plano.teste_premium_restante("u1") == "2026-10-01T00:00:00+00:00"


def test_teste_premium_offline_retorna_none(monkeypatch):
    monkeypatch.setattr(plano, "nuvem_supabase", type("NS", (), {
        "carregar_teste_banco": lambda uid: (_ for _ in ()).throw(RuntimeError("offline")),
    }))
    assert plano.teste_premium_restante("u1") is None


def test_plano_free_com_teste_ativo_vira_pago(monkeypatch):
    monkeypatch.setenv("PLANO", "free")
    monkeypatch.setattr(plano, "uid_logado", lambda: "u1")
    _mock_nuvem_trial(monkeypatch, teste_ate=(datetime.now(timezone.utc) + timedelta(days=2)).isoformat(), plano_b="free")
    assert plano.plano_atual() == "pago"
    assert plano.pago()


def test_plano_free_com_teste_expirado_fica_free(monkeypatch):
    monkeypatch.setenv("PLANO", "free")
    monkeypatch.setattr(plano, "uid_logado", lambda: "u1")
    _mock_nuvem_trial(monkeypatch, teste_ate=(datetime.now(timezone.utc) - timedelta(days=2)).isoformat(), plano_b="free")
    assert plano.plano_atual() == "free"
    assert not plano.pago()


def test_plano_sem_login_ignora_teste(monkeypatch):
    monkeypatch.setenv("PLANO", "free")
    monkeypatch.setattr(plano, "uid_logado", lambda: None)
    _mock_nuvem_trial(monkeypatch, teste_ate=(datetime.now(timezone.utc) + timedelta(days=2)).isoformat(), plano_b="free")
    assert plano.plano_atual() == "free"


def test_definir_trial_grava_ate_futuro(monkeypatch):
    monkeypatch.setattr(plano, "uid_logado", lambda: "u1")
    _mock_nuvem_trial(monkeypatch, teste_ate=None)
    assert plano.definir_trial("u1", 7) is True
    ate = datetime.fromisoformat(registros_trial["ate"].replace("Z", "+00:00"))
    assert ate > datetime.now(timezone.utc)
    assert (datetime.now(timezone.utc) + timedelta(days=7) - ate).days == 0


def test_definir_trial_offline_nao_levanta(monkeypatch):
    monkeypatch.setattr(plano, "uid_logado", lambda: "u1")
    monkeypatch.setattr(plano, "nuvem_supabase", type("NS", (), {
        "gravar_teste_banco": lambda uid, ate: (_ for _ in ()).throw(RuntimeError("offline")),
    }))
    assert plano.definir_trial("u1", 7) is False


def test_definir_plano_manual_encerra_teste(monkeypatch):
    _mock_nuvem_trial(monkeypatch, teste_ate=None)
    assert plano.definir_plano_manual("u1", "free") is True
    assert registros_trial["plano"] == "free"
    assert registros_trial["clear"] is True
    assert plano.definir_plano_manual("u1", "pago") is True
    assert registros_trial["plano"] == "pago"
    assert registros_trial["clear"] is True


def test_definir_plano_manual_invalido_vira_free(monkeypatch):
    _mock_nuvem_trial(monkeypatch)
    assert plano.definir_plano_manual("u1", "luxo") is True
    assert registros_trial["plano"] == "free"


# ─── nuvem_supabase: planos/trial ─────────────────────────────────────────────

class _Resp:
    status_code = 200

    def __init__(self, payload=None):
        self._payload = payload or []

    def json(self):
        return self._payload

    def raise_for_status(self):
        return None


def _mock_rest(monkeypatch, resp):
    monkeypatch.setattr(nuvem_supabase, "_config", lambda: ("https://supa.supabase.co", "chave"))
    monkeypatch.setattr(nuvem_supabase.requests, "get", lambda *a, **k: _Resp(resp))
    monkeypatch.setattr(nuvem_supabase.requests, "post", lambda *a, **k: _Resp())
    monkeypatch.setattr(nuvem_supabase.requests, "patch", lambda *a, **k: _Resp())
    return nuvem_supabase._headers()


def test_gravar_plano_pago_limpa_teste(monkeypatch):
    chamadas = {"post": 0, "patch": []}

    def _post(*a, **k):
        chamadas["post"] += 1
        return _Resp()

    def _patch(*a, **k):
        chamadas["patch"].append((k.get("params"), k.get("json")))
        return _Resp()

    monkeypatch.setattr(nuvem_supabase, "_config", lambda: ("https://supa.supabase.co", "chave"))
    monkeypatch.setattr(nuvem_supabase.requests, "post", _post)
    monkeypatch.setattr(nuvem_supabase.requests, "patch", _patch)
    assert nuvem_supabase.gravar_plano_banco("u1", "pago") is True
    assert chamadas["post"] == 1
    assert chamadas["patch"] == [({"uid": "eq.u1"}, {"teste_ate": None})]


def test_gravar_plano_free_com_clear_tambem_limpa(monkeypatch):
    chamadas = {"patch": []}

    def _patch(*a, **k):
        chamadas["patch"].append((k.get("params"), k.get("json")))
        return _Resp()

    monkeypatch.setattr(nuvem_supabase, "_config", lambda: ("https://supa.supabase.co", "chave"))
    monkeypatch.setattr(nuvem_supabase.requests, "post", lambda *a, **k: _Resp())
    monkeypatch.setattr(nuvem_supabase.requests, "patch", _patch)
    assert nuvem_supabase.gravar_plano_banco("u1", "free", clear_teste=True) is True
    assert chamadas["patch"] == [({"uid": "eq.u1"}, {"teste_ate": None})]


def test_gravar_plano_free_sem_clear_nao_faz_patch(monkeypatch):
    chamadas = {"patch": []}

    def _patch(*a, **k):
        chamadas["patch"].append(1)
        return _Resp()

    monkeypatch.setattr(nuvem_supabase, "_config", lambda: ("https://supa.supabase.co", "chave"))
    monkeypatch.setattr(nuvem_supabase.requests, "post", lambda *a, **k: _Resp())
    monkeypatch.setattr(nuvem_supabase.requests, "patch", _patch)
    assert nuvem_supabase.gravar_plano_banco("u1", "free") is True
    assert chamadas["patch"] == []


def test_carregar_teste_banco(monkeypatch):
    _mock_rest(monkeypatch, [{"teste_ate": "2026-10-01T00:00:00+00:00"}])
    assert nuvem_supabase.carregar_teste_banco("u1") == "2026-10-01T00:00:00+00:00"
    _mock_rest(monkeypatch, [])
    assert nuvem_supabase.carregar_teste_banco("u1") is None


def test_carregar_teste_banco_offline(monkeypatch):
    monkeypatch.setattr(nuvem_supabase, "_config", lambda: None)
    assert nuvem_supabase.carregar_teste_banco("u1") is None


def test_gravar_teste_banco_upsert(monkeypatch):
    chamadas = {}

    def _post(url, headers=None, params=None, json=None, timeout=None):
        chamadas["url"] = url
        chamadas["params"] = params
        chamadas["json"] = json
        return _Resp()

    monkeypatch.setattr(nuvem_supabase, "_config", lambda: ("https://supa.supabase.co", "chave"))
    monkeypatch.setattr(nuvem_supabase.requests, "post", _post)
    assert nuvem_supabase.gravar_teste_banco("u1", "2026-10-01T00:00:00+00:00") is True
    assert chamadas["url"].endswith("/planos_usuario")
    assert chamadas["params"] == {"on_conflict": "uid"}
    assert chamadas["json"] == {"uid": "u1", "teste_ate": "2026-10-01T00:00:00+00:00"}


def test_carregar_todos_planos(monkeypatch):
    _mock_rest(monkeypatch, [{"uid": "u1", "plano": "pago", "teste_ate": None}])
    assert nuvem_supabase.carregar_todos_planos() == [{"uid": "u1", "plano": "pago", "teste_ate": None}]


def test_carregar_todos_perfis(monkeypatch):
    _mock_rest(monkeypatch, [{"uid": "u1", "nome": "Iago", "empresa": "QA", "avatar": ""}])
    assert nuvem_supabase.carregar_todos_perfis() == [{"uid": "u1", "nome": "Iago", "empresa": "QA", "avatar": ""}]


# ─── nuvem_supabase: tabela usuarios ──────────────────────────────────────────

def test_registrar_usuario_banco_upsert(monkeypatch):
    chamadas = {}

    def _post(url, headers=None, params=None, json=None, timeout=None):
        chamadas["url"] = url
        chamadas["params"] = params
        chamadas["json"] = json
        return _Resp()

    monkeypatch.setattr(nuvem_supabase, "_config", lambda: ("https://supa.supabase.co", "chave"))
    monkeypatch.setattr(nuvem_supabase.requests, "post", _post)
    assert nuvem_supabase.registrar_usuario_banco("u1", "dev@qa.com") is True
    assert chamadas["url"].endswith("/usuarios")
    assert chamadas["params"] == {"on_conflict": "uid"}
    assert chamadas["json"]["uid"] == "u1"
    assert chamadas["json"]["email"] == "dev@qa.com"
    assert "ultimo_login" in chamadas["json"]


def test_registrar_usuario_banco_nunca_levanta(monkeypatch):
    monkeypatch.setattr(nuvem_supabase, "_config", lambda: ("x", "y"))
    monkeypatch.setattr(nuvem_supabase.requests, "post", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("rede")))
    nuvem_supabase.registrar_usuario_banco("u1", "dev@qa.com") is False
    monkeypatch.setattr(nuvem_supabase, "_config", lambda: None)
    assert nuvem_supabase.registrar_usuario_banco("u1", "dev@qa.com") is False


def test_carregar_usuarios_ordena_por_ultimo_login(monkeypatch):
    chamadas = {}

    def _get(url, headers=None, params=None, timeout=None):
        chamadas["url"] = url
        chamadas["params"] = params
        return _Resp([{"uid": "u2", "email": "b@qa.com"}, {"uid": "u1", "email": "a@qa.com"}])

    monkeypatch.setattr(nuvem_supabase, "_config", lambda: ("https://supa.supabase.co", "chave"))
    monkeypatch.setattr(nuvem_supabase.requests, "get", _get)
    assert nuvem_supabase.carregar_usuarios()[0]["uid"] == "u2"
    assert chamadas["url"].endswith("/usuarios")
    assert chamadas["params"]["order"] == "ultimo_login.desc"


def test_carregar_usuarios_offline_retorna_lista_vazia(monkeypatch):
    monkeypatch.setattr(nuvem_supabase, "_config", lambda: None)
    assert nuvem_supabase.carregar_usuarios() == []
    assert nuvem_supabase.carregar_todos_planos() == []
    assert nuvem_supabase.carregar_todos_perfis() == []


# ─── admin: quem é o dono ─────────────────────────────────────────────────────

def test_eh_dono_sem_admin_email_nunca(monkeypatch):
    monkeypatch.delenv("ADMIN_EMAIL", raising=False)
    monkeypatch.setattr(admin, "email_logado", lambda: "dev@qa.com")
    assert admin.eh_dono() is False


def test_eh_dono_email_igual(monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "dono@qa.com")
    monkeypatch.setattr(admin, "email_logado", lambda: "dono@qa.com")
    assert admin.eh_dono() is True


def test_eh_dono_email_diferente(monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "dono@qa.com")
    monkeypatch.setattr(admin, "email_logado", lambda: "outro@qa.com")
    assert admin.eh_dono() is False


def test_email_logado_sem_sessao_none(monkeypatch):
    import auth_supabase
    monkeypatch.setattr(auth_supabase, "sessao", lambda: None)
    assert admin.email_logado() is None


def test_eh_dono_com_case_diferente(monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "Dono@QA.com")
    monkeypatch.setattr(admin, "email_logado", lambda: "dono@qa.com")
    assert admin.eh_dono() is True


# ─── roteador: painel só aparece para o dono ─────────────────────────────────

def test_rotas_sem_dono_nao_incluem_painel(monkeypatch):
    import roteador

    monkeypatch.setattr(admin, "eh_dono", lambda: False)
    assert len(roteador.paginas_visiveis()) == 4


def test_rotas_do_dono_incluem_painel(monkeypatch):
    import roteador

    monkeypatch.setattr(admin, "eh_dono", lambda: True)
    assert len(roteador.paginas_visiveis()) == 5


# ─── formatadores da página do dono ──────────────────────────────────────────

def test_fmt_data_formata_iso_e_falha_amigavel():
    from datetime import datetime
    from secoes import painel_dono as pd

    esperado = datetime.fromisoformat("2026-09-15T13:00:00+00:00").astimezone().strftime("%d/%m/%Y %H:%M")
    assert pd._fmt_data("2026-09-15T13:00:00+00:00") == esperado
    assert pd._fmt_data(None) == "—"
    assert pd._fmt_data("lixo") == "lixo"


def test_badges_dos_planos():
    from secoes import painel_dono as pd

    for tipo in ("premium", "teste", "basic"):
        badge = pd._badge(tipo)
        assert tipo in "premium teste basic".split() and badge.startswith("<span")