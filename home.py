"""Entrada do app: rota (st.navigation) + CSS global + sidebar/rodapé comuns."""
import streamlit as st

from streamlit.errors import StreamlitAPIException

import auth_supabase
import ui_tema
import roteador
import ui_comum
import sessao_persist
from secoes import login as pagina_login


def _processar_link_email() -> None:
    """Processa o link do e-mail (query param token_hash) que o usuário abriu.

    Dois fluxos, dependendo do `?type=`:
    - `signup`  : confirma o cadastro e loga.
    - `recovery`: valida o link de "Esqueceu a senha?" e abre o formulário para
      definir uma nova senha (flag `_definir_nova_senha` renderizada no fim).
    """
    try:
        parametros = st.query_params
    except Exception:
        parametros = {}
    if not parametros or not parametros.get("token_hash"):
        return
    if parametros.get("type") not in ("signup", "recovery", None):
        return

    token_hash = parametros.get("token_hash")
    if isinstance(token_hash, list):
        token_hash = token_hash[0]
    if not token_hash:
        return

    if parametros.get("type") == "recovery":
        ok, msg, sessao = auth_supabase.recuperar_via_link(token_hash)
        if ok and sessao and sessao.get("access_token"):
            auth_supabase.guardar_sessao(sessao)
            sessao_persist.salvar(sessao)
            st.session_state["_definir_nova_senha"] = True
            st.success("Link de recuperação válido! Defina sua nova senha abaixo.")
        elif ok:
            st.error(msg)
        else:
            st.error(msg)
    else:
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

# Confirmação/recuperação vinda do link do e-mail (query param, não fragmento):
# ?token_hash=...&type=signup / type=recovery -> troca o hash por sessão.
_processar_link_email()

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

# Fim do fluxo "Esqueceu a senha?": depois que a página renderizou, oferece o
# formulário para definir a nova senha (acionado pelo link type=recovery).
if st.session_state.get("_definir_nova_senha"):
    with st.container(border=True):
        st.markdown("#### 🔑 Defina sua nova senha")
        with st.form("form_nova_senha"):
            senha1 = st.text_input("Nova senha", type="password", placeholder="mínimo 8 caracteres", key="_auth_nova_senha_1")
            senha2 = st.text_input("Confirme a nova senha", type="password", key="_auth_nova_senha_2")
            trocar = st.form_submit_button("Salvar nova senha", use_container_width=True)
        if trocar:
            if not senha1 or senha1 != senha2:
                st.error("As senhas não conferem ou estão vazias.")
            else:
                dados = auth_supabase.sessao() or {}
                ok, msg = auth_supabase.definir_senha(senha1, dados.get("access_token"))
                if ok:
                    st.session_state.pop("_definir_nova_senha", None)
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

ui_comum.rodape()

# Navegação pelo rodapé (Termos/Privacidade): o `st.switch_page` preserva a
# posição de rolagem, então a página Legal abria no fim. Roda o scroll-to-top
# só quando esse fluxo foi usado (flag setada em `_ir_para_legal`), depois que
# toda a página — inclusive o rodapé — já foi montada.
if st.session_state.pop("_legal_topo", False):
    ui_comum._rolar_topo()

# Botão interno do dialog usou st.rerun() (ex.: trocar tema), que fecha o modal.
# Este flag reabre o modal com o corpo re-renderizado.
if st.session_state.pop("_reabrir_config", False):
    ui_comum.abrir_configuracoes()
