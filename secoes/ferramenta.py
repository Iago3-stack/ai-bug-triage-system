"""Página Ferramenta — triagem de bugs (NLP + IA + RAG) com histórico e dashboard."""
import streamlit as st
import json
import pandas as pd
from urllib.parse import quote

from triagem import triar
import ia
import rag
from hero_animado import _svg_groq
import jira_client
import persistencia
import guardrails
import notificacoes
import plano
import dashboard as dashboard_qa


def render():
    # Divisória que separa o card "Sobre Mim" do título da ferramenta
    st.markdown("""
    <div style="height:3px;width:100%;background:linear-gradient(90deg,transparent,#25D366,#2E7CF6,#7c3aed,transparent);border-radius:999px;margin:8px 0"></div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:1.5em;font-weight:800;line-height:1.25;background:linear-gradient(90deg,#f59e0b 0%,#ef4444 45%,#ec4899 100%);-webkit-background-clip:text;background-clip:text;color:transparent;display:inline-block;margin-top:8px">🤖 Agente de Triagem e Documentação de Bugs 2026</div>
    """, unsafe_allow_html=True)
    st.info("Triagem automática de bugs com NLP + IA: técnico, emocional e com plano de ação em segundos.")

    # Barra de gradiente no topo da página (identidade visual)
    st.markdown("""
    <div style="height:6px;width:100%;background:linear-gradient(90deg,#25D366 0%,#2E7CF6 50%,#7c3aed 100%);border-radius:0 0 8px 8px;position:sticky;top:0;z-index:9999"></div>
    """, unsafe_allow_html=True)

    # Coluna de ação principal + formulário de triagem em card
    st.markdown("""
    <div style="font-size:1em;font-weight:700;background:linear-gradient(90deg,#06b6d4 0%,#3b82f6 45%,#8b5cf6 100%);-webkit-background-clip:text;background-clip:text;color:transparent;display:inline-block;margin:6px 0 2px">Entrada do Usuário (Relato do Bug):</div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="marca-form" style="display:none"></div>', unsafe_allow_html=True)
    descricao_bug = st.text_area("Entrada do Usuário (Relato do Bug):", height=150,
                                 placeholder="Ex: Estou tentando pagar e o botão não responde, estou muito frustrado!",
                                 label_visibility="collapsed")

    usar_llm = st.checkbox(
        "🔮 Usar IA para esta triagem",
        value=True,
        help="Ativa a análise por LLM. Se desmarcado, só o motor local determinístico roda."
    )

    modelos_custom = st.session_state.setdefault("modelos_custom", [])
    for m in modelos_custom:
        m["rotulo"] = m["nome"]
    _provid_classe = {"Automático (Gemini → Groq)": "auto", "Gemini": "gemini", "Groq": "groq"}
    _opcoes_provedor = list(_provid_classe)
    _opcoes_provedor += [f"⭐ {m['nome']}" for m in modelos_custom]

    # Seletor de provedor em cards-botão (o st.radio não aceita HTML/SVG no rótulo).
    provedor_ia = st.session_state.get("provedor_svg", _opcoes_provedor[0])
    if provedor_ia not in _opcoes_provedor:
        provedor_ia = _opcoes_provedor[0]

    st.markdown('<div class="campo-tit" style="font-weight:600;color:#0f172a;margin-bottom:4px">🤖️ Provedor de IA:</div>', unsafe_allow_html=True)
    _cols = st.columns(len(_opcoes_provedor))
    for _i, (_col, _op) in enumerate(zip(_cols, _opcoes_provedor)):
        _classe = _provid_classe.get(_op, "custom")
        _sel = _op == provedor_ia
        if _op == "Gemini":
            _icone = "✨"
        elif _op == "Groq":
            _icone = "⚡"
        elif _classe == "auto":
            _icone = "🔄"
        else:
            _icone = "⭐"
        with _col:
            st.markdown(
                f'<div class="marca-provid marca-prov-{_classe}{" prov-provid-sel" if _sel else ""}" style="display:none"></div>',
                unsafe_allow_html=True,
            )
            if st.button(f"{_icone} {_op}", key=f"prov_{_i}", width="stretch"):
                st.session_state["provedor_svg"] = _op
                st.rerun()
    st.caption("Escolha quem analisa o relato. Automático usa o Gemini e, se cair, troca para o Groq — "
               "ou adicione um modelo próprio no expander abaixo.")

    with st.expander("➕ Adicionar modelo próprio (use sua API de qualquer provedor)"):
        st.markdown('<div class="marca-modelo" style="display:none"></div>', unsafe_allow_html=True)
        nome_custom = st.text_input(
            "🏷️ Nome (aparece no seletor)", key="cm_nome",
            placeholder="Ex: Meu GPT-4o · Gemini Pro pago · DeepSeek")
        tipo_custom = st.radio(
            "Tipo:", ["Gemini (google-genai)", "OpenAI-compatível (OpenAI/DeepSeek/local)"],
            key="cm_tipo", horizontal=True)
        base_url_custom = ""
        if tipo_custom.startswith("Gemini"):
            modelo_custom = st.text_input(
                "Modelo", key="cm_modelo_gemini",
                placeholder="Ex: gemini-3-pro — qualquer modelo que sua chave acesse")
            chave_custom = st.text_input(
                "API Key (opcional — se vazia, usa a sua GEMINI_API_KEY)",
                type="password", key="cm_chave_gemini")
        else:
            base_url_custom = st.text_input(
                "Base URL (OpenAI-compatível)", key="cm_base",
                value="https://api.openai.com/v1",
                placeholder="Ex: api.openai.com/v1 · api.deepseek.com/v1 · localhost:11434/v1")
            modelo_custom = st.text_input(
                "Modelo", key="cm_modelo_openai",
                placeholder="Ex: gpt-4o · gpt-4o-mini · deepseek-chat")
            chave_custom = st.text_input(
                "API Key", type="password", key="cm_chave_openai",
                placeholder="sk-... (fica só na sessão, não é salva)")
        st.markdown('<div class="marca-modelo-btn" style="display:none"></div>', unsafe_allow_html=True)
        if st.button("💾 Adicionar modelo", key="cm_add"):
            nome, modelo = nome_custom.strip(), modelo_custom.strip()
            base = base_url_custom.strip().rstrip("/")
            tipo = "gemini" if tipo_custom.startswith("Gemini") else "openai"
            if not nome or not modelo:
                st.error("Informe o nome exibido e o modelo.")
            elif tipo == "openai" and (not base or not chave_custom.strip()):
                st.error("Para APIs OpenAI-compatíveis, informe a Base URL e a API Key.")
            elif any(m["nome"] == nome for m in modelos_custom):
                st.error(f"Já existe um modelo com o nome '{nome}'.")
            else:
                modelos_custom.append({
                    "nome": nome, "tipo": tipo, "modelo": modelo,
                    "base_url": base, "chave": chave_custom.strip(), "rotulo": nome,
                })
                st.success(f"Modelo '{nome}' adicionado! Selecione ⭐ {nome} no seletor acima.")
                for k in ("cm_nome", "cm_modelo_gemini", "cm_chave_gemini",
                          "cm_modelo_openai", "cm_chave_openai"):
                    st.session_state.pop(k, None)
        if modelos_custom:
            st.markdown("##### Modelos adicionados:")
            for i, m in enumerate(modelos_custom):
                c1, c2 = st.columns([5, 1])
                c1.caption(f"⭐ {m['nome']} · {m['tipo']} · {m['modelo']}")
                if c2.button("🗑", key=f"cm_del_{i}", help="Remover este modelo"):
                    modelos_custom.pop(i)
                    st.rerun()

    st.markdown('<div class="marca-executar" style="display:none"></div>', unsafe_allow_html=True)
    if st.button("Executar Triagem Inteligente"):
            if descricao_bug:
                # --- 1. TRIAGEM NLP (MOTOR LOCAL, DETERMINÍSTICO E OFFLINE) ---
                # O motor triagem.py analisa léxico PT + padrões de negação,
                # sem depender de internet nem de API de tradução.
                resultado = triar(descricao_bug)
                gravidade = resultado["gravidade"]
                sentimento = resultado["sentimento"]
                polaridade = resultado["score"]
                fatores = resultado["fatores"]
                motor = resultado["motor"]

                # Trata aspas digitadas pelo usuário (evita aspas duplicadas no relatório)
                descricao_limpa = descricao_bug.strip().strip('"\'')

                # Guardrails: bloqueia vazamento de credenciais/PII (token, chave, e-mail).
                # Se detectar, mascara o relato e avisa — nada sensível vai pro Gemini,
                # pro Jira, pro GitHub nem pro histórico persistido.
                flag_seguranca = None
                sensiveis = guardrails.detectar(descricao_limpa)
                if sensiveis:
                    descricao_limpa = guardrails.mascarar(descricao_limpa)
                    flag_seguranca = (
                        "🔒 **Credencial/PII detectada no relato** (" + ", ".join(sensiveis)
                        + "): " + guardrails.explicar(sensiveis)
                        + ". A informação sensível foi **mascarada** e não será enviada "
                        "à IA, ao Jira, ao GitHub ou ao histórico."
                    )
                st.session_state["flag_seguranca"] = flag_seguranca

                # --- 2. RELATÓRIO GHERKIN ---
                relatorio = f"""### 🛡️ Relatório de Triagem Técnica
    **Resumo:** {descricao_limpa[:100]}...
    **Prioridade:** {gravidade}
    **Análise de Sentimento:** {sentimento} (Score: {polaridade:.2f})
    **Motor de análise:** {motor}
    **Fatores identificados:** {', '.join(fatores) or 'Nenhum (relato neutro)'}

    **Cenário Gherkin:**
    - DADO QUE o sistema recebeu um relato de erro
    - QUANDO o agente processa a entrada: "{descricao_limpa[:50]}..."
    - ENTÃO a prioridade deve ser definida como {gravidade}."""

                # --- 2.5 ANÁLISE POR IA (LLM opcional; fallback seguro) ---
                resultado_llm = None
                erro_llm = None
                prioridade_final = None
                divergente = None
                if usar_llm and ia.disponivel(modelos_custom):
                    # Blindagem extra: nenhum erro da camada de IA/RAG pode derrubar
                    # o app. Qualquer exceção vira aviso + diagnóstico salvo na sessão.
                    try:
                        with st.spinner("🔮 A IA está analisando sua triagem — pode levar um tempo..."):
                            # RAG: se há histórico persistido, o Gemini consulta os top-k
                            # registros similares (retrieval local) para ver se já aconteceu.
                            registros_para_rag = persistencia.carregar_registros()
                            if not plano.pago():
                                # Plano free: RAG desligado (consulta direta do LLM).
                                registros_para_rag = []
                            provedor = {
                                "Automático (Gemini → Groq)": None,
                                "Gemini": "gemini",
                                "Groq": "groq",
                            }.get(provedor_ia)
                            if provedor is None and provedor_ia.startswith("⭐ "):
                                _cfg = next(
                                    (m for m in modelos_custom if m["nome"] == provedor_ia[2:]), None
                                )
                                if _cfg:
                                    provedor = _cfg
                            if registros_para_rag:
                                resultado_llm, erro_llm = rag.analisar_com_rag(
                                    descricao_limpa, registros_para_rag, provedor=provedor
                                )
                            else:
                                resultado_llm, erro_llm = ia.analisar_llm(descricao_limpa, provedor=provedor)
                    except Exception as exc:
                        import traceback
                        # Salva o erro REAL (sem redação) para o expander de diagnóstico.
                        st.session_state["erro_ia_bruto"] = traceback.format_exc()
                        erro_llm = f"IA/RAG: {type(exc).__name__}: {str(exc)[:200]}"
                        resultado_llm = None
                    if resultado_llm:
                        llm_modelo = (ia.ULTIMO_MODELO or ia.MODELO)
                        llm_provedor = ia.ULTIMO_PROVEDOR or "IA"
                        # Regra de reconciliação: o mais grave vence, e divergência vira alerta.
                        sev_local = {"NORMAL ✅": 1, "MÉDIA ⚠️": 2, "CRÍTICA 🚨": 4}[gravidade]
                        sev_ia = {"baixa": 1, "media": 2, "alta": 3, "critica": 4}.get(resultado_llm["severidade"], 2)
                        sev_final = max(sev_local, sev_ia)
                        prioridade_final = {1: "NORMAL ✅", 2: "MÉDIA ⚠️", 3: "ALTA 🚨", 4: "CRÍTICA 🚨"}[sev_final]
                        divergente = sev_local != sev_ia
                        relatorio += f"""
    ---
    🔮 **Análise por IA ({llm_provedor} · {llm_modelo}):**
    - Severidade sugerida: {resultado_llm['severidade']}
    - Categoria: {resultado_llm['categoria']}
    - Causa raiz provável: {resultado_llm['causa_raiz']}
    - Resumo técnico: {resultado_llm['resumo_tecnico']}
    - Passos para reproduzir:
    """ + "\n".join(f"\t{i}. {p}" for i, p in enumerate(resultado_llm["passos_repro"], 1)) + f"""

    - **Prioridade final (máx. entre motores): {prioridade_final}**
    - **Divergência entre motores: {'SIM ⚠️' if divergente else 'não'}**
    """
                        if resultado_llm.get("ja_aconteceu") is not None:
                            ids_rag = resultado_llm.get("registros_similar") or []
                            estado_rag = "SIM ⚠️" if resultado_llm.get("ja_aconteceu") else "não"
                            similar_tex = (
                                "`" + "`, `".join(ids_rag) + "`" if ids_rag else "sem registros similares"
                            )
                            relatorio += f"""
    📚 **Histórico consultado (RAG):**
    - **Já aconteceu antes?:** {estado_rag}
    - **Registros similares:** {similar_tex}
    - **Como foi resolvido antes:** {resultado_llm.get('resolucao_anterior') or '—'}
    """

                # --- 3. HISTÓRICO DA SESSÃO ---
                if "historico" not in st.session_state:
                    st.session_state["historico"] = []
                st.session_state["historico"].append({
                    "Relato": descricao_limpa,
                    "Score": round(polaridade, 2),
                    "Gravidade": gravidade,
                    "Sentimento": sentimento,
                })

                # --- 3.5 PERSISTÊNCIA (JSONL): snapshot fiel do que foi executado ---
                snapshot = {
                    "resumo": descricao_limpa[:100],
                    "descricao": descricao_limpa,
                    "motor": motor,
                    "gravidade": gravidade,
                    "score": round(polaridade, 2),
                    "sentimento": sentimento,
                    "fatores": fatores,
                    "usou_ia": bool(usar_llm),
                    "sensiveis_mascarados": list(sensiveis) if sensiveis else [],
                }
                if resultado_llm:
                    snapshot.update({
                        "provedor_ia": llm_provedor,
                        "modelo_ia": llm_modelo,
                        "severidade_ia": resultado_llm["severidade"],
                        "categoria_ia": resultado_llm["categoria"],
                        "causa_raiz_ia": resultado_llm["causa_raiz"],
                        "resumo_tecnico_ia": resultado_llm["resumo_tecnico"],
                        "passos_ia": resultado_llm["passos_repro"],
                        "prioridade_final": prioridade_final,
                        "divergente": divergente,
                    })
                    if resultado_llm.get("ja_aconteceu") is not None:
                        snapshot.update({
                            "rag_ja_aconteceu": resultado_llm.get("ja_aconteceu"),
                            "rag_resolucao": resultado_llm.get("resolucao_anterior"),
                            "rag_similares": resultado_llm.get("registros_similar") or [],
                        })
                else:
                    snapshot["erro_ia"] = erro_llm
                snapshot["relatorio_completo"] = relatorio
                # Guarda o id persistido: permite registrar a resolução depois e
                # alimentar o RAG ("como foi resolvido da última vez").
                st.session_state["ultimo_registro_id"] = persistencia.registrar_triagem(snapshot).get("id", "")

                # --- 3.6 ALERTA (e-mail/Discord) para prioridades CRÍTICA/ALTA ---
                # Roda em background silencioso: sem canal configurado ou em falha
                # de rede, a triagem segue normalmente (nunca levanta exceção).
                _provedor_alerta = ia.ULTIMO_PROVEDOR if usar_llm else None
                _prio_alerta = prioridade_final or gravidade
                _email_cfg, _discord_cfg = plano.aplicar_limite_canais(
                    notificacoes.email_configurado(), notificacoes.discord_configurado()
                )
                _email_ok = notificacoes.notificar_email(_prio_alerta, descricao_limpa, provedor=_provedor_alerta) if _email_cfg else None
                _discord_ok = notificacoes.notificar_discord(_prio_alerta, descricao_limpa, provedor=_provedor_alerta) if _discord_cfg else None
                if "CRÍTICA" in _prio_alerta or "ALTA" in _prio_alerta:
                    _detalhes = []
                    if _email_cfg:
                        _detalhes.append(f"✉️ e-mail {'enviado ✅' if _email_ok else 'FALHOU ❌'}")
                    if _discord_cfg:
                        _detalhes.append(f"🔔 Discord {'enviado ✅' if _discord_ok else 'FALHOU ❌'}")
                    st.session_state["status_alerta"] = (
                        ("🔔 **Alerta CRÍTICA/ALTA:** " + " · ".join(_detalhes))
                        if _detalhes
                        else "🔕 **Alerta CRÍTICA/ALTA:** nenhum canal configurado (e-mail/Discord) — configure os Secrets para ser avisado daqui pra frente."
                    )
                else:
                    st.session_state["status_alerta"] = None

                # --- 4. GUARDA O RESULTADO (sobrevive a reruns dos botões de exportação) ---
                st.session_state["resultado"] = {
                    "descricao_limpa": descricao_limpa,
                    "relatorio": relatorio,
                    "gravidade": gravidade,
                    "polaridade": polaridade,
                    "resultado_llm": resultado_llm,
                    "erro_llm": erro_llm,
                    "prioridade_final": prioridade_final,
                    "divergente": divergente,
                }
            else:
                st.warning("Digite a descrição do bug para executar a triagem.")

    # --- RENDERIZAÇÃO DO RESULTADO (fora do if do botão: não some em reruns) ---
    r = st.session_state.get("resultado")
    if r:
        flag_seguranca = st.session_state.get("flag_seguranca")
        if flag_seguranca:
            st.warning(flag_seguranca)
        relatorio = r["relatorio"]
        gravidade = r["gravidade"]
        descricao_limpa = r["descricao_limpa"]
        resultado_llm = r["resultado_llm"]
        erro_llm = r["erro_llm"]
        prioridade_final = r["prioridade_final"]
        divergente = r["divergente"]

        # --- 4. INTERFACE DASHBOARD ---
        st.divider()
        c1, c2, c3 = st.columns(3)
        c1.metric("Gravidade IA", gravidade)
        c2.metric("Sentimento", f"{r['polaridade']:.2f}")
        c3.metric("Status", "Análise Determinística OK")

        st.markdown("### 📝 Relatório Gerado! ✅")
        st.code(relatorio, language="markdown")

        status_alerta = st.session_state.get("status_alerta")
        if status_alerta:
            (st.warning if "FALHOU" in status_alerta or "nenhum canal" in status_alerta else st.success)(status_alerta)

        if resultado_llm:
            provedor_rotulo = ia.ULTIMO_PROVEDOR or "LLM"
            if provedor_rotulo.startswith("Gemini"):
                icone_ai = "✨️"
            elif provedor_rotulo.startswith("Groq"):
                icone_ai = _svg_groq(18)
            else:
                icone_ai = "🔮"
            st.markdown(f"### {icone_ai} Análise por IA ({provedor_rotulo})", unsafe_allow_html=True)
            ca, cb, cc = st.columns(3)
            ca.metric("Severidade (IA)", resultado_llm["severidade"].upper())
            cb.metric("Categoria", resultado_llm["categoria"].capitalize())
            cc.metric("Modelo", ia.ULTIMO_MODELO or ia.MODELO)
            st.write(f"**Causa raiz provável:** {resultado_llm['causa_raiz']}")
            st.write("**Passos para reproduzir:**")
            for i, p in enumerate(resultado_llm["passos_repro"], 1):
                st.write(f"{i}. {p}")
            st.caption("💡 Análise gerada por LLM — use como suporte à triagem determinística do motor local.")

            if resultado_llm.get("ja_aconteceu") is not None:
                st.markdown("---")
                st.markdown("### 📚 RAG — histórico consultado")
                ids_rag = resultado_llm.get("registros_similar") or []
                if resultado_llm["ja_aconteceu"]:
                    st.warning(
                        f"⚠️ Este problema **já aconteceu antes**! "
                        f"Registro(s) similar(es): `{'`, `'.join(ids_rag) if ids_rag else '—'}`"
                    )
                    if resultado_llm.get("resolucao_anterior"):
                        st.write(f"🔧 **Como foi resolvido da última vez:** {resultado_llm['resolucao_anterior']}")
                    else:
                        st.caption("Histórico não indicou uma resolução anterior para este caso.")
                else:
                    st.success("✅ Nenhum registro anterior similar encontrado — possível caso novo.")
                st.caption("Retrieval local por similaridade de tokens (Jaccard) sobre o histórico persistido — nada é enviado além do relato e dos registros similares.")

            st.markdown("---")
            if "CRÍTICA" in prioridade_final:
                cor_badge = "#dc2626"
            elif "ALTA" in prioridade_final:
                cor_badge = "#ea580c"
            elif "MÉDIA" in prioridade_final:
                cor_badge = "#d97706"
            elif "BAIXA" in prioridade_final or "NORMAL" in prioridade_final:
                cor_badge = "#059669"
            else:
                cor_badge = "#2563eb"
            st.markdown(f"""
    <div style="display:flex;align-items:center;gap:12px;margin-top:6px">
      <span class="badge-prioridade" style="background:{cor_badge}">🎯 {prioridade_final}</span>
      <span class="prio-final" style="font-weight:800;font-size:1.3em;color:#111827">Prioridade Final</span>
    </div>
    """, unsafe_allow_html=True)
            if divergente:
                st.warning(f"⚠️ Divergência detectada: motor local **{gravidade}** x IA **{resultado_llm['severidade'].upper()}**. Sinais conflitantes — revisão humana recomendada.")
            else:
                st.success("✅ Motores concordam na prioridade.")
        elif erro_llm:
            st.info("🔮 Análise por IA indisponível neste momento — o motor local determinístico segue no controle.")
            with st.expander("🔧 Diagnóstico interno (IA/RAG)", key="ex_diag"):
                st.markdown('<div class="marca-diag" style="display:none"></div>', unsafe_allow_html=True)
                st.write(f"**Módulo `ia` tem `analisar_llm_rag`:** {'sim' if hasattr(ia, 'analisar_llm_rag') else 'NÃO → deploy desatualizado'}")
                st.write(f"**Erro redigido pela Cloud:** `{erro_llm}`")
                trace_ia = st.session_state.get("erro_ia_bruto")
                if trace_ia:
                    st.code(trace_ia, language="python")
                else:
                    st.write("Nenhum traceback capturado localmente (padrão de erro veio do estado anterior).")

        # --- 5. EXPORTAR: baixar relatório + abrir no GitHub + enviar ao Jira ---
        colunas = st.columns(3)
        colunas[0].markdown('<div class="marca-download" style="display:none"></div>', unsafe_allow_html=True)
        colunas[0].download_button(
            "📥 Baixar relatório (.md)",
            data=relatorio.encode("utf-8"),
            file_name="relatorio_triagem_bug.md",
            mime="text/markdown",
        )
        titulo = quote(descricao_limpa[:80])
        corpo = quote(relatorio[:4000])
        colunas[1].markdown('<div class="marca-issue" style="display:none"></div>', unsafe_allow_html=True)
        colunas[1].link_button(
            "🐙 Nova Issue no GitHub",
            f"https://github.com/iago3-stack/ai-bug-triage-system/issues/new?title={titulo}&body={corpo}",
        )
        colunas[2].markdown('<div class="marca-jira" style="display:none"></div>', unsafe_allow_html=True)
        if colunas[2].button("📋 Exportar para Jira", use_container_width=True, key="btn_exportar_jira"):
            if jira_client.configurado():
                with st.spinner("📋 Enviando issue ao Jira..."):
                    ok_export, resultado_jira, erro_jira = jira_client.criar_issue(
                        descricao_limpa[:100], relatorio, gravidade
                    )
                if ok_export:
                    st.session_state["exportacao_jira"] = (True, resultado_jira["key"], resultado_jira["url"])
                    persistencia.registrar_exportacao_jira(resultado_jira["key"], resultado_jira["url"])
                else:
                    st.session_state["exportacao_jira"] = (False, None, erro_jira)
            else:
                st.session_state["exportacao_jira"] = (
                    False, None, "Configure o e-mail, o API token e a chave do projeto no sidebar."
                )

        if "exportacao_jira" in st.session_state:
            ok_export, chave_issue, detalhe = st.session_state["exportacao_jira"]
            if ok_export:
                st.success(f"✅ Issue **{chave_issue}** criada no Jira!")
                st.markdown(f"[🔗 Abrir issue no Jira]({detalhe})")
            else:
                st.error(f"❌ Não foi possível exportar para o Jira: {detalhe}")

        with st.expander("🔧 Registrar como este caso foi resolvido (alimenta o RAG)", key="ex_resolucao"):
            st.markdown('<div class="marca-resolucao" style="display:none"></div>', unsafe_allow_html=True)
            st.caption(
                "Depois de resolver o bug, volte e descreva a solução aqui. Nas próximas "
                "triagens similares, o RAG vai responder **'como foi resolvido da última vez'** "
                "usando esse registro."
            )
            resolucao_draft = st.text_area("Descreva a solução aplicada:", key="resolucao_draft")
            if st.button("💾 Registrar resolução", key="btn_registrar_resolucao"):
                texto = resolucao_draft.strip()
                registro_id = st.session_state.get("ultimo_registro_id", "")
                if texto and registro_id and persistencia.registrar_resolucao(registro_id, texto):
                    st.success("✅ Resolução gravada! Este aprendizado passou a integrar o histórico consultado pelo RAG.")
                else:
                    st.warning("Nada foi registrado — descreva a solução ou confira se a triagem foi persistida.")

        st.info("📋 O relatório também pode ser copiado direto da caixa acima para o Jira ou GitHub!")
        st.success("Triagem finalizada com sucesso! ✅")

        # --- 6. HISTÓRICO (TABELA pandas) ---
        with st.expander(f"📊 Histórico de triagens desta sessão ({len(st.session_state['historico'])})", key="ex_sessao"):
            st.markdown('<div class="marca-sessao" style="display:none"></div>', unsafe_allow_html=True)
            st.dataframe(pd.DataFrame(st.session_state["historico"]),
                         use_container_width=True, hide_index=True)
            if st.button("🗑️ Limpar histórico"):
                st.session_state["historico"] = []

    # --- 6.5 HISTÓRICO PERSISTIDO (JSONL local ou Supabase na nuvem) ---
    registros_totais = persistencia.carregar_registros()
    if not plano.pago() and len(registros_totais) > plano.limite_historico_free():
        # Plano free: resumo limitado às últimas triagens (história completa = pago).
        registros_totais = registros_totais[-plano.limite_historico_free():]
    if registros_totais:
        backend = (
            "☁️ Supabase (nuvem — público)"
            if persistencia._usar_nuvem()
            else "💾 JSONL local (efêmero na Cloud — só você vê)"
        )
        if not plano.pago():
            st.caption(
                f"🔓 Plano **Basic**: histórico resumido às últimas "
                f"{plano.limite_historico_free()} triagens · RAG desligado · 1 canal de alerta. "
                "O plano Premium libera histórico completo, multi-canal e análise de IA."
            )
        with st.expander(f"📁 Histórico persistido ({backend}) — {len(registros_totais)} triagem(ns) salva(s)", key="ex_historico"):
            st.markdown('<div class="marca-historico" style="display:none"></div>', unsafe_allow_html=True)
            st.markdown("##### 📤 Exportar histórico completo (backup)")
            col_js, col_csv, _ = st.columns([1, 1, 2])
            col_js.download_button(
                "⬇️ Exportar JSON",
                data=json.dumps(registros_totais, ensure_ascii=False, indent=2).encode("utf-8"),
                file_name="historico_triagens.json",
                mime="application/json",
                key="hp_exp_json",
            )
            col_csv.download_button(
                "⬇️ Exportar CSV",
                data=pd.DataFrame(registros_totais).to_csv(index=False).encode("utf-8"),
                file_name="historico_triagens.csv",
                mime="text/csv",
                key="hp_exp_csv",
            )
            datas = persistencia.datas_disponiveis()
            data_sel = st.selectbox("📅 Escolha a data", datas, key="hp_data")
            do_dia = persistencia.registros_por_data(data_sel)
            st.dataframe(pd.DataFrame([
                {
                    "Hora": r["data_hora"][11:19],
                    "Resumo": r["resumo"],
                    "Gravidade": r["gravidade"],
                    "Score": r["score"],
                    "IA": "sim" if r.get("usou_ia") else "não",
                    "Jira": r.get("jira_key") or "—",
                    "Resolvido": "sim" if r.get("resolucao") else "—",
                } for r in do_dia
            ]), use_container_width=True, hide_index=True)
            def _cor_gravidade(g):
                g = g.upper()
                if "CRÍTICA" in g:
                    return "#dc2626"
                if "ALTA" in g:
                    return "#ea580c"
                if "MÉDIA" in g:
                    return "#d97706"
                if "BAIXA" in g or "NORMAL" in g:
                    return "#059669"
                return "#2563eb"

            if do_dia:
                cards = []
                for r in do_dia:
                    c_g = _cor_gravidade(r["gravidade"])
                    cards.append(f"""
    <div class="hcard" style="background:#f0fdf4;border:1px solid #a7f3d0;border-radius:10px;padding:8px 12px;min-width:170px">
      <div class="hcard-t" style="font-weight:700;font-size:13px;color:#064e3b">🕐 {r['data_hora'][11:19]}</div>
      <div style="font-size:13px;font-weight:700;color:{c_g};margin-top:2px">{r['gravidade']} · score {r['score']:.2f}</div>
      <div class="hcard-s" style="font-size:12px;color:#475569;margin-top:2px">IA {'✅' if r.get('usou_ia') else '—'} · Jira {r.get('jira_key') or '—'} · 🔧 {'sim' if r.get('resolucao') else '—'}</div>
    </div>""")
                st.markdown(
                    f'<div style="display:flex;gap:10px;flex-wrap:wrap;margin:2px 0 10px">{"".join(cards)}</div>',
                    unsafe_allow_html=True,
                )
            rotulos = [
                f"{r['data_hora'][11:19]} · {r['gravidade']}"
                for r in do_dia
            ]
            indice = st.selectbox("📄 Selecione o relatório", range(len(do_dia)),
                                  format_func=lambda i: rotulos[i], key="hp_rel")
            reg = do_dia[indice]
            st.code(reg["relatorio_completo"], language="markdown")
            st.download_button(
                "📥 Baixar relatório desta triagem (.md)",
                data=reg["relatorio_completo"].encode("utf-8"),
                file_name=f"relatorio_{reg['data']}_{reg['data_hora'][11:16].replace(':', 'h')}.md",
                mime="text/markdown",
                key="hp_download",
            )
            st.divider()
            if reg.get("resolucao"):
                st.markdown("""
    <div style="font-weight:800;font-size:1.05em;background:linear-gradient(90deg,#059669 0%,#0d9488 100%);-webkit-background-clip:text;background-clip:text;color:transparent;display:inline-block">🔧 Resolução deste caso: <span style="background:transparent;color:#059669">✅ já registrada</span></div>
    """, unsafe_allow_html=True)
            else:
                st.markdown("""
    <div style="font-weight:800;font-size:1.05em;background:linear-gradient(90deg,#059669 0%,#0d9488 100%);-webkit-background-clip:text;background-clip:text;color:transparent;display:inline-block">🔧 Resolução deste caso: <span style="background:transparent;color:#d97706">não registrada</span></div>
    """, unsafe_allow_html=True)
            st.caption("Guarde aqui como o bug foi resolvido — vira aprendizado consultado pelo RAG nas próximas triagens similares.")
            nova_res = st.text_area(
                "Como este caso foi resolvido:",
                value=reg.get("resolucao") or "",
                key=f"res_{reg['id']}",
            )
            if st.button("💾 Salvar resolução", key=f"btn_res_{reg['id']}"):
                if nova_res.strip() and persistencia.registrar_resolucao(reg["id"], nova_res.strip()):
                    st.success("✅ Resolução salva no histórico!")
                else:
                    st.warning("Nada foi alterado (campo vazio ou registro não encontrado).")
    # --- 6.6 DASHBOARD DE QA (visão geral do histórico persistido) ---
    if registros_totais:
        with st.expander("📈 Dashboard de QA — visão geral do histórico", key="ex_dashboard"):
            st.markdown('<div class="marca-dashboard" style="display:none"></div>', unsafe_allow_html=True)
            dashboard_qa.render_dashboard(registros_totais)
