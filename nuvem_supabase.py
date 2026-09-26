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
# Tabela de perfis (Passo 5 do caminho SaaS — perfil do usuário):
#   create table if not exists perfis_usuario (
#     uid          text primary key,
#     nome         text not null default '',
#     empresa      text not null default '',
#     fuso         text not null default 'America/Sao_Paulo',
#     avatar       text not null default '',
#     atualizado_em timestamptz not null default now()
#   );
#   alter table perfis_usuario enable row level security;
#   create policy "anon insert" on perfis_usuario for insert to anon with check (true);
#   create policy "anon select" on perfis_usuario for select to anon using (true);
#   create policy "anon update" on perfis_usuario for update to anon using (true);
#
# Tabela de contas (Passo 6 do caminho SaaS — painel do dono):
#   create table if not exists usuarios (
#     uid          text primary key,
#     email        text not null default '',
#     criado_em    timestamptz not null default now(),
#     ultimo_login timestamptz not null default now()
#   );
#   alter table usuarios enable row level security;
#   create policy "anon insert" on usuarios for insert to anon with check (true);
#   create policy "anon select" on usuarios for select to anon using (true);
#   create policy "anon update" on usuarios for update to anon using (true);
#
# Tabela de feedbacks (avaliação pós-triagem — estrelas 1-5 + comentário):
#   create table if not exists feedbacks (
#     id          bigserial primary key,
#     uid         text not null default '',
#     email       text not null default '',
#     estrelas    int  not null default 5,
#     comentario  text not null default '',
#     criado_em   timestamptz not null default now()
#   );
#   alter table feedbacks enable row level security;
#   create policy "anon insert" on feedbacks for insert to anon with check (true);
#   create policy "anon select" on feedbacks for select to anon using (true);
#   create policy "anon update" on feedbacks for update to anon using (true);
#
# Teste Premium com validade (Passo 6 — expira sozinho):
#   alter table planos_usuario add column if not exists teste_ate timestamptz;
# Teste Premium autoatendimento (o PRÓPRIO usuário ativa uma única vez):
#   alter table planos_usuario add column if not exists teste_auto timestamptz;
#   `teste_auto` guarda QUANDO o usuário ativou o próprio teste; o teste dado
#   pelo dono (definir_trial) escreve só `teste_ate`. Enquanto a coluna não
#   existir, carregar_teste_auto devolve None e o botão fica oculto — o app
#   funciona igual ao de hoje, sem quebrar.
#
# Assinatura Premium mensal (Passo 7 — R$ 19,99/30 dias, expira sozinho):
#   alter table planos_usuario add column if not exists assinatura_ate timestamptz;
#   `assinatura_ate` guarda o FIM da assinatura paga (pagamento → +30 dias a
#   partir de hoje, sem empilhar); expirou → plano_atual volta a 'free'.
#   Legado: quem já era 'pago' SEM vencimento gravado ganha 30 dias contando
#   da data em que esta versão passar a ler o campo (backfill a partir de hoje).
#
# A configuração per-tenant usada na Cloud NÃO precisa desta tabela: se ela não
# existir ou a leitura falhar, o app cai no plano por variável de ambiente.
#
# ─── SEGURANÇA (Rota B) ─────────────────────────────────────────────────────
# O REST roda SOBR service_role (bypassa RLS) — anon NÃO tem mais acesso.
# Aplicar migrations/fechar_anon_rest.sql (drop das policies "anon ...") no
# SQL Editor DEPOIS de configurar SUPABASE_SERVICE_ROLE_KEY em todos os
# ambientes. /auth/v1 (login) continua usando a anon key — inalterado.

import os
import time
from datetime import datetime, timezone

import requests

_TABELA_PADRAO = "triagens"
_TABELA_PLANOS = "planos_usuario"
_TABELA_COBRANCAS = "solicitacoes_pagamento"
_TABELA_PERFIS = "perfis_usuario"
_TABELA_USUARIOS = "usuarios"
_TABELA_FEEDBACKS = "feedbacks"


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


