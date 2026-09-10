import streamlit as st
import json
import pandas as pd
from urllib.parse import quote

from triagem import triar
import ia
import rag
import hero_animado
from hero_animado import _svg_groq
import jira_client
import persistencia
import guardrails
import notificacoes
import dashboard as dashboard_qa
import pix

VERSAO = "v2.5.6"

# Símbolo oficial do Pix (Banco Central) — PD-textlogo via Wikimedia Commons.
# Só os 3 paths verdes da marca (o "losango"), sem a tipografia do logo.
_PIX_SIMBOLO_PATHS = (
    '<path d="m 596.82737,86.620206 c -3.08045,0 -5.97782,-1.19944 -8.15622,-3.37679 '
    "l -11.77678,-11.77713 c -0.82691,-0.82903 -2.26801,-0.82656 -3.09456,0 l -11.81982,11.82017 "
    "c -2.17841,2.17734 -5.07577,3.37679 -8.15623,3.37679 h -2.32092 l 14.9158,14.915444 "
    "c 4.65807,4.65808 12.21069,4.65808 16.86912,0 l 14.95813,-14.958484 z\"/>"
    '<path d="m 553.82362,44.963326 c 3.08046,0 5.97782,1.19944 8.15622,3.37679 l 11.81982,11.82193 '
    "c 0.85125,0.85161 2.2412,0.85479 3.09457,-10e-4 l 11.77678,-11.77784 c 2.1784,-2.17735 5.07576,-3.37679 "
    "8.15622,-3.37679 h 1.41852 l -14.95778,-14.95813 c -4.65878,-4.658432 -12.2114,-4.658432 -16.86948,0 "
    "l -14.91509,14.91509 z\"/>"
    '<path d="m 610.61844,57.378776 -9.03922,-9.03922 c -0.19897,0.0797 -0.41452,0.12946 -0.64206,0.12946 '
    "h -4.10986 c -2.12478,0 -4.20476,0.86184 -5.70618,2.36432 l -11.77643,11.77678 c -1.10207,1.10208 "
    "-2.55022,1.65347 -3.99697,1.65347 -1.44815,0 -2.89524,-0.55139 -3.99697,-1.65241 l -11.82088,-11.82088 "
    "c -1.50142,-1.50283 -3.5814,-2.36431 -5.70618,-2.36431 h -5.05354 c -0.21555,0 -0.41698,-0.0508 "
    "-0.60713,-0.12242 l -9.07521,9.07521 c -4.65843,4.65843 -4.65843,12.2107 0,16.86913 l 9.07486,9.07485 "
    "c 0.1905,-0.0716 0.39193,-0.12241 0.60748,-0.12241 h 5.05354 c 2.12478,0 4.20476,-0.86148 5.70618,-2.36396 "
    "l 11.81982,-11.81982 c 2.13643,-2.13466 5.8607,-2.13537 7.995,0.001 l 11.77643,11.77573 "
    "c 1.50142,1.50248 3.5814,2.36431 5.70618,2.36431 h 4.10986 c 0.22754,0 0.44309,0.0497 0.64206,0.12947 "
    "l 9.03922,-9.03922 c 4.65808,-4.65843 4.65808,-12.2107 0,-16.86913\"/>"
)


_TEXTO_APOIE = "Apoie este projeto"


def _svg_pix(tamanho: int = 16, cor: str = "#32bcad") -> str:
    # viewBox real do símbolo (paths nas coordenadas originais do logo oficial):
    # bbox medido = x 535.0..613.0, y 27.0..104.0 (78x77) -> margem de 4 unidades
    altura = max(10, round(tamanho * 85 / 86))
    return (
        f'<svg width="{tamanho}" height="{altura}" viewBox="531 23 86 85" '
        f'fill="{cor}" role="img" aria-label="Pix" style="display:inline-block">'
        f"{_PIX_SIMBOLO_PATHS}</svg>"
    )

# Configuração e Estilo
st.set_page_config(page_title="Iago Nunes | IA & QA Portfolio", page_icon="🤖", layout="wide")

