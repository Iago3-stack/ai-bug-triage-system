"""Pilar 1 de automação — "Colar falha e preencher relato automaticamente".

Transforma a evidência bruta que o usuário cola (stack trace, log de erro,
mensagem solta) em um relato estruturado pronto para revisão e triagem.

100% local e determinístico: não gasta token de LLM e não depende de rede.
Usa o motor de triagem offline (triagem.triar) para a severidade e regex
para extrair título, categoria, módulo, versão e o erro principal.
"""
import re
import unicodedata

from triagem import triar

SEVERIDADE = {1: "NORMAL ✅", 2: "MÉDIA ⚠️", 3: "ALTA 🚨", 4: "CRÍTICA 🚨"}

# Categoria na mesma taxonomia da análise por IA (ia.py): 5 valores, para o
# relato colado viajar igual pelo RAG/histórico.
_CATEGORIAS_RANK = ("seguranca", "performance", "design", "funcionalidade", "outro")
_CATEGORIAS = {
    "seguranca": (
        r"\blogin\b|\bauth\b|\bcredencial\b|\bsenha\b|\btoken\b|api[ _-]?key|"
        r"\b401\b|\b403\b|forbidden|authorization|unauthorized|acesso negado|"
        r"\bpermiss|vazament|pii|dado sens[ií]vel|privacidade"
    ),
    "performance": (
        r"\blent[oae]s?\b|\blentid[aã]o\b|\bdevagar\b|\btrava|timeout|timed out|"
        r"\b502\b|\b503\b|\b504\b|\b429\b|\bdemora|demorando|recarreg|refrescar|"
        r"loop infinito|travando"
    ),
    "design": (
        r"\blayout\b|\btela\b|\bcor\b|\bfonte\b|\bespa[çc]amento\b|\bresponsivo\b|"
        r"\balinhamento\b|\bestilo\b|\bcss\b|dark mode|interface|visual"
    ),
    "funcionalidade": (
        r"crash|travou|parou|quebr|corrompe|n[ãa]o\s+\w+|erro de (?:login|login de)|"
        r"bot[aã]o|clicar|click|n[ãa]o funciona|assertion|\bexception\b|\berror\b|"
        r"\bfalha\b|\bbug\b|n[ãa]o consegue|imposs[ií]vel"
    ),
    "outro": r"",
}

_MODULOS = [
    ("login", r"\b(?:login|logado|logar|logou|auth|entrar|entrou|credential|oauth|session|autentica)"),
    ("pagamento", r"\bpagament|\bpagar\b|\bpagando\b|\bcheckout\b|\bpix\b|\bcart[aã]o\b|\bpayment\b|\bboleto\b"),
    ("upload", r"\bupload\b|\barquivo\b|\banexo\b|\bimagem\b|\bfoto\b"),
    ("notificacao", r"\bnotifica|\be-?mail\b|\bdiscord\b|\bslack\b|\balerta\b|\btelegram\b"),
    ("integracao", r"\bgithub\b|\bjira\b|\bwebhook\b|\bapi\b|\bissue\b|pull request|\bpr\b"),
    ("exportacao", r"\bpdf\b|\bdownload\b|\bbaixar\b|\bexportar\b|\brelator|\bcsv\b|\bexcel\b"),
    ("dashboard", r"\bdashboard\b|\bhist[oó]rico\b|\bgr[áa]fico\b|\bm[ée]trica\b"),
    ("perfil", r"\bperfil\b|\bcadastro\b|\bregistr|\bsign ?up\b|\bprofile\b"),
    ("busca", r"\bbusca\b|\bpesquisar\b|\bsearch\b|\bfiltro\b|\bfiltrar\b"),
    ("interface", r"\bp[aá]gina\b|\btela\b|\baba\b|\bmenu\b|\bformul[aá]rio\b|\bcampo\b"),
]

_LINGUAGENS = [
    ("Python", r"Traceback \(most recent call last\)|File \"[^\"]*\.py\", line \d+"),
    ("JavaScript/TypeScript", r"\bat [^\s]+\.(?:js|ts|jsx|tsx):\d+"),
    ("Java", r"(?m)^\s*(?:com\.|org\.|java\.|javax\.)[\w.]+"),
    ("C#/.NET", r"Microsoft\.|System\..*Exception|\bin C:\\|\.cs:"),
    ("Go", r"goroutine \d+|\.go:\d+"),
    ("Ruby", r"\bin [a-z_]+\.rb:\d+"),
]

