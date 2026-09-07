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


def funcoes_afetadas(registros: list[dict]) -> Counter:
    """Conta menções de cada funcionalidade (uma vez por registro)."""
    contagem: Counter = Counter()
    for reg in registros:
        texto = (reg.get("descricao") or "").lower()
        for padrao, rotulo in FUNCOES:
            if padrao.search(texto):
                contagem[rotulo] += 1
    return contagem


def false_positivos_evitados(registros: list[dict]) -> int:
    """NORMALs que contêm vocabulário técnico de teste (erro/bug/falha)."""
    return sum(
        1 for reg in registros
        if reg.get("gravidade") == "NORMAL ✅" and bool(TERMOS_TESTE.search(reg.get("descricao") or ""))
    )


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
        "IA": df["usou_ia"].map({True: "sim", False: "não"}).values,
    })
    if "jira_key" in df.columns:
        jira = df["jira_key"].fillna("—").values
    else:
        jira = ["—"] * len(df)
    tabela["Jira"] = jira
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
    fp = false_positivos_evitados(registros)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🧺 Triagens", len(registros))
    c2.metric("🚨 Críticas/Altas", n_crit)
    c3.metric("⚠️ Médias", n_media)
    c4.metric("✅ Normais", n_normal)
    c5.metric("📉 Score médio", f"{score_medio:.2f}")

    fp_col, ia_col = st.columns(2)
    fp_col.metric("🟫 Falso-positivo evitado (vocab. de teste)", fp)
    ia_expandir = fp_col.expander("O que é esse número?", expanded=False)
    ia_expandir.caption(
        "Relatos que usam 'erro', 'bug' ou 'falha' como vocabulário normal de teste e "
        "foram classificados como NORMAL — prova de que o motor não dispara por palavra isolada."
    )

    esquerda, direita = st.columns(2)
    with esquerda:
        st.markdown("##### Distribuição de severidade")
        dados_sev = _contagem_por(registros, "gravidade", _ORDEM_SEVERIDADE).set_index("gravidade")
        st.bar_chart(dados_sev, color="#2E7CF6")
    with direita:
        st.markdown("##### Volume por dia")
        dados_dia = df.groupby("data").size().sort_index()
        st.line_chart(pd.DataFrame({"triagens": dados_dia}), color="#FF7043")

    st.markdown("##### Funcionalidades mais afetadas")
    funcoes = funcoes_afetadas(registros)
    if funcoes:
        top = pd.DataFrame(funcoes.most_common(), columns=["funcionalidade", "menções"]).set_index("funcionalidade")
        st.bar_chart(top, color="#9C27B0")
    else:
        st.caption("Nenhuma funcionalidade reconhecível nos relatos persistidos.")

    st.markdown("##### Comparativo IA vs. motor local")
    com_ia = df[df.get("usou_ia", False)]
    if com_ia.empty:
        st.caption(
            "Nenhuma triagem com IA no histórico ainda. Rode algumas triagens com a checkbox "
            "🔮 marcada para ver divergência entre motores aqui (linha do Jira e previsão IA)."
        )
    else:
        n_div = int(com_ia["divergente"].sum()) if "divergente" in com_ia else 0
        st.metric("Divergências entre IA e léxico", f"{n_div} de {len(com_ia)}")
    dados_ia = [_contagem_por(registros, "prioridade_final", _ORDEM_SEVERIDADE).set_index("prioridade_final")] if "prioridade_final" in df else []
    if dados_ia and not dados_ia[0].empty:
        st.bar_chart(dados_ia[0], color="#26A69A")

    st.markdown("##### Últimas triagens")
    tabela = tabela_recente(registros)
    if not tabela.empty:
        st.dataframe(tabela, use_container_width=True, hide_index=True)

    st.caption(
        "Fonte: `data/historico.jsonl` (persistência local). Números em tempo real a cada nova triagem. "
        "O Dashboard não envia dados para nada externo — análise 100% local."
    )