import json
import os
import pathlib
import uuid
from datetime import date, datetime
from zoneinfo import ZoneInfo

import nuvem_supabase
import plano

_RAIZ = pathlib.Path(__file__).resolve().parent
_ARQUIVO_PADRAO = _RAIZ / "data" / "historico.jsonl"
_FUSO = ZoneInfo(os.environ.get("PERSISTENCIA_FUSO", "America/Sao_Paulo"))


def _usar_nuvem() -> bool:
    """Nuvem ativa quando configurada; JSONL é sempre o fallback padrão."""
    if os.environ.get("PERSISTENCIA_BACKEND") == "jsonl":
        return False
    if os.environ.get("PERSISTENCIA_ARQUIVO"):
        # Caminho local explícito (testes/uso local) nunca depende da rede.
        return False
    return nuvem_supabase.disponivel()


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


def _salvar_jsonl(registro: dict) -> dict:
    caminho = _caminho()
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("a", encoding="utf-8") as f:
        f.write(_linha(registro) + "\n")
    return registro


def _ler_jsonl() -> list[dict]:
    caminho = _caminho()
    if not caminho.exists():
        return []
    with caminho.open(encoding="utf-8") as f:
        return [json.loads(linha) for linha in f if linha.strip()]


def registrar_triagem(dados: dict) -> dict:
    agora = datetime.now(_FUSO)
    registro = {
        "id": uuid.uuid4().hex[:12],
        "data_hora": agora.isoformat(timespec="seconds"),
        "data": agora.date().isoformat(),
    }
    registro.update(dados)
    plano.integrar_tenant(registro)
    if _usar_nuvem():
        try:
            return nuvem_supabase.registrar_triagem(registro)
        except Exception:
            # Failover: nuvem indisponível não pode perder a triagem — grava no local.
            return _salvar_jsonl(registro)
    return _salvar_jsonl(registro)


def _filtrar_tenant(registros: list[dict]) -> list[dict]:
    """Mantém só o que é do tenant atual (registros antigos sem tenant = global)."""
    return [r for r in registros if plano.dados_do_tenant(r)]


def carregar_registros() -> list[dict]:
    if _usar_nuvem():
        try:
            return _filtrar_tenant(nuvem_supabase.carregar_registros())
        except Exception:
            pass
    return _filtrar_tenant(_ler_jsonl())


def registros_por_data(data_iso: str) -> list[dict]:
    if _usar_nuvem():
        try:
            return _filtrar_tenant(nuvem_supabase.registros_por_data(data_iso))
        except Exception:
            pass
    return [r for r in _filtrar_tenant(_ler_jsonl()) if r.get("data") == data_iso]


def datas_disponiveis() -> list[str]:
    if _usar_nuvem():
        try:
            return sorted(
                {r.get("data", "") for r in _filtrar_tenant(nuvem_supabase.carregar_registros())},
                reverse=True,
            )
        except Exception:
            pass
    return sorted({r.get("data", "") for r in _filtrar_tenant(_ler_jsonl())}, reverse=True)


def registrar_exportacao_jira(chave: str, url: str) -> bool:
    """Vincula a issue do Jira ao último registro persistido."""
    if _usar_nuvem():
        try:
            return nuvem_supabase.registrar_exportacao_jira(chave, url)
        except Exception:
            pass
    registros = _ler_jsonl()
    if not registros:
        return False
    registros[-1]["jira_key"] = chave
    registros[-1]["jira_url"] = url
    _reescrever(registros)
    return True


def registrar_resolucao(registro_id: str, texto: str) -> bool:
    """Guarda 'como o caso foi resolvido' no registro — alimenta o RAG.

    Retorna True se o registro existir e a resolução for gravada (nuvem ou
    JSONL local, com failover automático).
    """
    if _usar_nuvem():
        try:
            return nuvem_supabase.registrar_resolucao(registro_id, texto)
        except Exception:
            pass
    registros = _ler_jsonl()
    for reg in registros:
        if reg.get("id") == registro_id:
            reg["resolucao"] = texto
            _reescrever(registros)
            return True
    return False


def excluir_antigos(dias: int) -> int:
    """Remove registros mais velhos que `dias`. Retorna quantos foram removidos.

    Na nuvem (Supabase REST) a exclusão em massa exige RPC/regras adicionais;
    hoje retorna 0 e o recorte de maioridades fica com o JSONL local.
    """
    if _usar_nuvem():
        return nuvem_supabase.excluir_antigos(dias)
    if dias <= 0:
        return 0
    hoje = date.today()
    registros = _ler_jsonl()
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