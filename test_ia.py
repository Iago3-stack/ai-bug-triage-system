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


def test_disponivel_true_com_modelo_proprio(monkeypatch):
    _sem_chaves(monkeypatch)
    assert ia.disponivel() is False
    assert ia.disponivel([{"nome": "Meu GPT-4o"}]) is True


def test_openai_compat_sucesso_parseia_json(monkeypatch):
    _sem_chaves(monkeypatch)
    chamadas = {}

    def _fake_post(url, headers=None, json=None, timeout=None):
        chamadas["url"] = url
        chamadas["json"] = json
        chamadas["headers"] = headers
        conteudo = '{"severidade": "alta", "categoria": "funcionalidade", ' \
                   '"causa_raiz": "timeout no login", "passos_repro": ["1"], ' \
                   '"resumo_tecnico": "login lento"}'
        return _FakeResposta(
            {"choices": [{"message": {"content": conteudo}}]}, status_code=200
        )

    monkeypatch.setattr(ia.requests, "post", _fake_post)
    config = {"tipo": "openai", "base_url": "https://api.openai.com/v1",
              "chave": "sk-test", "modelo": "gpt-4o", "rotulo": "Meu GPT-4o"}
    dados, erro = ia._chamar_openai_compat("app demora no login", config)
    assert erro is None
    assert dados["severidade"] == "alta"
    assert chamadas["url"] == "https://api.openai.com/v1/chat/completions"
    assert chamadas["json"]["model"] == "gpt-4o"
    assert chamadas["json"]["response_format"] == {"type": "json_object"}
    assert chamadas["headers"]["Authorization"] == "Bearer sk-test"
    assert ia.ULTIMO_PROVEDOR == "Meu GPT-4o"
    assert ia.ULTIMO_MODELO == "gpt-4o"


def test_openai_compat_sem_json_mode_quando_servidor_rejeita(monkeypatch):
    _sem_chaves(monkeypatch)
    chamadas = []
    conteudo = '{"severidade": "media", "categoria": "outro", "causa_raiz": "x", ' \
               '"passos_repro": [], "resumo_tecnico": "y"}'

    def _fake_post(url, headers=None, json=None, timeout=None):
        chamadas.append(json)
        if len(chamadas) == 1:
            return _FakeResposta({}, status_code=400, texto="response_format not supported")
        return _FakeResposta(
            {"choices": [{"message": {"content": conteudo}}]}, status_code=200
        )

    monkeypatch.setattr(ia.requests, "post", _fake_post)
    config = {"tipo": "openai", "base_url": "https://api.deepseek.com/v1",
              "chave": "dk", "modelo": "deepseek-chat", "rotulo": "DeepSeek"}
    dados, erro = ia._chamar_openai_compat("relato", config)
    assert erro is None
    assert dados["severidade"] == "media"
    assert len(chamadas) == 2
    assert "response_format" in chamadas[0]
    assert "response_format" not in chamadas[1]


def test_openai_compat_config_incompleta(monkeypatch):
    _sem_chaves(monkeypatch)
    dados, erro = ia._chamar_openai_compat(
        "relato", {"tipo": "openai", "base_url": "", "chave": "", "modelo": ""}
    )
    assert dados is None
    assert "incompleta" in erro


def test_dispatcher_dict_gemini_chama_modelo_especifico(monkeypatch):
    _sem_chaves(monkeypatch)
    chamado = {}

    def _fake_gemini(conteudo, temperatura=0.2, max_output_tokens=1024,
                     modelos=None, chave=None):
        chamado["modelos"] = modelos
        chamado["chave"] = chave
        return {"severidade": "critica", "ok": "gemini-custom"}, None

    monkeypatch.setattr(ia, "_chamar_gemini", _fake_gemini)
    config = {"tipo": "gemini", "nome": "Gemini Pro pago",
              "modelo": "gemini-3-pro", "chave": "chave-pro", "rotulo": "Gemini Pro pago"}
    dados, erro = ia._chamar_llm("relato", provedor=config)
    assert erro is None
    assert chamado["modelos"] == ["gemini-3-pro"]
    assert chamado["chave"] == "chave-pro"
    assert dados["ok"] == "gemini-custom"
    assert ia.ULTIMO_PROVEDOR == "Gemini Pro pago"


def test_dispatcher_dict_openai_nao_tenta_gemini_groq(monkeypatch):
    _sem_chaves(monkeypatch)

    def _fake_post(url, headers=None, json=None, timeout=None):
        conteudo = '{"severidade": "baixa", "categoria": "design", "causa_raiz": "c", ' \
                   '"passos_repro": [], "resumo_tecnico": "r"}'
        return _FakeResposta(
            {"choices": [{"message": {"content": conteudo}}]}, status_code=200
        )

    monkeypatch.setattr(ia.requests, "post", _fake_post)
    monkeypatch.setattr(ia, "_chamar_gemini",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("não deveria")))
    monkeypatch.setattr(ia, "_chamar_groq",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("não deveria")))
    config = {"tipo": "openai", "base_url": "https://x/v1", "chave": "k",
              "modelo": "m", "rotulo": "X"}
    dados, erro = ia._chamar_llm("relato", provedor=config)
    assert erro is None
    assert dados["severidade"] == "baixa"