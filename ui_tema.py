"""Tema próprio (claro/escuro) + CSS global + bootstrap em todas as páginas."""
import streamlit as st

_BASE_CSS = """
<style>
    [data-testid="stMainMenuButton"] {visibility: hidden;}
    /* Botão de recolher/expandir a sidebar: o Streamlit o mantém visibility:hidden
       por padrão; se a sidebar recolher (re-render, iframe do Cloud, viewport), não
       há como expandi-la de volta. Forçamos sempre visível. */
    [data-testid="stSidebarCollapseButton"] { visibility: visible !important; opacity: 1 !important; }
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
    [data-testid="stHeader"] { display: none !important; }

    /* Sidebar sempre aberta no desktop: o Streamlit pode colapsar sozinho em larguras
       ~768-820px (flutuação entre desktop e modo hambúrguer) — força 300px fixos e
       corta a transição que dava o efeito "aparece e some". (<769px segue hambúrguer.) */
    @media (min-width: 769px) {
        [data-testid="stSidebar"] {
            width: 300px !important;
            min-width: 300px !important;
            max-width: 300px !important;
            transform: none !important;
            transition: none !important;
        }
        /* Com a sidebar forçada aberta, o botão ">>" (recolher) vira controle morto —
           escondemos no desktop para não aparecer um controle que não faz nada. */
        [data-testid="stSidebarCollapseButton"] { display: none !important; }
    }

    /* Conteúdo do main sobe para ficar paralelo ao topo do sidebar (botão Configurações);
       padrão do Streamlit era 6rem (~96px) e sobrava um vão acima do masthead. */
    [data-testid="stMainBlockContainer"] { padding-top: 8px !important; }

    /* Masthead (card do plano) sobe para o topo da página, preenchendo o espaço
       vazio que sobrava antes da barra nativa do Streamlit (agora oculta). Os
       containers <style> zero-altura antecipam o card; compensamos com margem negativa. */
    .marca-mastro { margin-top: -66px !important; }
    body:has([data-st-tema="escuro"]) .marca-mastro { margin-top: -82px !important; }

    /* No mobile (largura < 768px) a barra nativa do Streamlit reaparece para que o
       botão hambúrguer (abrir sidebar) fique acessível; o masthead desce para logo
       abaixo dela (sem margem negativa). */
    @media (max-width: 767px) {
        [data-testid="stHeader"] { display: flex !important; }
        .marca-mastro { margin-top: 0 !important; }
        body:has([data-st-tema="escuro"]) .marca-mastro { margin-top: 0 !important; }
    }

    /* Card do formulário: textarea da triagem com moldura colorida (marcador irmão) */
    [data-testid="stElementContainer"]:has(.marca-form) + [data-testid="stElementContainer"] [data-testid="stTextArea"] textarea { background: #fbfefc !important; border: 1.5px solid #25D366 !important; border-radius: 12px !important; box-shadow: 0 2px 12px rgba(37, 211, 102, 0.14) !important; }

    /* Card CTA do Início: pinta APENAS o bloco do container border cujo único filho
       é o leiaute de colunas (o :has() simples vazaria para os ancestrais e tingiria
       a página inteira). */
    [data-testid="stVerticalBlock"]:has(.marca-cta):has(> [data-testid="stLayoutWrapper"]):not(:has(> :not([data-testid="stLayoutWrapper"]))) {
        background: linear-gradient(135deg,#0f172a 0%,#16233c 55%,#25D366 175%) !important;
        border-radius: 14px !important;
        padding: 14px 14px 12px !important;
    }
    .marca-cta { text-align: center; color: #e2e8f0 !important; font-size: 15px; line-height: 1.6; }
    .marca-cta-título { font-size: 19px; font-weight: 800; color: #ffffff !important; margin-bottom: 8px; }
    .marca-cta-desc { color: #94a3b8 !important; font-size: 14px; max-width: 640px; margin: 0 auto; }
    [data-testid="stVerticalBlock"]:has(.marca-cta):has(> [data-testid="stLayoutWrapper"]):not(:has(> :not([data-testid="stLayoutWrapper"]))) [data-testid="stColumn"]:nth-child(2) [data-testid="stButton"] button {
        background: linear-gradient(135deg,#e11d48 0%,#db2777 100%) !important;
        color: #ffffff !important; font-weight: 800 !important; font-size: 14px !important;
        border: none !important; border-radius: 10px !important; padding: 12px 16px !important;
        box-shadow: 0 4px 14px rgba(225,29,72,.35) !important;
    }
    [data-testid="stVerticalBlock"]:has(.marca-cta):has(> [data-testid="stLayoutWrapper"]):not(:has(> :not([data-testid="stLayoutWrapper"]))) [data-testid="stColumn"]:nth-child(3) [data-testid="stButton"] button {
        background: linear-gradient(135deg,#0d9488 0%,#25D366 100%) !important;
        color: #ffffff !important; font-weight: 800 !important; font-size: 14px !important;
        border: none !important; border-radius: 10px !important; padding: 12px 16px !important;
        box-shadow: 0 4px 14px rgba(13,148,136,.35) !important;
    }
    [data-testid="stVerticalBlock"]:has(.marca-cta):has(> [data-testid="stLayoutWrapper"]):not(:has(> :not([data-testid="stLayoutWrapper"]))) [data-testid="stButton"] button:hover {
        opacity: .92 !important; box-shadow: 0 6px 18px rgba(255,255,255,.12) !important;
    }

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
    [data-testid="stExpander"]:has(.marca-historico) [data-testid="stDownloadButton"] button:hover { background: #065f46 !important; color: #ffffff !important; }
    [data-testid="stExpander"]:has(.marca-historico) [data-testid="stButton"] button { background: #059669 !important; color: #ffffff !important; }
    [data-testid="stExpander"]:has(.marca-historico) [data-testid="stButton"] button:hover { background: #059669 !important; color: #ffffff !important; }
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
    [data-testid="stColumn"]:has(.marca-download) [data-testid="stDownloadButton"] button:hover { background: #0d9488 !important; color: #ffffff !important; }
    [data-testid="stColumn"]:has(.marca-issue) [data-testid="stLinkButton"] a { background: #18181b !important; color: #ffffff !important; }
    [data-testid="stColumn"]:has(.marca-jira) [data-testid="stButton"] button { background: #0052cc !important; color: #ffffff !important; }
    [data-testid="stColumn"]:has(.marca-jira) [data-testid="stButton"] button:hover { background: #0052cc !important; color: #ffffff !important; }
    [data-testid="stExpander"]:has(.marca-jira) { border: 2px solid #0052cc !important; border-radius: 12px !important; background: rgba(0, 82, 204, 0.05) !important; }
    [data-testid="stExpander"]:has(.marca-jira) summary { color: #0052cc !important; font-weight: 700 !important; }
    [data-testid="stSidebar"] [data-testid="stExpander"]:has(.marca-jira) summary { color: #3b82f6 !important; }
    [data-testid="stSidebar"] [data-testid="stExpander"]:has(.marca-jira) [data-testid="stButton"] button { background: #059669 !important; color: #ffffff !important; }
    [data-testid="stSidebar"] [data-testid="stExpander"]:has(.marca-jira) [data-testid="stButton"] button:hover { background: #059669 !important; color: #ffffff !important; }
</style>
"""

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

