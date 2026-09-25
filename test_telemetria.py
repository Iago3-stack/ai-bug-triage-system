"""Testes da telemetria de produto (telemetria.py).

Regra-chave: sem POSTHOG_API_KEY (ou falha de config) tudo é no-op — nada de rede,
nenhuma exceção. Com o SDK injetado (fake), conferimos o que chega ao PostHog:
evento, distinct_id e propriedades (sem dados pessoais/conteúdo do relato).
"""

import telemetria


class _SDK:
    def __init__(self):
        self.captures = []
        self.sets = []

    def capture(self, **kwargs):
        self.captures.append(kwargs)
        return None

    def set(self, **kwargs):
        self.sets.append(kwargs)
        return None


def test_capturar_no_op_sem_sdk(monkeypatch):
    # Sem os secrets/chave, o SDK não existe -> capturar vira no-op e nunca raisa.
    monkeypatch.setattr(telemetria, "_obter_sdk", lambda: None)
    assert telemetria.capturar("qualquer_evento", usuario="u1", severidade="CRÍTICA") is False
    assert telemetria.capturar("qualquer_evento") is False
    assert telemetria.identificar("u1", plano="pago") is False
    assert telemetria.disponivel() is False


def test_capturar_envia_evento_com_usuario(monkeypatch):
    sdk = _SDK()
    monkeypatch.setattr(telemetria, "_obter_sdk", lambda: sdk)
    ok = telemetria.capturar(
        "triagem_realizada",
        usuario="abc-123",
        gravidade="CRÍTICA 🚨",
        usou_ia=True,
        plano="free",
    )
    assert ok is True
    assert len(sdk.captures) == 1
    kw = sdk.captures[0]
    assert kw["event"] == "triagem_realizada"
    assert kw["distinct_id"] == "abc-123"
    assert kw["properties"]["gravidade"] == "CRÍTICA 🚨"
    assert kw["properties"]["usou_ia"] is True
    assert kw["properties"]["plano"] == "free"


def test_capturar_usuario_nunca_vira_propriedade(monkeypatch):
    sdk = _SDK()
    monkeypatch.setattr(telemetria, "_obter_sdk", lambda: sdk)
    telemetria.capturar("x", usuario="abc-123", outra="1")
    props = sdk.captures[0]["properties"]
    assert "usuario" not in props
    assert props["outra"] == "1"


def test_capturar_sem_usuario_vira_anonimo(monkeypatch):
    sdk = _SDK()
    monkeypatch.setattr(telemetria, "_obter_sdk", lambda: sdk)
    telemetria.capturar("x", plano="pago")
    assert sdk.captures[0]["distinct_id"] == "anonimo"


def test_identificar_envia_propriedades(monkeypatch):
    sdk = _SDK()
    monkeypatch.setattr(telemetria, "_obter_sdk", lambda: sdk)
    assert telemetria.identificar("abc-123", plano="pago") is True
    assert sdk.sets[0]["distinct_id"] == "abc-123"
    assert sdk.sets[0]["properties"] == {"plano": "pago"}


def test_capturar_engole_falha_do_sdk(monkeypatch):
    class _Quebra:
        def capture(self, **kwargs):
            raise RuntimeError("rede fora")

        def set(self, **kwargs):
            raise RuntimeError("rede fora")

    monkeypatch.setattr(telemetria, "_obter_sdk", lambda: _Quebra())
    assert telemetria.capturar("x", usuario="u") is False
    assert telemetria.identificar("u") is False


def test_sem_sdk_nunca_toca_rede(monkeypatch):
    # Garante que com o SDK desligado não há nem tentativa de captura.
    monkeypatch.setattr(telemetria, "_obter_sdk", lambda: None)
    telemetria.capturar("x")
    telemetria.identificar("y")
    telemetria.disponivel()