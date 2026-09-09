# Testes unitários das notificações (notificacoes.py)
# Roda com: pytest -v
# Confirma: só alerta CRÍTICA/ALTA, webhook ausente é no-op, falha de rede não derruba.

import notificacoes


# --- Critério de disparo ---
def test_nao_alerta_prioridade_normal():
    assert notificacoes.notificar_discord("NORMAL ✅", "resumo") is False


def test_nao_alerta_prioridade_media():
    assert notificacoes.notificar_discord("MÉDIA ⚠️", "resumo") is False


def test_alerta_critico_sem_webhook_fica_silencioso():
    assert notificacoes.notificar_discord("CRÍTICA 🚨", "resumo") is False


def test_alerta_vazio_nao_dispara():
    assert notificacoes.notificar_discord("", "resumo") is False


# --- Envio efetivo (webhook mockado, sem rede) ---
class _Resp:
    status = 204

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _mock_urlopen(monkeypatch, captura=None):
    def _abre(req, timeout):
        if captura is not None:
            captura.append(req)
        return _Resp()

    monkeypatch.setattr("urllib.request.urlopen", _abre)


def test_envia_alerta_critico(monkeypatch):
    monkeypatch.setattr(notificacoes, "webhook_discord", lambda: "https://discord.com/err")
    capturados = []
    _mock_urlopen(monkeypatch, capturados)
    assert notificacoes.notificar_discord("CRÍTICA 🚨", "bug fatal no login") is True
    corpo = capturados[0].data.decode()
    assert "bug fatal no login" in corpo
    assert "Triagem CRÍTICA 🚨" in corpo


def test_envia_alerta_alta(monkeypatch):
    monkeypatch.setattr(notificacoes, "webhook_discord", lambda: "https://discord.com/err")
    _mock_urlopen(monkeypatch)
    assert notificacoes.notificar_discord("ALTA 🚨", "falha no checkout") is True


def test_falha_de_rede_nao_levanta(monkeypatch):
    monkeypatch.setattr(notificacoes, "webhook_discord", lambda: "https://discord.com/err")

    def _boom(req, timeout):
        raise TimeoutError("sem net")

    monkeypatch.setattr("urllib.request.urlopen", _boom)
    assert notificacoes.notificar_discord("CRÍTICA 🚨", "resumo") is False


# --- Leitura do webhook (env → .env → secrets) ---
def test_webhook_le_da_variavel_de_ambiente(monkeypatch):
    monkeypatch.setattr("os.getenv", lambda nome, padrao="": "https://env/x")
    monkeypatch.setattr(notificacoes, "_ler_env", lambda nome: "")
    assert notificacoes.webhook_discord() == "https://env/x"


def test_webhook_cai_no_env_quando_falta_variavel(monkeypatch):
    monkeypatch.setattr("os.getenv", lambda nome, padrao="": "")
    monkeypatch.setattr(notificacoes, "_ler_env", lambda nome: "https://env-file/x")
    assert notificacoes.webhook_discord() == "https://env-file/x"