# Testes do rótulo humano de severidade (avaliacao.py). Herméticos:mockam o
# REST do Supabase (nuvem_supabase.requests) e nunca tocam a rede.

import pytest

import avaliacao
import nuvem_supabase


class _Resposta:
    def __init__(self, dados, status=200):
        self._dados = dados
        self.status_code = status

    def json(self):
        return self._dados

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class _FakeRequests:
    """requests.get/patch falsos que registram url/params/json de cada chamada."""

    def __init__(self, get=None, patch=None):
        self._get_impl = get or (lambda *a, **k: _Resposta([]))
        self._patch_impl = patch or (lambda *a, **k: _Resposta([]))
        self.chamadas = []

    def get(self, url, **kw):
        self.chamadas.append(("get", url, kw.get("params")))
        return self._get_impl(url, **kw)

    def patch(self, url, **kw):
        self.chamadas.append(("patch", url, kw.get("params"), kw.get("json")))
        return self._patch_impl(url, **kw)


# --- normalizar: 4 níveis da IA -> 3 canônicos -------------------------------
@pytest.mark.parametrize("entrada,esperado", [
    ("CRÍTICA 🚨", "CRÍTICA"),
    ("CRÍTICA", "CRÍTICA"),
    ("critica", "CRÍTICA"),
    ("ALTA 🚨", "CRÍTICA"),   # a IA usa 4 níveis: ALTA == CRÍTICA aqui
    ("MÉDIA ⚠️", "MÉDIA"),
    ("media", "MÉDIA"),
    ("NORMAL ✅", "NORMAL"),
    ("BAIXA", "NORMAL"),      # idem: BAIXA == NORMAL
    ("", ""),
    ("abc", ""),
])
def test_normalizar_mapeia_variacoes(entrada, esperado):
    assert avaliacao.normalizar(entrada) == esperado


# --- registrar: grava no payload sem migration -------------------------------
def test_registrar_grava_avaliacao_no_payload(monkeypatch):
    gravado = {}

    def _patch(url, **kw):
        gravado.update(kw["json"])
        return _Resposta([{"id": "x"}])

    fake = _FakeRequests(
        get=lambda *a, **k: _Resposta([{"id": "abc", "payload": {"descricao": "x", "gravidade": "MÉDIA ⚠️"}}]),
        patch=_patch,
    )
    monkeypatch.setattr(nuvem_supabase, "requests", fake)
    monkeypatch.setattr(nuvem_supabase, "_base_url", lambda: "http://api")
    monkeypatch.setattr(nuvem_supabase, "_headers", lambda: {})
    monkeypatch.setattr(nuvem_supabase, "_TABELA_PADRAO", "triagens")

    assert avaliacao.registrar("abc", "MÉDIA", "cliente sem acesso", "qa@x.com") is True
    aval = gravado["payload"]["avaliacao"]
    assert aval["rotulo"] == "MÉDIA"
    assert aval["comentario"] == "cliente sem acesso"
    assert aval["autor"] == "qa@x.com"
    assert aval["em"].startswith("20")  # timestamp ISO
    # o resto do payload é preservado (não pode perder nada da triagem)
    assert gravado["payload"]["descricao"] == "x"


def test_registrar_normaliza_ia_4_niveis(monkeypatch):
    gravado = {}
    fake = _FakeRequests(
        get=lambda *a, **k: _Resposta([{"id": "abc", "payload": {}}]),
        patch=lambda *a, **k: (gravado.update(k["json"]), _Resposta([{"id": "x"}]))[1],
    )
    monkeypatch.setattr(nuvem_supabase, "requests", fake)
    monkeypatch.setattr(nuvem_supabase, "_base_url", lambda: "http://api")
    monkeypatch.setattr(nuvem_supabase, "_headers", lambda: {})
    monkeypatch.setattr(nuvem_supabase, "_TABELA_PADRAO", "triagens")

    assert avaliacao.registrar("abc", "ALTA 🚨") is True
    assert gravado["payload"]["avaliacao"]["rotulo"] == "CRÍTICA"


def test_registrar_rejeita_rotulo_invalido_sem_chamar_rede(monkeypatch):
    def _get(*a, **k):
        raise AssertionError("não deveria chamar a rede")

    monkeypatch.setattr(nuvem_supabase, "requests", _FakeRequests(get=_get))
    assert avaliacao.registrar("abc", "sei lá") is False
    assert avaliacao.registrar("", "CRÍTICA") is False


def test_registrar_triagem_inexistente_retorna_false(monkeypatch):
    fake = _FakeRequests(get=lambda *a, **k: _Resposta([]))
    monkeypatch.setattr(nuvem_supabase, "requests", fake)
    monkeypatch.setattr(nuvem_supabase, "_base_url", lambda: "http://api")
    monkeypatch.setattr(nuvem_supabase, "_headers", lambda: {})
    monkeypatch.setattr(nuvem_supabase, "_TABELA_PADRAO", "triagens")
    assert avaliacao.registrar("nao-existe", "CRÍTICA") is False


def test_registrar_falha_de_rede_nao_levanta(monkeypatch):
    def _boom(*a, **k):
        raise OSError("sem rede")

    monkeypatch.setattr(nuvem_supabase, "requests", _FakeRequests(get=_boom))
    monkeypatch.setattr(nuvem_supabase, "_base_url", lambda: "http://api")
    monkeypatch.setattr(nuvem_supabase, "_headers", lambda: {})
    monkeypatch.setattr(nuvem_supabase, "_TABELA_PADRAO", "triagens")
    assert avaliacao.registrar("abc", "CRÍTICA") is False


