"""Pilar 2 — adaptadores de evidência estruturada (Playwright / Postman·newman).

Depois do colar_falha genérico (Pilar 1, texto livre), estes adaptadores
reconhecem a saída das ferramentas de automação de testes e extraem um relato
com o léxico próprio de cada uma:

- **Playwright** (texto do terminal + JSON do relator): nome do (spec +) teste,
  mensagem de erro (`Error: expect(...)`), Expected/Received e arquivo:linha.
- **Postman/newman**: método + URL, HTTP status **esperado × recebido**,
  detalhe da asserção que falhou e corpo da resposta.

Se a evidência não bater com nenhum formato, devolvem None e o
`colar_falha` genérico (texto livre) assume. 100% local e determinístico.
"""
import json
import re

from colar_falha import (
    _detectar_categoria,
    _detectar_modulo,
    _extrair_versao,
    _primeira_linha_util,
    _severidade,
)

# ── Playwright ──────────────────────────────────────────────────────────────

_CABECALHO_PW = re.compile(r"^\s*\d+\)\s+(?:\[[^\]]*\]\s*)?[^\n]*", re.MULTILINE)
_ERROR_PW = re.compile(
    r"^\s*Error:\s*(?P<msg>.*?)(?=\n\s*(?:at |Expected:|Received:|\d+\))|$)",
    re.MULTILINE | re.DOTALL,
)
_EXPECTED_PW = re.compile(r"^\s*Expected:\s*(?P<val>[^\n]+)", re.MULTILINE)
_RECEIVED_PW = re.compile(r"^\s*Received:\s*(?P<val>[^\n]+)", re.MULTILINE)
_FRAME_PW = re.compile(r"\bat\s+([^\s()]+(?:\.spec|\.test)\.\w+):(\d+)")
_JSON_PW = re.compile(r'"failures"\s*:\s*\[|"status"\s*:\s*"failed"')

_PADRAO_POSTMAN = re.compile(
    r"(?:AssertionError:.*status\s+code|expecting response to have status code|"
    r"HTTP/\d\.\d\s+\d{3}|\[\d{3}\s+(?:OK|[A-Z][a-z]+(?: [A-Z][a-z]+)*\])|"
    r"(?:GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD))\s?",
    re.IGNORECASE,
)
_METODO_URL_PM = re.compile(
    r"^\s*(?:[^\w]+\s+)?(GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)\s+(\S+)"
    r"(?:\s*\[(\d{3})[^\]]*\])?\s*$",
    re.MULTILINE,
)
_STATUS_PM = re.compile(
    r"expected(?:\s+(?:response|status code))*\s+(?:to\s+)?have\s+status\s+code\s+"
    r"(?P<esp>\d+)[^\d]*(?P<rec>\d{3})",
    re.IGNORECASE,
)
_ASSERT_PM = re.compile(r"^\s*AssertionError:.*$", re.MULTILINE)
_CORPO_PM = re.compile(r"(?i)^\s*(?:response|request)?[\s_]*body\s*:?\s*(?P<corpo>.{0,220})$")
_JSON_ERRO = re.compile(r'"(?:error|message|msg)"\s*:\s*"([^"]{1,160})"')

_METODOS = r"GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD"


def _eh_playwright(ev: str) -> bool:
    if "›" in ev:
        return True
    if re.search(r"\.spec\.[jt]sx?", ev) and re.search(r"\bError:|expect\(", ev):
        return True
    if _JSON_PW.search(ev):
        return True
    return False


def _eh_postman(ev: str) -> bool:
    if _METODO_URL_PM.search(ev) and _PADRAO_POSTMAN.search(ev):
        return True
    if re.search(r"(?i)assertionerror:.*status code", ev):
        return True
    return False


