# Testes unitários da camada de IA (ia.py) — Gemini com fallback Groq.
# Roda com: pytest -v
# 100% offline: chaves, HTTP e dispatcher são mockados — nunca sai da máquina.

import ia


class _FakeResposta:
    def __init__(self, payload=None, status_code=200, texto=""):
        self._payload = payload if payload is not None else {}
        self.status_code = status_code
        self.text = texto

    def json(self):
        return self._payload


def _sem_chaves(monkeypatch):
    monkeypatch.setattr(ia, "_chave", lambda nome: None)


def test_groq_sem_chave_retorna_erro(monkeypatch):
    _sem_chaves(monkeypatch)
    dados, erro = ia._chamar_groq("relato qualquer")
    assert dados is None
    assert "GROQ_API_KEY" in erro


def test_groq_sucesso_parseia_json(monkeypatch):
    _sem_chaves(monkeypatch)
    monkeypatch.setattr(ia, "_chave", lambda nome: "gsk_teste")
    chamadas = {}

    def _fake_post(url, headers=None, json=None, timeout=None):
        chamadas["url"] = url
        chamadas["json"] = json
        conteudo = '{"severidade": "critica", "categoria": "funcionalidade", ' \
                   '"causa_raiz": "exceção no login", "passos_repro": ["1", "2"], ' \
                   '"resumo_tecnico": "crash"}'
        return _FakeResposta(
            {"choices": [{"message": {"content": conteudo}}]}, status_code=200
        )

    monkeypatch.setattr(ia.requests, "post", _fake_post)
    dados, erro = ia._chamar_groq("app crasha no login")
    assert erro is None
    assert dados["severidade"] == "critica"
    assert dados["categoria"] == "funcionalidade"
    assert "chat/completions" in chamadas["url"]
    corpo = chamadas["json"]
    assert corpo["response_format"] == {"type": "json_object"}
    assert corpo["model"] == ia.GROQ_MODELO_PADRAO


def test_groq_http_429_retorna_mensagem(monkeypatch):
    _sem_chaves(monkeypatch)
    monkeypatch.setattr(ia, "_chave", lambda nome: "gsk_teste")

    def _fake_post(url, headers=None, json=None, timeout=None):
        return _FakeResposta({}, status_code=429, texto="rate limit")

    monkeypatch.setattr(ia.requests, "post", _fake_post)
    dados, erro = ia._chamar_groq("relato")
    assert dados is None
    assert "429" in erro


def test_groq_json_invalido_retorna_erro(monkeypatch):
    _sem_chaves(monkeypatch)
    monkeypatch.setattr(ia, "_chave", lambda nome: "gsk_teste")

    def _fake_post(url, headers=None, json=None, timeout=None):
        return _FakeResposta(
            {"choices": [{"message": {"content": "não sou json"}}]}, status_code=200
        )

    monkeypatch.setattr(ia.requests, "post", _fake_post)
    dados, erro = ia._chamar_groq("relato")
    assert dados is None
    assert erro


def test_dispatcher_gemini_ok_nao_chama_groq(monkeypatch):
    def _fake_gemini(*args, **kwargs):
        return {"severidade": "alta", "ok": "gemini"}, None

    def _fake_groq(*args, **kwargs):
        raise AssertionError("Groq não deveria ser chamado")

    monkeypatch.setattr(ia, "_chamar_gemini", _fake_gemini)
    monkeypatch.setattr(ia, "_chamar_groq", _fake_groq)
    dados, erro = ia._chamar_llm("relato")
    assert dados["ok"] == "gemini"
    assert erro is None


def test_dispatcher_gemini_falha_cai_no_groq(monkeypatch):
    monkeypatch.setattr(ia, "_chamar_gemini", lambda *a, **k: (None, "Gemini 503"))
    groq_ok = ({"severidade": "media", "ok": "groq"}, None)
    monkeypatch.setattr(ia, "_chamar_groq", lambda *a, **k: groq_ok)
    dados, erro = ia._chamar_llm("relato")
    assert dados["ok"] == "groq"
    assert erro is None


def test_dispatcher_ambos_falham_retorna_erro_composto(monkeypatch):
    monkeypatch.setattr(ia, "_chamar_gemini", lambda *a, **k: (None, "Gemini 503"))
    monkeypatch.setattr(ia, "_chamar_groq", lambda *a, **k: (None, "Groq 429"))
    dados, erro = ia._chamar_llm("relato")
    assert dados is None
    assert "Gemini 503" in erro and "Groq 429" in erro


def test_dispatcher_provedor_groq_forcado_nao_tenta_gemini(monkeypatch):
    chamou = []
    monkeypatch.setattr(ia, "_chamar_gemini", lambda *a, **k: chamou.append("gemini") or (None, "503"))
    groq_ok = ({"severidade": "baixa", "ok": "groq"}, None)
    monkeypatch.setattr(ia, "_chamar_groq", lambda *a, **k: groq_ok)
    dados, erro = ia._chamar_llm("relato", provedor="groq")
    assert dados["ok"] == "groq"
    assert not chamou, "Gemini não deveria ser chamado com provedor forçado"


def test_dispatcher_provedor_gemini_forcado_nao_tenta_groq(monkeypatch):
    chamou = []
    gemini_ok = ({"severidade": "media", "ok": "gemini"}, None)
    monkeypatch.setattr(ia, "_chamar_gemini", lambda *a, **k: chamou.append("gemini") or gemini_ok)
    monkeypatch.setattr(ia, "_chamar_groq", lambda *a, **k: chamou.append("groq") or (None, "429"))
    dados, erro = ia._chamar_llm("relato", provedor="gemini")
    assert dados["ok"] == "gemini"
    assert chamou == ["gemini"], "Groq não deveria ser chamado com provedor forçado"


def test_provedor_normalizado_aceita_rotulos_curtos(monkeypatch):
    assert ia._provedor_normalizado(None) is None
    assert ia._provedor_normalizado("auto") is None
    assert ia._provedor_normalizado("gemini") == "gemini"
    assert ia._provedor_normalizado("groq") == "groq"