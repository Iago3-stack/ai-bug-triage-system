# Testes do Painel do Dono (v2.11.0): Teste Premium com validade, tabela
# `usuarios` e ações de admin. Roda com: pytest -v

from datetime import datetime, timedelta, timezone


import admin
import plano
import nuvem_supabase


# ─── plano: Teste Premium com validade ────────────────────────────────────────

def _mock_nuvem_trial(monkeypatch, teste_ate=None, plano_b="free", ativa=True):
    """Máquina fake da nuvem com suporte a teste_ate."""
    class NS:
        @staticmethod
        def disponivel():
            return ativa

        @staticmethod
        def carregar_plano_banco(uid):
            return plano_b

        @staticmethod
        def carregar_teste_banco(uid):
            if teste_ate is _OFFLINE:
                raise RuntimeError("offline")
            return teste_ate

        @staticmethod
        def gravar_teste_banco(uid, ate_iso):
            registros_trial["ate"] = ate_iso
            return True

        @staticmethod
        def gravar_plano_banco(uid, plano_novo, clear_teste=False, clear_assinatura=False):
            registros_trial["plano"] = plano_novo
            registros_trial["clear"] = clear_teste
            registros_trial["clear_assinatura"] = clear_assinatura
            return True

        @staticmethod
        def assinatura_disponivel():
            return False

        @staticmethod
        def carregar_assinatura_banco(uid):
            return None

        @staticmethod
        def gravar_assinatura_banco(uid, ate_iso):
            return True

    registros_trial.clear()
    monkeypatch.setattr(plano, "nuvem_supabase", NS)
    return registros_trial


registros_trial = {}
_OFFLINE = object()


def test_teste_premium_restante_delega_para_nuvem(monkeypatch):
    monkeypatch.setattr(plano, "nuvem_supabase", type("NS", (), {
        "carregar_teste_banco": lambda uid: "2026-10-01T00:00:00+00:00",
    }))
    assert plano.teste_premium_restante("u1") == "2026-10-01T00:00:00+00:00"


def test_teste_premium_offline_retorna_none(monkeypatch):
    monkeypatch.setattr(plano, "nuvem_supabase", type("NS", (), {
        "carregar_teste_banco": lambda uid: (_ for _ in ()).throw(RuntimeError("offline")),
    }))
    assert plano.teste_premium_restante("u1") is None


def test_plano_free_com_teste_ativo_vira_pago(monkeypatch):
    monkeypatch.setenv("PLANO", "free")
    monkeypatch.setattr(plano, "uid_logado", lambda: "u1")
    _mock_nuvem_trial(monkeypatch, teste_ate=(datetime.now(timezone.utc) + timedelta(days=2)).isoformat(), plano_b="free")
    assert plano.plano_atual() == "pago"
    assert plano.pago()


def test_plano_free_com_teste_expirado_fica_free(monkeypatch):
    monkeypatch.setenv("PLANO", "free")
    monkeypatch.setattr(plano, "uid_logado", lambda: "u1")
    _mock_nuvem_trial(monkeypatch, teste_ate=(datetime.now(timezone.utc) - timedelta(days=2)).isoformat(), plano_b="free")
    assert plano.plano_atual() == "free"
    assert not plano.pago()


def test_plano_sem_login_ignora_teste(monkeypatch):
    monkeypatch.setenv("PLANO", "free")
    monkeypatch.setattr(plano, "uid_logado", lambda: None)
    _mock_nuvem_trial(monkeypatch, teste_ate=(datetime.now(timezone.utc) + timedelta(days=2)).isoformat(), plano_b="free")
    assert plano.plano_atual() == "free"


def test_definir_trial_grava_ate_futuro(monkeypatch):
    monkeypatch.setattr(plano, "uid_logado", lambda: "u1")
    _mock_nuvem_trial(monkeypatch, teste_ate=None)
    assert plano.definir_trial("u1", 7) is True
    ate = datetime.fromisoformat(registros_trial["ate"].replace("Z", "+00:00"))
    assert ate > datetime.now(timezone.utc)
    assert (datetime.now(timezone.utc) + timedelta(days=7) - ate).days == 0