def detectar_tipo(evidencia: str) -> str | None:
    """'playwright' | 'postman' | None (texto livre → Pilar 1)."""
    ev = (evidencia or "").strip()
    if not ev:
        return None
    if _eh_playwright(ev):
        return "playwright"
    if _eh_postman(ev):
        return "postman"
    return None


def _pm_metodo_url_status(ev: str) -> tuple[str, str, str | None]:
    m = _METODO_URL_PM.search(ev)
    if not m:
        return "POST", "", None
    return m.group(1), m.group(2), m.group(3)


def _pm_status_dupla(ev: str) -> tuple[str | None, str | None]:
    m = _STATUS_PM.search(ev)
    if not m:
        return None, None
    return m.group("esp"), m.group("rec")


def _pw_nome_teste(ev: str) -> str | None:
    for linha in _CABECALHO_PW.findall(ev):
        partes = [p.strip() for p in linha.split("›")]
        if len(partes) >= 2 and partes[-1]:
            return partes[-1]
    linhas = [l.strip() for l in ev.splitlines() if "›" in l]
    for l in linhas:
        nome = l.split("›")[-1].strip()
        if nome:
            return nome
    return None


def _pw_erro(ev: str) -> str | None:
    m = _ERROR_PW.search(ev)
    if m:
        msg = re.sub(r"\s+", " ", m.group("msg")).strip()
        if msg:
            return msg[:180]
    return None


def estruturar_playwright(evidencia: str) -> dict:
    """Extrai o relato de uma saída de teste Playwright (texto/JSON)."""
    texto = evidencia.strip()
    erro = _pw_erro(texto)
    try:
        dados = json.loads(texto)
        if isinstance(dados, list) and dados:
            d = next((x for x in dados if x.get("status") == "failed"), dados[0])
            erro = erro or (d.get("error") or {}).get("message") or None
    except (ValueError, TypeError, AttributeError):
        pass
    esperado = _EXPECTED_PW.search(texto)
    recebido = _RECEIVED_PW.search(texto)
    frame = list(_FRAME_PW.finditer(texto))
    local = f"{frame[-1].group(1).split('/')[-1]}:{frame[-1].group(2)}" if frame else None
    nome = _pw_nome_teste(texto)
    linguagem = "TypeScript" if any(f.group(1).endswith((".ts", ".tsx")) for f in frame) else (
        "JavaScript" if any(f.group(1).endswith((".js", ".jsx")) for f in frame) else "Playwright"
    )
    titulo = f"Teste falhou: {nome}" if nome else f"Falha de teste: {erro or 'asserção não passou'}"
    desc = "Falha em teste automatizado (Playwright)" + (f" — `{nome}`" if nome else "")
    desc += f". Erro: {erro}" if erro else f". {_primeira_linha_util(texto)}"
    if esperado or recebido:
        desc += f". Esperado: {esperado.group('val').strip() if esperado else '—'} · Recebido: {recebido.group('val').strip() if recebido else '—'}"
    passos = []
    if nome:
        passos.append(f"Rodar o teste: {nome}")
    passos.append(f"Observar a asserção que falhou: {erro or 'ver Expected/Received'}")
    if local:
        passos.append(f"Conferir o ponto do código: `{local}`")
    passos.append("Reproduzir o fluxo que o teste automatiza no app")
    return {
        "tipo": "playwright",
        "ferramenta": "Playwright",
        "titulo": titulo,
        "descricao": desc,
        "categoria": _detectar_categoria(texto),
        "modulo": _detectar_modulo(texto),
        "versao": _extrair_versao(texto),
        "severidade": _severidade(texto, erro),
        "erro": erro,
        "local": local,
        "linguagem": linguagem,
        "passos_repro": passos[:4],
        "teste": nome,
        "esperado": esperado.group("val").strip() if esperado else None,
        "recebido": recebido.group("val").strip() if recebido else None,
    }