_VERSAO_RE = re.compile(r"\bv?(\d+)\.(\d+)(?:\.(\d+))?\b")
_TIMESTAMP_RE = re.compile(r"^\s*\[\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?[Zz]?\]", re.MULTILINE)
_FRAME_PY_RE = re.compile(r'File\s+"([^"]+\.py)",\s*line\s+(\d+)')
_FRAME_JS_RE = re.compile(r"\bat\s+([^\s]+\.(?:js|ts|jsx|tsx)):\d+(?::\d+)?")
_CABECA_EXC_RE = re.compile(
    r"^(?:[A-Za-z][A-Za-z0-9_]*\.)*[A-Za-z][A-Za-z0-9_]*"
    r"(?:Error|Exception|FatalError|AssertionError)"
    r"(?::\s*(?P<detalhe>.+))?$"
)
_SEMPHORA_EXC = r"(?:[A-Za-z0-9_]*Error|Exception|AssertionError|FATAL|panic|SEGFAULT)"

_CRITICO = re.compile(
    r"crash|fatal|segfault|panic|corrompeu|perda de dados|erro 500|\b500\b|"
    r"RecursionError|MemoryError|SystemError|StopIteration|exception out of"
)


def _norm(texto: str) -> str:
    return unicodedata.normalize("NFC", texto.lower())


def _extrair_erro(evidencia: str) -> str | None:
    """Retorna o erro principal (nome + detalhe) achado na evidência, senão None."""
    linhas = _TIMESTAMP_RE.sub("", evidencia).splitlines()
    for linha in linhas:
        t = linha.strip().rstrip("`").strip()
        if not t:
            continue
        m = _CABECA_EXC_RE.match(t)
        if m:
            detalhe = (m.group("detalhe") or "").strip()
            detalhe = re.sub(r"\s*\(v\d+\.\d+.*\)\s*$", "", detalhe)
            return f"{m.group(0).split(':')[0]}: {detalhe[:120]}" if detalhe else m.group(0)
    return None


def _extrair_arquivo_linha(evidencia: str) -> str | None:
    """Primeira/local do erro: o frame mais interno (último) de um traceback Python."""
    frames_py = list(_FRAME_PY_RE.finditer(evidencia))
    if frames_py:
        m = frames_py[-1]
        return f"{m.group(1).split('/')[-1]}:{m.group(2)}"
    frames_js = list(_FRAME_JS_RE.finditer(evidencia))
    if frames_js:
        m = frames_js[-1]
        return f"{m.group(1)}"
    return None


def _detectar_linguagem(evidencia: str):
    for nome, padrao in _LINGUAGENS:
        if re.search(padrao, evidencia, re.IGNORECASE):
            return nome
    return None


def _extrair_versao(evidencia: str) -> str | None:
    texto = _norm(evidencia)
    for m in _VERSAO_RE.finditer(texto):
        if int(m.group(1)) >= 1000:
            continue  # quase-certeza de ano (ex.: 2026.09) — não é versão de app
        v = ".".join(p for p in m.groups() if p)
        return f"v{v}"
    return None


def _detectar_modulo(evidencia: str):
    texto = _norm(evidencia)
    for nome, padrao in _MODULOS:
        if re.search(padrao, texto):
            return nome
    return None


def _detectar_categoria(evidencia: str) -> str:
    texto = _norm(evidencia)
    for cat in _CATEGORIAS_RANK:
        if re.search(_CATEGORIAS[cat], texto):
            return cat
    return "outro"


def _severidade(evidencia: str, erro: str | None) -> str:
    """Severidade = motor local (triagem) com piso técnico para exceções."""
    r = triar(evidencia)
    grau = {"NORMAL ✅": 1, "MÉDIA ⚠️": 2, "ALTA 🚨": 3, "CRÍTICA 🚨": 4}[r["gravidade"]]
    if _CRITICO.search(_norm(evidencia)):
        grau = max(grau, 4)
    elif erro or re.search(_SEMPHORA_EXC, evidencia, re.IGNORECASE):
        grau = max(grau, 2)
    return SEVERIDADE[grau]


def _primeira_linha_util(evidencia: str) -> str:
    for ln in evidencia.splitlines():
        t = re.sub(r"^[\s#*`>\[\]-]+|[\s#*`]+$", "", ln).strip()
        if t and re.search(r"[A-Za-zÀ-ú0-9]", t):
            return t[:160]
    return (evidencia or "").strip()[:160]


