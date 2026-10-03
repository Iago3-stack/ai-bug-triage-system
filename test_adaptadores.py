
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

# --- Regressões: saída real de Playwright 1.62 e Newman 6.2.2 ---------
#
# Capturada de uma execução de verdade (Playwright 1.62.0 + Chromium, Newman
# 6.2.2) contra um servidor local. O path do container foi trocado por `/app`
# para o fixture não depender de máquina nenhuma.
#
# Antes destas correções: a linha `Received:` não existe quando o elemento
# some, então `element(s) not found` virava registro idêntico ao de outro
# defeito; e o Newman reportava 4 asserções quebradas das quais 1 chegava ao
# relato — as outras sumiam sem aviso.

PW_REAL_SEM_RECEIVED = """  1) tests/login.spec.ts:5:7 › login › login com sucesso leva ao painel (4.0s)

    Error: expect(locator).toHaveText(expected) failed

    Locator: locator('#area-usuario')
    Expected: "Bem-vindo"
    Timeout:  3000ms
    Error: element(s) not found

    Call log:
      - Expect "toHaveText" with timeout 3000ms
      - waiting for locator('#area-usuario')

       8 |     await page.fill('#senha', 'correta123');
       9 |     await page.click('#entrar');
    > 10 |     await expect(page.locator('#area-usuario')).toHaveText('Bem-vindo', { timeout: 3000 });
         |                                                 ^
        at /app/tests/login.spec.ts:10:49

  1 failed"""

PW_REAL_COM_RECEIVED = """  1) tests/login.spec.ts:5:7 › login › login com sucesso leva ao painel (3.8s)

    Error: expect(locator).toHaveText(expected) failed

    Locator:  locator('#msg')
    Expected: "Bem-vindo"
    Received: "Erro: credenciais invalidas"
    Timeout:  3000ms

        10 × locator resolved to <p id="msg" role="alert">Erro: credenciais invalidas</p>

    at /app/tests/login.spec.ts:10:40"""

NM_REAL_MULTIPLAS = """newman run collection.json

→ login com senha errada
  POST http://127.0.0.1:8766/api/login [401 Unauthorized, 62B, 3ms]
  1. login retorna 200

→ carrega relatorio
  GET http://127.0.0.1:8766/api/relatorio [500 Internal Server Error, 74B, 12ms]
  2. relatorio responde 200
  3. relatorio tem itens

→ painel traz usuario admin
  GET http://127.0.0.1:8766/api/painel [200 OK, 203B, 7ms]
  4. usuario e admin

  # failure        detail
 1.  AssertionError  login retorna 200
                     expected response to have status code 200 but got 401
                     at assertion:0 in test-script
                     inside "login com senha errada"
 2.  AssertionError  relatorio responde 200
                     expected response to have status code 200 but got 500
                     at assertion:0 in test-script
                     inside "carrega relatorio"
 3.  AssertionError  relatorio tem itens
                     expected undefined to be an array
                     at assertion:1 in test-script
                     inside "carrega relatorio"
 4.  AssertionError  usuario e admin
                     expected 'conta@exemplo.com' to deeply equal 'admin'
                     at assertion:0 in test-script
                     inside "painel traz usuario admin'

  4 assertions failed, 4 failed, 0 passed"""


def test_pw_motivo_real_vem_do_segundo_error():
    """`Error:` aparece duas vezes: a do header e a do motivo."""
    e = estruturar_playwright(PW_REAL_SEM_RECEIVED)
    assert e["motivo_falha"] == "element(s) not found"
    assert e["erro"] == "expect(locator).toHaveText(expected) failed"


def test_pw_extrai_locator_quando_recebido_vem_vazio():
    e = estruturar_playwright(PW_REAL_SEM_RECEIVED)
    assert e["locator"] == "#area-usuario"
    assert e["recebido"] is None
    assert e["local"] == "login.spec.ts:10"


def test_pw_nome_do_teste_nao_traz_tracos_do_reporter():
    e = estruturar_playwright(PW_REAL_SEM_RECEIVED)
    assert e["teste"] == "login com sucesso leva ao painel"
    assert "─" not in e["teste"]
    assert "─" not in e["titulo"]


def test_pw_defeitos_diferentes_ficam_distinguiveis():
    """Selector errado e elemento inexistente não podem gerar o mesmo registro."""
    sem_el = estruturar_playwright(PW_REAL_SEM_RECEIVED)
    com_texto = estruturar_playwright(PW_REAL_COM_RECEIVED)
    assert sem_el["locator"] != com_texto["locator"]
    assert com_texto["recebido"] == '"Erro: credenciais invalidas"'
    assert sem_el["descricao"] != com_texto["descricao"]


def test_pw_locator_vai_para_os_passos_de_reproducao():
    e = estruturar_playwright(PW_REAL_SEM_RECEIVED)
    assert any("#area-usuario" in p for p in e["passos_repro"])


def test_newman_preserva_todas_as_falhas():
    """A rodada teve 4 asserções quebradas; nenhuma pode sumir."""
    e = estruturar_postman(NM_REAL_MULTIPLAS)
    assert e["total_falhas"] == 4
    assert len(e["falhas"]) == 4
    nomes = [f["nome"] for f in e["falhas"]]
    assert "relatorio responde 200" in nomes
    assert "usuario e admin" in nomes


def test_newman_falha_traz_metodo_url_e_status():
    e = estruturar_postman(NM_REAL_MULTIPLAS)
    por_nome = {f["nome"]: f for f in e["falhas"]}
    rel = por_nome["relatorio responde 200"]
    assert rel["metodo"] == "GET"
    assert rel["url"].endswith("/api/relatorio")
    assert rel["status"] == "500"


def test_newman_descreve_as_demais_falhas_no_relato():
    """O HTTP 500 precisa estar visível no texto do relato, não só no payload."""
    e = estruturar_postman(NM_REAL_MULTIPLAS)
    relato = montar_relato(NM_REAL_MULTIPLAS, e)
    assert "4 asserções quebradas" in relato
    assert "500" in relato
    assert "relatorio responde 200" in relato
