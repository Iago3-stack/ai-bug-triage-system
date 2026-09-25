"""🛠️ Painel do Administrador (Passo 6 SaaS) — visão do dono sobre todas as contas.

Acesso restrito a ADMIN_EMAIL. Mostra métricas, a lista de contas (e-mail,
perfil, plano, último login) e ações diretas: ativar Premium, voltar a Basic
e dar Teste Premium com validade. Onde confirmar/estornar pagamentos? No
"Painel do responsável" dentro de Meu Plano (fluxo já existente).
"""
import datetime as _dt

import streamlit as st

import admin
import pixbilling
import plano
import nuvem_supabase


def _fmt_data(iso: str | None) -> str:
    """2026-09-15T12:00:00+00:00 → '15/09/2026 12:00' (hora do servidor)."""
    if not iso:
        return "—"
    try:
        dt = _dt.datetime.fromisoformat(str(iso).replace("Z", "+00:00")).astimezone()
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(iso)[:16]


def _teste_ativo(iso) -> bool:
    """True se `teste_ate` existe e ainda está no futuro."""
    if not iso:
        return False
    try:
        return _dt.datetime.fromisoformat(str(iso).replace("Z", "+00:00")) > _dt.datetime.now(_dt.timezone.utc)
    except Exception:
        return False


def _badge(tipo: str, sub: str | None = None) -> str:
    """Badge visual do plano da conta (sub = origem do teste: 'user'/'admin')."""
    if tipo == "premium":
        return ('<span style="background:rgba(251,191,36,.16);color:#f59e0b;border:1px solid rgba(251,191,36,.5);'
                'border-radius:999px;padding:2px 10px;font-size:11px;font-weight:800">⭐ Premium</span>')
    if tipo == "teste":
        _rotulo = {
            "user": "Teste Premium (User)",
            "admin": "Teste Premium (Admin)",
        }.get(sub or "", "Teste Premium")
        return (f'<span style="background:rgba(46,124,246,.16);color:#60a5fa;border:1px solid rgba(46,124,246,.5);'
                f'border-radius:999px;padding:2px 10px;font-size:11px;font-weight:800">🎁 {_rotulo}</span>')
    return ('<span style="background:rgba(37,211,102,.16);color:#22c55e;border:1px solid rgba(37,211,102,.5);'
            'border-radius:999px;padding:2px 10px;font-size:11px;font-weight:800">🔓 Basic</span>')


def _x_avatar(avatar: str, inicial: str) -> str:
    if avatar:
        return f'<img src="{avatar}" style="width:36px;height:36px;border-radius:50%;object-fit:cover;flex:none">'
    return (
        f'<div style="width:36px;height:36px;border-radius:50%;flex:none;display:flex;align-items:center;'
        f'justify-content:center;font-weight:800;font-size:13px;color:#ffffff;'
        f'background:linear-gradient(135deg,#25D366,#2E7CF6)">{inicial}</div>'
    )


