# 08 — Servidor MCP

O **AI Bug Triage System** expõe o próprio motor para agentes via **Model
Context Protocol (MCP)**: uma ponte local (`servidor_mcp.py`) que dá ao seu
agente as mesmas três capacidades do app — **triar severidade**, **ler evidência
de Playwright/Postman** e **gerar Gherkin**.

## Por que existe

O app já é um motor de triagem offline e determinístico. O MCP é a forma de um
agente (**Claude Desktop**, **Cursor**, **OpenCode**, etc.) chamar esse motor
diretamente, sem copiar o léxico para o prompt nem reimplementar o parser.

**Fonte única:** `servidor_mcp.py` importa `triagem.triar` e
`adaptadores.estruturar` — não duplica nada. Isso significa que a ponte **e o
app nunca divergem**: se o motor muda, a ponte muda junto.

## Garantias

- **Read-only** — nenhuma ferramenta escreve em disco, banco ou rede.
- **Offline** — nenhuma ferramenta toca a internet; o léxico é stdlib puro.
- **Sem segredo** — não pede chave de API nem lê `.env`. Não há nada para vazar.

## Instalação

O SDK `mcp` fica **fora** de `requirements.txt`/`requirements-dev.txt` de
propósito (traz pydantic/starlette/uvicorn/httpx e não é dependência do app).
Instale só quem for rodar o servidor:

```bash
pip install -r requirements-mcp.txt     # mcp==1.29.0
python servidor_mcp.py                  # sobe o servidor em stdio
```

O transporte é **stdio**: o cliente (o agente) inicia este processo e conversa
por stdin/stdout. Você não abre porta nem configura rede.

## Ferramentas

### `triar_bug(descricao)`

Classifica a severidade pelo léxico PT local. Entrada: o relato em texto livre.

```json
{
  "score": -3.0,
  "gravidade": "CRÍTICA 🚨",
  "sentimento": "Frustrado/Urgente",
  "fatores": ["pagamento", "não consigo (negacao)"],
  "motor": "Léxico PT local (determinístico, offline)"
}
```

### `estruturar_evidencia(evidencia)`

Lê a saída crua de **Playwright** ou **Postman/newman** e devolve JSON com
título, categoria, módulo, severidade prévia, erro e passos de reprodução.
Formatos não reconhecidos devolvem `{"tipo": "desconhecida"}`.

### `gerar_gherkin(relato, gravidade="")`

Gera um esqueleto Gherkin determinístico (`Dado/Quando/Então`). Se a gravidade
vier vazia, a própria ferramenta tria o relato antes. Se o relato for saída de
Playwright/Postman, o título do cenário usa o nome do teste/requisição.

```json
{
  "gherkin": "Funcionalidade: login falhou\n  Cenário: reproduzir a falha\n    Dado que o usuário executa o fluxo relatado\n    Quando o problema descrito ocorre\n    Então a falha é tratada com severidade CRÍTICA 🚨",
  "gravidade": "CRÍTICA 🚨"
}
```

## Registrar no cliente

Troque `/caminho/para/ai-bug-triage-system` pelo caminho real do seu clone. Use
o **interpretador do venv** (`.venv/bin/python`) ou qualquer `python3` que tenha
rodado o `pip install -r requirements-mcp.txt`.

**Claude Desktop** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "ai-bug-triage": {
      "command": "python",
      "args": ["/caminho/para/ai-bug-triage-system/servidor_mcp.py"]
    }
  }
}
```

**Cursor** (`.cursor/mcp.json` ou `~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "ai-bug-triage": {
      "command": "python",
      "args": ["/caminho/para/ai-bug-triage-system/servidor_mcp.py"]
    }
  }
}
```

**OpenCode** (`opencode.json`):

```json
{
  "mcp": {
    "ai-bug-triage": {
      "type": "local",
      "command": ["python", "/caminho/para/ai-bug-triage-system/servidor_mcp.py"],
      "enabled": true
    }
  }
}
```

> Como todo cliente MCP, a nova ferramenta só aparece **depois de reiniciar** o
> agente — a lista de tools é lida na subida do processo.

## Verificar sem agente

Para provar que o servidor sobe e que as tools chegam ao cliente, um script
mínimo de handshake (usa o SDK `mcp`):

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    p = StdioServerParameters(command=".venv/bin/python", args=["servidor_mcp.py"])
    async with stdio_client(p) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print([t.name for t in (await session.list_tools()).tools])
            r = await session.call_tool("triar_bug", {"descricao": "travou ao pagar"})
            print(r.content[0].text)

asyncio.run(main())
```

Saída esperada: `['triar_bug', 'estruturar_evidencia', 'gerar_gherkin']` e o JSON
da triagem. `tools/list` responde na subida, mas a ferramenta só entra na sessão
do agente após o reinício dele.

## Manutenção

- O SDK `mcp` é pinado em `requirements-mcp.txt` (não em `requirements*.txt`).
- Os testes (`test_servidor_mcp.py`) cobrem **só a lógica pura**
  (`nome_funcionalidade`, `montar_gherkin`) e **não** importam o SDK — assim
  rodam no CI, que não instala o `mcp`. As três ferramentas são wrappers finos
  sobre `triagem`/`adaptadores`, já cobertos pelos testes deles.
- O handshake real é verificado à parte (seção acima), no mesmo espírito do
  check de browser de `scripts/checar_scroll_legal.py`: o que depende de ambiente
  externo não entra no `pytest`.
