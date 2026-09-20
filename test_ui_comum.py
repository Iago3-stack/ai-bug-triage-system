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