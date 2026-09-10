# Dashboard de QA — leitura do histórico persistido (data/historico.jsonl).
# Visa responder, de relance:
#   - quantas CRÍTICAS/MÉDIAS/NORMais temos?       (inclui ALTA via IA)
#   - o volume está crescendo/subindo por dia?      (série por data)
#   - qual funcionalidade mais aparece nos relatos? (categorização por léxico local)
#   - a IA diverge do motor local?                  (quando há registros com IA)

import re
from collections import Counter

import pandas as pd
import streamlit as st

import guardrails
import plano

# Ordem de gravidade (da pior para a mais branda) para ordenar barras.
_ORDEM_SEVERIDADE = ["CRÍTICA 🚨", "ALTA 🚨", "MÉDIA ⚠️", "NORMAL ✅"]

# Funcionalidades reconhecíveis por expressões (categorização 100% offline).
FUNCOES = [
    (re.compile(r"\b(login|entr[ae]r|acessar|conta|credenciais)\b"), "Login/Conta"),
    (re.compile(r"\b(pag(amento|ando)?|cobr(ando)?|assinatura|carrinho|pedido)\b"), "Pagamento/Compra"),
    (re.compile(r"\brelat[óo]rio|pdf|export"), "Relatório/Exportação"),
    (re.compile(r"\b(busca|pesquis|consulta)\w*"), "Busca/Consulta"),
    (re.compile(r"\b(chat|suporte)\b"), "Chat/Suporte"),
    (re.compile(r"\binstal\w*"), "Instalação"),
    (re.compile(r"\b(sincroniz\w*|atualiza)\w*"), "Sincronização/Atualização"),
    (re.compile(r"\b(cadastr\w*|formul[áa]rio)\b"), "Cadastro/Formulário"),
    (re.compile(r"\b(import|anex|upload)\w*"), "Importação/Anexo"),
    (re.compile(r"\bgr[áa]fic\w*"), "Gráfico"),
    (re.compile(r"\bnotifica\w*"), "Notificação"),
    (re.compile(r"\b(senha|recupera\w*|redefinir)\b"), "Senha/Recuperação"),
    (re.compile(r"\b(extrato|banc[áa]rio)\w*"), "Extrato/Banco"),
    (re.compile(r"\b(imposto|financeir\w*|notas?)\b"), "Fiscal/Financeiro"),
    (re.compile(r"\bconfigura\w*"), "Configurações"),
    (re.compile(r"\b(tabela|planilha)\b"), "Tabela/Planilha"),
]

# Termos do vocabulário de teste que NÃO devem escalar severidade sozinhos.
TERMOS_TESTE = re.compile(r"\b(erro|bug|falha|defeito)\b")


def _texto(reg: dict, chave: str) -> str:
    valor = reg.get(chave)
    return " ".join(str(valor).lower().split()) if valor else ""


def taxa_divergencia(registros: list[dict]) -> float | None:
    """Percentual de triagens com IA em que a IA divergiu do motor local (0-100)."""
    com_ia = [r for r in registros if r.get("usou_ia")]
    if not com_ia:
        return None
    n_div = sum(1 for r in com_ia if r.get("divergente"))
    return round(n_div / len(com_ia) * 100, 1)


def top_causas(registros: list[dict], n: int = 5) -> pd.DataFrame:
    """Causas raiz apontadas pela IA, agrupadas por similaridade de texto (case/dupla espaço)."""
    contagem: Counter = Counter()
    for reg in registros:
        causa = _texto(reg, "causa_raiz_ia")
        if causa:
            contagem[causa] += 1
    if not contagem:
        return pd.DataFrame(columns=["causa raiz", "quantidade"])
    top = pd.DataFrame(contagem.most_common(n)[:n], columns=["causa raiz", "quantidade"])
    return top.set_index("causa raiz")


