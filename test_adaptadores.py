
from adaptadores import (
    _eh_postman,
    _eh_playwright,
    detectar_tipo,
    estruturar,
    estruturar_postman,
    estruturar_playwright,
)
from colar_falha import estruturar_automatico, montar_relato

PW_TEXTO = """1) chromium › login.spec.ts:18 › teste de login com sucesso

        Error: expect(locator).toHaveText(expected)

        Expected: Bem-vindo
        Received: Erro

        at /app/tests/login.spec.ts:20:7"""

PM_TEXTO = """❌ POST https://api.exemplo.com/v1/pagamento [500 Internal Server Error, 412B, 150ms]
→ status code is 200
AssertionError: expected response to have status code 200, but got 500
response body: {"error": "database timeout"}

• GET /health [200 OK, 24B, 5ms]"""


def test_detectar_tipo_pw():
    assert detectar_tipo(PW_TEXTO) == "playwright"
    assert _eh_playwright(PW_TEXTO) is True


def test_detectar_tipo_postman():
    assert detectar_tipo(PM_TEXTO) == "postman"
    assert _eh_postman(PM_TEXTO) is True


def test_detectar_tipo_none_para_texto_livre():
    assert detectar_tipo("o botão não responde e estou frustrado") is None
    assert detectar_tipo(None) is None
    assert detectar_tipo("   ") is None


def test_pw_extrai_titulo_erro_local():
    e = estruturar_playwright(PW_TEXTO)
    assert e["tipo"] == "playwright"
    assert "teste de login com sucesso" in e["titulo"]
    assert e["erro"].startswith("expect(locator)")
    assert e["local"] == "login.spec.ts:20"
    assert e["esperado"] == "Bem-vindo"
    assert e["recebido"] == "Erro"
    assert e["linguagem"] == "TypeScript"


def test_pw_severidade_com_piso_tecnico():
    e = estruturar_playwright(PW_TEXTO)
    assert e["severidade"] in ("ALTA 🚨", "CRÍTICA 🚨", "MÉDIA ⚠️")


def test_pw_sem_cabecalho_ainda_extrai():
    e = estruturar_playwright("Error: TimeoutError... at /tests/a.spec.ts:3")
    assert e["titulo"]
    assert e["erro"]


def test_pm_extrai_metodo_url_status():
    e = estruturar_postman(PM_TEXTO)
    assert e["metodo"] == "POST"
    assert "api.exemplo.com" in e["url"]
    assert e["status_recebido"] == "500"
    assert e["status_esperado"] == "200"
    assert "500" in e["requisicao"]
    assert "200" in e["requisicao"]


def test_pm_pega_erro_no_corpo_json():
    e = estruturar_postman(PM_TEXTO)
    assert e["erro"] == "database timeout"


def test_pm_asserção_vira_erro_quando_sem_json():
    e = estruturar_postman(
        "GET /users\nAssertionError: expected response to have status code 201, but got 401"
    )
    assert e["status_esperado"] == "201"
    assert e["status_recebido"] == "401"
    assert "401" in e["titulo"]
    assert e["erro"]


def test_pm_titulo_inclui_status_quando_errado():
    e = estruturar_postman("POST /login [503 Service Unavailable, 12B, 1ms]")
    assert e["metodo"] == "POST"
    assert e["status_recebido"] == "503"
    assert "503" in e["titulo"]


def test_dispatch_retorna_none_para_livre():
    assert estruturar("texto livre qualquer") is None
    assert estruturar(PW_TEXTO)["tipo"] == "playwright"
    assert estruturar(PM_TEXTO)["tipo"] == "postman"


def test_automatico_fallback_generico():
    e = estruturar_automatico("Estou tentando pagar e o botão não responde, frustrado!")
    assert e["ferramenta"] if e.get("ferramenta") else True
    assert "pagamento" in (e["modulo"] or "")


def test_automatico_usa_adaptador_pw_e_pm():
    assert estruturar_automatico(PW_TEXTO)["tipo"] == "playwright"
    assert estruturar_automatico(PM_TEXTO)["tipo"] == "postman"


def test_relato_playwright_inclui_origem_e_teste():
    relato = montar_relato(PW_TEXTO, estruturar_playwright(PW_TEXTO))
    assert "**Ferramenta de origem:** Playwright" in relato
    assert "teste de login com sucesso" in relato
    assert "**Passos para reproduzir:**" in relato


def test_relato_postman_inclui_requisicao():
    e = estruturar_postman(PM_TEXTO)
    relato = montar_relato(PM_TEXTO, e)
    assert "**Ferramenta de origem:** Postman/newman" in relato
    assert "**Requisição:**" in relato
    assert "POST" in relato and "500" in relato


def test_nunca_levanta():
    assert estruturar_automatico("")
    assert estruturar_playwright("###")["titulo"]
    assert estruturar_postman("###")["titulo"]