"""Testes do módulo de cobrança próprio ('nosso Stripe') — Passo 4 SaaS.

Usam PIXBILLING_ARQUIVO (tmp_path) para isolar o JSONL local; a nuvem é
mockada quando necessário. Nunca tocam data/ real nem a rede.
"""
import pixbilling
import pix
import pytest


@pytest.fixture(autouse=True)
def _sem_env_local(monkeypatch):
    """Hermeticidade: o .env do desenvolvedor (ex.: PAGBANK de sandbox local)
    não pode decidir se o PagBank está 'configurado' nos testes."""
    monkeypatch.setattr(pix, "_ler_env", lambda nome: "")


def _caminho_tmp(tmp_path, monkeypatch):
    arquivo = tmp_path / "cobrancas.jsonl"
    monkeypatch.setenv("PIXBILLING_ARQUIVO", str(arquivo))
    return arquivo


def test_preco_padrao_19399():
    assert float(pixbilling.preco()) == 19.99


def test_preco_texto_formatado(monkeypatch):
    monkeypatch.setenv("PLANO_PRECO", "19.99")
    assert pixbilling.preco_texto() == "R$ 19,99"


def test_preco_custom_aceita_virgula(monkeypatch):
    monkeypatch.setenv("PLANO_PRECO", "29,90")
    assert float(pixbilling.preco()) == 29.9
    assert pixbilling.preco_texto() == "R$ 29,90"


def test_preco_invalido_cai_no_padrao(monkeypatch):
    monkeypatch.setenv("PLANO_PRECO", "abc")
    assert float(pixbilling.preco()) == 19.99


