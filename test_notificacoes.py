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


# --- E-mail (SMTP mockado, sem rede) ---
class _Correio:
    def __init__(self, host, porta, timeout):
        self.host = host
        self.porta = porta
        self.enviadas = []
        self._voltou = False

    def starttls(self):
        self._voltou = True

    def login(self, user, senha):
        self.credenciais = (user, senha)
        return None

    def send_message(self, msg):
        self.enviadas.append(msg)
        return None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _sem_canal(monkeypatch):
    monkeypatch.setattr(notificacoes, "_ler", lambda nome: "")


def test_email_nao_alerta_prioridade_normal_sem_config():
    assert notificacoes.notificar_email("NORMAL ✅", "resumo") is False


def test_email_nao_dispara_sem_configuracao(monkeypatch):
    monkeypatch.setattr(notificacoes, "_ler", lambda nome: "")
    assert notificacoes.notificar_email("CRÍTICA 🚨", "resumo") is False


def test_email_envia_critico(monkeypatch):
    def _ler(nome):
        return {
            "ALERTA_EMAIL_TO": "qa@empresa.com",
            "SMTP_USER": "app@email.com",
            "SMTP_PASS": "app-1234",
        }.get(nome, "")

    monkeypatch.setattr(notificacoes, "_ler", _ler)
    correio = _Correio("x", 0, 0)
    monkeypatch.setattr(notificacoes.smtplib, "SMTP", lambda host, porta, timeout: correio)
    assert notificacoes.notificar_email("CRÍTICA 🚨", "bug fatal no pagamento") is True
    assert correio.credenciais == ("app@email.com", "app-1234")
    assert "bug fatal no pagamento" in correio.enviadas[0].get_body().get_content()
    assert correio.enviadas[0]["To"] == "qa@empresa.com"


def test_email_aceita_smtp_custom_secrets(monkeypatch):
    def _ler(nome):
        cfg = {
            "ALERTA_EMAIL_TO": "qa@empresa.com",
            "SMTP_USER": "u",
            "SMTP_PASS": "p",
            "SMTP_HOST": "mail.empresa.com",
            "SMTP_PORT": "465",
        }
        return cfg.get(nome, "")

    monkeypatch.setattr(notificacoes, "_ler", _ler)
    captura = []

    def _fake_smtp(host, porta, timeout):
        correio = _Correio(host, porta, timeout)
        captura.append(correio)
        return correio

    monkeypatch.setattr(notificacoes.smtplib, "SMTP", _fake_smtp)
    assert notificacoes.notificar_email("ALTA 🚨", "falha no checkout") is True
    assert captura[0].host == "mail.empresa.com"
    assert captura[0].porta == 465


def test_falha_smtp_nao_levanta(monkeypatch):
    def _ler(nome):
        return {
            "ALERTA_EMAIL_TO": "qa@empresa.com",
            "SMTP_USER": "u",
            "SMTP_PASS": "p",
        }.get(nome, "")

    monkeypatch.setattr(notificacoes, "_ler", _ler)
    correio = _Correio(None, None, None)
    correio.login = lambda user, senha: (_ for _ in ()).throw(PermissionError("senha errada"))
    monkeypatch.setattr(notificacoes.smtplib, "SMTP", lambda h, po, t: correio)
    assert notificacoes.notificar_email("CRÍTICA 🚨", "resumo") is False


# --- Detecção de canal configurado (mostra o status no app) ---
def test_email_configurado_detecta_quando_tem_tudo(monkeypatch):
    def _ler(nome):
        return {
            "ALERTA_EMAIL_TO": "qa@empresa.com",
            "SMTP_USER": "u",
            "SMTP_PASS": "p",
        }.get(nome, "")

    monkeypatch.setattr(notificacoes, "_ler", _ler)
    assert notificacoes.email_configurado() is True


def test_email_configurado_falso_sem_destino(monkeypatch):
    monkeypatch.setattr(notificacoes, "_ler", lambda nome: "")
    assert notificacoes.email_configurado() is False


def test_discord_configurado_reflete_webhook(monkeypatch):
    monkeypatch.setattr(notificacoes, "_ler", lambda nome: "" if nome == "DISCORD_WEBHOOK" else "x")
    assert notificacoes.discord_configurado() is False
    monkeypatch.setattr(notificacoes, "_ler", lambda nome: "https://discord/x")
    assert notificacoes.discord_configurado() is True