def _titulo(evidencia: str, erro: str | None, modulo: str | None) -> str:
    if erro:
        nome = erro.split(":", 1)[0].strip()
        if modulo:
            return f"Erro `{nome}` ao usar {modulo}"
        return f"Erro `{nome}` detectado"
    if modulo:
        return f"Problema ao usar {modulo}: {_primeira_linha_util(evidencia)}"
    return f"Relato de bug: {_primeira_linha_util(evidencia)}"


def _passos_repro(evidencia: str, erro: str | None, modulo: str | None) -> list[str]:
    base = "Reproduzir o cenário descrito pelo usuário"
    if erro:
        base = f"Reproduzir o fluxo que dispara `{erro.split(':', 1)[0]}`"
    elif modulo:
        base = f"Reproduzir o fluxo de {modulo}"
    passos = [base]
    local = _extrair_arquivo_linha(evidencia)
    if local:
        passos.append(f"Observar o erro em `{local}`")
    elif erro:
        passos.append(f"Observar o erro principal: `{erro[:80]}`")
    else:
        passos.append("Observar o comportamento relatado (aparece sempre ou de vez em quando?)")
    passos.append("Conferir em qual versão/ambiente o problema ocorre")
    return passos


def _descrever(evidencia: str, erro: str | None, modulo: str | None, versao: str | None) -> str:
    partes = [f"Falha reportada em {modulo}" if modulo else "Falha reportada"]
    if versao:
        partes.append(f"versão {versao}")
    if erro:
        partes.append(f"erro principal: `{erro}`")
    partes.append(f"primeira informação: \"{_primeira_linha_util(evidencia)}\"")
    return ". ".join(partes) + "."


def estruturar(evidencia: str) -> dict:
    """Analisa a evidência bruta e devolve um relato estruturado (dict).

    Campos: titulo, descricao, categoria, modulo, versao, severidade, erro,
    local, linguagem, passos_repro, sino. Nunca levanta; evidencia vazia
    vira um relato "outro" com o texto limpo.
    """
    texto = (evidencia or "").strip()
    erro = _extrair_erro(texto) if texto else None
    modulo = _detectar_modulo(texto) if texto else None
    versao = _extrair_versao(texto) if texto else None
    linguagem = _detectar_linguagem(texto) if texto else None
    local = _extrair_arquivo_linha(texto) if texto else None
    return {
        "titulo": _titulo(texto, erro, modulo),
        "descricao": _descrever(texto, erro, modulo, versao),
        "categoria": _detectar_categoria(texto),
        "modulo": modulo,
        "versao": versao,
        "severidade": _severidade(texto, erro),
        "erro": erro,
        "local": local,
        "linguagem": linguagem,
        "passos_repro": _passos_repro(texto, erro, modulo),
        "primeira_linha": _primeira_linha_util(texto),
    }


def montar_relato(evidencia: str, estrutura: dict | None = None) -> str:
    """Gera o texto do relato (markdown) que preenche a caixa de triagem."""
    if estrutura is None:
        estrutura = estruturar(evidencia)
    e = estrutura
    linhas = [f"**Título:** {e['titulo']}", "", f"**Descrição:** {e['descricao']}", ""]
    meta = (
        f"**Categoria:** {e['categoria']}"
        + (f" · **Módulo:** {e['modulo']}" if e.get("modulo") else "")
        + (f" · **Versão:** {e['versao']}" if e.get("versao") else "")
        + f" · **Severidade (prévia):** {e['severidade']}"
    )
    linhas.append(meta)
    erro = e.get("erro")
    if erro:
        linhas.append("")
        detalhe = f"`{erro}`" + (f" — em {e['local']}" if e.get("local") else "")
        linhas.append(f"**Erro principal:** {detalhe}")
    ling = e.get("linguagem")
    if ling:
        linhas.append("")
        linhas.append(f"**Linguagem detectada:** {ling}")
    linhas += ["", "", "**Passos para reproduzir:**"]
    linhas += [f"{i}. {p}" for i, p in enumerate(e["passos_repro"], 1)]
    linhas += [
        "",
        "",
        "> Relato estruturado automaticamente pela falha colada — revise antes de triar.",
    ]
    return "\n".join(linhas)


if __name__ == "__main__":
    demo = """Traceback (most recent call last):
  File "/app/secoes/ferramenta.py", line 312, in render
    resultado = triar(descricao_bug)
  File "/app/triagem.py", line 121, in triar
    return _analisar_lexico(texto)
TypeError: 'NoneType' object is not subscriptable (v2.12.0)"""
    estrutura = estruturar(demo)
    for k, v in estrutura.items():
        print(f"{k}: {v}")
    print("\n--- RELATO ---")
    print(montar_relato(demo, estrutura))