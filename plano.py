"""Planos SaaS e isolamento por tenant (multi-tenant por usuário).

Passo 3 do caminho SaaS: o plano agora é POR USUÁRIO, salvo na nuvem
(tabela `planos_usuario`, invertida via `nuvem_supabase`), e o `tenant_id`
dos registros é o UID da conta logada — cada usuário só vê os próprios dados.

Ordem de resolução:
  1. Usuário logado (Supabase Auth) => plano vem do banco (`planos_usuario`).
  2. Sem login / sem banco / erro de rede => variável de ambiente PLANO
     (comportamento antigo, usado em testes e deploys sem nuvem).

Variáveis de ambiente (fallback/depur):
  PLANO     = free | pago        (padrão: free)
  TENANT_ID = identificador do tenant (padrão: "global")

Regras atuais (gate mínimo, sem billing):
  - free : 1 canal de alerta (prioriza e-mail), histórico/dashboard resumidos
           às últimas N triagens, RAG desligado, deep-analysis do dashboard oculto.
  - pago : multi-canal de alerta, histórico/dashboard completo, RAG ligado.

Antes do login existir, tudo caía em "global" (variável de ambiente); os
registros legados com tenant 'global' são reivindicados pelo usuário na página
"Meu Plano" (migração de tenant).
"""

import os

import nuvem_supabase

_PLANOS = ("free", "pago")
_LIMITE_FREE = 30  # nº máx. de triagens que o plano free enxerga (histórico/dashboard)


def uid_logado() -> str | None:
    """UID (ou e-mail) da conta logada via Supabase Auth, ou None."""
    try:
        import auth_supabase

        if not auth_supabase.disponivel():
            return None
        sessao = auth_supabase.sessao()
        if not sessao:
            return None
        user = sessao.get("user") or {}
        return user.get("id") or user.get("email") or None
    except Exception:
        return None


def plano_no_banco(uid: str) -> str | None:
    """Plano do usuário salvo na nuvem, ou None se offline/sem linha."""
    try:
        return nuvem_supabase.carregar_plano_banco(uid)
    except Exception:
        return None


def definir_plano_no_banco(uid: str, plano: str) -> bool:
    """Grava o plano do usuário na nuvem. False se offline (sem efeito)."""
    try:
        return nuvem_supabase.gravar_plano_banco(uid, plano if plano in _PLANOS else "free")
    except Exception:
        return False


def plano_atual() -> str:
    """Plano ativo: do banco (se logado e nuvem ativa) senão da variável de ambiente.

    Usuário logado com nuvem ativa SEMPRE vem do banco — sem linha = 'free'
    (novo usuário) mesmo que haja PLANO=pago legado no env. O env só vale
    para quem não está logado ou quando a nuvem está off (testes/offline).
    """
    uid = uid_logado()
    if uid:
        nuvem_ativa = bool(getattr(nuvem_supabase, "disponivel", lambda: False)())
        banco = plano_no_banco(uid)
        if banco in _PLANOS:
            return banco
        if nuvem_ativa:
            return "free"
    plano = os.environ.get("PLANO", "free").strip().lower()
    if plano in _PLANOS:
        return plano
    return "free"


def pago() -> bool:
    """True se o plano atual é o pago."""
    return plano_atual() == "pago"


def limite_historico_free() -> int:
    """Triagens máximas visíveis no plano free (histórico e dashboard)."""
    return _LIMITE_FREE if not pago() else 10**9


def tenant_atual() -> str:
    """Tenant corrente: UID da conta logada, senão env TENANT_ID/global."""
    uid = uid_logado()
    if uid:
        return uid
    return (os.environ.get("TENANT_ID") or "global").strip() or "global"


def integrar_tenant(registro: dict) -> dict:
    """Garante que o registro carregue o tenant que o gravou (isolamento)."""
    registro["tenant_id"] = tenant_atual()
    return registro


def dados_do_tenant(registro: dict) -> bool:
    """True se o registro pertence ao tenant corrente (registros antigos = global)."""
    return (registro.get("tenant_id") or "global") == tenant_atual()


def aplicar_limite_canais(email_ok: bool, discord_ok: bool) -> tuple[bool, bool]:
    """Canais de alerta liberados: pago envia por TODOS configurados; free envia
    por UM canal (prioriza e-mail; sem e-mail, cai no Discord)."""
    if pago():
        return email_ok, discord_ok
    if email_ok:
        return True, False
    return False, discord_ok