def _config_service():
    """(url, service_role_key) se configurado, senão None. Prioridade: st.secrets → .env → os.environ.

    A service_role bypassa a RLS: é quem faz TODAS as operações no REST (Rota B).
    Nunca expor essa chave em client público.
    """
    url = None
    chave = None
    try:
        import streamlit as st

        url = st.secrets.get("SUPABASE_URL")
        chave = st.secrets.get("SUPABASE_SERVICE_ROLE_KEY")
    except Exception:
        pass
    if not url or not chave:
        env = _carregar_env()
        url = url or env.get("SUPABASE_URL")
        chave = chave or env.get("SUPABASE_SERVICE_ROLE_KEY")
    url = url or os.environ.get("SUPABASE_URL")
    chave = chave or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    return (url, chave) if url and chave else None


def disponivel() -> bool:
    return _config() is not None or _config_service() is not None


# Cache de leitura com TTL: evita que cada rerun de página dispare as 3 chamadas
# ao Supabase (histórico) de uma vez — os blocos montam "instantâneos" na troca
# de página em vez de deixar sombras vazias aguardando a rede (~3s).
_LEITURA_TTL = 60  # segundos
_leitura_cache: dict[str, tuple[float, object]] = {}


def _leitura_cacheada(chave: str):
    """Cache TTL para leituras que demoram (Supabase). Retorna o valor ou None (expirou)."""

    def _decorator(fn):
        def _wrapper(*args, **kwargs):
            agora = time.monotonic()
            item = _leitura_cache.get(chave)
            if item and (agora - item[0]) < _LEITURA_TTL:
                return item[1]
            valor = fn(*args, **kwargs)
            _leitura_cache[chave] = (agora, valor)
            return valor

        return _wrapper

    return _decorator


def _invalidar_leitura(chaves: tuple[str, ...] | None = None) -> None:
    """Zera o cache de leitura (depois de um INSERT/PATCH no histórico)."""
    alvos = chaves if chaves is not None else tuple(_leitura_cache)
    for c in alvos:
        _leitura_cache.pop(c, None)


def _base_url() -> str:
    cfg = _config() or _config_service()
    url, _ = cfg
    return str(url).rstrip("/") + "/rest/v1"


def _headers() -> dict:
    cfg = _config_service() or _config()
    _, chave = cfg
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
    _invalidar_leitura(("registros", "registros_por_data", "datas"))
    return dados


@_leitura_cacheada("registros")
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


@_leitura_cacheada("registros_por_data")
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


@_leitura_cacheada("datas")
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
    _invalidar_leitura(("registros", "registros_por_data", "datas"))
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
    _invalidar_leitura(("registros", "registros_por_data"))
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


def gravar_plano_banco(uid: str, plano: str, clear_teste: bool = False, clear_assinatura: bool = False) -> bool:
    """Define o plano de um usuário na nuvem (upsert por uid).

    Pagar ('pago') encerra qualquer Teste Premium ativo automaticamente;
    `clear_teste=True` faz o mesmo mesmo quando mantendo/voltando a 'free'.
    `clear_assinatura=True` limpa também o vencimento da assinatura (usado no
    estorno e no "voltar a Basic" do painel — encerra o ciclo mensal).
    """
    config = _config()
    if not config:
        return False
    plano = plano if plano in ("free", "pago") else "free"
    linha = {"uid": uid, "plano": plano}
    # Prefer: resolution=merge-duplicates + on_conflict=uid faz o UPSERT
    # (null não é aplicado num merge — por isso o teste é limpo via PATCH).
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
    if clear_teste or plano == "pago":
        # Best-effort: se a coluna `teste_ate` ainda não existir no Supabase
        # (ALTER TABLE pendente), o plano foi salvo mesmo assim — só não limpa o teste.
        try:
            requests.patch(
                _planos_url(),
                headers=_headers(),
                params={"uid": f"eq.{uid}"},
                json={"teste_ate": None},
                timeout=15,
            )
        except Exception:
            pass
    if clear_assinatura:
        # Mesma lógica de tolerância: coluna `assinatura_ate` pendente não derruba.
        try:
            requests.patch(
                _planos_url(),
                headers=_headers(),
                params={"uid": f"eq.{uid}"},
                json={"assinatura_ate": None},
                timeout=15,
            )
        except Exception:
            pass
    return True


def carregar_teste_banco(uid: str) -> str | None:
    """teste_ate (ISO) do usuário na nuvem, ou None (sem teste/sem linha)."""
    config = _config()
    if not config:
        return None
    try:
        resposta = requests.get(
            _planos_url(),
            headers=_headers(),
            params={"select": "teste_ate", "uid": f"eq.{uid}", "limit": "1"},
            timeout=15,
        )
        resposta.raise_for_status()
        docs = resposta.json() or []
        if not docs:
            return None
        valor = docs[0].get("teste_ate")
        return valor or None
    except Exception:
        return None


