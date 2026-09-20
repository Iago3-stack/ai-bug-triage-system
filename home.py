"""Entrada do app: rota (st.navigation) + CSS global + sidebar/rodapé comuns."""
import os


def _carregar_env_local() -> None:
    """Sobe o arquivo .env para os.environ (antes de importar o resto).

    Sem dependência externa (python-dotenv): imita o .env com linhas
    CHAVE=valor (espaços ao redor do "=" ignorados, "#" = comentário).
    Só aplica se a variável ainda não existe no ambiente (o export do
    terminal continua tendo prioridade). No Streamlit Cloud não existe
    .env: aqui é no-op e valem os Secrets.
    """
    try:
        caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        if not os.path.exists(caminho):
            return
        with open(caminho, encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if not linha or linha.startswith("#") or "=" not in linha:
                    continue
                chave, _, valor = linha.partition("=")
                chave = chave.strip()
                if chave:
                    os.environ.setdefault(chave, valor.strip())
    except Exception:
        pass


_carregar_env_local()

import streamlit as st

from streamlit.errors import StreamlitAPIException

import auth_supabase
import ui_tema
import roteador
import ui_comum
import sessao_persist
from secoes import login as pagina_login


def _ponte_fragmento() -> None:
    """Converte link do e-mail no formato fragmento (#...) para query (?).

    Dependendo do "Flow Type" no Supabase (Implicit), o link de recuperação/
    confirmação chega como `#access_token=...`, que o Streamlit ignora (só lê a
    query string). Este componente roda um script que reescreve a URL e
    recarrega, devolvendo os parâmetros para o Python processar.
    """
    js = r"""
<script>
(function(){
  try {
    var hash = (window.top.location.hash || "").replace(/^#/, "");
    if (hash.indexOf("access_token") === -1 && hash.indexOf("token_hash") === -1) return;
    var sep = window.top.location.search ? "&" : "?";
    window.top.location.replace(window.top.location.pathname + window.top.location.search + sep + hash);
  } catch (e) { /* mesma origem impedida: ignora (fluxo query continua funcionando) */ }
})();
</script>
"""
    # Injeta o componente UMA vez por sessão: re-renderizá-lo a cada rerun só
    # aumenta o churn de iframe e agrava o "removeChild" do frontend do React.
    if st.session_state.get("_ponte_fragmento_injetada"):
        return
    try:
        import streamlit.components.v1 as componentes

        componentes.html(js, height=0)
        st.session_state["_ponte_fragmento_injetada"] = True
    except Exception:
        pass


def _link_ja_usado(identificador: str, msg: str) -> None:
    """Link de uso único já consumido/expirado.

    Típico: o usuário conclui o reset e recarrega a página (F5). O session_state
    zera, a sessão é restaurada do localStorage e a URL ainda traz o token -> o
    re-processamento falha. Com sessão ativa não assusta com erro vermelho:
    marca como consumido e segue quieto. Sem sessão, mostra o erro normal.
    """
    if auth_supabase.usuario_logado():
        st.session_state["_link_email_consumido"] = identificador
        return
    st.error(msg)


def _processar_link_email() -> None:
    """Processa o link do e-mail (query param token_hash/access_token) que o usuário abriu.

    Dois fluxos, dependendo do `?type=`:
    - `signup`  : confirma o cadastro e loga.
    - `recovery`: valida o link de "Esqueceu a senha?" e abre o formulário para
      definir uma nova senha (flag `_definir_nova_senha` renderizada no topo).
    """
    try:
        parametros = st.query_params
    except Exception:
        parametros = {}
    if not parametros or not (parametros.get("token_hash") or parametros.get("access_token")):
        return
    tipo = parametros.get("type")
    if isinstance(tipo, list):
        tipo = tipo[0] if tipo else None
    if tipo not in ("signup", "recovery", None):
        return

    token_hash = parametros.get("token_hash")
    if isinstance(token_hash, list):
        token_hash = token_hash[0]

    access_token = parametros.get("access_token")
    if isinstance(access_token, list):
        access_token = access_token[0]

    # Um único link por sessão: se a query ainda estiver na URL após usar o
    # token (a limpeza de query_params pode não refletir na barra), não reprocessa.
    identificador = token_hash or access_token
    if identificador and st.session_state.get("_link_email_consumido") == identificador:
        return

    if token_hash:
        if tipo == "recovery":
            ok, msg, sessao = auth_supabase.recuperar_via_link(token_hash)
            if ok and sessao and sessao.get("access_token"):
                st.session_state["_link_email_consumido"] = token_hash
                auth_supabase.guardar_sessao(sessao)
                sessao_persist.salvar(sessao)
                st.session_state["_definir_nova_senha"] = True
                st.success("Link de recuperação válido! Defina sua nova senha abaixo.")
            else:
                _link_ja_usado(token_hash, msg)
        else:
            ok, msg, sessao = auth_supabase.confirmar_cadastro(token_hash)
            if ok and sessao and sessao.get("user"):
                st.session_state["_link_email_consumido"] = token_hash
                auth_supabase.guardar_sessao(sessao)
                sessao_persist.salvar(sessao)
                st.success("E-mail confirmado! Bem-vindo(a).")
            elif ok:
                st.session_state["_link_email_consumido"] = token_hash
                st.success("E-mail confirmado! Agora é só entrar com e-mail e senha.")
            else:
                _link_ja_usado(token_hash, msg)
    else:
        # Fluxo implícito (#access_token=... convertido para query pelo bridge):
        # o token já é uma sessão real — monta a sessão e decide pelo type.
        user = auth_supabase.usuario_por_token(access_token)
        refresh_token = parametros.get("refresh_token")
        if isinstance(refresh_token, list):
            refresh_token = refresh_token[0]
        user = auth_supabase.usuario_por_token(access_token)
        sessao = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user or {"email": None},
        }
        auth_supabase.guardar_sessao(sessao)
        sessao_persist.salvar(sessao)
        if tipo == "recovery":
            st.session_state["_link_email_consumido"] = access_token
            st.session_state["_definir_nova_senha"] = True
            st.success("Link de recuperação válido! Defina sua nova senha abaixo.")
        else:
            email = (user or {}).get("email")
            quem = f"({email})" if email else ""
            st.success(f"E-mail confirmado via link! Logado {quem}.")

    # Limpa o link (senão todo rerun reprocessaria o token já consumido).
    for chave in ("token_hash", "type", "access_token", "refresh_token"):
        try:
            del parametros[chave]
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

