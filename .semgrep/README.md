# Guard de tempo-constante (`.semgrep/`)

Regras Semgrep próprias do projeto — o quality gate que roda no CI, não a
configuração da minha máquina. Diferente de `.opencode/`, que fica só no disco
local: aqui o que se versiona é **proteção do repositório**, e proteção que
não está no branch não protege o branch.

## Rodar localmente

```bash
export SEMGREP_SEND_METRICS=off
.venv/bin/semgrep --config .semgrep/ --metrics=off --disable-version-check \
  $(git ls-files '*.py')
```

Sai com 0 hoje. Achado = 1 de verdade.

## As regras

### `python-secret-compared-with-equality`

Compara um segredo/token lido do ambiente por `==`/`!=` em vez de comparação em
tempo constante. CWE-208 (timing attack): o tempo de resposta revela quantos
bytes iniciais do segredo casaram, o que permite recuperar o token byte a byte.

O padrão do projeto está em `webhook.py:48`, que valida o `X-Webhook-Token` com
`hmac.compare_digest()`. Esse é hoje o **único** ponto do repo com comparação em
tempo constante — não existe outro segurando o padrão.

```python
# ERRADO — vaza por timing
if cabecalho == os.environ.get("WEBHOOK_TOKEN"):
    ...

# CERTO — tempo constante
if hmac.compare_digest(cabecalho.strip(), aceito.strip()):
    ...
```

## Como ela é validada

Não confie numa regra que nunca foi testada contra código bom. Em 2026-09-29 ela
foi checada nos dois sentidos:

- **71 arquivos `.py` versionados** → 0 achados (código atual limpo)
- **6 casos isolados** → detecta as 3 variantes vulneráveis, e **não** acusa
  as 3 formas corretas

O caso que mais importa é o falso positivo clássico: `WEBHOOK_REQUIRE_TOKEN` tem
`TOKEN` no nome mas é flag de modo, não segredo. O `metavariable-regex` tem um
lookahead negativo que impede esse alarme. Sem ele, a regra gritaria num código
correto e seria ignorada — que é o jeito mais rápido de uma regra de segurança
morrer.

## Limites conhecidos

1. Só enxerga segredo vindo de `os.environ` / `os.environ[]`. Segredo de
   arquivo, `.env` parseado em dict ou outra forma de acesso **escapa**.
2. Modo taint não atravessa `fstring`/formatação nem reatribuição via container.
3. Ampliar a fonte conforme novos segredos aparecerem (Jira, GitHub, Supabase
   service role).

Um guard de CI é uma rede, não uma prova. CWE-208 aqui é risco baixo, e o valor
dela é pegar a **regressão** — não ser um scanner perfeito.

## Versionamento

O CI roda isto em todo push/PR da `main`. Como o `auto-merge-dependabot.yml`
faz merge automático de PR do Dependabot, um achado aqui **trava o merge** —
que é o comportamento desejado: falha visível, não deploy em silêncio.
