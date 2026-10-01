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
``X-Webhook-Token`` (comparação em tempo constante). ``WEBHOOK_REQUIRE_TOKEN=1``
força o token mesmo sem valor configurado (falha fechada). IA (``ia`` no payload
ou env ``WEBHOOK_IA=1``) e persistência no histórico (env ``WEBHOOK_PERSISTE=1``)
são opcionais.

Para rodar:  python webhook.py [--porta 8080] [--host 0.0.0.0]
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import hmac
import json
import logging
import os
import sys

import colar_falha

LOGGER = logging.getLogger("webhook-falhas")
MAX_BYTES = 200_000  # teto da evidência aceita (evita payload gigante)
_DRENAGEM_TIMEOUT = 5.0  # quanto esperar o corpo rejeitado chegar, apos responder
_DRENAGEM_TETO = 1024 * 1024  # acima disso nao drena: fecha a conexao


def token_exigido() -> bool:
    return bool(os.environ.get("WEBHOOK_TOKEN")) or os.environ.get("WEBHOOK_REQUIRE_TOKEN") == "1"


def token_valido(cabecalho: str | None) -> bool:
    """Comparação em tempo constante (evita timing attack) contra o segredo."""
    aceito = os.environ.get("WEBHOOK_TOKEN")
    if not aceito:
        # Sem segredo definido: aberto, a menos que WEBHOOK_REQUIRE_TOKEN=1 (falha fechada).
        return os.environ.get("WEBHOOK_REQUIRE_TOKEN") != "1"
    return bool(cabecalho) and hmac.compare_digest(cabecalho.strip(), aceito.strip())


def assinatura_pagbank_valida(corpo: bytes, cabecalho: str | None) -> bool:
    """Confere o ``x-authenticity-token`` do PagBank.

    A assinatura oficial é ``SHA256(token_da_conta + "-" + payload)`` em hex,
    comparada em tempo constante. O hash é calculado sobre os **bytes crus** do
    corpo: reserializar o JSON parseado muda espaçamento e a validação falha
    sempre, que é o erro que a doc do PagBank avisa ("qualquer espaço adicional
    fará com que o hash tenha divergência").

    Sem ``PAGBANK_TOKEN`` no ambiente fica aberto, a menos que
    ``WEBHOOK_REQUIRE_TOKEN=1`` force a falha fechada (mesma política de
    ``token_valido``).
    """
    segredo = os.environ.get("PAGBANK_TOKEN")
    if not segredo:
        return os.environ.get("WEBHOOK_REQUIRE_TOKEN") != "1"
    if not cabecalho:
        return False
    esperado = hashlib.sha256(segredo.encode("utf-8") + b"-" + corpo).hexdigest()
    return hmac.compare_digest(cabecalho.strip().lower(), esperado)


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


def analisar_pagamento(dados: dict) -> tuple[int, dict]:
    """Confirma uma cobrança a partir da notificação de status do PagBank.

    A notificação é só o gatilho: o estado real do pedido é consultado na API
    de Pedidos (pelo order_id gravado na cobrança) e a confirmação só acontece
    quando uma charge está com status PAID. A chamada a
    ``pixbilling.confirmar_cobranca`` é idempotente (não estoura se já
    confirmada) e sempre respondemos 200 para o PagBank parar de reenviar.
    """
    try:
        import pagbank
        import pixbilling
    except Exception as ex:  # webhook nunca deve derrubar o servidor
        return 500, {"status": "erro", "erro": f"{type(ex).__name__}: {ex}"[:200]}

    if not isinstance(dados, dict):
        return 200, {"status": "ok", "acao": "ignorada"}
    referencia = str(dados.get("reference_id") or "").strip()
    if not referencia:
        return 200, {"status": "ok", "acao": "ignorada"}

    cobranca = pixbilling.buscar_cobranca(referencia)
    if not cobranca:
        return 200, {"status": "ok", "acao": "ignorada"}
    if cobranca.get("status") != "aguardando":
        return 200, {"status": "ok", "acao": "ja_resolvida"}

    order_id = str(cobranca.get("pagbank_order_id") or "").strip() or str(
        dados.get("id") or ""
    ).strip()
    if not order_id:
        return 200, {"status": "ok", "acao": "ignorada"}

    try:
        pedido = pagbank.consultar_pedido(order_id)
        pago = pagbank.pagamento_confirmado(pedido)
    except Exception as ex:
        LOGGER.warning("Falha ao verificar pedido %s: %s", order_id, ex)
        return 200, {"status": "ok", "acao": "nao_verificado"}

    if not pago:
        return 200, {"status": "ok", "acao": "aguardando"}

    confirmado = pixbilling.confirmar_cobranca(referencia)
    return 200, {"status": "ok", "acao": "confirmado" if confirmado else "ja_resolvida"}