def test_definir_trial_offline_nao_levanta(monkeypatch):
    monkeypatch.setattr(plano, "uid_logado", lambda: "u1")
    monkeypatch.setattr(plano, "nuvem_supabase", type("NS", (), {
        "gravar_teste_banco": lambda uid, ate: (_ for _ in ()).throw(RuntimeError("offline")),
    }))
    assert plano.definir_trial("u1", 7) is False


def test_definir_plano_manual_encerra_teste(monkeypatch):
    _mock_nuvem_trial(monkeypatch, teste_ate=None)
    assert plano.definir_plano_manual("u1", "free") is True
    assert registros_trial["plano"] == "free"
    assert registros_trial["clear"] is True
    assert plano.definir_plano_manual("u1", "pago") is True
    assert registros_trial["plano"] == "pago"
    assert registros_trial["clear"] is True


def test_definir_plano_manual_invalido_vira_free(monkeypatch):
    _mock_nuvem_trial(monkeypatch)
    assert plano.definir_plano_manual("u1", "luxo") is True
    assert registros_trial["plano"] == "free"


# ─── nuvem_supabase: planos/trial ─────────────────────────────────────────────

class _Resp:
    status_code = 200

    def __init__(self, payload=None):
        self._payload = payload or []

    def json(self):
        return self._payload

    def raise_for_status(self):
        return None


def _mock_rest(monkeypatch, resp):
    monkeypatch.setattr(nuvem_supabase, "_config", lambda: ("https://supa.supabase.co", "chave"))
    monkeypatch.setattr(nuvem_supabase.requests, "get", lambda *a, **k: _Resp(resp))
    monkeypatch.setattr(nuvem_supabase.requests, "post", lambda *a, **k: _Resp())
    monkeypatch.setattr(nuvem_supabase.requests, "patch", lambda *a, **k: _Resp())
    return nuvem_supabase._headers()


def test_gravar_plano_pago_limpa_teste(monkeypatch):
    chamadas = {"post": 0, "patch": []}

    def _post(*a, **k):
        chamadas["post"] += 1
        return _Resp()

    def _patch(*a, **k):
        chamadas["patch"].append((k.get("params"), k.get("json")))
        return _Resp()

    monkeypatch.setattr(nuvem_supabase, "_config", lambda: ("https://supa.supabase.co", "chave"))
    monkeypatch.setattr(nuvem_supabase.requests, "post", _post)
    monkeypatch.setattr(nuvem_supabase.requests, "patch", _patch)
    assert nuvem_supabase.gravar_plano_banco("u1", "pago") is True
    assert chamadas["post"] == 1
    assert chamadas["patch"] == [({"uid": "eq.u1"}, {"teste_ate": None})]


def test_gravar_plano_free_com_clear_tambem_limpa(monkeypatch):
    chamadas = {"patch": []}

    def _patch(*a, **k):
        chamadas["patch"].append((k.get("params"), k.get("json")))
        return _Resp()

    monkeypatch.setattr(nuvem_supabase, "_config", lambda: ("https://supa.supabase.co", "chave"))
    monkeypatch.setattr(nuvem_supabase.requests, "post", lambda *a, **k: _Resp())
    monkeypatch.setattr(nuvem_supabase.requests, "patch", _patch)
    assert nuvem_supabase.gravar_plano_banco("u1", "free", clear_teste=True) is True
    assert chamadas["patch"] == [({"uid": "eq.u1"}, {"teste_ate": None})]


def test_gravar_plano_free_sem_clear_nao_faz_patch(monkeypatch):
    chamadas = {"patch": []}

    def _patch(*a, **k):
        chamadas["patch"].append(1)
        return _Resp()

    monkeypatch.setattr(nuvem_supabase, "_config", lambda: ("https://supa.supabase.co", "chave"))
    monkeypatch.setattr(nuvem_supabase.requests, "post", lambda *a, **k: _Resp())
    monkeypatch.setattr(nuvem_supabase.requests, "patch", _patch)
    assert nuvem_supabase.gravar_plano_banco("u1", "free") is True
    assert chamadas["patch"] == []


