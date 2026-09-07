# Persistência em nuvem via Supabase (Postgres + API REST).
#
# V2.1 — camada "SaaS": o histórico passa a viver no Supabase quando configurado;
# sem configuração, o app continua 100% no JSONL local (fallback). As credenciais
# NUNCA vão para o repositório:
#   - Streamlit Cloud: Settings -> Secrets -> SUPABASE_URL / SUPABASE_ANON_KEY
#   - Local: arquivo .env (gitignored)
#
# Schema da tabela (colar no SQL Editor do Supabase):
#   create table if not exists triagens (
#     id         text primary key,
#     data_hora  timestamptz not null,
#     data       date not null,
#     jira_key   text,
#     jira_url   text,
#     payload    jsonb not null default '{}'::jsonb
#   );
#   alter table triagens enable row level security;
#   create policy "anon insert" on triagens for insert to anon with check (true);
#   create policy "anon select" on triagens for select to anon using (true);
#   create policy "anon update" on triagens for update to anon using (true);

import json
import os

import requests

_TABELA_PADRAO = "triagens"


def _carregar_env():
    """Lê chaves do arquivo .env (apenas leitura, nunca commitado)."""
    caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(caminho):
        return {}
    valores = {}
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            chave, _, valor = linha.partition("=")
            valores[chave.strip()] = valor.strip()
    return valores


def _config():
    """(url, anon_key) se configurado, senão None. Prioridade: st.secrets → .env → os.environ."""
    url = None
    chave = None
    try:
        import streamlit as st

        url = st.secrets.get("SUPABASE_URL")
        chave = st.secrets.get("SUPABASE_ANON_KEY")
    except Exception:
        pass
    if not url or not chave:
        env = _carregar_env()
        url = url or env.get("SUPABASE_URL")
        chave = chave or env.get("SUPABASE_ANON_KEY")
    url = url or os.environ.get("SUPABASE_URL")
    chave = chave or os.environ.get("SUPABASE_ANON_KEY")
    return (url, chave) if url and chave else None


def disponivel() -> bool:
    return _config() is not None


def _base_url() -> str:
    url, _ = _config()
    return str(url).rstrip("/") + "/rest/v1"


def _headers() -> dict:
    _url, chave = _config()
    return {
        "apikey": chave,
        "Authorization": f"Bearer {chave}",
        "Content-Type": "application/json",
    }


def _linha_para_doc(registro: dict) -> dict:
    """Converte o registro (formato do app) para a linha da tabela."""
    return {
        "id": registro["id"],
        "data_hora": registro.get("data_hora", ""),
        "data": registro.get("data", ""),
        "jira_key": registro.get("jira_key"),
        "jira_url": registro.get("jira_url"),
        "payload": registro,
    }


def _doc_para_linha(doc: dict) -> dict:
    """Converte a linha da tabela de volta ao formato do app (o payload original)."""
    registro = dict(doc.get("payload") or {})
    # Garante consistência mesmo se algum campo viver só na coluna tipada.
    registro.setdefault("id", doc.get("id"))
    registro.setdefault("data_hora", doc.get("data_hora"))
    registro.setdefault("data", doc.get("data"))
    if doc.get("jira_key"):
        registro["jira_key"] = doc["jira_key"]
    if doc.get("jira_url"):
        registro["jira_url"] = doc["jira_url"]
    return registro


def registrar_triagem(dados: dict) -> dict:
    """Cria e insere o registro na nuvem. Retorna o registro persistido."""
    config = _config()
    if not config:
        raise RuntimeError("Supabase não configurado.")
    resposta = requests.post(
        f"{_base_url()}/{_TABELA_PADRAO}",
        headers=_headers(),
        json=_linha_para_doc(dados),
        timeout=15,
    )
    resposta.raise_for_status()
    return dados


def carregar_registros() -> list[dict]:
    """Todos os registros em ordem cronológica (do mais antigo para o mais novo)."""
    config = _config()
    if not config:
        raise RuntimeError("Supabase não configurado.")
    resposta = requests.get(
        f"{_base_url()}/{_TABELA_PADRAO}",
        headers=_headers(),
        params={"select": "*", "order": "data_hora.asc"},
        timeout=15,
    )
    resposta.raise_for_status()
    docs = resposta.json()
    if not isinstance(docs, list):
        return []
    return [_doc_para_linha(doc) for doc in docs]


def registros_por_data(data_iso: str) -> list[dict]:
    config = _config()
    if not config:
        raise RuntimeError("Supabase não configurado.")
    resposta = requests.get(
        f"{_base_url()}/{_TABELA_PADRAO}",
        headers=_headers(),
        params={"select": "*", "data": f"eq.{data_iso}", "order": "data_hora.asc"},
        timeout=15,
    )
    resposta.raise_for_status()
    return [_doc_para_linha(doc) for doc in (resposta.json() or [])]


def datas_disponiveis() -> list[str]:
    config = _config()
    if not config:
        raise RuntimeError("Supabase não configurado.")
    resposta = requests.get(
        f"{_base_url()}/{_TABELA_PADRAO}",
        headers=_headers(),
        params={"select": "data", "order": "data.desc"},
        timeout=15,
    )
    resposta.raise_for_status()
    return sorted({doc.get("data") for doc in (resposta.json() or [])}, reverse=True)


def registrar_exportacao_jira(chave: str, url: str) -> bool:
    """Vincula a issue do Jira ao registro mais recente (fetch + PATCH por id)."""
    registros = carregar_registros()
    if not registros:
        return False
    mais_recente = registros[-1]
    resposta = requests.patch(
        f"{_base_url()}/{_TABELA_PADRAO}",
        headers=_headers(),
        params={"id": f"eq.{mais_recente['id']}"},
        json={"jira_key": chave, "jira_url": url},
        timeout=15,
    )
    resposta.raise_for_status()
    return True


def registrar_resolucao(registro_id: str, texto: str) -> bool:
    """Registra 'como o caso foi resolvido' num registro (vai no payload → alimenta o RAG)."""
    config = _config()
    if not config:
        raise RuntimeError("Supabase não configurado.")
    doc = requests.get(
        f"{_base_url()}/{_TABELA_PADRAO}",
        headers=_headers(),
        params={"select": "*", "id": f"eq.{registro_id}", "limit": "1"},
        timeout=15,
    )
    doc.raise_for_status()
    docs = doc.json() or []
    if not docs:
        return False
    payload = dict(docs[0].get("payload") or {})
    payload["resolucao"] = texto
    resposta = requests.patch(
        f"{_base_url()}/{_TABELA_PADRAO}",
        headers=_headers(),
        params={"id": f"eq.{registro_id}"},
        json={"payload": payload},
        timeout=15,
    )
    resposta.raise_for_status()
    return True


def excluir_antigos(dias: int) -> int:
    """Não aplicável por API REST simples — o app não usa exclusão pela nuvem."""
    return 0