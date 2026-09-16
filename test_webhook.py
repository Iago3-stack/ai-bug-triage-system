import json
import http.client
import os
import socket
import subprocess
import sys
import threading
import time

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


def test_transporte_raiz_e_health_head(servidor):
    conn = http.client.HTTPConnection(servidor.replace("http://", ""))
    conn.request("HEAD", "/")
    r = conn.getresponse()
    corpo = r.read()
    assert r.status == 200
    assert corpo == b""
    assert int(r.getheader("Content-Length")) > 0
    conn.close()
    conn = http.client.HTTPConnection(servidor.replace("http://", ""))
    conn.request("HEAD", "/health")
    r = conn.getresponse()
    assert r.status == 200
    conn.close()


def test_transporte_get_raiz(servidor):
    conn = http.client.HTTPConnection(servidor.replace("http://", ""))
    conn.request("GET", "/")
    r = conn.getresponse()
    assert r.status == 200
    assert json.loads(r.read())["status"] == "ok"
    conn.close()


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


def test_interpretar_args_defaults():
    assert webhook._interpretar_args([]) == ("0.0.0.0", 8080)


def test_interpretar_args_parseia_porta_host():
    assert webhook._interpretar_args(["--porta", "8087", "--host", "127.0.0.1"]) == ("127.0.0.1", 8087)


def test_interpretar_args_ignora_bandeira_desconhecida():
    assert webhook._interpretar_args(["--nao-existe", "1"]) == ("0.0.0.0", 8080)


def test_cli_inicia_e_responde():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    porta = s.getsockname()[1]
    s.close()
    proc = subprocess.Popen(
        [sys.executable, "webhook.py", "--porta", str(porta), "--host", "127.0.0.1"],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        resp_health = None
        for _ in range(40):
            try:
                conn = http.client.HTTPConnection("127.0.0.1", porta, timeout=2)
                conn.request("GET", "/health")
                resp_health = conn.getresponse()
                conn.close()
                if resp_health.status == 200:
                    break
            except OSError:
                time.sleep(0.25)
        assert resp_health is not None and resp_health.status == 200
        conn = http.client.HTTPConnection("127.0.0.1", porta, timeout=2)
        conn.request(
            "POST",
            "/webhook/falha",
            json.dumps({"evidencia": "POST /x [502 Bad Gateway, 1B, 1ms]"}).encode(),
            {"Content-Type": "application/json"},
        )
        r = conn.getresponse()
        dados = json.loads(r.read())
        conn.close()
        assert r.status == 200
        assert dados["tipo"] == "postman"
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_token_exige_autorizacao_no_transporte(servidor, monkeypatch):
    monkeypatch.setenv("WEBHOOK_TOKEN", "seg")
    conn = http.client.HTTPConnection(servidor.replace("http://", ""))
    conn.request("POST", "/webhook/falha", json.dumps({"evidencia": "x"}).encode(), {"Content-Type": "application/json"})
    r = conn.getresponse()
    assert r.status == 401
    monkeypatch.setenv("WEBHOOK_TOKEN", "seg")
    status, resp = _postar(servidor, "/webhook/falha", {"evidencia": PW}, token="seg")
    assert status == 200
    assert resp["tipo"] == "playwright"