import json

import auth_supabase
from auth_supabase import _mensagem_erro, _valida_email_senha


class _Resp:
    def __init__(self, status_code=200, dados=None, text=None):
        self.status_code = status_code
        self._dados = dados or {}
        self.text = text or json.dumps(self._dados)

    def json(self):
        return self._dados


# ── Validação de entrada ──────────────────────────────────────────────────────

def test_valida_rejeita_email_sem_arroba():
    ok, msg = _valida_email_senha("joaoempresa.com", "12345678")
    assert not ok
    assert "e-mail" in msg.lower()


def test_valida_rejeita_senha_curta():
    ok, msg = _valida_email_senha("joao@e.com", "123")
    assert not ok
    assert "8" in msg


def test_valida_aceita_dados_corretos():
    ok, _ = _valida_email_senha("joao@empresa.com", "12345678")
    assert ok


# ── Mensagens de erro ─────────────────────────────────────────────────────────

def test_mensagem_email_nao_confirmed():
    texto = json.dumps({"error": "email_not_confirmed", "error_description": "Email not confirmed"})
    assert "confirme" in _mensagem_erro(400, texto).lower()


def test_mensagem_429_signups_desativados():
    texto = json.dumps({"code": 429, "error_code": "over_request_rate_limit", "msg": "Email signups are disabled for this project"})
    msg = _mensagem_erro(429, texto)
    assert "email signups" in msg.lower()


def test_mensagem_429_rate_limit():
    texto = json.dumps({"code": 429, "error_code": "over_request_rate_limit", "msg": "Too many requests"})
    assert "aguarde" in _mensagem_erro(429, texto).lower()


def test_mensagem_429_email_send_rate_limit():
    texto = json.dumps({"code": 429, "error_code": "over_email_send_rate_limit", "msg": "email rate limit exceeded"})
    msg = _mensagem_erro(429, texto)
    assert "limite" in msg.lower()
    assert "smtp" in msg.lower()


def test_mensagem_invalid_grant():
    texto = json.dumps({"error": "invalid_grant", "error_description": "Invalid login credentials"})
    assert "inválidos" in _mensagem_erro(400, texto)


def test_mensagem_422_ja_cadastrado():
    assert "já" in _mensagem_erro(422, '{"error":"already registered"}').lower()


# ── Cadastro ──────────────────────────────────────────────────────────────────

def test_cadastrar_ok_confirma(monkeypatch):
    monkeypatch.setattr(auth_supabase, "_config", lambda: ("https://x.supabase.co", "key"))
    user = {"id": "u1", "email": "a@b.com", "confirmed_at": None}
    monkeypatch.setattr(auth_supabase.requests, "post", lambda *a, **k: _Resp(201, {"user": user}))
    ok, msg, dados = auth_supabase.cadastrar("a@b.com", "senhaforte123")
    assert ok and "confirme" in msg.lower()
    assert dados["user"]["id"] == "u1"


def test_cadastrar_ok_confirmado(monkeypatch):
    monkeypatch.setattr(auth_supabase, "_config", lambda: ("https://x.supabase.co", "key"))
    user = {"id": "u1", "email": "a@b.com", "confirmed_at": "2026-01-01T00:00:00Z"}
    monkeypatch.setattr(auth_supabase.requests, "post", lambda *a, **k: _Resp(201, {"user": user}))
    ok, msg, dados = auth_supabase.cadastrar("a@b.com", "senhaforte123")
    assert ok
    assert "criada" in msg.lower()
    assert dados["user"]["confirmed_at"]


def test_cadastrar_email_ja_existe(monkeypatch):
    monkeypatch.setattr(auth_supabase, "_config", lambda: ("https://x.supabase.co", "key"))
    monkeypatch.setattr(auth_supabase.requests, "post", lambda *a, **k: _Resp(422, {"error": "already registered"}))
    ok, msg, _ = auth_supabase.cadastrar("a@b.com", "senhaforte123")
    assert not ok and "já" in msg.lower()


def test_cadastrar_sem_credenciais(monkeypatch):
    monkeypatch.setattr(auth_supabase, "_config", lambda: None)
    ok, msg, _ = auth_supabase.cadastrar("a@b.com", "senhaforte123")
    assert not ok
    assert "supabase" in msg.lower()


# ── Login ─────────────────────────────────────────────────────────────────────

def test_logar_ok(monkeypatch):
    monkeypatch.setattr(auth_supabase, "_config", lambda: ("https://x.supabase.co", "key"))
    resp = _Resp(200, {"access_token": "tok1", "refresh_token": "r1", "user": {"email": "a@b.com"}})
    monkeypatch.setattr(auth_supabase.requests, "post", lambda *a, **k: resp)
    ok, msg, dados = auth_supabase.logar("a@b.com", "senhaforte123")
    assert ok and dados["access_token"] == "tok1"


def test_logar_credenciais_invalidas(monkeypatch):
    monkeypatch.setattr(auth_supabase, "_config", lambda: ("https://x.supabase.co", "key"))
    resp = _Resp(400, {"error": "invalid_grant", "error_description": "Invalid login credentials"})
    monkeypatch.setattr(auth_supabase.requests, "post", lambda *a, **k: resp)
    ok, msg, _ = auth_supabase.logar("a@b.com", "errada")
    assert not ok
    assert "inválidos" in msg.lower()