def saude_suite(registros: list[dict]) -> float:
    """Score de saúde da suíte 0-10: normalidade, divergência IA vs. local, score, uso de IA/RAG."""
    if not registros:
        return 0.0
    total = len(registros)
    taxa = sum(1 for r in registros if r.get("usou_ia"))
    score = saude = 5.0
    normal = sum(1 for r in registros if r.get("gravidade") == "NORMAL ✅")
    saude += (normal / total) * 2.0
    media_score = sum(float(r.get("score", 0.0)) for r in registros) / total
    normalizado = max(0.0, min(1.0, (media_score + 5.0) / 8.0))
    saude += normalizado * 1.0
    divergencia = taxa_divergencia(registros)
    if divergencia is not None:
        saude -= divergencia / 100 * 1.5
    if taxa:
        saude += 0.75
    if any(r.get("rag_resolucao") for r in registros):
        saude += 0.75
    return round(max(0.0, min(10.0, saude)), 1)


def funcoes_afetadas(registros: list[dict]) -> Counter:
    """Conta menções de cada funcionalidade (uma vez por registro)."""
    contagem: Counter = Counter()
    for reg in registros:
        texto = (reg.get("descricao") or "").lower()
        for padrao, rotulo in FUNCOES:
            if padrao.search(texto):
                contagem[rotulo] += 1
    return contagem


def _tem_funcionalidade(reg: dict, rotulo: str) -> bool:
    """True se o registro menciona a funcionalidade `rotulo`."""
    texto = (reg.get("descricao") or "").lower()
    return any(padrao.search(texto) for padrao, r in FUNCOES if r == rotulo)


def false_positivos_evitados(registros: list[dict]) -> int:
    """NORMALs que contêm vocabulário técnico de teste (erro/bug/falha)."""
    return sum(
        1 for reg in registros
        if reg.get("gravidade") == "NORMAL ✅" and bool(TERMOS_TESTE.search(reg.get("descricao") or ""))
    )


def _sensiveis(reg: dict) -> list[str]:
    valor = reg.get("sensiveis_mascarados")
    if isinstance(valor, list):
        return [str(v) for v in valor if v]
    if isinstance(valor, float) and valor != valor:  # NaN (coluna ausente no DataFrame)
        return []
    return [str(valor)] if valor else []


def guardrails_auditoria(registros: list[dict]) -> Counter:
    """Conta por tipo de credencial/PII mascarada (auditoria do guardrail)."""
    return Counter(tipo for reg in registros for tipo in _sensiveis(reg))


def _contagem_por(registros: list[dict], chave: str, ordenar: list[str] | None = None) -> pd.DataFrame:
    contagem = Counter(reg.get(chave, "—") for reg in registros)
    linhas = [(valor, n) for valor, n in contagem.items() if valor != "—"]
    linhas.sort(key=lambda item: (ordenar or []).index(item[0]) if (ordenar and item[0] in (ordenar or [])) else 99)
    return pd.DataFrame(linhas, columns=[chave, "quantidade"])


def tabela_recente(registros: list[dict], limite: int = 20) -> pd.DataFrame:
    """Últimas triagens em DataFrame pronto para exibir (tolera registros sem Jira)."""
    df = pd.DataFrame(registros)
    if df.empty:
        return df
    df = df.sort_values("data_hora", ascending=False).head(limite)
    tabela = pd.DataFrame({
        "hora": df["data_hora"].str[11:19].values,
        "data": df["data"].values,
        "Resumo": df["resumo"].values,
        "Gravidade": df["gravidade"].values,
        "Score": df["score"].values,
        "IA": [
            ("não" if not bool(r.get("usou_ia"))
             else (r.get("provedor_ia") if isinstance(r.get("provedor_ia"), str) and r.get("provedor_ia") else "sim"))
            for _, r in df.iterrows()
        ],
    })
    if "jira_key" in df.columns:
        jira = df["jira_key"].fillna("—").values
    else:
        jira = ["—"] * len(df)
    tabela["Jira"] = jira
    if "sensiveis_mascarados" in df.columns or any(_sensiveis(r) for r in registros):
        tabela["🔒"] = ["sim" if _sensiveis(r) else "—" for _, r in df.iterrows()]
    return tabela


