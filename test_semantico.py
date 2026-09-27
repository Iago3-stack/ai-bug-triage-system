# Testes do motor semântico (semantico.py). Herméticos: nunca tocam rede nem
# carregam o ONNX real (135MB) — simulam dependências ausentes, caminhos e cache.

from pathlib import Path

import numpy as np
import pytest


# --- Fallback sem dependências ----------------------------------------------
def test_semantico_indisponivel_sem_dependencias(monkeypatch):
    import semantico

    monkeypatch.setattr(semantico, "ort", None)
    assert not semantico.disponivel()
    r = semantico.analisar("o usuário está frustrado")
    assert r["motor"].endswith("(indisponível)")
    assert r["score"] == 0.0
    assert r["gravidade"] == "NORMAL ✅"


def test_motivo_indisponivel_reporta_causa(monkeypatch):
    import semantico

    monkeypatch.setattr(semantico, "ort", None)
    assert "onnxruntime" in semantico.motivo_indisponivel()


# --- Resolução de pasta do modelo ------------------------------------------
def test_dir_modelo_prioriza_semantico_dir(monkeypatch, tmp_path):
    import semantico

    semantico._ORT_SESSION = None
    semantico._VETORES_PROTOTIPOS = None
    monkeypatch.setenv("SEMANTICO_DIR", str(tmp_path))
    monkeypatch.setattr(semantico, "_DEV_DIR", tmp_path / "inexistente")
    assert semantico._dir_modelo() == tmp_path


def test_dir_modelo_cai_no_cache_quando_sem_fonte(monkeypatch, tmp_path):
    import semantico

    semantico._ORT_SESSION = None
    semantico._VETORES_PROTOTIPOS = None
    monkeypatch.delenv("SEMANTICO_DIR", raising=False)
    monkeypatch.setattr(semantico, "_DEV_DIR", tmp_path / "inexistente")
    assert semantico._dir_modelo() == semantico._CACHE_DIR


def test_dir_modelo_usa_dev_local_quando_existe(monkeypatch, tmp_path):
    import semantico

    semantico._ORT_SESSION = None
    semantico._VETORES_PROTOTIPOS = None
    monkeypatch.delenv("SEMANTICO_DIR", raising=False)
    monkeypatch.setattr(semantico, "_DEV_DIR", tmp_path)
    (tmp_path / "model_int8.onnx").touch()
    (tmp_path / "tokenizer.json").touch()
    assert semantico._dir_modelo() == tmp_path


# --- garantir_modelo: dev local não baixa; cache baixa uma vez -----------------
def test_modelo_ja_pronto_detecta_arquivos(monkeypatch, tmp_path):
    import semantico

    semantico._ORT_SESSION = None
    semantico._VETORES_PROTOTIPOS = None
    monkeypatch.setattr(semantico, "_DEV_DIR", tmp_path)
    assert not semantico.modelo_ja_pronto()
    (tmp_path / "model_int8.onnx").touch()
    (tmp_path / "tokenizer.json").touch()
    assert semantico.modelo_ja_pronto()


def test_garantir_modelo_dev_local_nao_baixa(monkeypatch, tmp_path):
    import semantico

    semantico._ORT_SESSION = None
    semantico._VETORES_PROTOTIPOS = None
    (tmp_path / "model_int8.onnx").touch()
    (tmp_path / "tokenizer.json").touch()

    def _nao_deveria_baixar(cache_dir):
        raise AssertionError("não deveria baixar em dev local")

    monkeypatch.setattr(semantico, "_DEV_DIR", tmp_path)
    monkeypatch.setattr(semantico, "_baixar", _nao_deveria_baixar)
    assert semantico.garantir_modelo()


def test_garantir_modelo_cache_baixa_uma_vez(monkeypatch, tmp_path):
    import semantico

    semantico._ORT_SESSION = None
    semantico._VETORES_PROTOTIPOS = None
    chamadas = []

    def _baixar(cache_dir):
        chamadas.append(cache_dir)
        (cache_dir / "model_int8.onnx").touch()
        (cache_dir / "tokenizer.json").touch()

    monkeypatch.delenv("SEMANTICO_DIR", raising=False)
    monkeypatch.setattr(semantico, "_DEV_DIR", tmp_path / "inexistente")
    monkeypatch.setattr(semantico, "_CACHE_DIR", tmp_path)
    monkeypatch.setattr(semantico, "_baixar", _baixar)

    assert semantico.garantir_modelo()
    assert semantico.garantir_modelo()
    assert len(chamadas) == 1