# --- estado_de: rótulo + prioridade mostrada ----------------------------------
def test_estado_de_trai_prioridade_persistida(monkeypatch):
    monkeypatch.setattr(nuvem_supabase, "requests", _FakeRequests(
        get=lambda *a, **k: _Resposta([{"payload": {
            "prioridade_final": "ALTA 🚨",
            "avaliacao": {"rotulo": "CRÍTICA", "comentario": "ok", "em": "2026-09-27T00:00:00+00:00"},
        }}])))
    monkeypatch.setattr(nuvem_supabase, "_base_url", lambda: "http://api")
    monkeypatch.setattr(nuvem_supabase, "_headers", lambda: {})
    monkeypatch.setattr(nuvem_supabase, "_TABELA_PADRAO", "triagens")

    e = avaliacao.estado_de("abc")
    assert e["rotulo"] == "CRÍTICA"
    assert e["prioridade"] == "CRÍTICA"  # ALTA normalizado
    assert avaliacao.estado_de("") == {"rotulo": "", "comentario": "", "em": "", "prioridade": ""}


def test_estado_de_sem_payload_ainda_tem_prioridade(monkeypatch):
    monkeypatch.setattr(nuvem_supabase, "requests", _FakeRequests(
        get=lambda *a, **k: _Resposta([{"payload": {"gravidade": "MÉDIA ⚠️"}}])))
    monkeypatch.setattr(nuvem_supabase, "_base_url", lambda: "http://api")
    monkeypatch.setattr(nuvem_supabase, "_headers", lambda: {})
    monkeypatch.setattr(nuvem_supabase, "_TABELA_PADRAO", "triagens")

    e = avaliacao.estado_de("abc")
    assert e["rotulo"] == ""
    assert e["prioridade"] == "MÉDIA"


# --- carregar_rotulados / progresso -------------------------------------------
def test_filtro_de_rotulado_ocorre_no_servidor(monkeypatch):
    """Trava o filtro no servidor: sem ele, a base varreria todas as triagens."""
    fake = _FakeRequests(get=lambda *a, **k: _Resposta([]))
    monkeypatch.setattr(nuvem_supabase, "requests", fake)
    monkeypatch.setattr(nuvem_supabase, "_base_url", lambda: "http://api")
    monkeypatch.setattr(nuvem_supabase, "_headers", lambda: {})
    monkeypatch.setattr(nuvem_supabase, "_TABELA_PADRAO", "triagens")

    avaliacao.carregar_rotulados()
    params = fake.chamadas[0][2]
    assert params.get("payload->avaliacao->>rotulo") == "not.is.null"
    assert params.get("order") == "data_hora.desc"


def test_carregar_rotulados_pula_quem_nao_tem_texto(monkeypatch):
    linhas = [
        {"id": "1", "data_hora": "2026-09-27T00:00:00Z", "payload": {
            "descricao": "app travou", "gravidade": "MÉDIA ⚠️",
            "avaliacao": {"rotulo": "CRÍTICA", "comentario": "", "em": "x"}}},
        {"id": "2", "data_hora": "2026-09-27T00:00:00Z", "payload": {
            "descricao": "  ", "gravidade": "NORMAL ✅", "avaliacao": {"rotulo": "NORMAL"}}},
    ]
    monkeypatch.setattr(nuvem_supabase, "requests", _FakeRequests(get=lambda *a, **k: _Resposta(linhas)))
    monkeypatch.setattr(nuvem_supabase, "_base_url", lambda: "http://api")
    monkeypatch.setattr(nuvem_supabase, "_headers", lambda: {})
    monkeypatch.setattr(nuvem_supabase, "_TABELA_PADRAO", "triagens")

    out = avaliacao.carregar_rotulados()
    assert len(out) == 1
    assert out[0]["rotulo"] == "CRÍTICA"
    assert out[0]["descricao"] == "app travou"
    assert out[0]["gravidade"] == "MÉDIA"  # o que o motor tinha acertado


def test_progresso_conta(monkeypatch):
    respostas = [
        _Resposta([{"id": str(i)} for i in range(9)]),  # total
        _Resposta([{"id": "1", "data_hora": "", "payload": {"descricao": "a", "avaliacao": {"rotulo": "MÉDIA"}}},
                   {"id": "2", "data_hora": "", "payload": {"descricao": "b", "avaliacao": {"rotulo": "zzz"}}}]),
    ]
    fake = _FakeRequests(get=lambda *a, **k: respostas.pop(0))
    monkeypatch.setattr(nuvem_supabase, "requests", fake)
    monkeypatch.setattr(nuvem_supabase, "_base_url", lambda: "http://api")
    monkeypatch.setattr(nuvem_supabase, "_headers", lambda: {})
    monkeypatch.setattr(nuvem_supabase, "_TABELA_PADRAO", "triagens")

    p = avaliacao.progresso()
    assert p["total"] == 9
    assert p["rotuladas"] == 1  # só o rótulo canônico conta
    assert p["pendentes"] == 8
    assert p["erro"] is False


def test_progresso_e_carregar_nao_quebram_sem_nuvem(monkeypatch):
    def _boom(*a, **k):
        raise OSError("sem rede")

    monkeypatch.setattr(nuvem_supabase, "requests", _FakeRequests(get=_boom))
    monkeypatch.setattr(nuvem_supabase, "_base_url", lambda: "http://api")
    monkeypatch.setattr(nuvem_supabase, "_headers", lambda: {})
    monkeypatch.setattr(nuvem_supabase, "_TABELA_PADRAO", "triagens")

    assert avaliacao.carregar_rotulados() == []
    assert avaliacao.progresso()["erro"] is True
    assert avaliacao.estado_de("abc")["rotulo"] == ""
