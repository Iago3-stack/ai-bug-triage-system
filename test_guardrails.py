import guardrails


def test_detectar_token_atlassian():
    token_sintetico = "ATATT3xFfG" + "A" * 50
    assert guardrails.detectar(f"bug ao usar {token_sintetico} no login") == ["token Atlassian"]


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


def test_detectar_senha_numerica():
    # regressão: senha numérica colada no relato (viago4415@gmail.com + 4323454321)
    resultado = guardrails.detectar("a senha 4323454321 expirou no login")
    assert "senha (com números)" in resultado


def test_detectar_senha_com_dois_pontos():
    assert "senha (com números)" in guardrails.detectar("senha:123456789")


def test_mascarar_senha_numerica():
    m = guardrails.mascarar("a senha 4323454321 e o email a@b.com vazaram")
    assert "4323454321" not in m
    assert "a@b.com" not in m


def test_nao_mascara_versao_com_numero():
    # falso-positivo: número comum não pode ser mascarado
    texto_fino = "o bug acontece na versão 2026 do sistema instalado"
    assert guardrails.detectar(texto_fino) == []
    assert guardrails.mascarar(texto_fino) == texto_fino


def test_detectar_telefone_e_cpf():
    assert guardrails.detectar("ligo do (11) 98765-4321") == ["telefone"]
    assert guardrails.detectar("cpf 123.456.789-00 cadastrado") == ["CPF"]