def test_gerar_cobranca_aguardando(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    doc = pixbilling.gerar_cobranca("u-um")
    assert doc["id"].startswith("cob-")
    assert doc["uid"] == "u-um"
    assert doc["status"] == "aguardando"
    assert float(doc["valor"]) == 19.99
    assert pixbilling.pendentes()[0]["id"] == doc["id"]


def test_regenerar_pagamento_atualiza_mesmo_doc(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    monkeypatch.delenv("PAGBANK_TOKEN", raising=False)
    doc = pixbilling.gerar_cobranca("u-um")
    assert "pagbank_erro" not in doc

    import pagbank
    monkeypatch.setenv("PAGBANK_TOKEN", "tok")
    monkeypatch.setenv("PAGBANK_WEBHOOK_URL", "https://x.onrender.com/webhook/pagamento")

    def fake_ok(valor, reference_id, cpf, nome, email):
        return {"order_id": "ORDE_NOVA", "qr_id": "QRCO_NOVA", "pix_copia": "0002010NOVO"}

    monkeypatch.setattr(pagbank, "criar_cobranca", fake_ok)
    nova = pixbilling.regenerar_pagamento(doc, cpf="52998224725", nome="Titular")
    assert nova["id"] == doc["id"]  # mesma cobrança, sem duplicar
    assert nova["pix_copia_pagbank"] == "0002010NOVO"
    assert nova["pagbank_order_id"] == "ORDE_NOVA"
    assert "pagbank_erro" not in nova

    # erro na tentativa é gravado (e não estoura)
    def fake_erro(valor, reference_id, cpf, nome, email):
        raise pagbank.PagbankErro("CPF inválido")

    monkeypatch.setattr(pagbank, "criar_cobranca", fake_erro)
    falhou = pixbilling.regenerar_pagamento(nova, cpf="11111111111")
    assert falhou["pagbank_erro"] == "CPF inválido"
    assert "pix_copia_pagbank" not in falhou


def test_cobrancas_do_uid_filtra(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    pixbilling.gerar_cobranca("u-um")
    pixbilling.gerar_cobranca("u-dois")
    pixbilling._salvar_jsonl({"id": "cob-antiga", "uid": "u-um", "valor": 19.99,
                              "status": "confirmado", "criado_em": "2099-01-01T10:00:00-03:00"})
    so_um = pixbilling.cobrancas_do_uid("u-um")
    ids_um = {c["id"] for c in so_um}
    assert "cob-antiga" in ids_um
    assert not any(c["uid"] == "u-dois" for c in so_um)
    # mais recente (2099) primeiro por ordem crescente de retorno decrescente
    assert so_um[0]["id"] == "cob-antiga"


def test_confirmar_ativa_plano_pago(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    doc = pixbilling.gerar_cobranca("u-um")
    renovado = {}
    monkeypatch.setattr("pixbilling.plano.renovar_assinatura", lambda uid: renovado.update(uid=uid) or True)
    novo = pixbilling.confirmar_cobranca(doc["id"])
    assert novo and novo["status"] == "confirmado"
    assert renovado == {"uid": "u-um"}
    assert pixbilling.confirmar_cobranca(doc["id"]) is None  # já confirmada


def test_gerar_cobranca_guarda_nome_email_cpf(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    doc = pixbilling.gerar_cobranca("u-um", cpf="52998224725", nome="Titular Teste", email="titular@exemplo.com")
    assert doc["nome"] == "Titular Teste"
    assert doc["email"] == "titular@exemplo.com"
    assert doc["cpf"] == "52998224725"


def test_comprovante_enviado_na_confirmacao(tmp_path, monkeypatch):
    """Webhook OU confirmação manual: confirmar_cobranca sempre envia o comprovante."""
    _caminho_tmp(tmp_path, monkeypatch)
    doc = pixbilling.gerar_cobranca("u-um", nome="Titular", email="titular@exemplo.com")
    monkeypatch.setattr("pixbilling.plano.renovar_assinatura", lambda uid: True)
    enviados = []

    def _fake_envia(para, assunto, corpo, corpo_html=None):
        enviados.append((para, assunto, corpo, corpo_html))
        return True

    monkeypatch.setattr("pixbilling.notificacoes.enviar_email", _fake_envia)
    pixbilling.confirmar_cobranca(doc["id"])
    assert len(enviados) == 1
    para, assunto, _, html = enviados[0]
    assert para == "titular@exemplo.com"
    assert "Comprovante" in assunto
    assert "19,99" in html
    assert "Titular" in html


def test_comprovante_sem_email_nao_quebra_confirmacao(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    doc = pixbilling.gerar_cobranca("u-um")
    monkeypatch.setattr("pixbilling.plano.renovar_assinatura", lambda uid: True)
    monkeypatch.setattr(
        "pixbilling.notificacoes.enviar_email",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("não deveria enviar")),
    )
    novo = pixbilling.confirmar_cobranca(doc["id"])
    assert novo and novo["status"] == "confirmado"


def test_falha_no_envio_nao_quebra_confirmacao(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    doc = pixbilling.gerar_cobranca("u-um", email="titular@exemplo.com")
    monkeypatch.setattr("pixbilling.plano.renovar_assinatura", lambda uid: True)
    monkeypatch.setattr(
        "pixbilling.notificacoes.enviar_email",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("SMTP fora do ar")),
    )
    novo = pixbilling.confirmar_cobranca(doc["id"])
    assert novo and novo["status"] == "confirmado"


def test_cancelar_nao_ativa_plano(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    doc = pixbilling.gerar_cobranca("u-um")
    cancelado = pixbilling.cancelar_cobranca(doc["id"])
    assert cancelado and cancelado["status"] == "cancelado"
    assert pixbilling.cancelar_cobranca(doc["id"]) is None  # não abre mais


def test_estorno_volta_a_basic(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    doc = pixbilling.gerar_cobranca("u-um")
    pixbilling.confirmar_cobranca(doc["id"])
    pedido = pixbilling.solicitar_estorno(doc["id"], motivo="arrependido")
    assert pedido and pedido["status"] == "estorno"
    assert pixbilling.estornos()[0]["id"] == doc["id"]
    voltou = {}
    monkeypatch.setattr("pixbilling.plano.encerrar_assinatura", lambda uid: voltou.update(uid=uid) or True)
    estornado = pixbilling.estornar(doc["id"])
    assert estornado and estornado["status"] == "estornado"
    assert voltou == {"uid": "u-um"}
    assert pixbilling.estornar(doc["id"]) is None  # já estornado


def test_solicitar_estorno_requer_confirmado(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    doc = pixbilling.gerar_cobranca("u-um")
    assert pixbilling.solicitar_estorno(doc["id"]) is None  # ainda aguardando


def test_payload_configurado_usa_pix(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    monkeypatch.setattr(pix, "payload_configurado", lambda: "00020126360014br.gov.bcb.pix6304BEEF")
    assert pixbilling.payload_pix() == "00020126360014br.gov.bcb.pix6304BEEF"


def test_payload_prioriza_pix_copia_plano(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    monkeypatch.setattr(pix, "_ler", lambda nome: "CODIGO_ASSINATURA_ITAU" if nome == "PIX_COPIA_PLANO" else "")
    monkeypatch.setattr(pix, "payload_configurado", lambda: "PAYLOAD_PADRAO")
    assert pixbilling.payload_pix() == "CODIGO_ASSINATURA_ITAU"


def test_payload_cai_no_pix_copia_geral(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    monkeypatch.setattr(pix, "_ler", lambda nome: "COPIA_GERAL_DOACAO" if nome == "PIX_COPIA" else "")
    monkeypatch.setattr(pix, "payload_configurado", lambda: "PAYLOAD_PADRAO")
    assert pixbilling.payload_pix() == "COPIA_GERAL_DOACAO"


def test_payload_configurado_se_nada_especifico(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    monkeypatch.setattr(pix, "_ler", lambda nome: "")
    monkeypatch.setattr(pix, "payload_configurado", lambda: "PAYLOAD_PADRAO")
    assert pixbilling.payload_pix() == "PAYLOAD_PADRAO"


def test_payload_sem_pix_retorna_vazio(tmp_path, monkeypatch):
    _caminho_tmp(tmp_path, monkeypatch)
    monkeypatch.setattr(pix, "payload_configurado", lambda: "")
    assert pixbilling.payload_pix() == ""


def test_status_rotulo():
    assert pixbilling.status_rotulo("aguardando") == "Aguardando pagamento"
    assert pixbilling.status_rotulo("confirmado") == "Pago"
    assert pixbilling.status_rotulo("estorno") == "Estorno solicitado"
    assert pixbilling.status_rotulo("estornado") == "Estornado"
    assert pixbilling.status_rotulo("cancelado") == "Cancelado"
    assert pixbilling.status_rotulo("x") == "x"