/* Modal "⚙️ Configurações" (@st.dialog) — mesmo visual do bloco do sidebar,
   escopado a [data-testid="stDialog"] (o conteúdo do dialog NÃO está no sidebar) */
[data-testid="stDialog"] [data-testid="stColumn"]:has(.marca-tema) [data-testid="stButton"] button {
  height:40px; min-height:40px; border-radius:9px; font-weight:600; width:100%;
  background:#eef2f7 !important; color:#334155 !important; border:1.5px solid #cbd5e1 !important;
}
[data-testid="stDialog"] [data-testid="stColumn"]:has(.marca-tema) [data-testid="stButton"] button:hover { background:#e2e8f0 !important; }
[data-testid="stDialog"] [data-testid="stColumn"]:has(.tema-ativo) [data-testid="stButton"] button { outline:2.5px solid #0f172a !important; outline-offset:2px !important; }

/* Seções do modal: Jira (azul) e Notificações (roxo), com ressalto de expansão */
[data-testid="stDialog"] [data-testid="stExpander"]:has(.marca-jira) { border:2px solid #0052cc !important; border-radius:12px !important; background:rgba(0,82,204,.05) !important; }
[data-testid="stDialog"] [data-testid="stExpander"]:has(.marca-jira) summary { color:#0052cc !important; font-weight:700 !important; }
[data-testid="stDialog"] [data-testid="stExpander"]:has(.marca-jira) [data-testid="stButton"] button,
[data-testid="stDialog"] [data-testid="stExpander"]:has(.marca-jira) [data-testid="stButton"] button:hover { background:#059669 !important; color:#ffffff !important; }
[data-testid="stDialog"] [data-testid="stExpander"]:has(.marca-notif) { border:2px solid #7c3aed !important; border-radius:12px !important; background:rgba(124,58,237,.05) !important; }
[data-testid="stDialog"] [data-testid="stExpander"]:has(.marca-notif) summary { color:#7c3aed !important; font-weight:700 !important; }

/* Corpo dos expanders com fundo próprio para os campos se destacarem sem depender de hover */
[data-testid="stDialog"] [data-testid="stExpanderDetails"] { background:#f4f7fa !important; border:1px solid #cfd8e3 !important; border-radius:0 0 10px 10px !important; }
[data-testid="stDialog"] [data-testid="stExpander"]:has(.marca-jira) [data-testid="stExpanderDetails"] { background:rgba(0,82,204,.07) !important; border-color:#9ec5ff !important; }
[data-testid="stDialog"] [data-testid="stExpander"]:has(.marca-notif) [data-testid="stExpanderDetails"] { background:rgba(124,58,237,.07) !important; border-color:#cbb7f7 !important; }

/* Botão "⚙️ Configurações" (sidebar) com cor sólida nos dois temas */
[data-testid="stSidebar"] [data-testid="stButton"] button[data-testid="stBaseButton-primary"] { background:#7c3aed !important; color:#ffffff !important; border:none !important; font-weight:600 !important; }
[data-testid="stSidebar"] [data-testid="stButton"] button[data-testid="stBaseButton-primary"]:hover { background:#6d28d9 !important; color:#ffffff !important; }

/* Ações do expander de Notificações com cor sólida por intenção */
[data-testid="stDialog"] [data-testid="stElementContainer"]:has(> [data-testid="stButton"]):has(~ [data-testid="stElementContainer"] .marca-notif-salvar) [data-testid="stButton"] button,
[data-testid="stDialog"] [data-testid="stElementContainer"]:has(> [data-testid="stButton"]):has(~ [data-testid="stElementContainer"] .marca-notif-salvar) [data-testid="stButton"] button:hover { background:#059669 !important; color:#ffffff !important; }
[data-testid="stDialog"] [data-testid="stColumn"]:has(.marca-notif-disc) [data-testid="stButton"] button,
[data-testid="stDialog"] [data-testid="stColumn"]:has(.marca-notif-disc) [data-testid="stButton"] button:hover { background:#2563eb !important; color:#ffffff !important; }
[data-testid="stDialog"] [data-testid="stColumn"]:has(.marca-notif-mail) [data-testid="stButton"] button,
[data-testid="stDialog"] [data-testid="stColumn"]:has(.marca-notif-mail) [data-testid="stButton"] button:hover { background:#7c3aed !important; color:#ffffff !important; }
[data-testid="stDialog"] [data-testid="stElementContainer"]:has(> [data-testid="stButton"]):has(~ [data-testid="stElementContainer"] .marca-notif-limpar) [data-testid="stButton"] button,
[data-testid="stDialog"] [data-testid="stElementContainer"]:has(> [data-testid="stButton"]):has(~ [data-testid="stElementContainer"] .marca-notif-limpar) [data-testid="stButton"] button:hover { background:#475569 !important; color:#ffffff !important; }

/* Seção "Status" das notificações no modal — legível e destacada nos dois temas */
[data-testid="stDialog"] .notif-st-tit { font-size:1.05rem !important; font-weight:700 !important; color:#0f172a !important; margin:8px 0 4px !important; }
[data-testid="stDialog"] .notif-st-linha { font-size:.92rem !important; color:#374151 !important; margin:2px 0 !important; }
[data-testid="stDialog"] .notif-st-lb { font-weight:600 !important; color:#111827 !important; }
[data-testid="stDialog"] .notif-st-ok { color:#059669 !important; font-weight:600 !important; }
[data-testid="stDialog"] .notif-st-falta { color:#b45309 !important; font-weight:600 !important; }

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
body:has([data-st-tema="escuro"]) [data-testid="stSidebar"] [data-testid="stExpander"] summary { color:#e4e9f0 !important; }
body:has([data-st-tema="escuro"]) [data-testid="stSidebar"] [data-testid="stExpander"] summary:hover { color:#f1f5f9 !important; }
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
body:has([data-st-tema="escuro"]) [data-testid="stExpander"]:not(:has(.marca-resolucao,.marca-sessao,.marca-historico,.marca-dashboard,.marca-diag,.marca-modelo,.marca-jira)) summary { color:#e6ecf2 !important; }
body:has([data-st-tema="escuro"]) [data-testid="stExpander"] summary:hover { color:#f1f5f9 !important; }

/* Título (summary) com FUNDO sólido escuro sempre — sem hover abrir/clarear:
   o Streamlit pinta o título de quase-branco quando o expander fica aberto,
   e de cinza translúcido no hover (herdado do tema claro); isso escondia o texto. */
body:has([data-st-tema="escuro"]) [data-testid="stExpander"] summary,
body:has([data-st-tema="escuro"]) [data-testid="stExpander"] summary:hover,
body:has([data-st-tema="escuro"]) [data-testid="stExpander"] summary:focus-visible { background:#0d1117 !important; }

/* Títulos-chave com cor sólida no escuro (não mudam nem com hover sobre eles) */
body:has([data-st-tema="escuro"]) [data-testid="stExpander"]:has(.marca-jira) summary,
body:has([data-st-tema="escuro"]) [data-testid="stExpander"]:has(.marca-jira) summary:hover { color:#3b82f6 !important; }
body:has([data-st-tema="escuro"]) [data-testid="stExpander"]:has(.marca-historico) summary,
body:has([data-st-tema="escuro"]) [data-testid="stExpander"]:has(.marca-historico) summary:hover { color:#34d399 !important; }
body:has([data-st-tema="escuro"]) [data-testid="stExpander"]:has(.marca-dashboard) summary,
body:has([data-st-tema="escuro"]) [data-testid="stExpander"]:has(.marca-dashboard) summary:hover { color:#a78bfa !important; }
body:has([data-st-tema="escuro"]) [data-testid="stExpander"]:has(.marca-modelo) summary,
body:has([data-st-tema="escuro"]) [data-testid="stExpander"]:has(.marca-modelo) summary:hover { color:#fb923c !important; }

/* Setinha de expandir/recolher (chevron) dos expanders — some sumindo no fundo claro do tema escuro */
body:has([data-st-tema="escuro"]) [data-testid="stExpander"] [data-testid="stBaseButton-secondary"] { background:transparent !important; color:#8b94a3 !important; border:none !important; box-shadow:none !important; }
body:has([data-st-tema="escuro"]) [data-testid="stExpander"] [data-testid="stBaseButton-secondary"]:hover { background:rgba(255,255,255,.1) !important; color:#ffffff !important; }

/* Botões de ação coloridos dentro de expanders voltam à cor sólida original no escuro
   (a regra do chevron acima apagava o fundo deles); leve = sem mudança com hover */
body:has([data-st-tema="escuro"]) [data-testid="stExpander"]:has(.marca-historico) [data-testid="stDownloadButton"] button,
body:has([data-st-tema="escuro"]) [data-testid="stExpander"]:has(.marca-historico) [data-testid="stDownloadButton"] button:hover { background:#065f46 !important; color:#ffffff !important; }
body:has([data-st-tema="escuro"]) [data-testid="stExpander"]:has(.marca-historico) [data-testid="stButton"] button,
body:has([data-st-tema="escuro"]) [data-testid="stExpander"]:has(.marca-historico) [data-testid="stButton"] button:hover { background:#059669 !important; color:#ffffff !important; }
body:has([data-st-tema="escuro"]) [data-testid="stElementContainer"]:has(.marca-modelo-btn) + [data-testid="stElementContainer"] [data-testid="stButton"] button { background:#f97316 !important; color:#ffffff !important; }
body:has([data-st-tema="escuro"]) [data-testid="stElementContainer"]:has(.marca-modelo-btn) + [data-testid="stElementContainer"] [data-testid="stButton"] button:hover { background:#ea580c !important; color:#ffffff !important; }

/* Botões de tema (☀️/🌙) no escuro — saem do visual claro default do Streamlit */
body:has([data-st-tema="escuro"]) [data-testid="stSidebar"] [data-testid="stColumn"]:has(.marca-tema) [data-testid="stButton"] button { background:#1a2029 !important; color:#e5e7eb !important; border:1.5px solid #2c3542 !important; }
body:has([data-st-tema="escuro"]) [data-testid="stSidebar"] [data-testid="stColumn"]:has(.marca-tema) [data-testid="stButton"] button:hover { background:#243040 !important; color:#ffffff !important; }
body:has([data-st-tema="escuro"]) [data-testid="stSidebar"] [data-testid="stColumn"]:has(.tema-ativo) [data-testid="stButton"] button { background:#1e3a5f !important; border:1.5px solid #3b82f6 !important; color:#ffffff !important; outline:2.5px solid #3b82f6 !important; outline-offset:2px !important; }

/* Modal "⚙️ Configurações" no escuro (mesma paleta do sidebar/expanders) */
body:has([data-st-tema="escuro"]) [data-testid="stDialog"] { background:#111721 !important; border:1px solid #2b3443 !important; }
body:has([data-st-tema="escuro"]) [data-testid="stDialog"] [data-testid="stMarkdownContainer"],
body:has([data-st-tema="escuro"]) [data-testid="stDialog"] caption { color:#d7dbe0 !important; }
body:has([data-st-tema="escuro"]) [data-testid="stDialog"] input { background:#151a21 !important; color:#e5e7eb !important; border:1px solid #2c3542 !important; }
body:has([data-st-tema="escuro"]) [data-testid="stDialog"] [data-testid="stExpander"] { border-color:#2b3443 !important; }
body:has([data-st-tema="escuro"]) [data-testid="stDialog"] [data-testid="stExpander"] summary,
body:has([data-st-tema="escuro"]) [data-testid="stDialog"] [data-testid="stExpander"] summary:hover,
body:has([data-st-tema="escuro"]) [data-testid="stDialog"] [data-testid="stExpander"] summary:focus-visible { background:#0d1117 !important; }
body:has([data-st-tema="escuro"]) [data-testid="stDialog"] [data-testid="stExpander"]:has(.marca-jira) summary,
body:has([data-st-tema="escuro"]) [data-testid="stDialog"] [data-testid="stExpander"]:has(.marca-jira) summary:hover { color:#3b82f6 !important; }
body:has([data-st-tema="escuro"]) [data-testid="stDialog"] [data-testid="stExpander"]:has(.marca-notif) summary,
body:has([data-st-tema="escuro"]) [data-testid="stDialog"] [data-testid="stExpander"]:has(.marca-notif) summary:hover { color:#a78bfa !important; }
body:has([data-st-tema="escuro"]) [data-testid="stDialog"] [data-testid="stColumn"]:has(.marca-tema) [data-testid="stButton"] button { background:#1a2029 !important; color:#e5e7eb !important; border:1.5px solid #2c3542 !important; }
body:has([data-st-tema="escuro"]) [data-testid="stDialog"] [data-testid="stColumn"]:has(.marca-tema) [data-testid="stButton"] button:hover { background:#243040 !important; color:#ffffff !important; }
body:has([data-st-tema="escuro"]) [data-testid="stDialog"] [data-testid="stColumn"]:has(.tema-ativo) [data-testid="stButton"] button { background:#1e3a5f !important; border:1.5px solid #3b82f6 !important; color:#ffffff !important; outline:2.5px solid #3b82f6 !important; outline-offset:2px !important; }
body:has([data-st-tema="escuro"]) [data-testid="stDialog"] [data-testid="stExpander"]:has(.marca-jira) [data-testid="stButton"] button,
body:has([data-st-tema="escuro"]) [data-testid="stDialog"] [data-testid="stExpander"]:has(.marca-jira) [data-testid="stButton"] button:hover { background:#059669 !important; color:#ffffff !important; }
body:has([data-st-tema="escuro"]) [data-testid="stDialog"] [data-testid="stExpanderDetails"] { background:#0b1018 !important; color:#d7dbe0 !important; border:1px solid #2b3443 !important; border-radius:0 0 10px 10px !important; }
body:has([data-st-tema="escuro"]) [data-testid="stDialog"] [data-testid="stExpander"]:has(.marca-jira) [data-testid="stExpanderDetails"] { background:#0d1523 !important; border-color:#1e3a5f !important; }
body:has([data-st-tema="escuro"]) [data-testid="stDialog"] [data-testid="stExpander"]:has(.marca-notif) [data-testid="stExpanderDetails"] { background:#141021 !important; border-color:#3b2f5a !important; }

/* Título do modal e "🎨 Tema" no escuro com cor de destaque (não esbranquiçados).
   O título do st.dialog é um h2 > span > stMarkdownContainer: o container interno
   ganha own-color #d7dbe0; por isso a regra precisa mirar o nó que pinta o texto. */
body:has([data-st-tema="escuro"]) [data-testid="stDialog"] h2,
body:has([data-st-tema="escuro"]) [data-testid="stDialog"] h2 [data-testid="stMarkdownContainer"],
body:has([data-st-tema="escuro"]) [data-testid="stDialog"] h2 [data-testid="stMarkdownContainer"] p { color:#a78bfa !important; }
body:has([data-st-tema="escuro"]) [data-testid="stDialog"] .tit-modal-sec { color:#3b82f6 !important; }

/* Seção "Status" no modo escuro — título branco destacado, linhas claras */
body:has([data-st-tema="escuro"]) [data-testid="stDialog"] .notif-st-tit { color:#ffffff !important; }
body:has([data-st-tema="escuro"]) [data-testid="stDialog"] .notif-st-linha { color:#d7dbe0 !important; }
body:has([data-st-tema="escuro"]) [data-testid="stDialog"] .notif-st-lb { color:#f1f5f9 !important; }
body:has([data-st-tema="escuro"]) [data-testid="stDialog"] .notif-st-ok { color:#34d399 !important; }
body:has([data-st-tema="escuro"]) [data-testid="stDialog"] .notif-st-falta { color:#fbbf24 !important; }

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

_PROVID_CSS = """
<style>
    [data-testid="stColumn"]:has(.marca-provid) [data-testid="stButton"] button { height:50px; min-height:50px; border-radius:10px; font-weight:600; width:100%; }
    [data-testid="stColumn"]:has(.marca-prov-auto) [data-testid="stButton"] button { background:linear-gradient(135deg,#2E7CF6 0%,#f55036 100%) !important; color:#ffffff !important; border:2px solid #1e293b !important; text-shadow:0 1px 2px rgba(15,23,42,.35) !important; }
    [data-testid="stColumn"]:has(.marca-prov-auto) [data-testid="stButton"] button:hover { filter:brightness(1.08) !important; }
    [data-testid="stColumn"]:has(.marca-prov-gemini) [data-testid="stButton"] button { background:linear-gradient(135deg,#2E7CF6 0%,#7c3aed 100%) !important; color:#ffffff !important; border:2px solid #4f46e5 !important; text-shadow:0 1px 2px rgba(15,23,42,.35) !important; }
    [data-testid="stColumn"]:has(.marca-prov-gemini) [data-testid="stButton"] button:hover { filter:brightness(1.08) !important; }
    [data-testid="stColumn"]:has(.marca-prov-groq) [data-testid="stButton"] button { background:#f55036 !important; color:#ffffff !important; border:2px solid #f55036 !important; text-shadow:0 1px 2px rgba(15,23,42,.35) !important; }
    [data-testid="stColumn"]:has(.marca-prov-groq) [data-testid="stButton"] button:hover { background:#d84523 !important; }
    [data-testid="stColumn"]:has(.marca-prov-custom) [data-testid="stButton"] button { background:#fff7ed !important; color:#9a3412 !important; border:2px solid #fdba74 !important; }
    [data-testid="stColumn"]:has(.marca-prov-custom) [data-testid="stButton"] button:hover { border-color:#f97316 !important; }
    [data-testid="stColumn"]:has(.prov-provid-sel) [data-testid="stButton"] button { outline:2.5px solid #0f172a !important; outline-offset:2px !important; box-shadow:0 6px 16px rgba(15,23,42,.22) !important; }
</style>
"""

_JS_BOOTSTRAP = """<script>
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
    </script>"""


def config_pagina():
    st.set_page_config(page_title="Iago Nunes | IA & QA Portfolio", page_icon="🤖", layout="wide")


def tema_atual() -> str:
    """Resolve o tema da sessão (fonte de verdade: URL ?tema=)."""
    _tema_url = st.query_params.get("tema")
    tema = st.session_state.get("tema", "claro")
    if _tema_url in ("claro", "escuro"):
        tema = st.session_state["tema"] = _tema_url
    elif tema not in ("claro", "escuro"):
        tema = st.session_state["tema"] = "claro"
    return tema


def aplicar_css():
    st.markdown(_BASE_CSS, unsafe_allow_html=True)
    st.markdown(_TEMA_CSS, unsafe_allow_html=True)
    st.markdown(_PROVID_CSS, unsafe_allow_html=True)
    if tema_atual() == "escuro":
        st.markdown('<div data-st-tema="escuro" style="display:none"></div>', unsafe_allow_html=True)
    st.components.v1.html(_JS_BOOTSTRAP, height=0)
