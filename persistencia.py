import json
import os
import pathlib
import uuid
from datetime import date, datetime

_RAIZ = pathlib.Path(__file__).resolve().parent
_ARQUIVO_PADRAO = _RAIZ / "data" / "historico.jsonl"


def _caminho() -> pathlib.Path:
    return pathlib.Path(os.environ.get("PERSISTENCIA_ARQUIVO", str(_ARQUIVO_PADRAO)))


def _linha(registro: dict) -> str:
    return json.dumps(registro, ensure_ascii=False, sort_keys=True)


def _reescrever(registros: list[dict]) -> None:
    caminho = _caminho()
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(".jsonl.tmp")
    with temporario.open("w", encoding="utf-8") as f:
        for registro in registros:
            f.write(_linha(registro) + "\n")
    temporario.replace(caminho)


def registrar_triagem(dados: dict) -> dict:
    agora = datetime.now().astimezone()
    registro = {
        "id": uuid.uuid4().hex[:12],
        "data_hora": agora.isoformat(timespec="seconds"),
        "data": agora.date().isoformat(),
    }
    registro.update(dados)
    caminho = _caminho()
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("a", encoding="utf-8") as f:
        f.write(_linha(registro) + "\n")
    return registro


def carregar_registros() -> list[dict]:
    caminho = _caminho()
    if not caminho.exists():
        return []
    with caminho.open(encoding="utf-8") as f:
        return [json.loads(linha) for linha in f if linha.strip()]


def registros_por_data(data_iso: str) -> list[dict]:
    return [r for r in carregar_registros() if r.get("data") == data_iso]


def datas_disponiveis() -> list[str]:
    return sorted({r.get("data", "") for r in carregar_registros()}, reverse=True)


def registrar_exportacao_jira(chave: str, url: str) -> bool:
    """Vincula a issue do Jira ao último registro persistido."""
    registros = carregar_registros()
    if not registros:
        return False
    registros[-1]["jira_key"] = chave
    registros[-1]["jira_url"] = url
    _reescrever(registros)
    return True


def excluir_antigos(dias: int) -> int:
    """Remove registros mais velhos que `dias`. Retorna quantos foram removidos."""
    if dias <= 0:
        return 0
    hoje = date.today()
    registros = carregar_registros()
    permanecem = []
    removidos = 0
    for registro in registros:
        try:
            data_registro = date.fromisoformat(registro["data"])
        except (KeyError, ValueError):
            permanecem.append(registro)
            continue
        if (hoje - data_registro).days > dias:
            removidos += 1
        else:
            permanecem.append(registro)
    if removidos:
        _reescrever(permanecem)
    return removidos