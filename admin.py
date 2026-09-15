"""Identificação do dono do app (ADMIN_EMAIL) — usado no painel do dono.

Fonte única de verdade para 'quem é o dono'; outras páginas podem (re)usar.
"""

import os


def email_logado() -> str | None:
    """E-mail da conta logada, ou None."""
    try:
        import auth_supabase

        sessao = auth_supabase.sessao() or {}
        return (sessao.get("user") or {}).get("email")
    except Exception:
        return None


def eh_dono() -> bool:
    """True se a conta logada é o dono (e-mail = ENV ADMIN_EMAIL).

    Sem ADMIN_EMAIL configurado, ninguém é dono (o painel não é exibido).
    """
    admin = os.environ.get("ADMIN_EMAIL", "").strip().lower()
    if not admin:
        return False
    return (email_logado() or "").strip().lower() == admin