def test_carregar_teste_banco(monkeypatch):
    _mock_rest(monkeypatch, [{"teste_ate": "2026-10-01T00:00:00+00:00"}])
    assert nuvem_supabase.carregar_teste_banco("u1") == "2026-10-01T00:00:00+00:00"
    _mock_rest(monkeypatch, [])
    assert nuvem_supabase.carregar_teste_banco("u1") is None


def test_carregar_teste_banco_offline(monkeypatch):
    monkeypatch.setattr(nuvem_supabase, "_config", lambda: None)
    assert nuvem_supabase.carregar_teste_banco("u1") is None


def test_gravar_teste_banco_upsert(monkeypatch):
    chamadas = {}

    def _post(url, headers=None, params=None, json=None, timeout=None):
        chamadas["url"] = url
        chamadas["params"] = params
        chamadas["json"] = json
        return _Resp()

    monkeypatch.setattr(nuvem_supabase, "_config", lambda: ("https://supa.supabase.co", "chave"))
    monkeypatch.setattr(nuvem_supabase.requests, "post", _post)
    assert nuvem_supabase.gravar_teste_banco("u1", "2026-10-01T00:00:00+00:00") is True
    assert chamadas["url"].endswith("/planos_usuario")
    assert chamadas["params"] == {"on_conflict": "uid"}
    assert chamadas["json"] == {"uid": "u1", "teste_ate": "2026-10-01T00:00:00+00:00"}


def test_carregar_todos_planos(monkeypatch):
    _mock_rest(monkeypatch, [{"uid": "u1", "plano": "pago", "teste_ate": None}])
    assert nuvem_supabase.carregar_todos_planos() == [
        {"uid": "u1", "plano": "pago", "teste_ate": None, "teste_auto": None, "assinatura_ate": None}
    ]


def test_carregar_todos_planos_cai_sem_teste_quando_coluna_falta(monkeypatch):
    """ALTER TABLE pendente: select c/ colunas novas falha → refaz sem elas."""
    chamadas = []

    class _Erro(_Resp):
        def raise_for_status(self):
            raise Exception("400: Bad Request (coluna inexistente)")

    def _get(url, headers=None, params=None, timeout=None):
        chamadas.append(params["select"])
        if "teste_auto" in params["select"] or "teste_ate" in params["select"] or "assinatura_ate" in params["select"]:
            return _Erro()
        return _Resp([{"uid": "u1", "plano": "pago"}, {"uid": "u2", "plano": "free"}])

    monkeypatch.setattr(nuvem_supabase, "_config", lambda: ("https://supa.supabase.co", "chave"))
    monkeypatch.setattr(nuvem_supabase.requests, "get", _get)
    docs = nuvem_supabase.carregar_todos_planos()
    assert len(chamadas) == 4
    assert docs[0] == {"uid": "u1", "plano": "pago", "teste_ate": None, "teste_auto": None, "assinatura_ate": None}
    assert docs[1] == {"uid": "u2", "plano": "free", "teste_ate": None, "teste_auto": None, "assinatura_ate": None}


def test_carregar_todos_planos_sem_tabela_retorna_vazio(monkeypatch):
    class _Erro(_Resp):
        def raise_for_status(self):
            raise Exception("400/404")

    def _get(*a, **k):
        return _Erro()

    monkeypatch.setattr(nuvem_supabase, "_config", lambda: ("https://supa.supabase.co", "chave"))
    monkeypatch.setattr(nuvem_supabase.requests, "get", _get)
    assert nuvem_supabase.carregar_todos_planos() == []


def test_carregar_teste_banco_erro_retorna_none(monkeypatch):
    class _Erro(_Resp):
        def raise_for_status(self):
            raise Exception("400: coluna inexistente")

    monkeypatch.setattr(nuvem_supabase, "_config", lambda: ("https://supa.supabase.co", "chave"))
    monkeypatch.setattr(nuvem_supabase.requests, "get", lambda *a, **k: _Erro())
    assert nuvem_supabase.carregar_teste_banco("u1") is None