def test_garantir_modelo_falha_nao_quebra(monkeypatch, tmp_path):
    import semantico

    semantico._ORT_SESSION = None
    semantico._VETORES_PROTOTIPOS = None

    def _baixar_quebra(cache_dir):
        raise OSError("sem rede")

    monkeypatch.delenv("SEMANTICO_DIR", raising=False)
    monkeypatch.setattr(semantico, "_DEV_DIR", tmp_path / "inexistente")
    monkeypatch.setattr(semantico, "_CACHE_DIR", tmp_path)
    monkeypatch.setattr(semantico, "_baixar", _baixar_quebra)
    assert not semantico.garantir_modelo()


# --- analisar: ramo semântico (sem modelo real, só aritmética) ---------------
def test_analisar_usa_vectores_semanticos(monkeypatch):
    import semantico

    monkeypatch.setattr(semantico, "_carregar", lambda: True)
    monkeypatch.setattr(
        semantico, "_VETORES_PROTOTIPOS",
        {desc: np.array([1.0, 0.0]) for desc, _ in semantico._PROTOTIPOS},
    )
    monkeypatch.setattr(semantico, "_vetor", lambda texto: np.array([1.0, 0.0]))

    r = semantico.analisar("pagamento falhando sem parar")
    assert r["motor"] == semantico.MOTOR
    assert r["score"] == -2.0
    assert r["gravidade"] == "CRÍTICA 🚨"
    assert "semântica ≈ 1.00" in r["fatores"][0]


# --- ensemble: o caminho de produção do Premium -------------------------------
def test_ensemble_media_lexico_e_semantico(monkeypatch):
    import semantico

    monkeypatch.setattr(semantico, "analisar", lambda texto: {
        "score": -2.0,
        "gravidade": "CRÍTICA 🚨",
        "sentimento": "Frustrado/Urgente",
        "fatores": ["semântica ≈ 0.95"],
        "motor": semantico.MOTOR,
    })
    lex = {"score": -1.0, "gravidade": "MÉDIA ⚠️", "sentimento": "X",
           "fatores": ["trava"], "motor": "Léxico"}
    r = semantico.ensemble("qualquer relato", lex)

    assert r["score"] == -1.5
    assert r["gravidade"] == "MÉDIA ⚠️"
    assert r["sentimento"] == "X"  # o sentimento do léxico é preservado
    assert r["fatores"] == ["trava", "semântica ≈ 0.95"]
    assert "ensemble" in r["motor"]


def test_ensemble_critica_no_limite(monkeypatch):
    import semantico

    monkeypatch.setattr(semantico, "analisar", lambda texto: {
        "score": -2.0, "gravidade": "CRÍTICA 🚨", "sentimento": "F",
        "fatores": [], "motor": semantico.MOTOR,
    })
    lex = {"score": -2.0, "gravidade": "CRÍTICA 🚨", "sentimento": "X",
           "fatores": [], "motor": "Léxico"}
    assert semantico.ensemble("x", lex)["gravidade"] == "CRÍTICA 🚨"


def test_ensemble_devolve_lexico_quando_semantico_indisponivel(monkeypatch):
    import semantico

    monkeypatch.setattr(semantico, "analisar", lambda texto: {
        "score": 0.0, "gravidade": "NORMAL ✅", "sentimento": "Neutro/Fallback",
        "fatores": [], "motor": f"{semantico.MOTOR} (indisponível)",
    })
    lex = {"score": -1.2, "gravidade": "MÉDIA ⚠️", "sentimento": "X",
           "fatores": ["trava"], "motor": "Léxico"}
    assert semantico.ensemble("x", lex) is lex