def render_dashboard(registros: list[dict]) -> None:
    if not registros:
        st.info("Nenhuma triagem persistida ainda — execute o relato de um bug para alimentar o Dashboard.")
        return

    df = pd.DataFrame(registros)
    n_crit = int((df["gravidade"] == "CRÍTICA 🚨").sum() + (df["gravidade"] == "ALTA 🚨").sum())
    n_media = int((df["gravidade"] == "MÉDIA ⚠️").sum())
    n_normal = int((df["gravidade"] == "NORMAL ✅").sum())
    score_medio = float(df["score"].mean())
    n_ia = int(df["usou_ia"].sum()) if "usou_ia" in df else 0
    fp = false_positivos_evitados(registros)

    st.markdown(f"""
<div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:8px">
  <div style="flex:1;min-width:180px;background:linear-gradient(135deg,#2563eb,#3b82f6);border-radius:14px;padding:14px 18px;color:#ffffff">
    <div style="font-size:12px;opacity:.85;font-weight:600">🧺 Total de triagens</div>
    <div style="font-size:30px;font-weight:800;line-height:1.1">{len(registros)}</div>
  </div>
  <div style="flex:1;min-width:180px;background:linear-gradient(135deg,#dc2626,#ef4444);border-radius:14px;padding:14px 18px;color:#ffffff">
    <div style="font-size:12px;opacity:.85;font-weight:600">🚨 Críticas / Altas</div>
    <div style="font-size:30px;font-weight:800;line-height:1.1">{n_crit}</div>
  </div>
  <div style="flex:1;min-width:180px;background:linear-gradient(135deg,#15803d,#22c55e);border-radius:14px;padding:14px 18px;color:#ffffff">
    <div style="font-size:12px;opacity:.85;font-weight:600">🔮 Com IA (LLM)</div>
    <div style="font-size:30px;font-weight:800;line-height:1.1">{n_ia}</div>
  </div>
  <div style="flex:1;min-width:180px;background:linear-gradient(135deg,#7c3aed,#8b5cf6);border-radius:14px;padding:14px 18px;color:#ffffff">
    <div style="font-size:12px;opacity:.85;font-weight:600">🛡️ Saúde da suíte</div>
    <div style="font-size:30px;font-weight:800;line-height:1.1">{saude_suite(registros):.1f}<span style="font-size:14px;font-weight:600;opacity:.8">/10</span></div>
  </div>
</div>
""", unsafe_allow_html=True)

    pct_crit = round(n_crit / len(registros) * 100, 1)
    st.markdown(
        f"<span style='font-size:13px'>🚨 <b>{pct_crit:.0f}%</b> das triagens são CRÍTICAS/ALTAS</span>",
        unsafe_allow_html=True,
    )
    st.progress(min(1.0, pct_crit / 100))

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🧺 Triagens", len(registros))
    c2.metric("🚨 Críticas/Altas", n_crit)
    c3.metric("⚠️ Médias", n_media)
    c4.metric("✅ Normais", n_normal)
    c5.metric("📉 Score médio", f"{score_medio:.2f}")

    fp_col, mask_col, ia_col = st.columns(3)
    fp_col.metric("🟫 Falso-positivo evitado (vocab. de teste)", fp)
    fp_expandir = fp_col.expander("O que é esse número?", expanded=False)
    fp_expandir.caption(
        "Relatos que usam 'erro', 'bug' ou 'falha' como vocabulário normal de teste e "
        "foram classificados como NORMAL — prova de que o motor não dispara por palavra isolada."
    )
    n_sens = sum(1 for r in registros if _sensiveis(r))
    mask_col.metric("🔒 Credenciais/PII mascaradas", n_sens)
    mask_exp = mask_col.expander("Por que mascaramos?", expanded=False)
    tipos = guardrails_auditoria(registros)
    if tipos:
        linhas = [
            f"- **{tipo}** ({n}×): {guardrails.MOTIVOS.get(tipo, 'dado sensível')}"
            for tipo, n in tipos.most_common()
        ]
        mask_exp.markdown(
            "Nenhum token/chave/e-mail/CPF vai para a IA, Jira, GitHub ou histórico:\n\n"
            + "\n".join(linhas)
        )
    else:
        mask_exp.caption("Nenhuma ocorrência ainda — os guardrails vêm bloqueando o vazamento desde o início.")

    # --- Filtro global por funcionalidade ---
    funcoes_globais = funcoes_afetadas(registros)
    opcoes = ["🧺 Todas as funcionalidades"] + [rot for rot in funcoes_globais]
    escolha = st.selectbox("Filtrar relatório por funcionalidade", opcoes)
    if escolha == opcoes[0]:
        regs = list(registros)
    else:
        regs = [r for r in registros if _tem_funcionalidade(r, escolha)]
    df_f = pd.DataFrame(regs)
    if regs:
        esquerda, direita = st.columns(2)
        with esquerda:
            st.markdown("##### Distribuição de severidade")
            dados_sev = _contagem_por(regs, "gravidade", _ORDEM_SEVERIDADE).set_index("gravidade")
            st.bar_chart(dados_sev, color="#2E7CF6")
        with direita:
            st.markdown("##### Volume por dia")
            dados_dia = df_f.groupby("data").size().sort_index()
            st.line_chart(pd.DataFrame({"triagens": dados_dia}), color="#FF7043")

        dias_score = df_f.groupby("data")["score"].mean().dropna()
        if not dias_score.empty:
            st.markdown("##### Evolução do score médio por dia")
            st.line_chart(pd.DataFrame({"score médio": dias_score}), color="#7C4DFF")

        if escolha == opcoes[0]:
            st.markdown("##### Funcionalidades mais afetadas")
            if funcoes_globais:
                top = pd.DataFrame(
                    funcoes_globais.most_common(), columns=["funcionalidade", "menções"]
                ).set_index("funcionalidade")
                st.bar_chart(top, color="#9C27B0")
            else:
                st.caption("Nenhuma funcionalidade reconhecível nos relatos persistidos.")
        else:
            st.markdown(f"##### Relatos em {escolha}")
            st.caption(f"{len(regs)} triagens nesta funcionalidade — severidade, volume e score médio acima já refletem o filtro.")
    else:
        st.warning(f"Nenhum relato reconhecível na funcionalidade '{escolha}'.")

    if plano.pago():
        st.markdown("##### Causas raiz mais comuns (via IA)")
        causas = top_causas(regs)
        if not causas.empty:
            st.bar_chart(causas, color="#26A69A")
        else:
            st.caption("Nenhuma causa raiz registrada pela IA nos relatos persistidos.")

        st.markdown("##### Comparativo IA vs. motor local")
        if "usou_ia" in df_f and not df_f[df_f["usou_ia"]].empty:
            com_ia = df_f[df_f["usou_ia"]]
            n_div = int(com_ia["divergente"].sum()) if "divergente" in com_ia else 0
            taxa = taxa_divergencia(regs)
            m1, m2 = st.columns(2)
            m1.metric("Divergências IA vs. léxico", f"{n_div} de {len(com_ia)}")
            m2.metric("Taxa de divergência", "—" if taxa is None else f"{taxa:.1f}%")
            if n_div:
                cols = {
                    "data_hora": "quando",
                    "resumo": "Resumo",
                    "gravidade": "Local",
                    "severidade_ia": "IA",
                    "prioridade_final": "Final",
                }
                div_df = com_ia[com_ia["divergente"]].sort_values("data_hora", ascending=False).head(10)
                st.dataframe(div_df[list(cols)].rename(columns=cols), use_container_width=True, hide_index=True)
            else:
                st.caption("Nenhuma divergência registrada até agora — IA e motor local em sintonia ✓")
        else:
            st.caption(
                "Nenhuma triagem com IA no histórico ainda. Rode algumas triagens com a checkbox "
                "🔮 marcada para ver a divergência entre os motores aqui."
            )
    else:
        st.caption(
            "🔓 Plano **grátis**: as análises avançadas (causas raiz via IA e comparativo "
            "IA vs. motor local) fazem parte do plano pago."
        )

    st.markdown("##### Últimas triagens")
    tabela = tabela_recente(regs)
    if not tabela.empty:
        st.dataframe(tabela, use_container_width=True, hide_index=True)

    st.caption(
        "Fonte: `data/historico.jsonl` (persistência local). Números em tempo real a cada nova triagem. "
        "O Dashboard não envia dados para nada externo — análise 100% local."
    )