def test_gravar_plano_pago_patch_falha_nao_anula_upsert(monkeypatch):
    class _Erro(_Resp):
        def raise_for_status(self):
            raise Exception("400: coluna inexistente")

    def _patch(*a, **k):
        return _Erro()

    monkeypatch.setattr(nuvem_supabase, "_config", lambda: ("https://supa.supabase.co", "chave"))
    monkeypatch.setattr(nuvem_supabase.requests, "post", lambda *a, **k: _Resp())
    monkeypatch.setattr(nuvem_supabase.requests, "patch", _patch)
    assert nuvem_supabase.gravar_plano_banco("u1", "pago") is True


def test_carregar_todos_perfis(monkeypatch):
    _mock_rest(monkeypatch, [{"uid": "u1", "nome": "Iago", "empresa": "QA", "avatar": ""}])
    assert nuvem_supabase.carregar_todos_perfis() == [{"uid": "u1", "nome": "Iago", "empresa": "QA", "avatar": ""}]


# ─── nuvem_supabase: tabela usuarios ──────────────────────────────────────────

def test_registrar_usuario_banco_upsert(monkeypatch):
    chamadas = {}

    def _post(url, headers=None, params=None, json=None, timeout=None):
        chamadas["url"] = url
        chamadas["params"] = params
        chamadas["json"] = json
        return _Resp()

    monkeypatch.setattr(nuvem_supabase, "_config", lambda: ("https://supa.supabase.co", "chave"))
    monkeypatch.setattr(nuvem_supabase.requests, "post", _post)
    assert nuvem_supabase.registrar_usuario_banco("u1", "dev@qa.com") is True
    assert chamadas["url"].endswith("/usuarios")
    assert chamadas["params"] == {"on_conflict": "uid"}
    assert chamadas["json"]["uid"] == "u1"
    assert chamadas["json"]["email"] == "dev@qa.com"
    assert "ultimo_login" in chamadas["json"]


def test_registrar_usuario_banco_nunca_levanta(monkeypatch):
    monkeypatch.setattr(nuvem_supabase, "_config", lambda: ("x", "y"))
    monkeypatch.setattr(nuvem_supabase.requests, "post", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("rede")))
    nuvem_supabase.registrar_usuario_banco("u1", "dev@qa.com") is False
    monkeypatch.setattr(nuvem_supabase, "_config", lambda: None)
    assert nuvem_supabase.registrar_usuario_banco("u1", "dev@qa.com") is False


def test_carregar_usuarios_ordena_por_ultimo_login(monkeypatch):
    chamadas = {}

    def _get(url, headers=None, params=None, timeout=None):
        chamadas["url"] = url
        chamadas["params"] = params
        return _Resp([{"uid": "u2", "email": "b@qa.com"}, {"uid": "u1", "email": "a@qa.com"}])

    monkeypatch.setattr(nuvem_supabase, "_config", lambda: ("https://supa.supabase.co", "chave"))
    monkeypatch.setattr(nuvem_supabase.requests, "get", _get)
    assert nuvem_supabase.carregar_usuarios()[0]["uid"] == "u2"
    assert chamadas["url"].endswith("/usuarios")
    assert chamadas["params"]["order"] == "ultimo_login.desc"


def test_carregar_usuarios_offline_retorna_lista_vazia(monkeypatch):
    monkeypatch.setattr(nuvem_supabase, "_config", lambda: None)
    assert nuvem_supabase.carregar_usuarios() == []
    assert nuvem_supabase.carregar_todos_planos() == []
    assert nuvem_supabase.carregar_todos_perfis() == []


# ─── admin: quem é o dono ─────────────────────────────────────────────────────

def test_eh_dono_sem_admin_email_nunca(monkeypatch):
    monkeypatch.delenv("ADMIN_EMAIL", raising=False)
    monkeypatch.setattr(admin, "email_logado", lambda: "dev@qa.com")
    assert admin.eh_dono() is False


def test_eh_dono_email_igual(monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "dono@qa.com")
    monkeypatch.setattr(admin, "email_logado", lambda: "dono@qa.com")
    assert admin.eh_dono() is True