def test_logar_email_nao_confirmed(monkeypatch):
    monkeypatch.setattr(auth_supabase, "_config", lambda: ("https://x.supabase.co", "key"))
    resp = _Resp(400, {"error": "email_not_confirmed", "error_description": "Email not confirmed"})
    monkeypatch.setattr(auth_supabase.requests, "post", lambda *a, **k: resp)
    ok, msg, _ = auth_supabase.logar("a@b.com", "senhaforte123")
    assert not ok
    assert "confirme" in msg.lower()


def test_logar_campos_vazios():
    ok, msg, _ = auth_supabase.logar("", "")
    assert not ok


# ── Sessão ────────────────────────────────────────────────────────────────────

def test_sessao_guarda_e_limpa(monkeypatch):
    fake = {}
    monkeypatch.setattr(auth_supabase, "_armazem", lambda: fake)
    assert auth_supabase.usuario_logado() is None

    dados = {"access_token": "t1", "user": {"email": "u@e.com"}}
    auth_supabase.guardar_sessao(dados)
    assert auth_supabase.usuario_logado() == "u@e.com"

    auth_supabase.limpar_sessao()
    assert auth_supabase.usuario_logado() is None


def test_sair_limpa_sessao(monkeypatch):
    fake = {"_auth_sessao": {"access_token": "t1", "user": {"email": "u@e.com"}}}
    monkeypatch.setattr(auth_supabase, "_armazem", lambda: fake)
    monkeypatch.setattr(auth_supabase, "_config", lambda: ("https://x.supabase.co", "key"))
    chamou = []

    def _logout(*a, **k):
        chamou.append(True)
        return _Resp(204)

    monkeypatch.setattr(auth_supabase, "_base_auth_url", lambda: "https://x/auth/v1")
    monkeypatch.setattr(auth_supabase.requests, "post", _logout)
    auth_supabase.sair("t1")
    assert chamou  # logout chamado
    assert "_auth_sessao" not in fake


def test_sair_da_conta_usa_sessao_logada(monkeypatch):
    fake = {"_auth_sessao": {"access_token": "t1", "user": {"email": "u@e.com"}}}
    monkeypatch.setattr(auth_supabase, "_armazem", lambda: fake)
    monkeypatch.setattr(auth_supabase, "_config", lambda: ("https://x.supabase.co", "key"))
    chamou = []

    def _logout(*a, **k):
        chamou.append(a)
        return _Resp(204)

    monkeypatch.setattr(auth_supabase, "_base_auth_url", lambda: "https://x/auth/v1")
    monkeypatch.setattr(auth_supabase.requests, "post", _logout)
    auth_supabase.sair_da_conta()
    assert chamou  # logout chamado
    assert "_auth_sessao" not in fake


def test_disponivel_true_e_false(monkeypatch):
    monkeypatch.setattr(auth_supabase, "_config", lambda: ("https://x", "k"))
    assert auth_supabase.disponivel()
    monkeypatch.setattr(auth_supabase, "_config", lambda: None)
    assert not auth_supabase.disponivel()


# ── OAuth (Google/GitHub) ─────────────────────────────────────────────────

def test_url_autorizacao_monta_url(monkeypatch):
    monkeypatch.setattr(auth_supabase, "_config", lambda: ("https://x.supabase.co", "k"))
    url = auth_supabase.url_autorizacao("google", "https://app.streamlit.app")
    assert url.startswith("https://x.supabase.co/auth/v1/authorize?")
    assert "provider=google" in url
    assert "redirect_to=https%3A%2F%2Fapp.streamlit.app" in url


def test_providers_habilitados_retorna_external(monkeypatch):
    monkeypatch.setattr(auth_supabase, "_config", lambda: ("https://x.supabase.co", "k"))
    monkeypatch.setattr(
        auth_supabase.requests, "get",
        lambda *a, **k: _Resp(200, {"external": {"google": True, "github": False}}),
    )
    assert auth_supabase.providers_habilitados() == {"google": True, "github": False}


def test_providers_habilitados_sem_credenciais(monkeypatch):
    monkeypatch.setattr(auth_supabase, "_config", lambda: None)
    assert auth_supabase.providers_habilitados() == {}


def test_sessao_oauth_enriquece_com_user(monkeypatch):
    monkeypatch.setattr(auth_supabase, "_config", lambda: ("https://x.supabase.co", "k"))
    monkeypatch.setattr(
        auth_supabase.requests, "get",
        lambda *a, **k: _Resp(200, {"id": "u1", "email": "u@e.com"}),
    )
    dados = {"access_token": "tok1", "refresh_token": "r1"}
    sessao = auth_supabase.sessao_oauth(dados)
    assert sessao["user"]["email"] == "u@e.com"
    monkeypatch.setattr(
        auth_supabase.requests, "get",
        lambda *a, **k: _Resp(400, {}),
    )
    assert auth_supabase.sessao_oauth(dados) is None


def test_sessao_oauth_sem_token():
    assert auth_supabase.sessao_oauth({}) is None
