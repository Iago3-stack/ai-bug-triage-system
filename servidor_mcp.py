"""Servidor MCP (stdio) do AI Bug Triage System.

Expõe o motor real do app — `triagem.triar` (severidade pelo léxico PT local) e
`adaptadores.estruturar` (leitura de saída de Playwright/Postman) — para
qualquer cliente que fale **Model Context Protocol** (Claude Desktop, Cursor,
OpenCode, etc.).

**Fonte única:** esta ponte não duplica léxico nem parser — ela importa o motor
do app, então ponte e app nunca divergem. Todas as ferramentas são **read-only**
e **offline**: nenhuma escreve nada, nenhuma pede chave de API, nenhuma toca a
rede.

Rodar (transporte stdio):

    pip install -r requirements-mcp.txt
    python servidor_mcp.py

O cliente MCP inicia este processo e fala com ele por stdin/stdout. Veja
`docs/08-mcp.md` para exemplos de configuração.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# A raiz do repo entra no sys.path para `triagem`/`adaptadores` resolverem
# mesmo quando o servidor é iniciado de outra pasta — é o que o cliente MCP
# faz (o processo não nasce na raiz do repo).
_RAIZ = Path(__file__).resolve().parent
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

from adaptadores import estruturar as _estruturar
from triagem import triar as _triar

NOME_SERVIDOR = "ai-bug-triage"
INSTRUCOES = (
    "Motor de QA do AI Bug Triage System: triagem de severidade pelo léxico "
    "PT local (offline, determinístico) e leitura de evidências de "
    "Playwright/Postman. Read-only — não escreve nada."
)


def nome_funcionalidade(relato: str, evidencia: dict | None) -> str:
    """Título curto da funcionalidade para o cenário Gherkin.

    Prefere o nome do teste/requisição quando a evidência foi estruturada;
    senão, usa a primeira frase do relato (cortada em 80 caracteres).
    """
    if evidencia:
        for chave in ("teste", "requisicao", "titulo"):
            valor = evidencia.get(chave)
            if valor:
                return str(valor)
    primeira = re.split(r"[.\n]", relato.strip(), maxsplit=1)[0].strip()
    return primeira[:80] or "funcionalidade"


def montar_gherkin(relato: str, gravidade: str = "") -> dict:
    """Esqueleto Gherkin determinístico a partir do relato.

    Heurístico: é um rascunho para o QA editar, não um caso final. Se
    `gravidade` vier vazia, o próprio léxico tria o relato antes. Se o relato
    for saída de Playwright/Postman, o título usa o nome do teste/requisição.

    Returns:
        dict com 'gherkin' (str) e 'gravidade' (str).
    """
    if not gravidade:
        gravidade = _triar(relato)["gravidade"]
    ev = _estruturar(relato)
    funcionalidade = nome_funcionalidade(relato, ev)
    gherkin = (
        f"Funcionalidade: {funcionalidade}\n"
        f"  Cenário: reproduzir a falha\n"
        f"    Dado que o usuário executa o fluxo relatado\n"
        f"    Quando o problema descrito ocorre\n"
        f"    Então a falha é tratada com severidade {gravidade}"
    )
    return {"gherkin": gherkin, "gravidade": gravidade}


def criar_servidor():
    """Cria o servidor MCP com as três ferramentas registradas.

    O SDK `mcp` é importado **aqui dentro**, não no topo do módulo: assim
    `import servidor_mcp` (e os testes) não exige o SDK — que fica fora de
    `requirements.txt`/`requirements-dev.txt` e só entra via
    `requirements-mcp.txt` para quem for rodar o servidor.
    """
    try:
        from mcp.server.fastmcp import FastMCP

        server = FastMCP(name=NOME_SERVIDOR, instructions=INSTRUCOES)
    except ImportError:  # SDK antigo, com a API `MCPServer`
        from mcp.server.mcpserver import MCPServer

        server = MCPServer(
            name=NOME_SERVIDOR,
            version="1.0.0",
            description=INSTRUCOES,
        )

    @server.tool()
    def triar_bug(descricao: str) -> dict:
        """Classifica a severidade de um relato de bug com o léxico local.

        Args:
            descricao: O relato do bug em texto livre, em português.

        Returns:
            dict com score (float), gravidade ('CRÍTICA 🚨' / 'MÉDIA ⚠️' /
            'NORMAL ✅'), sentimento, fatores (lista) e motor.
        """
        return _triar(descricao)

    @server.tool()
    def estruturar_evidencia(evidencia: str) -> dict:
        """Lê saída crua de Playwright ou Postman/newman e devolve JSON.

        Args:
            evidencia: A saída do teste (Playwright) ou da rodada do
                Postman/newman. JSON de Playwright também é aceito.

        Returns:
            dict com tipo, titulo, descricao, categoria, modulo, severidade,
            erro e passos_repro; e, conforme o formato, teste/locator
            (Playwright) ou metodo/url/status_recebido/falhas (Postman).
            Formato não reconhecido devolve {"tipo": "desconhecida"}.
        """
        return _estruturar(evidencia) or {"tipo": "desconhecida"}

    @server.tool()
    def gerar_gherkin(relato: str, gravidade: str = "") -> dict:
        """Gera um esqueleto de caso de teste Gherkin a partir do relato.

        Args:
            relato: A descrição do bug ou a evidência crua.
            gravidade: Severidade já triada (ex.: 'CRÍTICA 🚨'). Se vazia, a
                própria ferramenta tria o relato antes.

        Returns:
            dict com 'gherkin' e 'gravidade'.
        """
        return montar_gherkin(relato, gravidade)

    return server


def main() -> None:
    criar_servidor().run()


if __name__ == "__main__":
    main()