def test_eh_dono_email_diferente(monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "dono@qa.com")
    monkeypatch.setattr(admin, "email_logado", lambda: "outro@qa.com")
    assert admin.eh_dono() is False


def test_email_logado_sem_sessao_none(monkeypatch):
    import auth_supabase
    monkeypatch.setattr(auth_supabase, "sessao", lambda: None)
    assert admin.email_logado() is None


def test_eh_dono_com_case_diferente(monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "Dono@QA.com")
    monkeypatch.setattr(admin, "email_logado", lambda: "dono@qa.com")
    assert admin.eh_dono() is True


# ─── roteador: painel só aparece para o dono ─────────────────────────────────

def test_rotas_sem_dono_nao_incluem_painel(monkeypatch):
    import roteador

    monkeypatch.setattr(admin, "eh_dono", lambda: False)
    assert len(roteador.paginas_visiveis()) == 6


def test_rotas_do_dono_incluem_painel(monkeypatch):
    import roteador

    monkeypatch.setattr(admin, "eh_dono", lambda: True)
    assert len(roteador.paginas_visiveis()) == 7


# ─── formatadores da página do dono ──────────────────────────────────────────

def test_fmt_data_formata_iso_e_falha_amigavel():
    from datetime import datetime
    from secoes import painel_dono as pd

    esperado = datetime.fromisoformat("2026-09-15T13:00:00+00:00").astimezone().strftime("%d/%m/%Y %H:%M")
    assert pd._fmt_data("2026-09-15T13:00:00+00:00") == esperado
    assert pd._fmt_data(None) == "—"
    assert pd._fmt_data("lixo") == "lixo"


def test_badges_dos_planos():
    from secoes import painel_dono as pd

    for tipo in ("premium", "teste", "basic"):
        badge = pd._badge(tipo)
        assert tipo in "premium teste basic".split() and badge.startswith("<span")


def test_painel_tem_secao_de_feedbacks():
    from pathlib import Path

    raiz = Path(__file__).resolve().parent
    fonte = (raiz / "secoes" / "painel_dono.py").read_text(encoding="utf-8")
    nuvem = (raiz / "nuvem_supabase.py").read_text(encoding="utf-8")
    # Seção visível no painel + carregamento tolerante (sem quebrar quandodo vazio)
    assert "💬 Feedbacks de usuários" in fonte
    assert "carregar_feedbacks" in fonte
    assert "dono_fb_del" in fonte
    assert "excluir_feedback" in fonte and "excluir_feedback" in nuvem
    assert "média" in fonte and "⭐" in fonte
    # Cartão usa classe .fb-card (sem cores inline lavadas) e o Remover é vermelho sem glow
    assert 'class="fb-card"' in fonte
    css = (raiz / "ui_tema.py").read_text(encoding="utf-8")
    assert ".fb-card" in css and "box-shadow: none !important" in css
    assert "marca-fb-del" in css and "#dc2626" in css
    assert "focus-visible" in css
    assert "body:has([data-st-tema=\"escuro\"]) .fb-card" in css


# ─── teste_disponivel: coluna teste_ate na schema cache do PostgREST ────────

def test_teste_disponivel_detecta_coluna_faltando(monkeypatch):
    chamadas = []

    def _fake_get(url, headers=None, params=None, timeout=None):
        chamadas.append(params)
        class R:
            status_code = 400  # PGRST204: teste_ate fora do schema cache

        return R()

    monkeypatch.setattr(nuvem_supabase.requests, "get", _fake_get)
    monkeypatch.setattr(nuvem_supabase, "_config", lambda: {"url": "x", "chave": "k"})
    assert nuvem_supabase.teste_disponivel() is False
    assert chamadas and "teste_ate" in chamadas[0]["select"]


def test_teste_disponivel_true_quando_coluna_existe(monkeypatch):
    def _fake_get(url, headers=None, params=None, timeout=None):
        class R:
            status_code = 200

        return R()

    monkeypatch.setattr(nuvem_supabase.requests, "get", _fake_get)
    monkeypatch.setattr(nuvem_supabase, "_config", lambda: {"url": "x", "chave": "k"})
    assert nuvem_supabase.teste_disponivel() is True


