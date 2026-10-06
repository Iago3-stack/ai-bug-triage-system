# Testes unitários do validador anti-SSRF (url_segura.py)
# Roda com: pytest -v
# Confirma: nenhum destino interno passa; o loopback do modelo local (Ollama)
# só entra com ALLOW_LOCAL_MODELS=1, e a flag NÃO abre privado/metadata.

import socket

import url_segura


def _resolver_fake(host, porta, proto=socket.IPPROTO_TCP, ips=("1.2.3.4",)):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, porta)) for ip in ips]


# --- Base: url_segura sem exceção (webhooks) ---
def test_url_segura_aceita_url_publica(monkeypatch):
    monkeypatch.setattr(url_segura, "_resolver",
                        lambda h, p, proto=socket.IPPROTO_TCP: _resolver_fake(h, p))
    assert url_segura.url_segura("https://discord.com/api/webhooks/abc") is True


def test_url_segura_bloqueia_metadata_aws(monkeypatch):
    monkeypatch.setattr(url_segura, "_resolver",
                        lambda h, p, proto=socket.IPPROTO_TCP: _resolver_fake(h, p, ips=("169.254.169.254",)))
    assert url_segura.url_segura("http://169.254.169.254/latest/meta-data") is False


def test_url_segura_bloqueia_ip_privado(monkeypatch):
    monkeypatch.setattr(url_segura, "_resolver",
                        lambda h, p, proto=socket.IPPROTO_TCP: _resolver_fake(h, p, ips=("192.168.0.10",)))
    assert url_segura.url_segura("http://192.168.0.10/hook") is False


def test_url_segura_bloqueia_localhost(monkeypatch):
    monkeypatch.setattr(url_segura, "_resolver",
                        lambda h, p, proto=socket.IPPROTO_TCP: _resolver_fake(h, p, ips=("127.0.0.1",)))
    assert url_segura.url_segura("http://localhost:3000/hook") is False


def test_url_segura_bloqueia_esquema_nao_http():
    assert url_segura.url_segura("file:///etc/passwd") is False
    assert url_segura.url_segura("ftp://discord.com/x") is False
    assert url_segura.url_segura("localhost:11434/v1") is False


def test_url_segura_bloqueia_url_vazia_e_dns_invalido(monkeypatch):
    assert url_segura.url_segura("") is False
    assert url_segura.url_segura(None) is False
    monkeypatch.setattr(url_segura, "_resolver",
                        lambda h, p, proto=socket.IPPROTO_TCP: (_ for _ in ()).throw(
                            socket.gaierror("nxdomain")))
    assert url_segura.url_segura("https://nao-existe.invalid/x") is False


def test_url_segura_com_loopback_explícito_passa(monkeypatch):
    """Só o parâmetro explícito (uso do próprio validador) deixa loopback."""
    monkeypatch.setattr(url_segura, "_resolver",
                        lambda h, p, proto=socket.IPPROTO_TCP: _resolver_fake(h, p, ips=("127.0.0.1",)))
    assert url_segura.url_segura("http://localhost:11434/v1", permitir_loopback=True) is True


# --- url_modelo_segura: flag ALLOW_LOCAL_MODELS decide o loopback ---
def test_flag_default_e_negar(monkeypatch):
    monkeypatch.delenv("ALLOW_LOCAL_MODELS", raising=False)
    assert url_segura.loopback_de_modelo_permitido() is False


def test_flag_só_com_1(monkeypatch):
    monkeypatch.setenv("ALLOW_LOCAL_MODELS", "1")
    assert url_segura.loopback_de_modelo_permitido() is True
    monkeypatch.setenv("ALLOW_LOCAL_MODELS", "0")
    assert url_segura.loopback_de_modelo_permitido() is False


def test_url_modelo_bloqueia_localhost_sem_flag(monkeypatch):
    monkeypatch.delenv("ALLOW_LOCAL_MODELS", raising=False)
    monkeypatch.setattr(url_segura, "_resolver",
                        lambda h, p, proto=socket.IPPROTO_TCP: _resolver_fake(h, p, ips=("127.0.0.1",)))
    assert url_segura.url_modelo_segura("http://localhost:11434/v1") is False


def test_url_modelo_permite_localhost_com_flag(monkeypatch):
    monkeypatch.setenv("ALLOW_LOCAL_MODELS", "1")
    monkeypatch.setattr(url_segura, "_resolver",
                        lambda h, p, proto=socket.IPPROTO_TCP: _resolver_fake(h, p, ips=("127.0.0.1",)))
    assert url_segura.url_modelo_segura("http://localhost:11434/v1") is True


def test_flag_nao_abre_ip_privado(monkeypatch):
    """A flag relaxa SÓ loopback: rede privada continua bloqueada com ela ligada."""
    monkeypatch.setenv("ALLOW_LOCAL_MODELS", "1")
    monkeypatch.setattr(url_segura, "_resolver",
                        lambda h, p, proto=socket.IPPROTO_TCP: _resolver_fake(h, p, ips=("192.168.1.10",)))
    assert url_segura.url_modelo_segura("http://meu-servidor.local/hook") is False


def test_flag_nao_abre_metadata(monkeypatch):
    monkeypatch.setenv("ALLOW_LOCAL_MODELS", "1")
    monkeypatch.setattr(url_segura, "_resolver",
                        lambda h, p, proto=socket.IPPROTO_TCP: _resolver_fake(h, p, ips=("169.254.169.254",)))
    assert url_segura.url_modelo_segura("http://169.254.169.254/latest/meta-data") is False


def test_url_modelo_aceita_provedor_publico(monkeypatch):
    monkeypatch.delenv("ALLOW_LOCAL_MODELS", raising=False)
    monkeypatch.setattr(url_segura, "_resolver",
                        lambda h, p, proto=socket.IPPROTO_TCP: _resolver_fake(h, p))
    assert url_segura.url_modelo_segura("https://api.deepseek.com/v1") is True


def test_url_modelo_sem_esquema_bloqueada():
    """Placeholder pede esquema; sem http(s):// não passa (e não é destino interno)."""
    assert url_segura.url_modelo_segura("api.deepseek.com/v1") is False
