import guardrails


def test_detectar_token_atlassian():
    import jira_client
    jira_client._ler_env()
    token = jira_client.JIRA_API_TOKEN
    assert guardrails.detectar(f"bug ao usar {token} no login") == ["token Atlassian"]


def test_detectar_chave_gemini():
    chave_sintetica = "AQ.Ab" + "1" * 36
    resultado = guardrails.detectar(f"minha chave {chave_sintetica} vazou")
    assert "chave Gemini/Google (Shift)" in resultado


def test_detectar_chave_google_clara():
    assert guardrails.detectar(f"AIza{'x' * 30}") == ["chave API Google"]


def test_detectar_email():
    assert guardrails.detectar("meu email e viago4415@gmail.com obrigado") == ["e-mail"]


def test_texto_comum_nao_detecta():
    texto_fino = "o aplicativo travou na hora do pagamento, o botão não responde, estou frustrado"
    assert guardrails.detectar(texto_fino) == []
    assert guardrails.contem_credencial(texto_fino) is False


def test_palavra_email_com_arroba_detecta():
    # "email" sozinho (sem @) NÃO dispara; com @ dispara
    assert guardrails.detectar("meu email todo") == []
    assert guardrails.detectar("contato@empresa.com.br") == ["e-mail"]


def test_mascarar_remove_credenciais():
    resultado = guardrails.mascarar("use o token ATATT3xFfGabc123 abc e o email a@b.com no fim")
    assert "ATATT3xFfGabc123" not in resultado
    assert "a@b.com" not in resultado
    assert resultado.count("***") >= 2


def test_mascarar_string_vazia():
    assert guardrails.mascarar("") == ""
    assert guardrails.mascarar(None) == ""


def test_detectar_token_openai_e_github():
    # evita depender de chaves reais: usa padrões sintetizados
    assert "token OpenAI" in guardrails.detectar(f"sk-{'a' * 30}")
    assert "token GitHub (clássico)" in guardrails.detectar(f"ghp_{'a' * 40}")
    assert "token GitHub (fine-grained)" in guardrails.detectar(f"github_pat_{'a' * 50}")