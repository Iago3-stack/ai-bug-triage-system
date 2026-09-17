"""Entrada do app: rota (st.navigation) + CSS global + sidebar/rodapé comuns."""
import streamlit as st

from streamlit.errors import StreamlitAPIException

import auth_supabase
import ui_tema
import roteador
import ui_comum
import sessao_persist
from secoes import login as pagina_login


def _processar_confirmacao_email() -> None:
    """Confirma o cadastro quando a URL traz o token_hash vindo do e-mail.

    O template de e-mail do Supabase aponta o link para
    `SiteURL?token_hash=...&type=signup` (query param). O Streamlit lê a query
    string, mas ignora o fragmento (#) que o fluxo padrão usa — por isso o
    template usa token_hash. Aqui trocamos o hash por uma sessão real.
    """
    try:
        parametros = st.query_params
    except Exception:
        parametros = {}
    if not parametros or not parametros.get("token_hash"):
        return
    if parametros.get("type") not in ("signup", None):
        return

    token_hash = parametros.get("token_hash")
    if isinstance(token_hash, list):
        token_hash = token_hash[0]
    if not token_hash:
        return

    ok, msg, sessao = auth_supabase.confirmar_cadastro(token_hash)
    if ok and sessao and sessao.get("user"):
        auth_supabase.guardar_sessao(sessao)
        sessao_persist.salvar(sessao)
        st.success("E-mail confirmado! Bem-vindo(a).")
    elif ok:
        st.success("E-mail confirmado! Agora é só entrar com e-mail e senha.")
    else:
        st.error(msg)

    # Limpa o link (senão todo rerun reprocessaria o token_hash já consumido).
    try:
        del parametros["token_hash"]
        del parametros["type"]
    except Exception:
        pass


ui_tema.config_pagina()

# Reload (F5): restaura a sessão salva no navegador (localStorage) renovando o
# access_token via refresh_token. Assim o usuário não desloga ao recarregar e a
# navegação (abaixo) já sabe se é o dono.
sessao_persist.carregar()

# Ponte de escrita para o navegador (login/logout enfileirados): mantém o
# componente montado até o iframe confirmar a gravação.
sessao_persist.processar_pendente()

# Confirmação de cadastro vinda do link do e-mail (query param, não fragmento):
# ?token_hash=...&type=signup -> troca o hash por uma sessão e loga o usuário.
_processar_confirmacao_email()

# Páginas visíveis: o Painel do Administrador só entra quando a conta logada é ADMIN_EMAIL.
pg = st.navigation(roteador.paginas_visiveis(), position="sidebar")
st.session_state["_url_atual"] = pg.url_path

ui_tema.aplicar_css()

with st.sidebar:
    ui_comum.sidebar_comum()

ui_comum.menu_top(pg)

# Passo 2 (SaaS): Início é público; as demais páginas exigem login quando o
# Supabase Auth está configurado. Sem configuração, o app segue integralmente aberto.
if pg.url_path in ("triagem", "meu_plano", "dashboard", "painel_dono") and pagina_login.render():
    st.stop()

# Sessão iniciada numa versão anterior (a lista de páginas mudou no deploy) pode
# deixar a navegação do frontend dessincronizada: o pg devolvido chega
# "desqualificado" e o pg.run() levanta. Em vez de mostrar a tela de erro, manda
# para o Início uma vez — a navegação recomeça limpa na próxima execução.
try:
    pg.run()
except StreamlitAPIException as _exc:
    if "cannot be called directly" in str(_exc):
        st.switch_page(roteador.PAGINAS["inicio"])
    else:
        raise
ui_comum.rodape()

# Botão interno do dialog usou st.rerun() (ex.: trocar tema), que fecha o modal.
# Este flag reabre o modal com o corpo re-renderizado.
if st.session_state.pop("_reabrir_config", False):
    ui_comum.abrir_configuracoes()
