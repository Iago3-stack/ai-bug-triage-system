# Testes unitários da persistência em nuvem (nuvem_supabase.py) e do facade.
# Roda com: pytest -v
# 100% offline: config e HTTP são mockados — nunca sai da máquina.

import persistencia
import nuvem_supabase


class _FakeResposta:
    def __init__(self, dados=None):
        self._dados = dados or []

    def raise_for_status(self):
        return None

    def json(self):
        return self._dados


def _sem_config(monkeypatch):
    monkeypatch.setattr(nuvem_supabase, "_carregar_env", lambda: {})


# --- Configuração ------------------------------------------------------
def test_disponivel_falso_sem_credenciais(monkeypatch):
    _sem_config(monkeypatch)
    assert nuvem_supabase.disponivel() is False


def test_config_ignora_meias_credenciais(monkeypatch):
    _sem_config(monkeypatch)
    monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
    assert nuvem_supabase._config() is None


def test_config_lida_secrets_e_env(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-teste")
    url, chave = nuvem_supabase._config()
    assert url == "https://x.supabase.co"
    assert chave == "anon-teste"


# --- Conversão linha <-> doc (formato do app) -------------------------
def test_linha_para_doc_extrai_colunas():
    registro = {
        "id": "abc123",
        "data_hora": "2026-09-07T10:00:00-03:00",
        "data": "2026-09-07",
        "resumo": "bug",
        "gravidade": "CRÍTICA 🚨",
    }
    doc = nuvem_supabase._linha_para_doc(registro)
    assert doc["id"] == "abc123"
    assert doc["data"] == "2026-09-07"
    assert doc["payload"] is registro  # payload guarda o registro inteiro


def test_doc_para_linha_restaura_payload_e_jira():
    doc = {
        "id": "abc123",
        "data_hora": "2026-09-07T10:00:00-03:00",
        "data": "2026-09-07",
        "jira_key": "KAN-9",
        "jira_url": "https://jira.x/9",
        "payload": {"id": "abc123", "resumo": "bug", "gravidade": "CRÍTICA 🚨",
                    "data_hora": "2026-09-07T10:00:00-03:00", "data": "2026-09-07"},
    }
    registro = nuvem_supabase._doc_para_linha(doc)
    assert registro["resumo"] == "bug"
    assert registro["jira_key"] == "KAN-9"
    assert registro["data"] == "2026-09-07"


# --- HTTP (requests mockado) -------------------------------------------
def test_registrar_triagem_envia_post(monkeypatch):
    _sem_config(monkeypatch)
    monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-test")
    chamadas = {}

    def _fake_post(url, headers=None, json=None, timeout=None):
        chamadas["url"] = url
        chamadas["json"] = json
        return _FakeResposta([json])

    monkeypatch.setattr(nuvem_supabase.requests, "post", _fake_post)
    dados = {"id": "abc", "resumo": "bug na nuvem"}
    retorno = nuvem_supabase.registrar_triagem(dados)
    assert retorno is dados
    assert "rest/v1/triagens" in chamadas["url"]
    assert chamadas["json"]["payload"] is dados


def test_carregar_registros_retorna_payloads(monkeypatch):
    _sem_config(monkeypatch)
    monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-test")
    doc = {
        "id": "a1", "data": "2026-09-07",
        "data_hora": "2026-09-07T10:00:00-03:00",
        "jira_key": None, "jira_url": None,
        "payload": {"resumo": "bug", "data": "2026-09-07",
                    "data_hora": "2026-09-07T10:00:00-03:00", "id": "a1"},
    }

    def _fake_get(url, headers=None, params=None, timeout=None):
        assert params["order"] == "data_hora.asc"
        return _FakeResposta([doc])

    monkeypatch.setattr(nuvem_supabase.requests, "get", _fake_get)
    registros = nuvem_supabase.carregar_registros()
    assert len(registros) == 1
    assert registros[0]["resumo"] == "bug"
    assert registros[0]["id"] == "a1"


def test_registrar_resolucao_faz_fetch_e_patch_por_id(monkeypatch):
    _sem_config(monkeypatch)
    monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-test")

    def _fake_get(url, headers=None, params=None, timeout=None):
        assert params["id"] == "eq.abc123"
        return _FakeResposta([
            {"id": "abc123", "payload": {"id": "abc123", "resumo": "bug"}}
        ])

    patch_info = {}

    def _fake_patch(url, headers=None, params=None, json=None, timeout=None):
        patch_info["params"] = params
        patch_info["json"] = json
        return _FakeResposta([json])

    monkeypatch.setattr(nuvem_supabase.requests, "get", _fake_get)
    monkeypatch.setattr(nuvem_supabase.requests, "patch", _fake_patch)
    ok = nuvem_supabase.registrar_resolucao("abc123", "rollback da versão 1.2.0")
    assert ok is True
    assert patch_info["params"]["id"] == "eq.abc123"
    # a resolução entra no payload (o RAG lê do payload convertido)
    assert patch_info["json"]["payload"]["resolucao"] == "rollback da versão 1.2.0"
    assert patch_info["json"]["payload"]["resumo"] == "bug"


def test_registrar_resolucao_id_inexistente_retorna_falso(monkeypatch):
    _sem_config(monkeypatch)
    monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-test")
    monkeypatch.setattr(nuvem_supabase.requests, "get",
                        lambda *a, **k: _FakeResposta([]))
    assert nuvem_supabase.registrar_resolucao("xyz", "nada") is False


# --- Facade persistencia.py (dispatch) ----------------------------------
def test_facade_usa_nuvem_quando_configurada(monkeypatch, tmp_path):
    # Sem caminho local nem backend forçado -> dispatches para a nuvem.
    monkeypatch.delenv("PERSISTENCIA_ARQUIVO", raising=False)
    monkeypatch.delenv("PERSISTENCIA_BACKEND", raising=False)
    monkeypatch.setattr(nuvem_supabase, "disponivel", lambda: True)
    destino = {}

    def _fake_registrar(dados):
        destino["dados"] = dados
        return dados

    monkeypatch.setattr(nuvem_supabase, "registrar_triagem", _fake_registrar)
    registro = persistencia.registrar_triagem({"resumo": "vai pra nuvem"})
    assert destino["dados"] is registro
    assert registro["resumo"] == "vai pra nuvem"


def test_facade_forca_jsonl_por_env(monkeypatch, tmp_path):
    # PERSISTENCIA_BACKEND=jsonl manda para o arquivo mesmo com nuvem disponível.
    arquivo = tmp_path / "hist.jsonl"
    monkeypatch.setenv("PERSISTENCIA_BACKEND", "jsonl")
    monkeypatch.delenv("PERSISTENCIA_ARQUIVO", raising=False)
    monkeypatch.setattr(nuvem_supabase, "disponivel", lambda: True)
    monkeypatch.setattr(persistencia, "_caminho", lambda: arquivo)

    def _nao_deve_chamar_nuvem(*args, **kwargs):
        raise AssertionError("nuvem não deveria ser chamada")

    monkeypatch.setattr(nuvem_supabase, "registrar_triagem", _nao_deve_chamar_nuvem)
    persistencia.registrar_triagem({"resumo": "local forçado"})
    assert arquivo.exists()
    assert len(persistencia.carregar_registros()) == 1


def test_facade_failover_grava_local_quando_nuvem_indisponivel(monkeypatch, tmp_path):
    # Filosofia do app: falha da nuvem NUNCA perde a triagem — faz failover p/ JSONL.
    arquivo = tmp_path / "hist.jsonl"
    monkeypatch.delenv("PERSISTENCIA_ARQUIVO", raising=False)
    monkeypatch.delenv("PERSISTENCIA_BACKEND", raising=False)
    monkeypatch.setattr(nuvem_supabase, "disponivel", lambda: True)
    monkeypatch.setattr(persistencia, "_caminho", lambda: arquivo)

    def _supabase_fora_do_ar(*args, **kwargs):
        raise OSError("Supabase indisponível")

    monkeypatch.setattr(nuvem_supabase, "registrar_triagem", _supabase_fora_do_ar)
    monkeypatch.setattr(nuvem_supabase, "carregar_registros", _supabase_fora_do_ar)

    registro = persistencia.registrar_triagem({"resumo": "sobreviveu"})
    assert registro["resumo"] == "sobreviveu"
    assert arquivo.exists()
    with open(arquivo, encoding="utf-8") as f:
        linhas = f.read().strip().splitlines()
    assert len(linhas) == 1


def test_facade_registrar_resolucao_em_jsonl(monkeypatch, tmp_path):
    # Sem nuvem: a resolução é gravada no registro local pelo id.
    arquivo = tmp_path / "hist.jsonl"
    monkeypatch.setenv("PERSISTENCIA_ARQUIVO", str(arquivo))
    registro = persistencia.registrar_triagem({"resumo": "bug com resolução"})
    assert persistencia.registrar_resolucao(registro["id"], "trocar o servidor NFS") is True
    registros = persistencia.carregar_registros()
    assert registros[0]["resolucao"] == "trocar o servidor NFS"


def test_facade_registrar_resolucao_id_inexistente_falha(monkeypatch, tmp_path):
    arquivo = tmp_path / "hist.jsonl"
    monkeypatch.setenv("PERSISTENCIA_ARQUIVO", str(arquivo))
    persistencia.registrar_triagem({"resumo": "um"})
    assert persistencia.registrar_resolucao("id-que-nao-existe", "x") is False