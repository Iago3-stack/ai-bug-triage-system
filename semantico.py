# Motor de Triagem Semântico (BERTabaporu ONNX int8, 100% offline e determinístico).
# Camada sênior do léxico (triagem.py): usa embeddings semânticos reais para
# entender intenção/contexto. Premium (plano.pago()) usa este motor; Basic fica
# no léxico. A API analisar() devolve o mesmo dict de triagem.triar().
#
# O modelo (model_int8.onnx, 135MB) NÃO fica no repositório (GitHub não aceita
# arquivo >100MB): é baixado do GitHub Release na 1ª execução e cacheado em
# ~/.cache/abt/. Em dev, se a pasta local do autor existir, usa direto nela.

import os
import unicodedata
import urllib.request
from pathlib import Path

import numpy as np

try:
    import onnxruntime as ort
    from tokenizers import Tokenizer
except Exception:  # pragma: no cover - ambiente sem as libs
    ort = None
    Tokenizer = None

MOTOR = "Semântico BERTabaporu (ONNX int8, local)"

_BASE_URL = "https://github.com/Iago3-stack/ai-bug-triage-system/releases/latest/download"
_MODELO_URL = _BASE_URL + "/model_int8.onnx"
_TOKENIZER_URL = _BASE_URL + "/tokenizer.json"

_CACHE_DIR = Path(os.path.expanduser("~/.cache/abt"))
_DEV_DIR = Path(os.path.expanduser("~/Documentos/semantico_nlp/modelo/onnx"))

MAX_TOKENS = 128

_PROTOTIPOS = [
    ("o usuário está frustrado e tentou pagar várias vezes", -2.0),
    ("o sistema está fora do ar e ninguém consegue acessar", -2.0),
    ("os dados foram apagados e o cliente precisa restaurar", -2.0),
    ("houve vazamento de dados sensíveis ou insegurança", -2.0),
    ("a cobrança foi duplicada e o valor está errado", -1.8),
    ("o usuário não conseguiu entrar na conta e ficou bravo", -1.8),
    ("o login falhou e o usuário não consegue entrar", -1.5),
    ("a página não carrega e mostra erro de servidor", -1.5),
    ("o botão não responde e a operação não conclui", -1.2),
    ("o aplicativo apresenta um pequeno atraso de resposta", -0.4),
    ("a interface poderia ser mais moderna e bonita", 0.2),
    ("o usuário elogiou e os testes passaram normalmente", 0.8),
]

_ORT_SESSION = None
_TOKENIZER_OBJ = None
_VETORES_PROTOTIPOS = None
_ERRO = None


def _dir_modelo() -> Path:
    """Resolve a pasta do modelo: SEMANTICO_DIR > dev local do autor > cache."""
    env = os.environ.get("SEMANTICO_DIR")
    if env:
        caminho = Path(env)
        if caminho.is_dir():
            return caminho
    if _DEV_DIR.is_dir():
        return _DEV_DIR
    return _CACHE_DIR


