# Testes unitários do perfil do usuário (perfil.py)
# Roda com: pytest -v
# Confirma: fallback JSONL, nuvem ganha do local, nome exibição e fuso/avatar.


import perfil
import nuvem_supabase


def _caminho_tmp(tmp_path, monkeypatch):
    arquivo = str(tmp_path / "perfis.jsonl")
    monkeypatch.setenv("PERFIL_ARQUIVO", arquivo)
    return arquivo


def _mock_nuvem(monkeypatch, perfil_banco=None):
    """Nuvem desativada (retorna None) ou com perfil fixo."""

    class Falso:
        @staticmethod
        def carregar_perfil_banco(uid):
            if perfil_banco is None:
                raise RuntimeError("offline")
            return perfil_banco

        @staticmethod
        def gravar_perfil_banco(uid, perfil):
            return False  # nunca salva na nuvem nos testes de fallback

    monkeypatch.setattr(perfil, "nuvem_supabase", Falso)


# --- Fallback JSONL local ---
def test_padrao_vazio(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    _mock_nuvem(monkeypatch)
    assert perfil.carregar("u1") == {
        "nome": "", "empresa": "", "fuso": "America/Sao_Paulo", "avatar": ""
    }


def test_salvar_e_carregar_jsonl(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    _mock_nuvem(monkeypatch)
    assert perfil.salvar("u1", {"nome": "Iago Nunes", "empresa": "QA", "fuso": "America/Manaus"}) is True
    dados = perfil.carregar("u1")
    assert dados["nome"] == "Iago Nunes"
    assert dados["empresa"] == "QA"
    assert dados["fuso"] == "America/Manaus"


def test_jsonl_isola_por_uid(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    _mock_nuvem(monkeypatch)
    perfil.salvar("u1", {"nome": "A", "empresa": "", "fuso": "", "avatar": ""})
    perfil.salvar("u2", {"nome": "B", "empresa": "", "fuso": "", "avatar": ""})
    assert perfil.carregar("u1")["nome"] == "A"
    assert perfil.carregar("u2")["nome"] == "B"


# --- Nuvem ganha do local ---
def test_nuvem_ganha_do_jsonl(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    _mock_nuvem(monkeypatch, perfil_banco={
        "nome": "Nome da Nuvem", "empresa": "Supabase", "fuso": "America/Fortaleza", "avatar": ""
    })
    perfil.salvar("u1", {"nome": "Nome Local", "empresa": "", "fuso": "", "avatar": ""})
    assert perfil.carregar("u1")["nome"] == "Nome da Nuvem"


def test_erro_de_rede_na_leitura_cai_no_jsonl(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    _mock_nuvem(monkeypatch, perfil_banco=None)
    perfil.salvar("u1", {"nome": "Local", "empresa": "", "fuso": "", "avatar": ""})
    assert perfil.carregar("u1")["nome"] == "Local"


# --- nome_exibicao ---
def test_nome_exibicao_prioriza_nome(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    _mock_nuvem(monkeypatch)
    perfil.salvar("u1", {"nome": "Iago Nunes", "empresa": "iago.dev", "fuso": "", "avatar": ""})
    assert perfil.nome_exibicao("u1", "iago@qa.com") == "Iago Nunes"


def test_nome_exibicao_cai_na_empresa(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    _mock_nuvem(monkeypatch)
    perfil.salvar("u1", {"nome": "", "empresa": "QA Solutions", "fuso": "", "avatar": ""})
    assert perfil.nome_exibicao("u1", "iago@qa.com") == "QA Solutions"


def test_nome_exibicao_sem_dados_usa_parte_do_email(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    _mock_nuvem(monkeypatch)
    assert perfil.nome_exibicao("u1", "iago.nunes@qa.com") == "Iago Nunes"
    assert perfil.nome_exibicao("u1", "qa@solo.dev") == "Qa"


def test_nome_exibicao_sem_nada_devolve_usuario(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    _mock_nuvem(monkeypatch)
    assert perfil.nome_exibicao("u1") == "usuario"


# --- Fuso ---
def test_fuso_invalido_cai_no_padrao(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    _mock_nuvem(monkeypatch)
    perfil.salvar("u1", {"nome": "X", "empresa": "", "fuso": "Etc/Lugar_Inexistente", "avatar": ""})
    assert perfil.carregar("u1")["fuso"] == "America/Sao_Paulo"


def test_fuso_valido_aceito(tmp_path, monkeypatch):
    assert perfil.normalizar_fuso("America/Manaus") == "America/Manaus"
    assert perfil.normalizar_fuso("") == "America/Sao_Paulo"
    assert perfil.fuso_valido("America/Recife") is True
    assert perfil.fuso_valido("Nope/Foo") is False


# --- Avatar + iniciais ---
def test_avatar_salvo_e_carregado(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    _mock_nuvem(monkeypatch)
    perfil.salvar("u1", {"nome": "Iago", "empresa": "", "fuso": "", "avatar": "data:image/png;base64,AAAA"})
    assert perfil.carregar("u1")["avatar"] == "data:image/png;base64,AAAA"


def test_iniciais_para_bolinha():
    assert perfil._iniciais("Iago Nunes de Araujo") == "IA"
    assert perfil._iniciais("Solo") == "S"
    assert perfil._iniciais("") == "?"


def test_salvar_sem_uid_nao_quebra(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    _mock_nuvem(monkeypatch)
    assert perfil.salvar("", {"nome": "X", "empresa": "", "fuso": "", "avatar": ""}) is False


# --- nuvem_supabase: gravar/carregar perfil (Semântica REST) ---
def test_gravar_perfil_banco_envia_upsert(monkeypatch):
    calls = {}

    class _Resp:
        status_code = 200

        def raise_for_status(self):
            return None

    def _fake_post(url, headers=None, params=None, json=None, timeout=None):
        calls["url"] = url
        calls["headers"] = dict(headers or {})
        calls["params"] = params
        calls["json"] = json
        return _Resp()

    monkeypatch.setattr(nuvem_supabase, "_config", lambda: ("https://supa.supabase.co", "chave"))
    monkeypatch.setattr(nuvem_supabase.requests, "post", _fake_post)
    assert nuvem_supabase.gravar_perfil_banco("u1", {"nome": "Iago", "empresa": "QA", "fuso": "America/Manaus", "avatar": ""}) is True
    assert calls["url"].endswith("/perfis_usuario")
    assert calls["params"] == {"on_conflict": "uid"}
    assert calls["json"]["uid"] == "u1"
    assert calls["json"]["nome"] == "Iago"


def test_carregar_perfil_banco_offline_retorna_none(monkeypatch):
    monkeypatch.setattr(nuvem_supabase, "_config", lambda: None)
    assert nuvem_supabase.carregar_perfil_banco("u1") is None
    assert nuvem_supabase.gravar_perfil_banco("u1", {}) is False