def render():
    import ui_comum  # lazy (ciclo: ui_comum -> roteador -> painel_dono)

    _aviso = st.session_state.pop("dono_aviso", None)
    if _aviso:
        st.success(_aviso)

    st.markdown('<div style="height:3px;width:100%;background:linear-gradient(90deg,transparent,#25D366,#2E7CF6,#7c3aed,transparent);border-radius:999px;margin:8px 0"></div>', unsafe_allow_html=True)

    st.markdown("""
    <div style="width:100%;background:linear-gradient(135deg,#0f172a 0%,#1a2740 55%,#7c3aed 180%);border-radius:16px;padding:30px 34px 28px 34px;margin:4px 0 16px;box-shadow:0 8px 22px rgba(15,23,42,.18);border:1px solid rgba(139,92,246,.22)">
      <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap">
        <span style="background:rgba(139,92,246,.18);color:#c4b5fd;border:1px solid rgba(139,92,246,.5);border-radius:999px;padding:4px 14px;font-size:12px;font-weight:800;letter-spacing:.04em">🛠️ ACESSO RESTRITO AO ADMIN</span>
        <span style="color:#94a3b8;font-size:12px;font-weight:700;letter-spacing:.04em">TODAS AS CONTAS · AÇÕES IMEDIATAS</span>
      </div>
      <div style="color:#ffffff;font-size:29px;font-weight:800;margin-top:18px;letter-spacing:-.01em;line-height:1.25">🛠️ Painel do Administrador</div>
      <div style="color:#cbd5e1;font-size:16.5px;line-height:1.7;margin-top:8px;max-width:96%">Visão geral de <b style="color:#86efac">todas as contas</b> registradas no app: Premium, testes, Basic e cobranças. As ações <b style="color:#86efac">refletem imediatamente</b> no plano de cada usuário.</div>
    </div>
    """, unsafe_allow_html=True)

    if not admin.eh_dono():
        st.warning(
            "Esta página é **restrita ao dono** (e-mail configurado em `ADMIN_EMAIL`). "
            "Se você não é o dono, pode seguir usando o app normalmente."
        )
        return

    # Cada fonte é carregada isolada: se uma tabela/coluna ainda não existir no
    # Supabase (ex.: o ALTER TABLE do teste_aTE pendente), as outras continuam.
    def _carregar(tarefa, padrao):
        try:
            return tarefa() or padrao
        except Exception:
            return padrao

    usuarios = _carregar(nuvem_supabase.carregar_usuarios, [])
    planos = _carregar(nuvem_supabase.carregar_todos_planos, [])
    perfis = _carregar(nuvem_supabase.carregar_todos_perfis, [])
    pendentes = _carregar(pixbilling.pendentes, [])
    estornos = _carregar(pixbilling.estornos, [])

    # ─── Mescla todas as fontes por uid ───────────────────────────────────────
    por_uid: dict = {}
    for u in usuarios:
        por_uid.setdefault(u.get("uid"), {})["email"] = u.get("email") or "—"
        por_uid[u.get("uid")]["criado_em"] = u.get("criado_em")
        por_uid[u.get("uid")]["ultimo_login"] = u.get("ultimo_login")
    for p in planos:
        por_uid.setdefault(p.get("uid"), {})["plano"] = p.get("plano") or "free"
        por_uid[p.get("uid")]["teste_ate"] = p.get("teste_ate")
        por_uid[p.get("uid")]["teste_auto"] = p.get("teste_auto")
        por_uid[p.get("uid")].setdefault("assinatura_ate", p.get("assinatura_ate"))
    for pf in perfis:
        por_uid.setdefault(pf.get("uid"), {})["nome"] = pf.get("nome") or ""
        por_uid[pf.get("uid")]["empresa"] = pf.get("empresa") or ""
        por_uid[pf.get("uid")]["avatar"] = pf.get("avatar") or ""
    for dados in por_uid.values():
        dados.setdefault("email", "—")
        dados.setdefault("plano", "free")
        dados.setdefault("teste_ate", None)
        dados.setdefault("teste_auto", None)

    # ─── Métricas ──────────────────────────────────────────────────────────────
    qtd_premium = qtd_teste = 0
    for dados in por_uid.values():
        em_teste = _teste_ativo(dados.get("teste_ate"))
        dados["_teste"] = em_teste
        if dados.get("plano") == "pago":
            qtd_premium += 1
        elif em_teste:
            qtd_teste += 1
    total = len(por_uid)
    _base = total - qtd_premium - qtd_teste
    _cards = (
        ("👥 Contas", f"{total}", "#2E7CF6"),
        ("⭐ Premium", f"{qtd_premium}", "#f59e0b"),
        ("🎁 Em teste", f"{qtd_teste}", "#60a5fa"),
        ("🔓 Basic", f"{_base}", "#22c55e"),
    )
    _html_cards = "".join(
        f'<div style="flex:1;min-width:120px;background:#0f172a;border:1px solid rgba(148,163,184,.18);'
        f'border-radius:14px;padding:14px 16px">'
        f'<div style="color:#64748b;font-size:12px;font-weight:700">{rotulo}</div>'
        f'<div style="color:{cor};font-size:26px;font-weight:800;margin-top:4px">{valor}</div></div>'
        for rotulo, valor, cor in _cards
    )
    st.markdown(
        f'<div style="display:flex;gap:10px;flex-wrap:wrap;margin:6px 0 14px">{_html_cards}</div>',
        unsafe_allow_html=True,
    )
    if pendentes or estornos:
        st.info(
            f"**{len(pendentes)}** pagamento(s) aguardando confirmação e **{len(estornos)}** estorno(s) "
            "pendentes — trate-os no **💼 Meu Plano → Painel do responsável**."
        )

    # ─── Feedbacks (avaliações pós-triagem) ─────────────────────────────────
    st.markdown("### 💬 Feedbacks de usuários")
    feedbacks = _carregar(nuvem_supabase.carregar_feedbacks, [])
    if not feedbacks:
        st.caption(
            "Nenhum feedback ainda — eles aparecem aqui depois que um usuário logado "
            "avalia uma triagem. (Sem a tabela `feedbacks` no Supabase nada quebra, só fica vazio.)"
        )
    else:
        _fb_busca = st.text_input("🔍 Filtrar por e-mail / uid / comentário", key="dono_fb_busca").strip().lower()
        _media = round(sum(int(f.get("estrelas") or 0) for f in feedbacks) / len(feedbacks), 1)
        st.caption(f"**{len(feedbacks)}** avaliação(ões) · **média {_media:.1f}/5** · mostrando {len(feedbacks)}")
        for _i, fb in enumerate(feedbacks):
            _emiss = fb.get("email") or "—"
            _uidf = str(fb.get("uid") or "")
            _texto = (fb.get("comentario") or "").strip()
            _est = int(fb.get("estrelas") or 0)
            _linha_busca = " ".join((_emiss, _uidf, _texto)).lower()
            if _fb_busca and _fb_busca not in _linha_busca:
                continue
            _estrelas_html = "⭐" * min(max(_est, 0), 5)
            st.markdown(
                f'<div class="fb-card" style="padding:10px 14px;margin:6px 0">'
                f'<div class="fb-meta" style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">'
                f'<span class="fb-estrelas" style="font-size:15px;letter-spacing:2px">{_estrelas_html}</span>'
                f'<span>{_emiss} · {_fmt_data(fb.get("criado_em"))}</span>'
                f'<span class="fb-uid">…{_uidf[-10:]}</span>'
                f'</div>'
                f'<div class="fb-texto" style="font-size:14px;margin-top:6px">{_texto or "—"}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            _c1, _c2 = st.columns([4, 1])
            with _c2:
                _marca("marca-fb-del")
                if st.button("🗑️ Remover", key=f"dono_fb_del_{_i}", use_container_width=True):
                    if nuvem_supabase.excluir_feedback(fb.get("id")):
                        _toast("Feedback removido.")
                        st.rerun()
                    else:
                        st.error("Falha ao remover (offline/Supabase).")
        st.caption("Os feedbacks alimentam as melhorias — estrelas e comentários são dos próprios usuários do app.")

    if not por_uid:
        st.caption("Nenhuma conta registrada ainda (usuários aparecem aqui depois do primeiro login — e a tabela `usuarios` precisa existir no Supabase).")
        return

    # ─── Busca ─────────────────────────────────────────────────────────────────
    st.markdown("### 📇 Contas")
    _filtro = st.text_input("🔍 Filtrar por nome / e-mail / uid", key="dono_busca").strip().lower()

    for idx, (uid, dados) in enumerate(sorted(
        por_uid.items(),
        key=lambda kv: str(kv[1].get("ultimo_login") or "") ,
        reverse=True,
    )):
        nome = (dados.get("nome") or "").strip()
        empresa = (dados.get("empresa") or "").strip()
        email = dados.get("email") or "—"
        oque_mostra = " ".join((nome, empresa, email, uid)).lower()
        if _filtro and _filtro not in oque_mostra:
            continue

        _tipo = "premium" if dados.get("plano") == "pago" else ("teste" if dados.get("_teste") else "basic")
        _tipo_teste = "user" if dados.get("teste_auto") else "admin"
        _linha1 = f"{nome + ' · ' + empresa if nome and empresa else (nome or empresa or email)}"
        _inicial = (nome or email or "?").strip()[0].upper()
        st.markdown(
            f'<div style="border:1px solid rgba(148,163,184,.22);border-radius:14px;background:rgba(148,163,184,.05);'
            f'padding:12px 14px;margin:6px 0;display:flex;align-items:center;gap:12px">'
            f'{_x_avatar(dados.get("avatar") or "", _inicial)}'
            f'<div style="flex:1;min-width:0">'
            f'<div style="font-weight:700;color:#f1f5f9;font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{_linha1}</div>'
            f'<div style="color:#94a3b8;font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'
            f"{email} · <span style='font-family:monospace'>{(uid or '')[:14]}…</span></div>"
            f'<div style="color:#64748b;font-size:11px;margin-top:2px">'
            f'último acesso: {_fmt_data(dados.get("ultimo_login"))} · criado: {_fmt_data(dados.get("criado_em"))}'
            f'{" · 🎁 teste até " + _fmt_data(dados.get("teste_ate")) if dados.get("teste_ate") else ""}'
            f'{" · ⭐ assinatura até " + _fmt_data(dados.get("assinatura_ate")) if dados.get("assinatura_ate") else ""}'
            f"</div></div>{_badge(_tipo, _tipo_teste)}"
            f'</div>',
            unsafe_allow_html=True,
        )
        _ca1, _ca2, _ca3 = st.columns(3)
        with _ca1:
            _marca("marca-dono-premium")
            if st.button("⭐ Ativar Premium", key=f"dono_premium_{idx}", use_container_width=True, type="primary"):
                if plano.definir_plano_manual(uid, "pago"):
                    _toast("⭐ Premium ativado.")
                else:
                    st.error("Falha (offline/Supabase).")
        with _ca2:
            _marca("marca-dono-teste")
            if st.button("🎁 Dar teste 7 dias", key=f"dono_teste_{idx}", use_container_width=True):
                if plano.definir_trial(uid, 7):
                    _toast("🎁 Teste Premium de 7 dias iniciado.")
                elif not nuvem_supabase.teste_disponivel():
                    st.error(
                        "🎁 **Trial precisa da coluna `teste_ate` no Supabase.** "
                        "Pendente: rode `alter table planos_usuario add column if not exists "
                        "teste_ate timestamptz;` e depois `NOTIFY pgrst, 'reload schema';` "
                        "no SQL Editor (ou clique em Reload schema em Settings → API). "
                        "Os outros botões seguem funcionando."
                    )
                else:
                    st.error("Falha (offline/Supabase).")
        with _ca3:
            _marca("marca-dono-basic")
            if st.button("🔓 Voltar a Basic", key=f"dono_basic_{idx}", use_container_width=True):
                if plano.definir_plano_manual(uid, "free"):
                    _toast("🔓 Conta voltou ao Basic.")
                else:
                    st.error("Falha (offline/Supabase).")

    st.caption(f"Versão {ui_comum.VERSAO} · o cadastro das contas é feito automaticamente a cada login.")


def _marca(classe: str) -> None:
    st.markdown(f'<div class="{classe}" style="display:none"></div>', unsafe_allow_html=True)


def _toast(mensagem: str) -> None:
    st.session_state["dono_aviso"] = mensagem
    st.rerun()