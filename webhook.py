"""Pilar 3 — Webhook de CI: recebe falhas de teste e devolve o relato pronto.

Micro-servidor HTTP 100% stdlib que escuta ``POST /webhook/falha`` com a
evidência de uma execução que falhou no CI (GitHub Actions, GitLab CI, cron
do newman/Playwright...) e responde com o **relato já estruturado**, usando os
adaptadores do Pilar 2 (Playwright/Postman) e o parser genérico do Pilar 1.

    curl -s http://localhost:8080/webhook/falha \
        -H 'Content-Type: application/json' \
        -d @payload.json

Payload (JSON):
    {"evidencia": "<saida do teste/run>",   # obrigatorio (max 200 KB)
     "origem": "github-actions",            # opcional
     "repositorio": "...", "run_id": "...", "commit": "..."}  # opcional

Segurança: se a env ``WEBHOOK_TOKEN`` estiver definida, exige o cabeçalho
``X-Webhook-Token``. IA (``ia`` no payload ou env ``WEBHOOK_IA=1``) e
persistência no histórico (env ``WEBHOOK_PERSISTE=1``) são opcionais.

Para rodar:  python webhook.py [--porta 8080] [--host 0.0.0.0]
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
import os
import sys

import colar_falha

LOGGER = logging.getLogger("webhook-falhas")
MAX_BYTES = 200_000  # teto da evidência aceita (evita payload gigante)


def token_exigido() -> bool:
    return bool(os.environ.get("WEBHOOK_TOKEN"))


def token_valido(cabecalho: str | None) -> bool:
    aceito = os.environ.get("WEBHOOK_TOKEN")
    if not aceito:
        return True
    return bool(cabecalho) and cabecalho.strip() == aceito.strip()


def _quer_ia(dados: dict) -> bool:
    return bool(dados.get("ia")) or os.environ.get("WEBHOOK_IA") == "1"


def _quer_persistir() -> bool:
    return os.environ.get("WEBHOOK_PERSISTE") == "1"


def analisar_payload(dados: dict) -> tuple[int, dict]:
    """Valida o payload, extrai o relato e devolve (status HTTP, resposta)."""
    if not isinstance(dados, dict):
        return 400, {"status": "erro", "erro": "payload deve ser um JSON object"}
    evidencia = dados.get("evidencia")
    if not isinstance(evidencia, str) or not evidencia.strip():
        return 400, {"status": "erro", "erro": "campo 'evidencia' é obrigatório (texto)"}
    if len(evidencia) > MAX_BYTES:
        return 413, {
            "status": "erro",
            "erro": f"evidência grande demais (máx. {MAX_BYTES} caracteres)",
        }

    estrutura = colar_falha.estruturar_automatico(evidencia)
    relato = colar_falha.montar_relato(evidencia, estrutura)
    resposta = {
        "status": "ok",
        "tipo": estrutura.get("tipo", "livre"),
        "origem": str(dados.get("origem") or "ci")[:60],
        "repositorio": str(dados.get("repositorio") or ""),
        "run_id": str(dados.get("run_id") or ""),
        "commit": str(dados.get("commit") or ""),
        "estrutura": estrutura,
        "relato": relato,
        "analise": None,
    }

    if _quer_ia(dados):
        try:
            import ia as _ia

            analise, erro = _ia.analisar_llm(relato)
            resposta["analise"] = analise
            if erro:
                resposta["aviso_ia"] = str(erro)[:200]
        except Exception as ex:  # nunca derruba o webhook
            resposta["aviso_ia"] = f"{type(ex).__name__}: {ex}"[:200]

    if _quer_persistir():
        try:
            import persistencia as _persistencia

            registro = {
                "relato": relato,
                **{k: (estrutura.get(k) or "") for k in
                   ("severidade", "categoria", "modulo", "versao", "erro")},
                "origem": resposta["origem"],
                "repositorio": resposta["repositorio"],
                "run_id": resposta["run_id"],
                "commit": resposta["commit"],
                "fechado": False,
            }
            _persistencia.registrar_triagem(registro)
            resposta["persistido"] = True
        except Exception as ex:
            resposta["persistido"] = False
            resposta["aviso_persistencia"] = f"{type(ex).__name__}: {ex}"[:200]

    return 200, resposta


class TratadorWebhook(BaseHTTPRequestHandler):
    server_version = "AI-BugTriage-Webhook/1.0"
    protocol_version = "HTTP/1.1"

    def _responder(self, status: int, payload: dict) -> None:
        corpo = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self) -> None:
        if self.path.rstrip("/") == "/health":
            self._responder(200, {"status": "ok"})
            return
        self._responder(404, {"status": "erro", "erro": "rota desconhecida"})

    def do_POST(self) -> None:
        if not self.path.rstrip("/").startswith("/webhook/falha"):
            self._responder(404, {"status": "erro", "erro": "rota desconhecida"})
            return
        if token_exigido() and not token_valido(
            self.headers.get("X-Webhook-Token")
        ):
            self._responder(401, {"status": "erro", "erro": "token ausente ou inválido"})
            return

        tamanho = self.headers.get("Content-Length")
        try:
            n = int(tamanho) if tamanho else 0
        except ValueError:
            self._responder(400, {"status": "erro", "erro": "Content-Length inválida"})
            return
        if n <= 0:
            self._responder(400, {"status": "erro", "erro": "corpo vazio"})
            return
        if n > MAX_BYTES:
            self._responder(413, {"status": "erro", "erro": "payload grande demais"})
            return
        corpo = self.rfile.read(n)
        if not corpo:
            self._responder(400, {"status": "erro", "erro": "corpo vazio"})
            return
        try:
            dados = json.loads(corpo.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self._responder(400, {"status": "erro", "erro": "corpo não é JSON válido"})
            return
        status, resposta = analisar_payload(dados)
        self._responder(status, resposta)

    def log_message(self, formato, *args) -> None:
        LOGGER.info("%s - %s", self.address_string(), formato % args)


def criar_servidor(porta: int = 0):
    return ThreadingHTTPServer(("127.0.0.1", porta), TratadorWebhook)


def _interpretar_args(args: list[str]) -> tuple[str, int]:
    """--host <H> e --porta <P>; defaults: 0.0.0.0:8080."""
    porta = 8080
    host = "0.0.0.0"
    fila = list(args)
    while fila:
        arg = fila.pop(0)
        if arg == "--porta" and fila:
            porta = int(fila.pop(0))
        elif arg == "--host" and fila:
            host = fila.pop(0)
    return host, porta


def principal(argv: list[str] | None = None) -> None:
    host, porta = _interpretar_args(list(argv or []))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    servidor = ThreadingHTTPServer((host, porta), TratadorWebhook)
    abertura = "aberto (sem token)" if not token_exigido() else "protegido por WEBHOOK_TOKEN"
    LOGGER.info(
        "Webhook de CI no ar em http://%s:%s — %s | envie POST /webhook/falha",
        host,
        porta,
        abertura,
    )
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        servidor.shutdown()


if __name__ == "__main__":
    principal(sys.argv[1:])