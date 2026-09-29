# Upload de foto do perfil: JPG/PNG/WebP abrem; HEIC sem pillow-heif dá recado amigável.
import io
import types

import pytest
from PIL import Image

import ui_comum


def _arquivo(nome: str, dados: bytes) -> types.SimpleNamespace:
    return types.SimpleNamespace(name=nome, getvalue=lambda: dados)


def test_abrir_png(tmp_path):
    buf = io.BytesIO()
    Image.new("RGB", (10, 10)).save(buf, format="PNG")
    img = ui_comum._abrir_imagem_enviada(_arquivo("foto.png", buf.getvalue()))
    assert img.size == (10, 10)


def test_abrir_jpeg(tmp_path):
    buf = io.BytesIO()
    Image.new("RGB", (12, 8)).save(buf, format="JPEG")
    img = ui_comum._abrir_imagem_enviada(_arquivo("foto.jpg", buf.getvalue()))
    assert img.size == (12, 8)


def test_heic_sem_pillow_heif_da_recado(tmp_path):
    from ui_comum import _ImagemHeicSemSuporte

    dados = b"\x00\x00\x00\x18ftypheic" + b"\x00" * 8 + b"\x00" * 64
    with pytest.raises(_ImagemHeicSemSuporte):
        ui_comum._abrir_imagem_enviada(_arquivo("foto.heic", dados))


def test_magia_reconhece_formatos():
    buf_png, buf_jpg, buf_webp = io.BytesIO(), io.BytesIO(), io.BytesIO()
    Image.new("RGB", (4, 4)).save(buf_png, format="PNG")
    Image.new("RGB", (4, 4)).save(buf_jpg, format="JPEG")
    Image.new("RGB", (4, 4)).save(buf_webp, format="WEBP")
    assert ui_comum._tem_magia_de_imagem(buf_png.getvalue()) is True
    assert ui_comum._tem_magia_de_imagem(buf_jpg.getvalue()) is True
    assert ui_comum._tem_magia_de_imagem(buf_webp.getvalue()) is True
    heic = b"\x00\x00\x00\x18ftypheic" + b"\x00" * 8
    assert ui_comum._tem_magia_de_imagem(heic) is True


def test_magia_rejeita_arquivo_disfarcado():
    assert ui_comum._tem_magia_de_imagem(b"<script>alert(1)</script>") is False
    assert ui_comum._tem_magia_de_imagem(b"") is False
    assert ui_comum._tem_magia_de_imagem(b"\x89PNG\r\n") is False


def test_abrir_rejeita_conteudo_fingindo_ser_png():
    with pytest.raises(ValueError):
        ui_comum._abrir_imagem_enviada(_arquivo("foto.png", b"<script>alert(1)</script>"))


def test_abrir_rejeita_imagem_grande():
    buf = io.BytesIO()
    Image.new("RGB", (ui_comum._MAX_AVATAR_LADO + 1, 2)).save(buf, format="PNG")
    with pytest.raises(ValueError, match="dimens"):
        ui_comum._abrir_imagem_enviada(_arquivo("gigante.png", buf.getvalue()))


def test_deep_link_aba_termos():
    assert ui_comum._aba_para_deep_link("legal", "termos") == "termos"


def test_deep_link_aba_privacidade():
    assert ui_comum._aba_para_deep_link("legal", "privacidade") == "privacidade"


def test_deep_link_padrao_termos_quando_aba_vazia():
    assert ui_comum._aba_para_deep_link("legal", "") == "termos"


def test_deep_link_aceita_lista_de_abas():
    assert ui_comum._aba_para_deep_link("legal", ["privacidade", "termos"]) == "privacidade"


def test_deep_link_ignora_outras_paginas():
    assert ui_comum._aba_para_deep_link("triagem", "termos") is None
    assert ui_comum._aba_para_deep_link("inicio", "privacidade") is None
    assert ui_comum._aba_para_deep_link(None, "termos") is None


def _js_do_rolar_topo(monkeypatch) -> str:
    """Captura o HTML que `_rolar_topo` injeta, sem renderizar o Streamlit."""
    capturado = {}

    def fake_html(html, height=None, **kwargs):
        capturado["html"] = html
        capturado["height"] = height

    monkeypatch.setattr(ui_comum.components, "html", fake_html)
    ui_comum._rolar_topo()
    assert capturado["height"] == 0
    return capturado["html"]


def test_rolar_topo_cede_ao_primeiro_gesto_do_usuario(monkeypatch):
    """O reset de scroll para no primeiro gesto: a pessoa vence o timer.

    Regressão do `setInterval(400ms) × 12`, que segura o topo por 4,8s e
    produz uma dente-de-serra de 400ms para quem rola na página Legal.
    """
    js = _js_do_rolar_topo(monkeypatch)
    for evento in ("wheel", "touchstart", "keydown", "mousedown"):
        assert evento in js, f"falta escutar {evento} para liberar o scroll"
    assert "livre" in js
    assert "setInterval" not in js, "setInterval fixo volta a brigar com o usuario"
    assert "setTimeout(sobe,60)" in js


def test_rolar_topo_ainda_reseta_o_container(monkeypatch):
    """A correção não pode virar no-op: o topo continua sendo forçado."""
    js = _js_do_rolar_topo(monkeypatch)
    assert 'stMain' in js
    assert "m.scrollTop=0" in js