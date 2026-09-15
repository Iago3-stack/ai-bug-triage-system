"""Perfil do usuário (Passo 5 do caminho SaaS).

Dados não-sensíveis da conta logada: nome de exibição, empresa, fuso horário e
avatar (base64 compacto). Salvos na nuvem (tabela `perfis_usuario`) com
fallback JSONL local em `data/perfis.jsonl` (mesmo padrão do plano/cobranças).

Ordem de resolução:
  1. Usuário logado (Supabase Auth) => perfil vem do banco (`perfis_usuario`).
  2. Sem login / sem banco / erro de rede => fallback local JSONL (ou padrão).

Variáveis de ambiente (fallback/depur):
  PERFIL_ARQUIVO = caminho alternativo do JSONL (usado nos testes)
"""

import os

import nuvem_supabase

_FUSOS_PADRAO = ["America/Sao_Paulo", "America/Manaus", "America/Fortaleza",
                 "America/Belem", "America/Recife", "America/Porto_Velho"]


def _padrao() -> dict:
    return {"nome": "", "empresa": "", "fuso": _FUSOS_PADRAO[0], "avatar": ""}


def _arquivo_jsonl() -> str:
    return os.environ.get("PERFIL_ARQUIVO", "") or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data", "perfis.jsonl"
    )


def _iniciais(texto: str, limite: int = 2) -> str:
    """Iniciais para a bolinha (ex.: 'Iago Nunes' -> 'IN')."""
    partes = [p for p in (texto or "").split() if p]
    if not partes:
        return "?"
    letras = [partes[0][0]]
    if len(partes) > 1:
        letras.append(partes[-1][0])
    return "".join(letras).upper()[:limite]


def _carregar_jsonl() -> dict[str, dict]:
    """Lê todos os perfis do JSONL local: {uid: perfil}."""
    caminho = _arquivo_jsonl()
    if not os.path.exists(caminho):
        return {}
    import json

    perfis = {}
    try:
        with open(caminho, encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if not linha:
                    continue
                try:
                    doc = json.loads(linha)
                except Exception:
                    continue
                uid = doc.get("uid")
                if uid:
                    perfis[uid] = doc.get("perfil") or {}
    except Exception:
        return {}
    return perfis


def _gravar_jsonl(perfis: dict[str, dict]) -> None:
    """Grava todos os perfis no JSONL local (cria o diretório data/ se preciso)."""
    import json

    caminho = _arquivo_jsonl()
    try:
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "w", encoding="utf-8") as f:
            for uid, perfil in sorted(perfis.items()):
                f.write(json.dumps({"uid": uid, "perfil": perfil}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def fuso_valido(fuso: str, padrao: str | None = None) -> bool:
    """True se o fuso é conhecido pelo sistema de zonas do SO."""
    import zoneinfo

    padrao = padrao or _FUSOS_PADRAO[0]
    try:
        zoneinfo.ZoneInfo((fuso or "").strip() or padrao)
        return True
    except Exception:
        return False


def normalizar_fuso(fuso: str, padrao: str | None = None) -> str:
    """Retorna o fuso normalizado; inválido/vazio cai no padrão (América/São_Paulo)."""
    valor = (fuso or "").strip()
    if valor and fuso_valido(valor, padrao):
        return valor
    return padrao or _FUSOS_PADRAO[0]


def carregar(uid: str) -> dict:
    """Perfil do usuário: banco (nuvem) first, senão JSONL local, senão padrão."""
    if not uid:
        return _padrao()
    try:
        banco = nuvem_supabase.carregar_perfil_banco(uid)
        if banco is not None:
            perfil = {**_padrao(), **banco}
            perfil["fuso"] = normalizar_fuso(perfil.get("fuso") or "")
            return perfil
    except Exception:
        pass
    local = _carregar_jsonl().get(uid)
    if local:
        perfil = {**_padrao(), **local}
        perfil["fuso"] = normalizar_fuso(perfil.get("fuso") or "")
        return perfil
    return _padrao()


def salvar(uid: str, dados: dict) -> bool:
    """Salva o perfil: nuvem first; em fallback grava/atualiza o JSONL local."""
    if not uid:
        return False
    perfil = {
        "nome": (dados.get("nome") or "").strip()[:120],
        "empresa": (dados.get("empresa") or "").strip()[:120],
        "fuso": normalizar_fuso(dados.get("fuso") or ""),
        "avatar": (dados.get("avatar") or "").strip(),
    }
    try:
        if nuvem_supabase.gravar_perfil_banco(uid, perfil):
            return True
    except Exception:
        pass
    try:
        local = _carregar_jsonl()
        local[uid] = perfil
        _gravar_jsonl(local)
    except Exception:
        return False
    return True


def nome_exibicao(uid: str, email: str | None = None) -> str:
    """Nome exibido: nome -> empresa -> parte local do e-mail -> e-mail completo."""
    perfil = carregar(uid)
    if perfil.get("nome"):
        return perfil["nome"]
    if perfil.get("empresa"):
        return perfil["empresa"]
    email = (email or "").strip()
    if email:
        return email.split("@")[0].replace(".", " ").title() or email
    return email or "usuario"


def iniciais_para_bolinha(uid: str) -> str:
    """Iniciais usadas na bolinha quando não há foto."""
    return _iniciais(nome_exibicao(uid)) or "?"