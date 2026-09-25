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
from datetime import datetime, timedelta, timezone

import nuvem_supabase

_PLANOS = ("free", "pago")
_LIMITE_FREE = 30  # nº máx. de triagens que o plano free enxerga (histórico/dashboard)


def _datetime_de_iso(iso: str) -> datetime | None:
    """Converte ISO do Postgres (ex.: 2026-09-20T12:00:00+00:00 ou ...Z) para datetime."""
    if not iso:
        return None
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except Exception:
        return None


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


def definir_plano_no_banco(uid: str, plano: str, clear_teste: bool = False) -> bool:
    """Grava o plano do usuário na nuvem. False se offline (sem efeito).

    `clear_teste=True` encerra também um Teste Premium ativo (usado ao pagar).
    """
    try:
        return nuvem_supabase.gravar_plano_banco(
            uid,
            plano if plano in _PLANOS else "free",
            clear_teste=clear_teste,
        )
    except Exception:
        return False


def plano_atual() -> str:
    """Plano ativo: do banco (se logado e nuvem ativa) senão da variável de ambiente.

    Usuário logado com nuvem ativa SEMPRE vem do banco — sem linha = 'free'
    (novo usuário) mesmo que haja PLANO=pago legado no env. O env só vale
    para quem não está logado ou quando a nuvem está off (testes/offline).
    O **Teste Premium** (teste_ate no futuro) e a **assinatura paga vigente**
    (assinatura_ate no futuro) também contam como 'pago'; a assinatura
    expirada volta a 'free' sozinha (sem ação manual).
    """
    uid = uid_logado()
    if uid:
        nuvem_ativa = bool(getattr(nuvem_supabase, "disponivel", lambda: False)())
        banco = plano_no_banco(uid)
        if banco == "pago":
            if _teste_em_vigor(uid) or assinatura_vigente(uid):
                return "pago"
            return "free"
        if banco == "free":
            return "pago" if _teste_em_vigor(uid) else "free"
        if banco is None:
            if _teste_em_vigor(uid):
                return "pago"
            if nuvem_ativa:
                return "free"
    # sem login, sem banco ou banco inválido → variável de ambiente
    plano = os.environ.get("PLANO", "free").strip().lower()
    if plano in _PLANOS:
        return plano
    return "free"


def teste_premium_restante(uid: str) -> str | None:
    """teste_ate (ISO) do usuário se houver Teste Premium com validade; senão None."""
    try:
        return nuvem_supabase.carregar_teste_banco(uid)
    except Exception:
        return None


def _teste_em_vigor(uid: str) -> bool:
    ate = _datetime_de_iso(teste_premium_restante(uid) or "")
    return bool(ate) and ate > datetime.now(timezone.utc)


# ─── Assinatura Premium mensal (Passo 7 — 30 dias, expira sozinho) ───────────

_DIAS_ASSINATURA = 30


def assinatura_vencimento(uid: str) -> str | None:
    """assinatura_ate (ISO) do usuário na nuvem, ou None (sem assinatura)."""
    try:
        _ler = getattr(nuvem_supabase, "carregar_assinatura_banco", None)
        if _ler is None:
            return None
        return _ler(uid) or None
    except Exception:
        return None


def _assinatura_fim(uid: str) -> datetime | None:
    return _datetime_de_iso(assinatura_vencimento(uid) or "")


def _assinatura_coluna_disponivel() -> bool:
    """Se a coluna `assinatura_ate` existe no Supabase (ALTER pendente → False)."""
    try:
        return bool(getattr(nuvem_supabase, "assinatura_disponivel", lambda: False)())
    except Exception:
        return False


