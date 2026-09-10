"""Planos SaaS e isolamento por tenant (preparação p/ multi-tenant).

Variáveis de ambiente:
  PLANO     = free | pago        (padrão: free)
  TENANT_ID = identificador da empresa/tenant (padrão: "global")

Regras atuais (gate mínimo, sem billing):
  - free : 1 canal de alerta (prioriza e-mail), histórico/dashboard resumidos
           às últimas N triagens, RAG desligado, deep-analysis do dashboard oculto.
  - pago : multi-canal de alerta, histórico/dashboard completo, RAG ligado.

Numeração de tenants: por enquanto não há login, então tudo cai em "global";
o campo tenant_id já é gravado e filtrado para o esquema estar pronto quando
houver contas (cada empresa só vê os próprios dados).
"""

import os

_PLANOS = ("free", "pago")
_LIMITE_FREE = 30  # nº máx. de triagens que o plano free enxerga (histórico/dashboard)


def plano_atual() -> str:
    """Nome do plano ativo ('free' ou 'pago'); qualquer valor diferente de pago = free."""
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
    """Identificador do tenant corrente (padrão 'global' até haver login)."""
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