def test_teste_disponivel_sem_config_false(monkeypatch):
    monkeypatch.setattr(nuvem_supabase, "_config", lambda: None)
    assert nuvem_supabase.teste_disponivel() is False

# ─── Rótulo de severidade: contrato de tema claro/escuro (v3.5.0) ────────────
# A tela nasceu com cor CLARA fixa (pensada só para o tema escuro) e o texto
# sumia no tema claro; os botões ainda herdavam o hover nativo do Streamlit.
# Estes testes existem para ninguém reintroduzir os dois defeitos.

import re  # noqa: E402  (no topo do arquivo, junto dos demais imports)

import ui_tema  # noqa: E402
from secoes import painel_dono  # noqa: E402


def _contraste(cor: str, fundo: str = "#ffffff") -> float:
    """Razão de contraste WCAG entre duas cores hex."""
    def _l(h):
        canais = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        canais = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in canais]
        return 0.2126 * canais[0] + 0.7152 * canais[1] + 0.0722 * canais[2]
    a, b = _l(cor), _l(fundo)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


def test_cartao_nao_usa_cor_fixa():
    html = painel_dono._cartao("app caiu")
    assert 'class="rot-cartao"' in html
    assert "color:#" not in html  # cor fixa = invisível no tema claro


def test_css_da_rotulagem_tem_as_duas_variantes_de_tema():
    css = ui_tema._ROTULAGEM_CSS
    for seletor in (".rot-cartao", ".rot-topo", ".rot-nota"):
        assert f'body:has([data-st-tema="escuro"]) {seletor}' in css, (
            f"{seletor} não tem variante escura: some quando o tema é claro"
        )
        assert seletor in css


def test_botoes_da_fila_sao_solidos_e_nao_mudam_no_hover():
    css = ui_tema._ROTULAGEM_CSS
    for marca, fundo in (("crit", "#dc2626"), ("med", "#b45309"),
                         ("norm", "#047857"), ("pular", "#475569")):
        base = f"[data-testid=\"stColumn\"]:has(.marca-rot-{marca}) [data-testid=\"stButton\"] button {{"
        normal = css.split(base)[1].split("}")[0]
        assert f"background:{fundo} !important" in normal
        assert "color:#ffffff !important" in normal
        # O truque do app para desligar o hover nativo é repetir a MESMA cor
        # de fundo na regra :hover — se sumir, o botão volta a mudar de cor.
        hover = f".marca-rot-{marca}) [data-testid=\"stButton\"] button:hover"
        assert hover in css
        assert f"background:{fundo} !important" in css.split(hover)[1].split("}")[0]


def test_cores_dos_botoes_passam_contraste_aa_com_texto_branco():
    # Tons -600 reprovam: #d97706 = 3,19:1 e #059669 = 3,77:1 (mínimo AA: 4,5).
    for fundo in ("#dc2626", "#b45309", "#047857", "#475569", "#334155"):
        assert _contraste(fundo) >= 4.5, f"{fundo} reprova em contraste AA"


def test_toda_marca_usada_no_painel_existe_no_css():
    """Trava o modo de falha real: marca no código com nome diferente do CSS
    deixa o botão sem estilo nenhum, sem erro nenhum."""
    css = ui_tema._ROTULAGEM_CSS
    usadas = set(re.findall(r"marca-rot-\w+", __import__("inspect").getsource(painel_dono)))
    assert usadas, "esperava marcas de rotulamento no painel"
    for marca in usadas:
        assert marca in css, f"{marca} é usada no painel mas não existe no CSS"


# ─── Pré-rotulados do agente (v3.5.9): revisão e promoção ────────────────────
# A tela é a única janela para o rótulo de agente, que é invisível nos outros
# dois lugares: não volta para a fila de pendentes (já tem rótulo) e não entra
# na métrica (filtro por autor). Estes testes travam o contrato dessa janela.

