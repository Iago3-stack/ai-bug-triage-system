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
#
# Tabela de planos por usuário (Passo 3 do caminho SaaS):
#   create table if not exists planos_usuario (
#     uid         text primary key,
#     plano       text not null default 'free' check (plano in ('free','pago')),
#     atualizado_em timestamptz not null default now()
#   );
#   alter table planos_usuario enable row level security;
#   create policy "anon insert" on planos_usuario for insert to anon with check (true);
#   create policy "anon select" on planos_usuario for select to anon using (true);
#   create policy "anon update" on planos_usuario for update to anon using (true);
#
# Tabela de cobranças Pix (Passo 4 do caminho SaaS — "nosso Stripe"):
#   create table if not exists solicitacoes_pagamento (
#     id         text primary key,
#     data_hora  timestamptz not null,
#     payload    jsonb not null default '{}'::jsonb
#   );
#   alter table solicitacoes_pagamento enable row level security;
#   create policy "anon insert" on solicitacoes_pagamento for insert to anon with check (true);
#   create policy "anon select" on solicitacoes_pagamento for select to anon using (true);
#   create policy "anon update" on solicitacoes_pagamento for update to anon using (true);
#
# A configuração per-tenant usada na Cloud NÃO precisa desta tabela: se ela não
# existir ou a leitura falhar, o app cai no plano por variável de ambiente.

import json
import os

import requests

_TABELA_PADRAO = "triagens"
_TABELA_PLANOS = "planos_usuario"
_TABELA_COBRANCAS = "solicitacoes_pagamento"


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


# ─── Planos por usuário (Passo 3 SaaS): tabela planos_usuario ────────────────

def _planos_url() -> str:
    return f"{_base_url()}/{_TABELA_PLANOS}"


def carregar_plano_banco(uid: str) -> str | None:
    """Plano do usuário na nuvem ('free'/'pago') ou None (sem linha na tabela)."""
    config = _config()
    if not config:
        return None
    resposta = requests.get(
        _planos_url(),
        headers=_headers(),
        params={"select": "plano", "uid": f"eq.{uid}", "limit": "1"},
        timeout=15,
    )
    resposta.raise_for_status()
    docs = resposta.json() or []
    if not docs:
        return None
    plano = docs[0].get("plano")
    return plano if plano in ("free", "pago") else None


def gravar_plano_banco(uid: str, plano: str) -> bool:
    """Define o plano de um usuário na nuvem (upsert por uid)."""
    config = _config()
    if not config:
        return False
    plano = plano if plano in ("free", "pago") else "free"
    linha = {"uid": uid, "plano": plano}
    # Prefer: resolution=merge-duplicates + on_conflict=uid faz o UPSERT.
    resposta = requests.post(
        _planos_url(),
        headers={
            **_headers(),
            "Prefer": "resolution=merge-duplicates,return=minimal",
        },
        params={"on_conflict": "uid"},
        json=linha,
        timeout=15,
    )
    resposta.raise_for_status()
    return True


def migrar_tenant_global(uid: str) -> int:
    """Re-tag dos registros legados (tenant 'global') para o uid do usuário.

    Depois do Passo 3 o isolamento é por usuário; os registros antigos gravados
    com tenant 'global' (era o padrão antes do login) ficam invisíveis para
    todos. Este helper adota esses registros para a conta do usuário que os
    reivindica. Retorna quantos foram re-tagados.
    """
    config = _config()
    if not config:
        return 0
    registros = carregar_registros()
    legados = [r for r in registros if (r.get("tenant_id") or "global") == "global"]
    if not legados:
        return 0
    for reg in legados:
        payload = dict(reg or {})
        payload["tenant_id"] = uid
        requests.patch(
            f"{_base_url()}/{_TABELA_PADRAO}",
            headers=_headers(),
            params={"id": f"eq.{reg.get('id')}"},
            json={"payload": payload},
            timeout=15,
        )
    return len(legados)


# ─── Cobranças Pix ("nosso Stripe", Passo 4 SaaS): solicitacoes_pagamento ─────

def _cobrancas_url() -> str:
    return f"{_base_url()}/{_TABELA_COBRANCAS}"


def carregar_cobrancas() -> list[dict]:
    """Todas as linhas da tabela, decodificando o payload jsonb (último formato)."""
    config = _config()
    if not config:
        return []
    resposta = requests.get(_cobrancas_url(), headers=_headers(), params={"select": "*"}, timeout=15)
    resposta.raise_for_status()
    docs = resposta.json() or []
    resultado = []
    for doc in docs:
        linha = dict(doc.get("payload") or {})
        if not linha:
            # linha vazia (controle) — mantém o essencial com os campos da coluna
            linha = {"id": doc.get("id")}
        linha.setdefault("id", doc.get("id"))
        linha.setdefault("data_hora", doc.get("data_hora"))
        resultado.append(linha)
    return resultado


def gravar_cobranca(cobranca: dict) -> bool:
    """Insere uma cobrança na nuvem (payload em jsonb)."""
    config = _config()
    if not config:
        return False
    linha = {
        "id": cobranca.get("id"),
        "data_hora": cobranca.get("criado_em") or cobranca.get("data_hora"),
        "payload": cobranca,
    }
    resposta = requests.post(
        _cobrancas_url(),
        headers={**_headers(), "Prefer": "return=minimal"},
        json=linha,
        timeout=15,
    )
    resposta.raise_for_status()
    return True


def atualizar_cobranca(doc_id: str, cobranca: dict) -> bool:
    """Atualiza o payload de uma cobrança (status, motivo, etc.)."""
    config = _config()
    if not config:
        return False
    resposta = requests.patch(
        _cobrancas_url(),
        headers=_headers(),
        params={"id": f"eq.{doc_id}"},
        json={"payload": cobranca},
        timeout=15,
    )
    resposta.raise_for_status()
    return True