def gravar_teste_banco(uid: str, ate_iso: str) -> bool:
    """Define o fim do Teste Premium de um usuário (upsert por uid)."""
    config = _config()
    if not config:
        return False
    linha = {"uid": uid, "teste_ate": ate_iso}
    resposta = requests.post(
        _planos_url(),
        headers={**_headers(), "Prefer": "resolution=merge-duplicates,return=minimal"},
        params={"on_conflict": "uid"},
        json=linha,
        timeout=15,
    )
    resposta.raise_for_status()
    return True


def assinatura_disponivel() -> bool:
    """True se a coluna `assinatura_ate` existe na schema cache do PostgREST.

    Semelhante à `teste_auto_disponivel`: enquanto o ALTER TABLE não for rodado
    (ou a schema cache estiver desatualizada), o upsert devolveria 400
    (PGRST204). Nunca levanta — apenas relata se o PostgREST enxerga a coluna.
    """
    config = _config()
    if not config:
        return False
    try:
        resposta = requests.get(
            _planos_url(),
            headers=_headers(),
            params={"select": "assinatura_ate", "limit": "1"},
            timeout=15,
        )
        return resposta.status_code == 200
    except Exception:
        return False


def carregar_assinatura_banco(uid: str) -> str | None:
    """assinatura_ate (ISO) do usuário na nuvem, ou None (sem assinatura/sem linha)."""
    config = _config()
    if not config:
        return None
    try:
        resposta = requests.get(
            _planos_url(),
            headers=_headers(),
            params={"select": "assinatura_ate", "uid": f"eq.{uid}", "limit": "1"},
            timeout=15,
        )
        resposta.raise_for_status()
        docs = resposta.json() or []
        if not docs:
            return None
        valor = docs[0].get("assinatura_ate")
        return valor or None
    except Exception:
        return None


def gravar_assinatura_banco(uid: str, ate_iso: str) -> bool:
    """Define o fim da assinatura Premium de um usuário (upsert por uid)."""
    config = _config()
    if not config:
        return False
    linha = {"uid": uid, "assinatura_ate": ate_iso}
    resposta = requests.post(
        _planos_url(),
        headers={**_headers(), "Prefer": "resolution=merge-duplicates,return=minimal"},
        params={"on_conflict": "uid"},
        json=linha,
        timeout=15,
    )
    resposta.raise_for_status()
    return True


def teste_auto_disponivel() -> bool:
    """True se a coluna `teste_auto` existe na schema cache do PostgREST.

    O botão de "Teste grátis" só aparece quando o dono rodou o ALTER TABLE
    (senão o upsert devolveria 400 PGRST204). Nunca levanta — só relata se o
    PostgREST enxerga a coluna.
    """
    config = _config()
    if not config:
        return False
    try:
        resposta = requests.get(
            _planos_url(),
            headers=_headers(),
            params={"select": "teste_auto", "limit": "1"},
            timeout=15,
        )
        return resposta.status_code == 200
    except Exception:
        return False


def carregar_teste_auto(uid: str) -> str | None:
    """Quando o PRÓPRIO usuário ativou o Teste Premium (teste_auto, ISO) ou None.

    Sem linha na tabela, offline ou coluna ainda não criada → None (não usado).
    """
    config = _config()
    if not config:
        return None
    try:
        resposta = requests.get(
            _planos_url(),
            headers=_headers(),
            params={"select": "teste_auto", "uid": f"eq.{uid}", "limit": "1"},
            timeout=15,
        )
        resposta.raise_for_status()
        docs = resposta.json() or []
        if not docs:
            return None
        valor = docs[0].get("teste_auto")
        return valor or None
    except Exception:
        return None