def test_ensemble_fallback_no_caminho_real_sem_libs(monkeypatch):
    """Fallback testado no caminho de verdade: sem onnxruntime instalado.

    analisar() devolve o marcador "(indisponível)" e o ensemble devolve o
    léxico intacto — é o que mantém o Premium funcionando se o modelo ou as
    libs quebrarem na nuvem.
    """
    import semantico

    monkeypatch.setattr(semantico, "ort", None)
    monkeypatch.setattr(semantico, "_ORT_SESSION", None)
    monkeypatch.setattr(semantico, "_VETORES_PROTOTIPOS", None)
    assert semantico.analisar("qualquer relato")["motor"].endswith("(indisponível)")

    lex = {"score": -1.2, "gravidade": "MÉDIA ⚠️", "sentimento": "X",
           "fatores": ["trava"], "motor": "Léxico"}
    assert semantico.ensemble("qualquer relato", lex) is lex


# --- download do Release: tag fixada + tamanho exato ---------------------------
def test_url_do_release_fixa_por_tag():
    import semantico

    for nome, (url, tamanho) in semantico._ARQUIVOS.items():
        assert f"/releases/download/{semantico._TAG}/" in url
        assert "/latest/" not in url  # latest poderia apontar p/ outro release
        assert url.endswith(f"/{nome}")
        assert tamanho > 0


def test_baixar_instalar_e_reusar_arquivo_do_tamanho_certo(monkeypatch, tmp_path):
    import semantico

    baixados = []

    def _fake_urlretrieve(url, destino):
        baixados.append(url)
        Path(destino).write_bytes(b"x" * 10)

    monkeypatch.setattr(semantico, "_ARQUIVOS", {"modelo.onnx": ("http://x/modelo.onnx", 10)})
    monkeypatch.setattr(semantico.urllib.request, "urlretrieve", _fake_urlretrieve)

    assert semantico._baixar(tmp_path) is True
    assert (tmp_path / "modelo.onnx").read_bytes() == b"x" * 10
    assert semantico._baixar(tmp_path) is True  # já está no tamanho: não rebaixa
    assert len(baixados) == 1


def test_baixar_rejeita_tamanho_divergente(monkeypatch, tmp_path):
    """Download truncado não pode ser instalado: some e devolve False."""
    import semantico

    def _fake_urlretrieve(url, destino):
        Path(destino).write_bytes(b"x" * 3)  # tamanho errado

    monkeypatch.setattr(semantico, "_ARQUIVOS", {"modelo.onnx": ("http://x/modelo.onnx", 10)})
    monkeypatch.setattr(semantico.urllib.request, "urlretrieve", _fake_urlretrieve)

    assert semantico._baixar(tmp_path) is False
    assert not (tmp_path / "modelo.onnx").exists()
    assert not (tmp_path / "modelo.onnx.part").exists()


def test_baixar_limpa_parcial_quando_rede_quebra(monkeypatch, tmp_path):
    import semantico

    def _fake_urlretrieve(url, destino):
        Path(destino).write_bytes(b"x" * 5)  # began a escrever...
        raise OSError("conexão caiu")

    monkeypatch.setattr(semantico, "_ARQUIVOS", {"modelo.onnx": ("http://x/modelo.onnx", 10)})
    monkeypatch.setattr(semantico.urllib.request, "urlretrieve", _fake_urlretrieve)

    with pytest.raises(OSError):
        semantico._baixar(tmp_path)
    assert not (tmp_path / "modelo.onnx.part").exists()
    assert not (tmp_path / "modelo.onnx").exists()


def test_garantir_modelo_cache_nao_instala_arquivo_truncado(monkeypatch, tmp_path):
    """Caminho completo: download truncado -> app fica no léxico (retorna False)."""
    import semantico

    def _fake_urlretrieve(url, destino):
        Path(destino).write_bytes(b"x" * 7)

    monkeypatch.delenv("SEMANTICO_DIR", raising=False)
    monkeypatch.setattr(semantico, "_DEV_DIR", tmp_path / "inexistente")
    monkeypatch.setattr(semantico, "_CACHE_DIR", tmp_path)
    monkeypatch.setattr(semantico, "_ARQUIVOS", {"modelo.onnx": ("http://x/modelo.onnx", 10)})
    monkeypatch.setattr(semantico.urllib.request, "urlretrieve", _fake_urlretrieve)

    assert semantico.garantir_modelo() is False
    assert not (tmp_path / "modelo.onnx").exists()