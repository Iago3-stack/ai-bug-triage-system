import json
import http.client
import os
import threading

import pytest

import webhook

PW = "1) chromium › login.spec.ts:18 › teste de login\n\n Error: expect(locator).toHaveText(expected)\n\n Expected: Bem-vindo\n Received: Erro"
PM = "❌ POST https://api.exemplo.com/v1/pagamento [500 Internal Server Error, 412B, 150ms]\nAssertionError: expected response to have status code 200, but got 500\n→ response body: {\"error\": \"database timeout\"}"


def test_pm_payload_ok():
    status, resp = webhook.analisar_payload(
        {"evidencia": PM, "origem": "github-actions", "repositorio": "a/b", "run_id": "1234", "commit": "abc"}
    )
    assert status == 200
    assert resp["status"] == "ok"
    assert resp["tipo"] == "postman"
    assert resp["origem"] == "github-actions"
    assert resp["repositorio"] == "a/b"
    assert resp["run_id"] == "1234"
    assert resp["commit"] == "abc"
    assert "500" in resp["relato"]
    assert resp["analise"] is None


def test_pw_payload_ok():
    status, resp = webhook.analisar_payload({"evidencia": PW})
    assert status == 200
    assert resp["tipo"] == "playwright"
    assert "teste de login" in resp["relato"]


def test_evidencia_livre_cai_no_parser_generico():
    status, resp = webhook.analisar_payload({"evidencia": "os dados sumiram da tela!"})
    assert status == 200
    assert resp["tipo"] == "livre"
    assert resp["relato"]


def test_evidencia_ausente_ou_vazia():
    status, resp = webhook.analisar_payload({})
    assert status == 400 and resp["status"] == "erro"
    status, resp = webhook.analisar_payload({"evidencia": "   "})
    assert status == 400


def test_payload_nao_dict():
    status, resp = webhook.analisar_payload(["evidencia"])
    assert status == 400


def test_evidencia_grande_demais():
    status, resp = webhook.analisar_payload({"evidencia": "x" * (webhook.MAX_BYTES + 1)})
    assert status == 413


def test_token_opcional_sem_env():
    os.environ.pop("WEBHOOK_TOKEN", None)
    assert webhook.token_exigido() is False
    assert webhook.token_valido(None) is True
    assert webhook.token_valido("qualquer") is True


def test_token_exigido_quando_set(monkeypatch):
    monkeypatch.setenv("WEBHOOK_TOKEN", "segredo123")
    assert webhook.token_exigido() is True
    assert webhook.token_valido("segredo123") is True
    assert webhook.token_valido("errado") is False
    assert webhook.token_valido(None) is False


def test_quer_ia_flag_ou_env(monkeypatch):
    assert webhook._quer_ia({"ia": True}) is True
    assert webhook._quer_ia({}) is False
    monkeypatch.setenv("WEBHOOK_IA", "1")
    assert webhook._quer_ia({}) is True


@pytest.fixture(scope="module")
def servidor():
    if webhook.token_exigido():
        pytest.skip("WEBHOOK_TOKEN setado no ambiente; testes de transporte não se aplicam")
    webhook.LOGGER.disabled = True
    srv = webhook.criar_servidor(0)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{srv.server_port}"
    srv.shutdown()


def _postar(base, rota, corpo, token=None):
    u = base.replace("http://", "")
    conn = http.client.HTTPConnection(u)
    cab = {"Content-Type": "application/json"}
    if token:
        cab["X-Webhook-Token"] = token
    conn.request("POST", rota, json.dumps(corpo).encode("utf-8"), cab)
    r = conn.getresponse()
    return r.status, json.loads(r.read().decode("utf-8"))


def test_transporte_webhook_ok(servidor):
    status, resp = _postar(servidor, "/webhook/falha", {"evidencia": PM})
    assert status == 200
    assert resp["tipo"] == "postman"


def test_transporte_health(servidor):
    conn = http.client.HTTPConnection(servidor.replace("http://", ""))
    conn.request("GET", "/health")
    r = conn.getresponse()
    assert r.status == 200
    assert json.loads(r.read())["status"] == "ok"


def test_transporte_sem_evidencia(servidor):
    status, resp = _postar(servidor, "/webhook/falha", {})
    assert status == 400


def test_transporte_rota_desconhecida(servidor):
    conn = http.client.HTTPConnection(servidor.replace("http://", ""))
    conn.request("POST", "/outra")
    r = conn.getresponse()
    assert r.status == 404


def test_transporte_json_mal_formado(servidor):
    conn = http.client.HTTPConnection(servidor.replace("http://", ""))
    conn.request("POST", "/webhook/falha", b"isto nao eh json", {"Content-Type": "application/json"})
    r = conn.getresponse()
    assert r.status == 400


def test_transporte_exige_token(servidor, monkeypatch):
    monkeypatch.setenv("WEBHOOK_TOKEN", "seg")
    conn = http.client.HTTPConnection(servidor.replace("http://", ""))
    conn.request("POST", "/webhook/falha", json.dumps({"evidencia": "x"}).encode(), {"Content-Type": "application/json"})
    r = conn.getresponse()
    assert r.status == 401
    monkeypatch.setenv("WEBHOOK_TOKEN", "seg")
    status, resp = _postar(servidor, "/webhook/falha", {"evidencia": PW}, token="seg")
    assert status == 200
    assert resp["tipo"] == "playwright"