def ativar_teste_usuario(uid: str, ate_iso: str, auto_iso: str) -> bool:
    """Auto-trial idempotente do usuário: grava `teste_ate` + `teste_auto`.

    1) PATCH condicional só quando `teste_auto` é NULL — se a linha já tem o
       teste próprio marcado, nada é sobrescrito; 2) sem linha (usuário novo),
       cria via upsert. Assim, dois cliques/abas concorrentes nunca dão 14 dias
       nem reativam quem já usou o teste.
    """
    config = _config()
    if not config:
        return False
    # 1) linha existe e nunca auto-ativou -> PATCH condicional
    try:
        resposta = requests.patch(
            _planos_url(),
            headers={**_headers(), "Prefer": "return=representation"},
            params={"uid": f"eq.{uid}", "teste_auto": "is.null"},
            json={"teste_ate": ate_iso, "teste_auto": auto_iso},
            timeout=15,
        )
        resposta.raise_for_status()
        if resposta.json() or []:
            return True
    except Exception:
        return False
    # 2) PATCH não tocou nada: ou não há linha, ou já usado.
    if carregar_teste_auto(uid):
        return False
    try:
        linha = {"uid": uid, "plano": "free", "teste_ate": ate_iso, "teste_auto": auto_iso}
        resposta = requests.post(
            _planos_url(),
            headers={**_headers(), "Prefer": "resolution=merge-duplicates,return=minimal"},
            params={"on_conflict": "uid"},
            json=linha,
            timeout=15,
        )
        resposta.raise_for_status()
        return True
    except Exception:
        return False


def teste_disponivel() -> bool:
    """True se a coluna `teste_ate` existe na schema cache do PostgREST.

    O painel do dono usa isso para explicar por que "Dar teste 7 dias" pode
    falhar mesmo com as demais ações funcionando: o upsert de `teste_ate`
    devolve 400 (PGRST204) enquanto a coluna estiver pendente no Supabase
    (ALTER TABLE não rodado ou schema cache desatualizado). Nunca levanta —
    apenas relata se o PostgREST consegue enxergar a coluna.
    """
    config = _config()
    if not config:
        return False
    try:
        resposta = requests.get(
            _planos_url(),
            headers=_headers(),
            params={"select": "teste_ate", "limit": "1"},
            timeout=15,
        )
        return resposta.status_code == 200
    except Exception:
        return False


def carregar_todos_planos() -> list[dict]:
    """Todas as linhas de planos_usuario (uid, plano, teste_ate, teste_auto,
    assinatura_ate) — painel do dono.

    Se uma coluna ainda não existir (ALTER TABLE pendente), o PostgREST
    responde 400 no select — então refaz sem ela e preenche o campo ausente
    como None (o painel funciona; o dado só aparece depois do SQL aplicado).
    """
    config = _config()
    if not config:
        return []
    campos = ["uid", "plano", "teste_ate", "teste_auto", "assinatura_ate"]
    for tentativa in range(len(campos)):
        try:
            if tentativa >= len(campos):
                break
            selecao = ",".join(campos[: len(campos) - tentativa])
            resposta = requests.get(
                _planos_url(),
                headers=_headers(),
                params={"select": selecao},
                timeout=15,
            )
            resposta.raise_for_status()
            docs = resposta.json() or []
            for doc in docs:
                doc.setdefault("teste_ate", None)
                doc.setdefault("teste_auto", None)
                doc.setdefault("assinatura_ate", None)
            return docs
        except Exception:
            continue
    return []


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


# ─── Perfil do usuário (Passo 5 SaaS): tabela perfis_usuario ──────────────────

def _perfis_url() -> str:
    return f"{_base_url()}/{_TABELA_PERFIS}"


def carregar_perfil_banco(uid: str) -> dict | None:
    """Perfil ('nome', 'empresa', 'fuso', 'avatar') do usuário ou None (sem linha)."""
    config = _config()
    if not config:
        return None
    resposta = requests.get(
        _perfis_url(),
        headers=_headers(),
        params={"select": "nome,empresa,fuso,avatar", "uid": f"eq.{uid}", "limit": "1"},
        timeout=15,
    )
    resposta.raise_for_status()
    docs = resposta.json() or []
    if not docs:
        return None
    perfil = dict(docs[0] or {})
    return {k: (perfil.get(k) or "") for k in ("nome", "empresa", "fuso", "avatar")}


def gravar_perfil_banco(uid: str, perfil: dict) -> bool:
    """Upsert do perfil de um usuário na nuvem (por uid)."""
    config = _config()
    if not config:
        return False
    linha = {"uid": uid}
    for k in ("nome", "empresa", "fuso", "avatar"):
        linha[k] = (perfil.get(k) or "").strip() if k != "avatar" else (perfil.get(k) or "")
    resposta = requests.post(
        _perfis_url(),
        headers={**_headers(), "Prefer": "resolution=merge-duplicates,return=minimal"},
        params={"on_conflict": "uid"},
        json=linha,
        timeout=15,
    )
    resposta.raise_for_status()
    return True


