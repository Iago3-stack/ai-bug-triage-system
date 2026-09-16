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

    with pytest.raises(_ImagemHeicSemSuporte):
        ui_comum._abrir_imagem_enviada(_arquivo("foto.heic", b"fake"))