def _baixar(cache_dir: Path) -> None:
    """Baixa model_int8.onnx + tokenizer.json do Release para o cache (uma vez)."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    for nome, url in (("model_int8.onnx", _MODELO_URL), ("tokenizer.json", _TOKENIZER_URL)):
        destino = cache_dir / nome
        if destino.exists() and destino.stat().st_size > 0:
            continue
        temporario = destino.with_suffix(destino.suffix + ".part")
        urllib.request.urlretrieve(url, temporario)
        temporario.replace(destino)


def modelo_ja_pronto() -> bool:
    """True se modelo + tokenizer já estão no lugar resolvido (não baixa nada)."""
    pasta = _dir_modelo()
    return (pasta / "model_int8.onnx").exists() and (pasta / "tokenizer.json").exists()


def garantir_modelo() -> bool:
    """Garante que modelo + tokenizer existem (baixa do Release se for o cache).

    Só chama a rede quando a pasta resolve para o cache (~/.cache/abt), nunca em
    dev local. Não quebra o app: retorna False e o chamador segue no léxico.
    """
    try:
        if modelo_ja_pronto():
            return True
        pasta = _dir_modelo()
        if pasta == _CACHE_DIR:
            _baixar(_CACHE_DIR)
            return modelo_ja_pronto()
        return False
    except Exception:
        return False


def _carregar():
    global _ORT_SESSION, _TOKENIZER_OBJ, _VETORES_PROTOTIPOS, _ERRO
    if ort is None:
        _ERRO = "dependências ausentes (onnxruntime/tokenizers)"
        return False
    if _ORT_SESSION is not None:
        return True
    pasta = _dir_modelo()
    modelo = pasta / "model_int8.onnx"
    tokenizer = pasta / "tokenizer.json"
    if not (modelo.exists() and tokenizer.exists()):
        _ERRO = f"modelo não encontrado em {pasta} (rode garantir_modelo())"
        return False
    try:
        _ORT_SESSION = ort.InferenceSession(str(modelo), providers=["CPUExecutionProvider"])
        _TOKENIZER_OBJ = Tokenizer.from_file(str(tokenizer))
        _TOKENIZER_OBJ.enable_truncation(max_length=MAX_TOKENS)
        _TOKENIZER_OBJ.enable_padding(pad_id=0, pad_token="[PAD]")
        _VETORES_PROTOTIPOS = {desc: _vetor(desc) for desc, _ in _PROTOTIPOS}
        return True
    except Exception as e:
        _ORT_SESSION = None
        _ERRO = f"{type(e).__name__}: {e}"
        return False


def disponivel() -> bool:
    try:
        return _carregar()
    except Exception:
        return False


def motivo_indisponivel() -> str:
    _carregar()
    return _ERRO or ""


def _vetor(descricao):
    enc = _TOKENIZER_OBJ.encode(descricao)
    ids = np.array([enc.ids], dtype=np.int64)
    mask = np.array([enc.attention_mask], dtype=np.int64)
    seg = np.zeros_like(ids, dtype=np.int64)
    saida = _ORT_SESSION.run(
        ["last_hidden_state"],
        {"input_ids": ids, "attention_mask": mask, "token_type_ids": seg},
    )[0]
    v = saida[0][0]
    norma = np.linalg.norm(v)
    return v / norma if norma > 0 else v


def _cosseno(a, b):
    return float(np.dot(a, b))


def _carregar_texto(descricao):
    return unicodedata.normalize("NFC", descricao.lower()).strip()


def analisar(descricao):
    """Classifica a severidade de um relato usando embeddings semânticos.

    Mesmo formato de triagem.triar(): score, gravidade, sentimento, fatores, motor.
    """
    if not disponivel():
        return {
            "score": 0.0,
            "gravidade": "NORMAL ✅",
            "sentimento": "Neutro/Fallback",
            "fatores": [],
            "motor": f"{MOTOR} (indisponível)",
        }

    texto = _carregar_texto(descricao)
    vetor = _vetor(texto)

    if _VETORES_PROTOTIPOS is None:
        return {
            "score": 0.0,
            "gravidade": "NORMAL ✅",
            "sentimento": "Neutro/Calmo",
            "fatores": [],
            "motor": MOTOR,
        }

    resultados = []
    for prot_desc, peso in _PROTOTIPOS:
        sim = _cosseno(vetor, _VETORES_PROTOTIPOS[prot_desc])
        resultados.append((sim, peso, prot_desc))
    resultados.sort(reverse=True, key=lambda r: r[0])
    top = resultados[0]

    score = float(top[1])
    fatores = [f"semântica ≈ {top[0]:.2f} → “{top[2][:48]}”"]

    if score <= -2.0:
        gravidade = "CRÍTICA 🚨"
        sentimento = "Frustrado/Urgente"
    elif score <= -0.5:
        gravidade = "MÉDIA ⚠️"
        sentimento = "Negativo/Insatisfeito"
    elif score >= 0.5:
        gravidade = "NORMAL ✅"
        sentimento = "Positivo/Satisfeito"
    else:
        gravidade = "NORMAL ✅"
        sentimento = "Neutro/Calmo"

    return {
        "score": score,
        "gravidade": gravidade,
        "sentimento": sentimento,
        "fatores": fatores,
        "motor": MOTOR,
    }


def ensemble(descricao, resultado_lexico):
    """Soma o semântico ao léxico (média dos scores) — o Premium usa este caminho.

    Medido nos 30 relatos rotulados (avaliar_motores.py): léxico 61% estrito,
    semântico sozinho 39%, ensemble 74%. Então o semântico NUNCA substitui o
    léxico — ele entra como segundo sinal. Se o semântico estiver indisponível,
    devolve o léxico intacto (fallback).
    """
    sem = analisar(descricao)
    if sem["motor"].endswith("(indisponível)"):
        return resultado_lexico

    score_lexico = float(resultado_lexico.get("score", 0.0))
    score = (score_lexico + float(sem["score"])) / 2

    if score <= -2.0:
        gravidade = "CRÍTICA 🚨"
    elif score <= -0.5:
        gravidade = "MÉDIA ⚠️"
    else:
        gravidade = "NORMAL ✅"

    return {
        "score": score,
        "gravidade": gravidade,
        "sentimento": resultado_lexico.get("sentimento", "Neutro/Calmo"),
        "fatores": list(resultado_lexico.get("fatores", [])) + sem["fatores"],
        "motor": f"{MOTOR} + léxico (ensemble)",
    }


if __name__ == "__main__":
    casos = [
        "O usuário está tentando pagar e a tela fica carregando para sempre",
        "O sistema travou e perdeu todos os dados do cliente",
        "A interface está um pouco lenta mas funciona",
        "Cara, to muito bravo, não consigo nem acessar minha conta",
    ]
    print("modelo:", "disponível" if garantir_modelo() else motivo_indisponivel())
    for c in casos:
        r = analisar(c)
        print(f"• {c}\n  → {r['gravidade']} | score={r['score']:.2f} | "
              f"{r['fatores'][0] if r['fatores'] else '—'} | {r['motor']}")