# Esconde rodapé "Made with Streamlit", menu principal "⋮" e botão Deploy. O tema
# claro/escuro é controlado por um seletor PRÓPRIO no sidebar (paleta via CSS própria);
# ocultamos o menu nativo p/ não misturar o tema do Streamlit com o tema do app.
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}

    /* Fundo do app: gradiente sutil no topo (verde-claro desvanecendo p/ branco) */
    [data-testid="stAppViewContainer"] { background: linear-gradient(180deg, #f0fdf4 0%, #ffffff 300px) !important; }
    .stSidebar { background: #ffffff !important; }

    /* Blindagem do tema claro: se o tema NATIVO do Streamlit vazar escuro (preferência
       salva no navegador + menu "⋮" oculto), o texto default viraria branco sobre fundo
       claro. Fixamos os tons claros aqui — o tema escuro do app (body:has) sobrescreve depois. */
    [data-testid="stMarkdownContainer"] { color: #1f2937 !important; }
    [data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3, [data-testid="stMarkdownContainer"] h4,
    [data-testid="stMarkdownContainer"] h5, [data-testid="stMarkdownContainer"] h6 { color: #0f172a !important; }
    [data-testid="stCaptionContainer"], [data-testid="stSidebar"] caption { color: #64748b !important; }
    [data-testid="stMetricLabel"] { color: #64748b !important; }
    [data-testid="stMetricValue"] { color: #0f172a !important; }
    [data-testid="stHeader"] { background: #ffffff !important; }

    /* Card do formulário: textarea da triagem com moldura colorida (marcador irmão) */
    [data-testid="stElementContainer"]:has(.marca-form) + [data-testid="stElementContainer"] [data-testid="stTextArea"] textarea { background: #fbfefc !important; border: 1.5px solid #25D366 !important; border-radius: 12px !important; box-shadow: 0 2px 12px rgba(37, 211, 102, 0.14) !important; }

    /* Badge de prioridade animado (pulando) */
    @keyframes iago-pulse { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-4px); } }
    .badge-prioridade { display: inline-block; padding: 3px 12px; border-radius: 999px; font-weight: 800; font-size: 14px; color: #fff; animation: iago-pulse 1.4s ease-in-out infinite; box-shadow: 0 2px 8px rgba(0,0,0,.18); }
    [data-testid="stElementContainer"]:has(.marca-pri) + [data-testid="stElementContainer"] .badge-prioridade { animation-delay: .1s; }

    /* Destaque colorido por expander: marcador oculto dentro do corpo +
       seleção via :has() (funciona msm sem id estável no DOM) */
    [data-testid="stExpander"]:has(.marca-resolucao) { border: 2px solid #e11d48 !important; border-radius: 12px !important; background: rgba(225, 29, 72, 0.05) !important; }
    [data-testid="stExpander"]:has(.marca-resolucao) summary { color: #e11d48 !important; font-weight: 700 !important; }
    [data-testid="stExpander"]:has(.marca-sessao) { border: 2px solid #2563eb !important; border-radius: 12px !important; }
    [data-testid="stExpander"]:has(.marca-sessao) summary { color: #2563eb !important; font-weight: 700 !important; }
    [data-testid="stExpander"]:has(.marca-historico) { border: 2px solid #059669 !important; border-radius: 12px !important; }
    [data-testid="stExpander"]:has(.marca-historico) summary { color: #059669 !important; font-weight: 700 !important; }
    [data-testid="stExpander"]:has(.marca-historico) [data-testid="stDownloadButton"], [data-testid="stExpander"]:has(.marca-historico) [data-testid="stButton"] { width: 100%; }
    [data-testid="stExpander"]:has(.marca-historico) [data-testid="stDownloadButton"] button { background: #065f46 !important; color: #ffffff !important; }
    [data-testid="stExpander"]:has(.marca-historico) [data-testid="stButton"] button { background: #059669 !important; color: #ffffff !important; }
    [data-testid="stExpander"]:has(.marca-dashboard) { border: 2px solid #7c3aed !important; border-radius: 12px !important; }
    [data-testid="stExpander"]:has(.marca-dashboard) summary { color: #7c3aed !important; font-weight: 700 !important; }
    [data-testid="stExpander"]:has(.marca-diag) { border: 2px solid #d97706 !important; border-radius: 12px !important; }
    [data-testid="stExpander"]:has(.marca-diag) summary { color: #d97706 !important; font-weight: 700 !important; }
    [data-testid="stExpander"]:has(.marca-modelo) { border: 2px solid #f97316 !important; border-radius: 12px !important; background: rgba(249, 115, 22, 0.05) !important; }
    [data-testid="stExpander"]:has(.marca-modelo) summary { color: #f97316 !important; font-weight: 700 !important; }
    [data-testid="stElementContainer"]:has(.marca-modelo-btn) + [data-testid="stElementContainer"] [data-testid="stButton"] button { background: #f97316 !important; color: #ffffff !important; }
    [data-testid="stElementContainer"]:has(.marca-modelo-btn) + [data-testid="stElementContainer"] [data-testid="stButton"] button:hover { background: #ea580c !important; }

    /* Cores dos botões de ação — mesma tática :has() + marcador oculto */
    [data-testid="stElementContainer"]:has(.marca-executar) + [data-testid="stElementContainer"] [data-testid="stButton"] button { background: #059669 !important; color: #ffffff !important; }
    [data-testid="stElementContainer"]:has(.marca-executar) + [data-testid="stElementContainer"] [data-testid="stButton"] button:hover { background: #047857 !important; }
    [data-testid="stColumn"]:has(.marca-download) [data-testid="stDownloadButton"] button { background: #0d9488 !important; color: #ffffff !important; }
    [data-testid="stColumn"]:has(.marca-issue) [data-testid="stLinkButton"] a { background: #18181b !important; color: #ffffff !important; }
    [data-testid="stColumn"]:has(.marca-jira) [data-testid="stButton"] button { background: #0052cc !important; color: #ffffff !important; }
    [data-testid="stExpander"]:has(.marca-jira) { border: 2px solid #0052cc !important; border-radius: 12px !important; background: rgba(0, 82, 204, 0.05) !important; }
    [data-testid="stExpander"]:has(.marca-jira) summary { color: #0052cc !important; font-weight: 700 !important; }
</style>
""", unsafe_allow_html=True)

# --- TEMA PRÓPRIO (claro/escuro) ----------------------------------------------
# O tema nativo do Streamlit só cobre a interface dele; o resto do app usa cores
# fixas no CSS. O seletor abaixo troca uma paleta NOSSA via marcador no DOM +
# regras scoped em `body:has([data-st-tema="escuro"])` (a paleta clara fica intacta).
# A escolha vai para a URL (?tema=escuro) para sobreviver a reload/reconexão
# (o Streamlit Cloud perde o session_state quando o WebSocket cai).
_tema_url = st.query_params.get("tema")
tema = st.session_state.get("tema", "claro")
if _tema_url in ("claro", "escuro"):
    tema, st.session_state["tema"] = _tema_url, _tema_url
elif tema not in ("claro", "escuro"):
    tema, st.session_state["tema"] = "claro", "claro"

_TEMA_CSS = """
<style>
/* Botões do seletor de tema (topo do sidebar) */
[data-testid="stSidebar"] [data-testid="stColumn"]:has(.marca-tema) [data-testid="stButton"] button {
  height:40px; min-height:40px; border-radius:9px; font-weight:600; width:100%;
  background:#eef2f7 !important; color:#334155 !important; border:1.5px solid #cbd5e1 !important;
}
[data-testid="stSidebar"] [data-testid="stColumn"]:has(.marca-tema) [data-testid="stButton"] button:hover { background:#e2e8f0 !important; }
[data-testid="stSidebar"] [data-testid="stColumn"]:has(.tema-ativo) [data-testid="stButton"] button {
  outline:2.5px solid #0f172a !important; outline-offset:2px !important;
}

/* -------- MODO ESCURO: paleta própria do app -------- */
body:has([data-st-tema="escuro"]) { color-scheme: dark; }
body:has([data-st-tema="escuro"]) [data-testid="stAppViewContainer"] { background: linear-gradient(180deg, #0d1410 0%, #0f1115 420px) !important; }
body:has([data-st-tema="escuro"]) [data-testid="stHeader"] { background:#0a0c0f !important; border-bottom:1px solid rgba(255,255,255,.07) !important; }
body:has([data-st-tema="escuro"]) [data-testid="stMainMenuButton"] { color:#e5e7eb !important; }
body:has([data-st-tema="escuro"]) [data-testid="stMainMenuPopover"] { background:#161b22 !important; }

/* Sidebar */
body:has([data-st-tema="escuro"]) [data-testid="stSidebar"],
body:has([data-st-tema="escuro"]) .stSidebar { background:#0f1217 !important; }
body:has([data-st-tema="escuro"]) [data-testid="stSidebarContent"],
body:has([data-st-tema="escuro"]) [data-testid="stSidebarUserContent"] { background:transparent !important; color:#d7dbe0 !important; }
body:has([data-st-tema="escuro"]) [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] { color:#d7dbe0 !important; }
body:has([data-st-tema="escuro"]) [data-testid="stSidebar"] h1, body:has([data-st-tema="escuro"]) [data-testid="stSidebar"] h2,
body:has([data-st-tema="escuro"]) [data-testid="stSidebar"] h3, body:has([data-st-tema="escuro"]) [data-testid="stSidebar"] h4,
body:has([data-st-tema="escuro"]) [data-testid="stSidebar"] h5, body:has([data-st-tema="escuro"]) [data-testid="stSidebar"] h6 { color:#f1f5f9 !important; }
body:has([data-st-tema="escuro"]) [data-testid="stSidebar"] [data-testid="stCaptionContainer"],
body:has([data-st-tema="escuro"]) [data-testid="stSidebar"] caption { color:#9aa3af !important; }
body:has([data-st-tema="escuro"]) [data-testid="stSidebar"] [data-testid="stExpander"] { border-color:#2b3443 !important; }
body:has([data-st-tema="escuro"]) [data-testid="stSidebar"] [data-testid="stExpander"] summary { color:#d7dbe0 !important; }
body:has([data-st-tema="escuro"]) [data-testid="stSidebar"] input { background:#151a21 !important; color:#e5e7eb !important; border:1px solid #2c3542 !important; }

/* Texto principal */
body:has([data-st-tema="escuro"]) [data-testid="stMain"] [data-testid="stMarkdownContainer"] { color:#d7dbe0 !important; }
body:has([data-st-tema="escuro"]) [data-testid="stMain"] h1, body:has([data-st-tema="escuro"]) [data-testid="stMain"] h2,
body:has([data-st-tema="escuro"]) [data-testid="stMain"] h3, body:has([data-st-tema="escuro"]) [data-testid="stMain"] h4,
body:has([data-st-tema="escuro"]) [data-testid="stMain"] h5, body:has([data-st-tema="escuro"]) [data-testid="stMain"] h6 { color:#f3f4f6 !important; }
body:has([data-st-tema="escuro"]) [data-testid="stCaptionContainer"] { color:#9aa3af !important; }

/* Campos e controles */
body:has([data-st-tema="escuro"]) [data-testid="stTextArea"] textarea,
body:has([data-st-tema="escuro"]) [data-testid="stTextInput"] input,
body:has([data-st-tema="escuro"]) [data-testid="stNumberInput"] input { background:#151a21 !important; color:#e5e7eb !important; border:1px solid #2c3542 !important; }
body:has([data-st-tema="escuro"]) [data-testid="stTextArea"] textarea::placeholder,
body:has([data-st-tema="escuro"]) [data-testid="stTextInput"] input::placeholder { color:#64748b !important; }
/* textarea do formulário (empata a especificidade da regra clara do .marca-form) */
body:has([data-st-tema="escuro"]) [data-testid="stElementContainer"]:has(.marca-form) + [data-testid="stElementContainer"] [data-testid="stTextArea"] textarea { background:#151a21 !important; color:#e5e7eb !important; border:1.5px solid #25D366 !important; box-shadow:none !important; }
body:has([data-st-tema="escuro"]) [data-testid="stCheckbox"] label,
body:has([data-st-tema="escuro"]) [data-testid="stCheckbox"] label p,
body:has([data-st-tema="escuro"]) [data-testid="stCheckbox"] label span,
body:has([data-st-tema="escuro"]) [data-testid="stRadio"] label,
body:has([data-st-tema="escuro"]) [data-testid="stRadio"] label p,
body:has([data-st-tema="escuro"]) [data-testid="stRadioOption"] label p { color:#d7dbe0 !important; }
body:has([data-st-tema="escuro"]) [data-testid="stSelectbox"] [role="combobox"] { background:#151a21 !important; color:#e5e7eb !important; }

/* Expanda o rest (unmarked) */
body:has([data-st-tema="escuro"]) [data-testid="stExpander"]:not(:has(.marca-resolucao,.marca-sessao,.marca-historico,.marca-dashboard,.marca-diag,.marca-modelo,.marca-jira)) { background:transparent !important; border:1px solid #2b3443 !important; }
body:has([data-st-tema="escuro"]) [data-testid="stExpander"]:not(:has(.marca-resolucao,.marca-sessao,.marca-historico,.marca-dashboard,.marca-diag,.marca-modelo,.marca-jira)) summary { color:#d7dbe0 !important; }

/* Métricas e código */
body:has([data-st-tema="escuro"]) [data-testid="stMetricValue"] { color:#f3f4f6 !important; }
body:has([data-st-tema="escuro"]) [data-testid="stMetricLabel"] { color:#9aa3af !important; }
body:has([data-st-tema="escuro"]) [data-testid="stCodeBlock"] { background:#0d1117 !important; }
body:has([data-st-tema="escuro"]) [data-testid="stCodeBlock"] pre,
body:has([data-st-tema="escuro"]) [data-testid="stCodeBlock"] code { background:transparent !important; color:#c9d1d9 !important; }
body:has([data-st-tema="escuro"]) [data-testid="stDataFrame"],
body:has([data-st-tema="escuro"]) [data-testid="stTable"] { color-scheme: dark; }

/* Textos/cards com cor fixa inline que ficariam escuros demais no fundo escuro */
body:has([data-st-tema="escuro"]) h1.nome-site { color:#ffffff !important; }
body:has([data-st-tema="escuro"]) .campo-tit { color:#e2e8f0 !important; }
body:has([data-st-tema="escuro"]) .prio-final { color:#f3f4f6 !important; }
body:has([data-st-tema="escuro"]) .hero-sub { color:#cbd5e1 !important; }
body:has([data-st-tema="escuro"]) .hcard { background:#0f1720 !important; border:1px solid #14532d !important; }
body:has([data-st-tema="escuro"]) .hcard-t { color:#6ee7b7 !important; }
body:has([data-st-tema="escuro"]) .hcard-s { color:#94a3b8 !important; }

/* Card custom do provedor (fundo laranja claro) e outlines do que está ativo */
body:has([data-st-tema="escuro"]) [data-testid="stColumn"]:has(.marca-prov-custom) [data-testid="stButton"] button { background:#2b1608 !important; color:#fdba74 !important; border:2px solid #7c2d12 !important; }
body:has([data-st-tema="escuro"]) [data-testid="stColumn"]:has(.prov-provid-sel) [data-testid="stButton"] button { outline-color:#f8fafc !important; }
body:has([data-st-tema="escuro"]) [data-testid="stSidebar"] [data-testid="stColumn"]:has(.tema-ativo) [data-testid="stButton"] button { outline:2.5px solid #7dd3fc !important; }
</style>
"""
st.markdown(_TEMA_CSS, unsafe_allow_html=True)
if tema == "escuro":
    st.markdown('<div data-st-tema="escuro" style="display:none"></div>', unsafe_allow_html=True)
# Bootstrap no CLIENTE: no Streamlit o `st.query_params` do primeiro run às vezes
# chega vazio (race), então o Python não vê o `?tema=...` da URL. Este iframe roda
# JS na página (mesmo truque do botão pix) e sincroniza o marcador direto da URL —
# determinístico; cobre reload/reconexão/sessão nova sem perder o tema escolhido.
st.components.v1.html(
    """<script>
    (() => {
      const T = '[data-st-tema="escuro"]';
      const sync = () => {
        const p = parent || window, d = p.document;
        const tema = new URL(p.location.href).searchParams.get('tema');
        if (tema === 'escuro' && !d.querySelector(T)) {
          const m = d.createElement('div'); m.setAttribute('data-st-tema', 'escuro'); d.body.appendChild(m);
        } else if (tema !== 'escuro') {
          d.querySelectorAll(T).forEach((n) => n.remove());
        }
        setTimeout(sync, 600);
      };
      sync();
    })();
    </script>""",
    height=0,
)

# Seletor de provedor em cards simples: um st.button nativo por opção (emoji + rótulo dentro do card).
_PROVID_CSS = """
<style>
    [data-testid="stColumn"]:has(.marca-provid) [data-testid="stButton"] button { height:50px; min-height:50px; border-radius:10px; font-weight:600; width:100%; }
    [data-testid="stColumn"]:has(.marca-prov-auto) [data-testid="stButton"] button { background:#334155 !important; color:#ffffff !important; border:1.5px solid #1e293b !important; }
    [data-testid="stColumn"]:has(.marca-prov-auto) [data-testid="stButton"] button:hover { background:#24303f !important; }
    [data-testid="stColumn"]:has(.marca-prov-gemini) [data-testid="stButton"] button { background:linear-gradient(135deg,#2E7CF6 0%,#7c3aed 100%) !important; color:#ffffff !important; border:2px solid #4f46e5 !important; text-shadow:0 1px 2px rgba(15,23,42,.35) !important; }
    [data-testid="stColumn"]:has(.marca-prov-gemini) [data-testid="stButton"] button:hover { filter:brightness(1.08) !important; }
    [data-testid="stColumn"]:has(.marca-prov-groq) [data-testid="stButton"] button { background:#f55036 !important; color:#ffffff !important; border:2px solid #f55036 !important; text-shadow:0 1px 2px rgba(15,23,42,.35) !important; }
    [data-testid="stColumn"]:has(.marca-prov-groq) [data-testid="stButton"] button:hover { background:#d84523 !important; }
    [data-testid="stColumn"]:has(.marca-prov-custom) [data-testid="stButton"] button { background:#fff7ed !important; color:#9a3412 !important; border:2px solid #fdba74 !important; }
    [data-testid="stColumn"]:has(.marca-prov-custom) [data-testid="stButton"] button:hover { border-color:#f97316 !important; }
    [data-testid="stColumn"]:has(.prov-provid-sel) [data-testid="stButton"] button { outline:2.5px solid #0f172a !important; outline-offset:2px !important; box-shadow:0 6px 16px rgba(15,23,42,.22) !important; }
</style>
"""
st.markdown(_PROVID_CSS, unsafe_allow_html=True)

# --- CABEÇALHO ---
col_foto, col_info = st.columns([1, 2])
with col_info:
    st.markdown('<h1 class="nome-site" style="font-weight:700; line-height:1.2; letter-spacing:-0.02em; padding:0; margin:0; color:black">Iago Nunes<span style="font-size:0.5em; vertical-align:super; font-weight:400; color:#6b7280; margin-left:2px">©</span></h1>', unsafe_allow_html=True)
    hero_animado.linha()
    st.markdown('<img src="https://capsule-render.vercel.app/api?type=soft&color=gradient&customColorList=20,24,25&height=56&section=header&text=Bem-vindo%20ao%20meu%20site&fontSize=22&fontColor=fff&fontAlignY=62" width="100%" />', unsafe_allow_html=True)
    hero_animado.typing_frases()
with col_foto:    
    st.image("assets/o novo.png", width=250,caption="Iago Nunes")
    st.markdown("""
<div style="margin-top:10px;width:100%;background:linear-gradient(135deg,#047857 0%,#0d9488 50%,#7c3aed 185%);border-radius:14px;color:#ffffff;font-size:14px;line-height:1.5;padding:14px 16px">
  <div style="font-weight:700">🚀 Construo automação de QA com IA (NLP + Gemini) | Auxiliar Administrativo | Graduando IA &amp; ML Uniasselvi (Dez/2027)</div>
  <div style="margin-top:6px;color:#dcfce7">📍 São Luís, MA (Disponível para Remote Global)</div>
</div>
""", unsafe_allow_html=True)
    
    st.markdown("""
<div style="height:3px;width:100%;background:linear-gradient(90deg,transparent,#25D366,#2E7CF6,#7c3aed,transparent);border-radius:999px;margin:8px 0"></div>
""", unsafe_allow_html=True)

# HERO animado centralizado: abaixo do Bem-vindo/digitação e acima do Sobre Mim
hero_animado.render()

esq, centro = st.columns([1, 8])
with centro:
    st.markdown("""
<div style="margin-top:14px;width:100%;background:linear-gradient(135deg,#0f172a 0%,#16233c 55%,#25D366 170%);border-radius:16px;color:#e2e8f0;font-size:15px;line-height:1.6;padding:22px 24px">
  <div style="font-size:19px;font-weight:800;color:#ffffff;margin-bottom:12px">🎯 Sobre Mim 🧔🏾‍♂️️</div>
  <p style="margin:0 0 12px">Sou um entusiasta de tecnologia e estudante de <b style="color:#25D366">IA &amp; Machine Learning</b>, focado em transformar a garantia de qualidade (QA) através da automação inteligente. Minha missão no laboratório <b style="color:#94a3b8">Hack28</b> é construir ferramentas que não apenas encontrem falhas, mas que tragam <b style="color:#94a3b8">insights valiosos para o negócio</b> usando <b style="color:#94a3b8">NLP</b> e <b style="color:#94a3b8">Engenharia de Prompt</b>.</p>
  <p style="margin:0 0 12px">🚀 <b style="color:#94a3b8">Hoje:</b> Já coloco IA em produção lucidamente — motor NLP determinístico + Gemini com fallback automático, aplicação pública, open-source e <b style="color:#94a3b8">container publicada no GHCR</b>.</p>
  <p style="margin:0 0 12px">🌟 <b style="color:#94a3b8">Visão:</b> evoluir esse mesmo motor para a próxima geração — <b style="color:#94a3b8">agentes de IA, RAG e MLOps</b> — transformando QA de "caça-bugs" em <b style="color:#94a3b8">inteligência de produto</b>. Com a graduação em IA &amp; ML (UNIASSELVI · Dez/2027), esse caminho está documentado passo a passo no meu GitHub aberto.</p>
  <p style="margin:0"><b style="color:#94a3b8">O que eu busco agora:</b> Oportunidades <b style="color:#94a3b8">Home Office / Remote</b> para aplicar automação híbrida, acelerar ciclos de entrega e elevar o padrão de qualidade — fazendo parte de um time que constrói o futuro do software.</p>
</div>
""", unsafe_allow_html=True)

# --- SOBRE O PROJETO ---
st.markdown("""
<div style="height:3px;width:100%;background:linear-gradient(90deg,transparent,#25D366,#2E7CF6,#7c3aed,transparent);border-radius:999px;margin:8px 0"></div>
""", unsafe_allow_html=True)
st.markdown("""
<div style="width:100%;background:linear-gradient(135deg,#1e293b 0%,#24344f 55%,#2E7CF6 175%);border-radius:16px;color:#e2e8f0;font-size:15px;line-height:1.6;padding:20px 24px">
  <p style="margin:0">Atualmente, dedico meus estudos na <b style="color:#7aa5ff">UNIASSELVI</b> para aprofundar conhecimentos em <b style="color:#7aa5ff">Redes Neurais</b> e <b style="color:#7aa5ff">Modelos de Linguagem (LLMs)</b>. No meu dia a dia, utilizo o <b style="color:#7aa5ff">Linux Mint</b> como base para desenvolver scripts em <b style="color:#7aa5ff">Python</b> que integram APIs de inteligência artificial à automação de testes, buscando sempre reduzir o tempo de triagem de bugs e melhorar a precisão dos relatórios técnicos.</p>
</div>
""", unsafe_allow_html=True)
st.markdown("""
<div style="font-size:1.5em;font-weight:800;line-height:1.25;background:linear-gradient(90deg,#f59e0b 0%,#ef4444 45%,#ec4899 100%);-webkit-background-clip:text;background-clip:text;color:transparent;display:inline-block;margin-top:8px">🤖 Agente de Triagem e Documentação de Bugs 2026</div>
""", unsafe_allow_html=True)
st.info("Esta ferramenta demonstra o uso de NLP para automatizar a triagem técnica e emocional de falhas de software.")

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
            _email_cfg = notificacoes.email_configurado()
            _discord_cfg = notificacoes.discord_configurado()
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
if registros_totais:
    backend = (
        "☁️ Supabase (nuvem — público)"
        if persistencia._usar_nuvem()
        else "💾 JSONL local (efêmero na Cloud — só você vê)"
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
# --- CONFIGURAÇÕES (tema + Jira + futuras opções) no sidebar ---
with st.sidebar.expander("⚙️ Configurações", expanded=False):
    st.markdown('<div class="marca-config" style="display:none"></div>', unsafe_allow_html=True)

    # 🎨 Tema (claro/escuro — fonte de verdade é a URL ?tema=)
    st.markdown('<div class="campo-tit" style="font-weight:600;color:#0f172a;margin-bottom:2px">🎨 Tema</div>', unsafe_allow_html=True)
    _tcols = st.columns(2)
    for _tc, (_tv, _tl) in zip(_tcols, (("claro", "☀️ Claro"), ("escuro", "🌙 Escuro"))):
        _ativo = tema == _tv
        with _tc:
            st.markdown(
                f'<div class="marca-tema marca-tema-{_tv}{" tema-ativo" if _ativo else ""}" style="display:none"></div>',
                unsafe_allow_html=True,
            )
            if st.button(_tl, key=f"tema_{_tv}", width="stretch"):
                st.session_state["tema"] = _tv
                st.query_params["tema"] = _tv
                st.rerun()

    st.markdown("---")

    # 🔑 Jira — exportação de relatórios
    if not jira_client.configurado():
        st.markdown("**🔑 Jira — configurar exportação**")
        st.caption("Cole suas credenciais para ativar o botão 'Exportar para Jira'.")
        j_email = st.text_input("E-mail Atlassian", key="jira_email")
        j_token = st.text_input("API Token", type="password", key="jira_token")
        j_key = st.text_input("Chave do projeto", placeholder="ex.: KAN", key="jira_key")
        j_issue_type = st.text_input("Tipo de item (padrão: Tarefa)", placeholder="ex.: Tarefa", key="jira_issue_type")
        if st.button("Salvar configuração (sessão)", use_container_width=True):
            jira_client.configurar(j_email, j_token, j_key, j_issue_type)
            if jira_client.configurado():
                st.success("✅ Jira configurado nesta sessão!")
            else:
                st.warning("Preencha e-mail, token e chave do projeto.")
    else:
        st.markdown("**🔑 Jira**")
        st.success("✅ Jira configurado nesta sessão")
        st.caption("Botão 'Exportar para Jira' ativo.")
        if st.button("🔄 Reconectar / trocar credenciais", use_container_width=True):
            limpar = getattr(jira_client, "limpar_config", None)
            if limpar is not None:
                limpar()
                st.rerun()
            else:
                st.error("Cache antigo detectado — clique em 'Manage app' > 'Rebuild' (limpa o cache) e rode a triagem de novo.")

# --- CTA: ESTRELA NO GITHUB ---
st.sidebar.markdown("### ⭐ Apoie o projeto")
st.sidebar.write("Se esta triagem te ajudou, dá uma estrelinha no repositório — é de graça e ajuda mais QAs a encontrarem o app.")

repo_url = "https://github.com/Iago3-stack/ai-bug-triage-system/"
st.sidebar.markdown(f"""
<a href="{repo_url}" target="_blank">
    <button style="background-color: #2E7CF6; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; width: 100%;">
        ⭐ Dar estrela no GitHub
    </button>
</a>
""", unsafe_allow_html=True)
# --- RODAPÉ DE CONTATO ---
with st.sidebar:
    st.markdown("### Contate-me")
    hero_animado.render_contato()
st.sidebar.markdown("""
<div style="margin-top:14px;padding:10px 12px;border:1px solid rgba(46,124,246,.28);border-radius:10px;background:rgba(46,124,246,.06);font-size:13px;line-height:1.6">
  🐧 <b>Linux Mint Debian</b> · 🧠 Lab <b>Hack28</b><br/>
  ⚡ <i>Automatizando qualidade — um bug de cada vez.</i>
</div>
""", unsafe_allow_html=True)

# --- RODAPÉ DE CRÉDITO (autoria blindada, visível mesmo em forks) ---
pix_bloco = ""
_link_pix = pix.link_pagamento()
if _link_pix:
    pix_bloco = f"""
  <div style="flex:1 1 320px;text-align:center">
    <div style="display:inline-flex;align-items:center;gap:8px;font-size:15px;font-weight:800;color:#ffffff">{_svg_pix(18)}{_TEXTO_APOIE} 🤝</div>
    <div style="color:#94a3b8;font-size:13px;margin:6px auto 12px;max-width:340px">Este é um projeto independente, feito por uma pessoa. Se ele te ajudou, considere uma contribuição voluntária via Pix.</div>
    <a href="{_link_pix}" target="_blank" style="text-decoration:none">
      <button style="display:inline-flex;align-items:center;gap:8px;background:#25D366;color:#0b1e14;font-weight:800;font-size:14px;border:none;padding:12px 24px;border-radius:10px;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.25)">
        {_svg_pix(16, "#0b1e14")}
        Pagar com Pix via link
      </button>
    </a>
    <div style="color:#64748b;font-size:12px;margin-top:8px">Link de pagamento com valor fixo — sem desconto aplicado.</div>
  </div>"""
elif pix.configurado():
    try:
        _payload_pix = pix.payload_configurado()
        _qr_pix = pix.qrcode_png_base64(_payload_pix)
        _chave_pix = pix.chave()
        _bloco_copia = (
            f"""
    <div style="text-align:center;margin-top:12px">
      <button id="btn-copiar-pix" onclick="copiarChave()"
              style="display:inline-flex;align-items:center;gap:8px;background:#25D366;color:#0b1e14;font-weight:700;font-size:14px;border:none;padding:10px 22px;border-radius:8px;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.25)">
        {_svg_pix(14, "#0b1e14")}
        <span id="lbl-copiar-pix">copiar chave pix</span>
      </button>
    </div>
    <div style="color:#94a3b8;font-size:12px;margin-top:8px">Escaneie o QR Code com a câmera do seu banco — ou use o botão para copiar a chave acima.</div>
    <script>
    function copiarChave() {{
      navigator.clipboard.writeText("{pix.chave_copia()}").then(function() {{
        var l = document.getElementById('lbl-copiar-pix');
        l.textContent = '✓ chave copiada!';
        setTimeout(function() {{ l.textContent = 'copiar chave pix'; }}, 2200);
      }});
    }}
    </script>""" if _chave_pix else "\n    <div style=\"color:#64748b;font-size:12px;margin-top:8px\">Escaneie o QR Code com a câmera do seu banco — e ajude a manter este projeto open source.</div>"
        )
        pix_bloco = f"""
  <div style="flex:1 1 320px;text-align:center">
    <div style="display:inline-flex;align-items:center;gap:8px;font-size:15px;font-weight:800;color:#ffffff">{_svg_pix(18)}{_TEXTO_APOIE} 🤝</div>
    <div style="color:#94a3b8;font-size:13px;margin:6px auto 12px;max-width:340px">Este é um projeto independente, feito por uma pessoa. Se ele te ajudou, considere uma contribuição voluntária via Pix.</div>
    <img src="{_qr_pix}" width="140" style="border-radius:10px;background:#ffffff;padding:6px" alt="QR Code Pix"/>
    {_bloco_copia}
  </div>"""
    except Exception:
        pix_bloco = ""
_footer_html = f"""
<div style="margin-top:32px;width:100%;background:linear-gradient(135deg,#0f172a 0%,#16233c 55%,#25D366 170%);border-radius:18px 18px 0 0;color:#e2e8f0;font-size:14px;line-height:1.55">
  <div style="display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:24px;padding:26px 26px 20px">
    <div style="flex:1 1 320px;text-align:center">
      <div style="font-size:17px;font-weight:700;color:#ffffff">Gostou do <span style="color:#25D366">AI Bug Triage System</span>?</div>
      <div style="color:#94a3b8;font-size:13px;margin:6px 0 14px">Uma estrelinha no repositório ajuda mais QAs a encontrarem o app.</div>
      <a href="{repo_url}" target="_blank" style="text-decoration:none">
        <button style="display:inline-flex;align-items:center;gap:8px;background:#2E7CF6;color:#ffffff;font-weight:700;font-size:14px;border:none;padding:10px 22px;border-radius:8px;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.25)">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="#ffd76e" role="img"><path d="M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.719 4.192a.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L.818 6.374a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25z"/></svg>
          Dar estrela no GitHub
        </button>
      </a>
    </div>
    {pix_bloco}
  </div>
  <div style="display:flex;justify-content:center;gap:26px;flex-wrap:wrap;padding:14px 16px;font-size:13px;color:#cbd5e1;border-top:1px solid rgba(255,255,255,.12)">
    <a href="{repo_url}" target="_blank" style="color:#cbd5e1;text-decoration:none;display:inline-flex;align-items:center;gap:6px">
      <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.5 7.5 0 014 0c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
      Repositório
    </a>
    <a href="{repo_url}blob/main/README.md" target="_blank" style="color:#cbd5e1;text-decoration:none;display:inline-flex;align-items:center;gap:6px">
      <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M0 1.75A.75.75 0 01.75 1h4.253c1.227 0 2.317.59 3 1.501A3.744 3.744 0 0111.006 1h4.245a.75.75 0 01.75.75v10.5a.75.75 0 01-.75.75h-4.507a2.25 2.25 0 00-1.591.659l-.622.621a.75.75 0 01-1.06 0l-.622-.621A2.25 2.25 0 005.258 13H.75a.75.75 0 01-.75-.75V1.75zm8.755 3a2.25 2.25 0 012.25-2.25H14.5v9h-3.757c-.71 0-1.4.201-1.988.557V4.75zM7.25 12.307c.588-.356 1.278-.557 1.988-.557H7.25v.557zM1.5 2.5h3.735a2.25 2.25 0 012.015 1.25v7.307a3.74 3.74 0 00-1.988-.557H1.5V2.5z"/></svg>
      Documentação
    </a>
    <a href="https://github.com/Iago3-stack" target="_blank" style="color:#cbd5e1;text-decoration:none;display:inline-flex;align-items:center;gap:6px">
      <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.5 7.5 0 014 0c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
      Perfil
    </a>
    <a href="{repo_url}blob/main/LICENSE" target="_blank" style="color:#cbd5e1;text-decoration:none;display:inline-flex;align-items:center;gap:6px">
      ⚖️ Licença MIT
    </a>
    <a href="https://www.gov.br/anpd/pt-br" target="_blank" rel="noopener" style="color:#cbd5e1;text-decoration:none;display:inline-flex;align-items:center;gap:6px">
      🛡️ LGPD · Proteção de Dados
    </a>
  </div>
  <div style="padding:12px 16px;text-align:center;font-size:12px;color:#64748b;border-top:1px solid rgba(255,255,255,.08)">
    © {VERSAO} <b style="color:#94a3b8">Iago Nunes de Araújo</b> · 🚀 QA Automation Engineer · Estudante de IA &amp; ML (UNIASSELVI)<br/>
    Projeto original, documentado e publicado por <b style="color:#94a3b8">Iago Nunes (Iago3-stack)</b> — qualquer cópia deve manter o crédito (MIT).
  </div>
</div>
"""
st.iframe(_footer_html, height=560)