def estruturar_postman(evidencia: str) -> dict:
    """Extrai o relato de uma execução do Postman/newman (status + asserções)."""
    texto = evidencia.strip()
    metodo, url, status_colchete = _pm_metodo_url_status(texto)
    esp, rec = _pm_status_dupla(texto)
    recebido = status_colchete or rec
    preenchido_esp, preenchido_rec = bool(esp), bool(rec)
    assert_linha = _ASSERT_PM.search(texto)
    assert_txt = assert_linha.group(0).strip()[:180] if assert_linha else None
    erro = None
    m_json = _JSON_ERRO.search(texto)
    if m_json:
        erro = m_json.group(1).strip()
    elif assert_txt:
        erro = assert_txt
    elif recebido:
        erro = f"Resposta HTTP {recebido} para {metodo} {url[:80]}"
    corpo = _CORPO_PM.search(texto)
    det_http = (
        f"{metodo} {url}"
        + (f" → HTTP {recebido}" if recebido else "")
        + (f" (esperado {esp})" if esp else "")
    )
    if not url:
        url = _primeira_linha_util(texto)[:60]
    titulo = f"Falha em {metodo} {url[:60]}"
    if recebido:
        titulo += f" — HTTP {recebido}"
        if esp and esp != recebido:
            titulo += f" (esperado {esp})"
    desc = f"Falha em requisição (Postman/newman). {det_http}."
    if preenchido_esp and preenchido_rec and esp != rec:
        desc += f" A asserção esperava {esp}, mas a API retornou {rec}."
    if assert_txt and not (preenchido_esp and preenchido_rec):
        desc += f" Detalhe: {assert_txt}."
    if corpo and corpo.group("corpo").strip():
        desc += f" Corpo da resposta: {corpo.group('corpo').strip()[:200]}."
    passos = [
        f"Enviar `{metodo}` para {url}",
        f"Esperar o status {esp or '2xx/esperado'}",
    ]
    if recebido:
        passos.append(f"Observar o status recebido: {recebido}")
        if esp and esp != recebido:
            passos.append(f"Conferir por que a API retornou {recebido} em vez de {esp}")
    else:
        passos.append("Observar o corpo/erro retornado pela API")
    return {
        "tipo": "postman",
        "ferramenta": "Postman/newman",
        "titulo": titulo,
        "descricao": desc,
        "categoria": _detectar_categoria(texto + " " + url),
        "modulo": _detectar_modulo(texto + " " + url),
        "versao": _extrair_versao(url),
        "severidade": _severidade(texto, erro or f"{metodo} {recebido or ''}"),
        "erro": erro,
        "local": None,
        "linguagem": "HTTP/REST",
        "passos_repro": passos[:4],
        "requisicao": det_http,
        "metodo": metodo,
        "url": url,
        "status_esperado": esp,
        "status_recebido": recebido,
    }


def estruturar(evidencia: str) -> dict | None:
    """Dispara o adaptador certo. None se nenhum formato foi reconhecido."""
    tipo = detectar_tipo(evidencia)
    if tipo == "playwright":
        return estruturar_playwright(evidencia)
    if tipo == "postman":
        return estruturar_postman(evidencia)
    return None


if __name__ == "__main__":
    pw = """1) chromium › login.spec.ts:18 › teste de login com sucesso

        Error: expect(locator).toHaveText(expected)

        Expected: Bem-vindo
        Received: Erro

        at /app/tests/login.spec.ts:20:7"""
    pm = """❌ POST https://api.exemplo.com/v1/pagamento [500 Internal Server Error, 412B, 150ms]
→ status code is 200
AssertionError: expected response to have status code 200, but got 500
response body: {"error": "database timeout"}

• GET /health [200 OK, 24B, 5ms]"""
    for rotulo, ev in (("PLAYWRIGHT", pw), ("POSTMAN", pm)):
        e = estruturar(ev)
        print(f"=== {rotulo} [{e['tipo']}] ===")
        for k, v in e.items():
            print(f"  {k}: {v}")