def assinatura_dias_restantes(uid: str) -> int | None:
    """Dias (inteiros) de assinatura restantes; None sem vencimento registrado."""
    fim = _assinatura_fim(uid)
    if not fim:
        return None
    restante = fim - datetime.now(timezone.utc)
    if restante.total_seconds() <= 0:
        return 0
    return int(restante.total_seconds() // 86400)


def assinatura_vigente(uid: str) -> bool:
    """True se o usuário tem assinatura Premium ativa (vencimento futuro).

    **Legado** (pago SEM vencimento gravado — quem assinou antes desta regra)
    passa a valer a partir de HOJE: no primeiro acesso concede 30 dias
    (backfill idempotente). Sem a coluna no Supabase (ALTER pendente/offline)
    mantém o 'pago' ativo como antes, para nada quebrar antes do SQL.
    """
    fim = _assinatura_fim(uid)
    if fim:
        return fim > datetime.now(timezone.utc)
    if not _assinatura_coluna_disponivel():
        return True  # coluna pendente/offline → comportamento atual (graça)
    renovar_assinatura(uid)  # backfill legado: +30 dias contando de hoje
    return True


def renovar_assinatura(uid: str, dias: int = _DIAS_ASSINATURA) -> bool:
    """Renova/ativa a assinatura Premium: +`dias` (30) contando de hoje.

    Idempotente e **sem empilhar**: se já há assinatura ativa com vencimento
    futuro MAIOR que hoje+dias, mantém a maior (nunca encurta nem soma dias).
    Garante plano='pago' no banco e encerra qualquer teste ativo do usuário.
    Usado tanto na confirmação do Pix (renovação mensal) quanto na ativação
    manual do painel do dono.
    """
    if not uid:
        return False
    if not _assinatura_coluna_disponivel():
        # ALTER pendente/offline → ativa 'pago' sem vencimento (comportamento antigo)
        return definir_plano_no_banco(uid, "pago", clear_teste=True)
    agora = datetime.now(timezone.utc)
    fim = agora + timedelta(days=int(dias))
    atual = _assinatura_fim(uid)
    if atual and atual > agora and atual > fim:
        fim = atual
    try:
        if not definir_plano_no_banco(uid, "pago", clear_teste=True):
            return False
        return bool(nuvem_supabase.gravar_assinatura_banco(uid, fim.isoformat()))
    except Exception:
        return False


def encerrar_assinatura(uid: str) -> bool:
    """Encerra o ciclo pago (estorno / "voltar a Basic"): free + limpa vencimento e teste."""
    try:
        return bool(nuvem_supabase.gravar_plano_banco(uid, "free", clear_teste=True, clear_assinatura=True))
    except Exception:
        return False


def definir_trial(uid: str, dias: int) -> bool:
    """Dá N dias de Teste Premium (conta como pago até expirar)."""
    try:
        ate = (datetime.now(timezone.utc) + timedelta(days=int(dias))).isoformat()
        return nuvem_supabase.gravar_teste_banco(uid, ate)
    except Exception:
        return False


# ─── Teste Premium autoatendimento (o usuário ativa, uma única vez) ─────────

def teste_usuario_usado(uid: str) -> bool:
    """True se o PRÓPRIO usuário já ativou o Teste Premium (coluna teste_auto).

    Enquanto o ALTER TABLE não for rodado no Supabase, a coluna não existe e
    isso devolve False (botão aparece) — o click a mais só avisa "não deu",
    sem quebrar nada. Tolerante a offline.
    """
    try:
        return bool(nuvem_supabase.carregar_teste_auto(uid))
    except Exception:
        return False


def teste_auto_disponivel() -> bool:
    """True se o PostgREST enxerga a coluna `teste_auto` (botão pode aparecer)."""
    try:
        return nuvem_supabase.teste_auto_disponivel()
    except Exception:
        return False


def dias_restantes_teste(uid: str) -> int | None:
    """Dias (inteiros) de Teste Premium restantes; None sem teste ativo."""
    ate = _datetime_de_iso(teste_premium_restante(uid) or "")
    if not ate:
        return None
    restante = ate - datetime.now(timezone.utc)
    if restante.total_seconds() <= 0:
        return 0
    return int(restante.total_seconds() // 86400)


def ativar_teste_automatico(uid: str, dias: int = 7) -> tuple[bool, str]:
    """Self-service: dá N dias de Teste Premium ao usuário, uma única vez.

    Idempotente: quem já usou (teste_auto) não reativa. Se já há uma validade
    maior (ex.: teste dado pelo dono), mantém a maior — nunca encurta nem
    estende o dobro. Retorna (ok, chave) para a UI.
    """
    if not uid:
        return False, "sem_uid"
    if teste_usuario_usado(uid):
        return False, "usado"
    agora = datetime.now(timezone.utc)
    atual = _datetime_de_iso(teste_premium_restante(uid) or "")
    limite = agora + timedelta(days=int(dias))
    if atual and atual > agora and atual > limite:
        limite = atual
    try:
        ok = nuvem_supabase.ativar_teste_usuario(uid, limite.isoformat(), agora.isoformat())
        if ok and teste_usuario_usado(uid):
            return True, "ok"
        return False, "erro"
    except Exception:
        return False, "erro"


def definir_plano_manual(uid: str, plano: str) -> bool:
    """Ação do painel do dono: ativar Premium inicia +30 dias, voltar a Basic
    encerra o ciclo (limpa teste e vencimento da assinatura)."""
    if plano == "pago":
        return renovar_assinatura(uid)
    return encerrar_assinatura(uid)


def pago() -> bool:
    """True se o plano atual é o pago."""
    return plano_atual() == "pago"


def limite_historico_free() -> int:
    """Triagens máximas visíveis no plano free (histórico e dashboard)."""
    return _LIMITE_FREE if not pago() else 10**9


def limite_historico_free_fixo() -> int:
    """Limite fixo do plano free (30) para textos comparativos Basic × Premium."""
    return _LIMITE_FREE


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