# Bridge do link do e-mail no formato fragmento (#access_token...) -> query (?).
_ponte_fragmento()

# Confirmação/recuperação vinda do link do e-mail (query param, não fragmento):
# ?token_hash=...&type=signup / type=recovery -> troca o hash por sessão.
_processar_link_email()

# Fim do fluxo "Esqueceu a senha?": logo ao abrir o link type=recovery, oferece o
# formulário para definir a nova senha (topo da página, acima do conteúdo).
if st.session_state.pop("_senha_alterada_ok", False):
    st.success("Senha alterada com sucesso! Use a nova senha da próxima vez.")

if st.session_state.get("_definir_nova_senha"):
    with st.container(border=True):
        st.markdown("#### 🔑 Defina sua nova senha")
        with st.form("form_nova_senha"):
            senha1 = st.text_input(
                "Nova senha", type="password", placeholder="mínimo 8 caracteres", key="_auth_nova_senha_1"
            )
            senha2 = st.text_input("Confirme a nova senha", type="password", key="_auth_nova_senha_2")
            trocar = st.form_submit_button("Salvar nova senha", use_container_width=True)
        if trocar:
            if not senha1 or senha1 != senha2:
                st.error("As senhas não conferem ou estão vazias.")
            else:
                dados = auth_supabase.sessao() or {}
                ok, msg = auth_supabase.definir_senha(senha1, dados.get("access_token"))
                if ok:
                    # Recarrega a página limpa: garante que o quadrado do
                    # formulário desapareça na hora (st.rerun sozinho não bastava).
                    st.session_state["_senha_alterada_ok"] = True
                    st.session_state.pop("_definir_nova_senha", None)
                    try:
                        st.switch_page(roteador.PAGINAS["inicio"])
                    except Exception:
                        st.rerun()
                else:
                    st.error(msg)

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