# ─── Usuários/contas (Passo 6 SaaS — painel do dono): tabela usuarios ─────────

def _usuarios_url() -> str:
    return f"{_base_url()}/{_TABELA_USUARIOS}"


def registrar_usuario_banco(uid: str, email: str) -> bool:
    """Registra/atualiza o login de uma conta (último acesso + e-mail).

    Best-effort: nunca levanta exceção (login não pode quebrar por causa disso).
    """
    config = _config()
    if not config:
        return False
    try:
        linha = {
            "uid": uid,
            "email": (email or "").strip(),
            "ultimo_login": datetime.now(timezone.utc).isoformat(),
        }
        requests.post(
            _usuarios_url(),
            headers={**_headers(), "Prefer": "resolution=merge-duplicates,return=minimal"},
            params={"on_conflict": "uid"},
            json=linha,
            timeout=15,
        )
        return True
    except Exception:
        return False


def carregar_usuarios() -> list[dict]:
    """Todas as contas registradas (uid, email, criado_em, ultimo_login)."""
    config = _config()
    if not config:
        return []
    resposta = requests.get(
        _usuarios_url(),
        headers=_headers(),
        params={"select": "*", "order": "ultimo_login.desc"},
        timeout=15,
    )
    resposta.raise_for_status()
    return resposta.json() or []


def carregar_todos_perfis() -> list[dict]:
    """Todos os perfis (uid, nome, empresa, avatar) — painel do dono."""
    config = _config()
    if not config:
        return []
    resposta = requests.get(
        _perfis_url(),
        headers=_headers(),
        params={"select": "uid,nome,empresa,avatar"},
        timeout=15,
    )
    resposta.raise_for_status()
    return resposta.json() or []


# ─── Feedbacks (avaliação pós-triagem, estrelas 1-5 + comentário) ─────────────

def _feedbacks_url() -> str:
    return f"{_base_url()}/{_TABELA_FEEDBACKS}"


def registrar_feedback(uid: str, email: str, estrelas: int, comentario: str) -> bool:
    """Grava uma avaliação de pós-triagem. Best-effort: nunca levanta (a triagem
    nunca pode quebrar por causa de feedback). Sem a tabela criada no Supabase,
    devolve False e o app mostra um aviso suave.
    """
    config = _config()
    if not config:
        return False
    try:
        linha = {
            "uid": (uid or "").strip(),
            "email": (email or "").strip(),
            "estrelas": int(estrelas),
            "comentario": (comentario or "").strip(),
        }
        resposta = requests.post(
            _feedbacks_url(),
            headers={**_headers(), "Prefer": "resolution=merge-duplicates,return=minimal"},
            json=linha,
            timeout=15,
        )
        resposta.raise_for_status()
        return True
    except Exception:
        return False


def carregar_feedbacks() -> list[dict]:
    """Todas as avaliações (uid, email, estrelas, comentario, criado_em), das
    mais recentes para as mais antigas. Empty/aviso suave se a tabela não existir.
    """
    config = _config()
    if not config:
        return []
    try:
        resposta = requests.get(
            _feedbacks_url(),
            headers=_headers(),
            params={"select": "*", "order": "criado_em.desc"},
            timeout=15,
        )
        resposta.raise_for_status()
        return resposta.json() or []
    except Exception:
        return []


def ultimo_feedback_em(uid: str) -> str | None:
    """Data (ISO) da avaliação mais recente do usuário, ou None se nunca avaliou."""
    config = _config()
    if not config:
        return None
    try:
        resposta = requests.get(
            _feedbacks_url(),
            headers=_headers(),
            params={"select": "criado_em", "uid": f"eq.{uid}", "order": "criado_em.desc", "limit": "1"},
            timeout=15,
        )
        resposta.raise_for_status()
        docs = resposta.json() or []
        if not docs:
            return None
        return (docs[0] or {}).get("criado_em") or None
    except Exception:
        return None


def excluir_feedback(fb_id) -> bool:
    """Remove uma avaliação (gestão do painel do dono). Best-effort."""
    config = _config()
    if not config:
        return False
    try:
        resposta = requests.delete(
            _feedbacks_url(),
            headers=_headers(),
            params={"id": f"eq.{fb_id}"},
            timeout=15,
        )
        resposta.raise_for_status()
        return True
    except Exception:
        return False
