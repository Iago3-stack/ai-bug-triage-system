# Testes unitários do cliente GitHub (github_client.py)
# Roda com: pytest -v
# Confirma: normalização do repositório, detecção de config e criação via
# api.github.com (com mocks, sem rede real) + mensagens de erro amigáveis.

import json

import urllib.error

import pytest

import github_client


# --- Normalização de 'dono/repo' (aceita URL completa ou com .git) ---
def test_normalizar_repo_url_completa():
    assert github_client.normalizar_repo("https://github.com/empresa/qa-bugs") == "empresa/qa-bugs"


def test_normalizar_repo_aceita_git():
    assert github_client.normalizar_repo("empresa/qa-bugs.git") == "empresa/qa-bugs"


def test_normalizar_repo_aceita_url_com_git():
    assert github_client.normalizar_repo("https://github.com/empresa/qa-bugs.git") == "empresa/qa-bugs"


def test_normalizar_repo_simples():
    assert github_client.normalizar_repo("empresa/qa-bugs") == "empresa/qa-bugs"


def test_normalizar_repo_apenas_slug_sem_barra_fica_intacto():
    assert github_client.normalizar_repo("apenasumrepositorio") == "apenasumrepositorio"


def test_normalizar_repo_vazio():
    assert github_client.normalizar_repo("") == ""


# --- Detecção de configuração ---
def test_configurado_exige_token_e_repo():
    assert github_client.configurado({"repo": "empresa/qa", "token": "github_pat_abc"}) is True


def test_configurado_falso_sem_token():
    assert github_client.configurado({"repo": "empresa/qa", "token": ""}) is False


def test_configurado_falso_sem_repo_valido():
    assert github_client.configurado({"repo": "sem-barra", "token": "github_pat_abc"}) is False


def test_configurado_falso_config_vazia():
    assert github_client.configurado({}) is False


def test_configurado_normaliza_repo_com_url():
    config = {"repo": "https://github.com/empresa/qa", "token": "ghp_abc"}
    assert github_client.configurado(config) is True


# --- Criação de issue (payload via POST em api.github.com, com mock) ---
class _RespostaFake:
    def __init__(self, corpo):
        self._corpo = corpo

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self._corpo


def _mock_urlopen(monkeypatch, codigo=201, corpo=None):
    if corpo is None:
        corpo = json.dumps({"number": 42, "html_url": "https://github.com/empresa/qa/issues/42"}).encode()
    capturado = {}

    def _fake(request, timeout=30):
        capturado["url"] = request.full_url
        capturado["headers"] = dict(request.headers)
        capturado["dados"] = json.loads(request.data.decode("utf-8"))
        if codigo >= 400:
            raise urllib.error.HTTPError(request.full_url, codigo, "erro", None, None)
        return _RespostaFake(corpo)

    monkeypatch.setattr(github_client.urllib.request, "urlopen", _fake)
    return capturado


def test_criar_issue_usa_api_github(monkeypatch):
    capturado = _mock_urlopen(monkeypatch)
    ok, resultado, erro = github_client.criar_issue(
        {"repo": "empresa/qa-bugs", "token": "github_pat_xyz"}, "Titulo", "Corpo"
    )
    assert ok is True
    assert erro is None
    assert resultado["number"] == 42
    assert resultado["html_url"].startswith("https://github.com/")
    assert capturado["url"] == "https://api.github.com/repos/empresa/qa-bugs/issues"
    assert capturado["headers"]["Authorization"] == "Bearer github_pat_xyz"


def test_criar_issue_envia_title_e_body(monkeypatch):
    capturado = _mock_urlopen(monkeypatch)
    github_client.criar_issue({"repo": "empresa/qa-bugs", "token": "ghp_x"}, "Título do bug", "Relatório")
    assert capturado["dados"] == {"title": "Título do bug", "body": "Relatório"}
    assert "labels" not in capturado["dados"]


def test_criar_issue_normaliza_repo_com_url(monkeypatch):
    capturado = _mock_urlopen(monkeypatch)
    github_client.criar_issue({"repo": "https://github.com/empresa/qa.git", "token": "ghp_x"}, "t", "c")
    assert capturado["url"] == "https://api.github.com/repos/empresa/qa/issues"


def test_criar_issue_erro_404(monkeypatch):
    _mock_urlopen(monkeypatch, codigo=404)
    ok, resultado, erro = github_client.criar_issue({"repo": "empresa/qa", "token": "ghp_x"}, "t", "c")
    assert ok is False
    assert "Repositório não encontrado" in erro


def test_criar_issue_erro_401(monkeypatch):
    _mock_urlopen(monkeypatch, codigo=401)
    ok, resultado, erro = github_client.criar_issue({"repo": "empresa/qa", "token": "ghp_x"}, "t", "c")
    assert ok is False
    assert "Issues: write" in erro


def test_criar_issue_erro_422_detalha_http(monkeypatch):
    _mock_urlopen(monkeypatch, codigo=422)
    ok, resultado, erro = github_client.criar_issue({"repo": "empresa/qa", "token": "ghp_x"}, "t", "c")
    assert ok is False
    assert erro.startswith("HTTP 422")


def test_criar_issue_sem_config_nao_tenta_rede():
    ok, resultado, erro = github_client.criar_issue({}, "t", "c")
    assert ok is False
    assert "Configure" in erro