def test_secao_de_rotulagem_chama_as_duas_filas():
    corpo = __import__("inspect").getsource(painel_dono._secao_rotulagem)
    # `return` de "fila vazia" não pode engolir a tela de pré-rotulados: são
    # tarefas diferentes, e a fila vazia é justamente o caso em que sobra só a outra.
    assert "_bloco_fila()" in corpo
    assert "_secao_pre_rotulados()" in corpo


def test_bloco_da_fila_devolve_so_quando_vazio():
    corpo = __import__("inspect").getsource(painel_dono._bloco_fila)
    guarda = corpo.index("if not fila:")
    trecho = corpo[guarda:guarda + 300]
    assert 'st.success("🎉 Tudo rotulado' in trecho
    # o return precisa vir DEPOIS do success, dentro da guarda: antes dele, a
    # seção de pré-rotulados nunca renderizaria.
    assert trecho.index("return") > trecho.index("st.success")


def test_tela_de_pre_rotulados_existe_e_nao_usa_cor_inline():
    corpo = __import__("inspect").getsource(painel_dono._secao_pre_rotulados)
    assert "🤖 Pré-rotulados pelo agente" in corpo
    assert "carregar_pre_rotulados" in corpo
    # Cor fixa = invisível no tema claro (mesmo defeito do .rot-cartao).
    assert "color:#" not in corpo and "background:#" not in corpo
    assert "agente sugeriu" in corpo  # a sugestão precisa ficar visível
    assert "Não contam" in corpo and "métrica" in corpo


def test_promover_passa_pelo_guard_de_autor_humano():
    corpo = __import__("inspect").getsource(painel_dono._promover_grupo)
    # Registrar direto deixaria o rótulo de agente na métrica sem revisão humana.
    assert "avaliacao.promover(" in corpo
    assert "registrar_varios" not in corpo


def test_paginacao_da_fila_usa_o_deslocamento_da_sessao():
    corpo = __import__("inspect").getsource(painel_dono._bloco_fila)
    # Regressão: `_rot_offset` era escrito pelos botões e nunca lido, então
    # "Ver mais →" apenas redesenhavam a mesma primeira página.
    assert 'st.session_state.get("_rot_offset", 0)' in corpo
    assert corpo.count("deslocamento=deslocamento") >= 2  # a página e a sondagem do "mais"


def test_bloco_da_fila_preserva_o_titulo_da_secao():
    corpo = __import__("inspect").getsource(painel_dono._bloco_fila)
    # Regressão: ao extrair a fila para função própria, o `#### Fila para rotular`
    # ficou para trás e a fila passou a ler como preâmbulo da tela de
    # pré-rotulados, sem landmark próprio.
    assert "#### Fila para rotular" in corpo
    assert corpo.index("#### Fila para rotular") < corpo.index("if not fila:")


def test_atalho_zero_avanca_o_offset_como_o_botao_pular():
    corpo = __import__("inspect").getsource(painel_dono._campo_atalho)
    # A caption e o `help` do campo anunciam "0 pular"; o botão foi consertado
    # para avançar o offset, e o teclado ficava só com `rerun` — as duas
    # afordâncias de "pular" discordando entre si.
    assert 'st.session_state["_rot_offset"]' in corpo
    assert '_rot_offset", 0) + 1' in corpo


def test_promover_comentario_vazio_preserva_o_do_agente():
    corpo = __import__("inspect").getsource(painel_dono._secao_pre_rotulados)
    # A tela não mostra o comentário que o agente gravou, então promover sem
    # digitar nada é o caminho fácil de apagar a justificativa da sugestão.
    assert "item.get(\"comentario\")" in corpo
    assert "(comentario or \"\").strip() or" in corpo


def test_voltar_ao_inicio_existe_antes_do_return_de_lista_vazia():
    corpo = __import__("inspect").getsource(painel_dono._bloco_fila)
    guarda = corpo.index("if not fila:")
    trecho = corpo[guarda:guarda + 400]
    # Promover o último item da página esvazia a lista e leva o offset junto; sem
    # o botão antes do `return` não há como voltar.
    assert "_voltar_ao_inicio(" in trecho
    assert trecho.index("_voltar_ao_inicio(") < trecho.index("return")
