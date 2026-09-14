# Testes do fluxo de restauração de sessão persistida (sessao_persist).
#
# O _restaurar é a lógica pura (dependências mockadas): renova o access_token
# pelo refresh_token salvo no navegador. Testamos o contrato de status, que
# alimenta o motivo exibido na tela de login quando a restauração falha.

import pytest
import sessao_persist

# ── _restaurar (reidratação da sessão) ───────────────────────────────────────

def test_restaurar_sem_valor_retorna_ausente(monkeypatch):
    monkeypatch.setattr(sessao_persist, "salvar", lambda *a, **k: None)
    assert sessao_persist._restaurar(None) == "ausente"
    assert sessao_persist._restaurar({}) == "ausente"
    assert sessao_persist._restaurar({"access_token": "x"}) == "ausente"


def test_restaurar_refresh_token_sem_access_token_retorna_expirada(monkeypatch):
    monkeypatch.setattr(
        "auth_supabase.renovar_sessao",
        lambda _rt: (True, "ok", {"access_token": None}),
    )
    monkeypatch.setattr(sessao_persist, "salvar", lambda *a, **k: None)
    assert sessao_persist._restaurar({"refresh_token": "abc"}) == "expirada"


def test_restaurar_renovacao_recusada_retorna_expirada(monkeypatch):
    monkeypatch.setattr(
        "auth_supabase.renovar_sessao",
        lambda _rt: (False, "invalid_grant", None),
    )
    monkeypatch.setattr(sessao_persist, "salvar", lambda *a, **k: None)
    assert sessao_persist._restaurar({"refresh_token": "abc"}) == "expirada"


def test_restaurar_falha_de_rede_retorna_erro(monkeypatch):
    def _boom(_rt):
        raise RuntimeError("timeout")

    monkeypatch.setattr("auth_supabase.renovar_sessao", _boom)
    monkeypatch.setattr(sessao_persist, "salvar", lambda *a, **k: None)
    assert sessao_persist._restaurar({"refresh_token": "abc"}) == "erro"


def test_restaurar_sucesso_guarda_e_resalva(monkeypatch):
    nova = {"access_token": "novo", "refresh_token": "rt-novo", "user": {"email": "a@b.com"}}
    guardado = []
    registros = []
    import auth_supabase

    def _guardar(dados):
        registros.append(dados)

    monkeypatch.setattr("auth_supabase.renovar_sessao", lambda _rt: (True, "ok", nova))
    monkeypatch.setattr(auth_supabase, "guardar_sessao", _guardar)
    monkeypatch.setattr(sessao_persist, "salvar", lambda d: guardado.append(d))
    assert sessao_persist._restaurar({"refresh_token": "abc"}) == "ok"
    assert guardado == [nova]
    assert registros == [nova]


# ── _tem_limpar_pendente (guard do logout) ───────────────────────────────────

def test_tem_limpar_pendente_sem_fila(monkeypatch):
    class SS:
        def get(self, _k, _d=None):
            return _d

    monkeypatch.setattr(sessao_persist.st, "session_state", SS())
    assert sessao_persist._tem_limpar_pendente() is False


def test_tem_limpar_pendente_com_salvar_na_fila(monkeypatch):
    class SS:
        def get(self, _k, _d=None):
            if _k == sessao_persist._KEY_FILA:
                return ("salvar", {"access_token": "x"})
            return _d

    monkeypatch.setattr(sessao_persist.st, "session_state", SS())
    assert sessao_persist._tem_limpar_pendente() is False


def test_tem_limpar_pendente_com_limpar_na_fila(monkeypatch):
    class SS:
        def get(self, _k, _d=None):
            if _k == sessao_persist._KEY_FILA:
                return ("limpar", None)
            return _d

    monkeypatch.setattr(sessao_persist.st, "session_state", SS())
    assert sessao_persist._tem_limpar_pendente() is True