class TratadorWebhook(BaseHTTPRequestHandler):
    # Socket não pode ficar aberto indefinidamente esperando um corpo que não vem.
    timeout = 30

    server_version = "AI-BugTriage-Webhook/1.0"
    protocol_version = "HTTP/1.1"

    def _responder(self, status: int, payload: dict) -> None:
        corpo = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def _responder_rejeitando(self, status: int, payload: dict) -> None:
        """Responde a um payload **ainda não lido**, sem corromper o keep-alive.

        Rejeitar sem consumir o corpo deixa os bytes do request pendurados no
        socket. Com ``protocol_version = HTTP/1.1``, a conexão seguinte
        recomeça a leitura no meio desses bytes e o servidor interpreta a
        sobra do JSON como método — ``501 Unsupported method ('{...}POST')``,
        erro que aparece para um cliente que fez tudo certo. Foi observado em
        produção depois de um ``401``.

        Fechar a conexão não resolve: o cliente legítimo que reaproveita a
        conexão toma ``BrokenPipeError`` na requisição seguinte. Drenar
        **antes** de responder também não: o cliente espera a resposta antes
        de terminar de enviar o corpo, então um ``rfile.read()`` bloqueante
        antes do ``send_response`` é deadlock.

        A ordem que funciona é responder, **depois** drenar, com timeout curto
        no socket e sem esperar mais que o necessário. Se o corpo não chegar
        inteiro nesse tempo, marcamos a conexão para fechar e seguimos — não
        vale segurar uma thread por causa de cliente malformado.
        """
        pendente = 0
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = 0
        if n <= 0 or n > _DRENAGEM_TETO:
            # Corpo vazio não suja o socket; corpo enorme não vale drenar.
            self.close_connection = n > _DRENAGEM_TETO
        else:
            pendente = n

        self._responder(status, payload)

        if pendente:
            self._drenar(pendente)

    def _drenar(self, pendente: int) -> None:
        """Consome o resto do corpo já respondendo, com socket em timeout curto."""
        try:
            self.connection.settimeout(_DRENAGEM_TIMEOUT)
            while pendente > 0:
                lido = self.rfile.read(min(pendente, 8192))
                if not lido:
                    break
                pendente -= len(lido)
        except (OSError, ValueError):
            self.close_connection = True
        finally:
            try:
                self.connection.settimeout(self.timeout)
            except OSError:
                self.close_connection = True

    def _responder_sem_corpo(self, status: int, payload: dict) -> None:
        corpo = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()

    def do_HEAD(self) -> None:
        if self.path.rstrip("/") in ("", "/health"):
            self._responder_sem_corpo(200, {"status": "ok"})
            return
        self._responder_sem_corpo(404, {"status": "erro", "erro": "rota desconhecida"})

    def do_GET(self) -> None:
        if self.path.rstrip("/") in ("", "/health"):
            self._responder(200, {"status": "ok"})
            return
        self._responder(404, {"status": "erro", "erro": "rota desconhecida"})

    def do_POST(self) -> None:
        caminho = self.path.rstrip("/")
        if caminho.startswith("/webhook/falha"):
            pass
        elif caminho.startswith("/webhook/pagamento"):
            self._do_post_pagamento()
            return
        else:
            self._responder(404, {"status": "erro", "erro": "rota desconhecida"})
            return
        if token_exigido() and not token_valido(
            self.headers.get("X-Webhook-Token")
        ):
            self._responder_rejeitando(401, {"status": "erro", "erro": "token ausente ou inválido"})
            return

        tamanho = self.headers.get("Content-Length")
        try:
            n = int(tamanho) if tamanho else 0
        except ValueError:
            self._responder_rejeitando(400, {"status": "erro", "erro": "Content-Length inválida"})
            return
        if n <= 0:
            self._responder(400, {"status": "erro", "erro": "corpo vazio"})
            return
        if n > MAX_BYTES:
            self._responder_rejeitando(413, {"status": "erro", "erro": "payload grande demais"})
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

    def _do_post_pagamento(self) -> None:
        """Recebe a notificação de status do PagBank (POST em /webhook/pagamento).

        O PagBank envia a mudança de status de um pedido. Nós NÃO confiamos no
        corpo da notificação: confirmamos a cobrança apenas se a consulta na API
        de Pedidos (server-side) mostrar o charge com status PAID. Resposta 200
        sempre que a notificação foi recebida (o PagBank para de reenviar) e a
        confirmação é idempotente.

        A autenticação é o header ``x-authenticity-token`` do próprio PagBank
        (SHA256 do token da conta + corpo cru) — não há como configurar header
        customizado na conta, então ``X-Webhook-Token`` não serviria aqui. É
        defesa em profundidade: mesmo forjando o corpo, nada é confirmado sem
        a consulta server-side na API.
        """
        tamanho = self.headers.get("Content-Length")
        try:
            n = int(tamanho) if tamanho else 0
        except ValueError:
            self._responder_rejeitando(400, {"status": "erro", "erro": "Content-Length inválida"})
            return
        if n <= 0:
            self._responder(200, {"status": "ok", "acao": "ignorada"})
            return
        if n > MAX_BYTES:
            self._responder_rejeitando(413, {"status": "erro", "erro": "payload grande demais"})
            return
        corpo = self.rfile.read(n)
        if not corpo:
            self._responder(200, {"status": "ok", "acao": "ignorada"})
            return
        if not assinatura_pagbank_valida(corpo, self.headers.get("X-Authenticity-Token")):
            LOGGER.warning("Assinatura do PagBank ausente ou inválida em %s", self.path)
            # O corpo já foi lido em `corpo = self.rfile.read(n)`: drenar aqui
            # corromperia a conexão em vez de protegê-la.
            self._responder(401, {"status": "erro", "erro": "assinatura ausente ou inválida"})
            return
        try:
            dados = json.loads(corpo.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self._responder(200, {"status": "ok", "acao": "ignorada"})
            return
        status, resposta = analisar_pagamento(dados)
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