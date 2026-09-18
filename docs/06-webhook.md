# 06 — Webhook de CI (Pilar 3 de automação)

O **Pilar 3** fecha o ciclo de automação: além de **colar** a falha na página
(Pilar 1) e de reconhecer a saída de **Playwright/Postman** (Pilar 2), o app agora
**recebe as falhas direto do CI** por um webhook HTTP e devolve o **relato já estruturado**.
O mesmo servidor também **recebe a notificação de pagamento do PagBank** e ativa o
Premium automaticamente (`POST /webhook/pagamento`).

## Como funciona

`webhook.py` é um micro-servidor HTTP (100% stdlib, sem novos requisitos) que escuta:

```http
POST /webhook/falha
Content-Type: application/json
X-Webhook-Token: <WEBHOOK_TOKEN>          # exigido apenas se a env estiver definida

{
  "evidencia": "<saída do Playwright / newman / log bruto>",
  "origem": "github-actions",             # opcional
  "repositorio": "usuario/repo",          # opcional
  "run_id": "123456",                     # opcional
  "commit": "9f8...",                     # opcional
  "ia": true                              # opcional: envia para o LLM
}
```

Resposta `200`:

```json
{
  "status": "ok",
  "tipo": "postman",                    // "playwright" | "postman" | "livre"
  "origem": "github-actions",
  "estrutura": { "titulo": "...", "categoria": "...", "severidade": "..." },
  "relato": "# Titulo\n\n... \n**Passos para reproduzir:**...",
  "analise": null                        // dict do LLM se pedido (ia:true)
}
```

Erros: `400` payload inválido, `401` token incorreto (se `WEBHOOK_TOKEN` setado),
`413` evidência acima de **200 KB**, `404` rota desconhecida. O webhook **nunca cai**:
IA e persistência são opcionais e qualquer exceção vira campo de `aviso_*`.

## Confirmação automática de pagamento (`POST /webhook/pagamento`)

Quando o cliente paga o QR dinâmico do PagBank, o banco notifica a
`PAGBANK_WEBHOOK_URL` cadastrada no pedido. O webhook **não confia no corpo**:
consulta o estado real do pedido na API do PagBank (`/orders/{id}`) e, se `PAID`,
chama `pixbilling.confirmar_cobranca` — operação **idempotente** que vira o plano
em `pago`. Ex.: `https://seu-host/webhook/pagamento`.

## Rodar

```bash
python webhook.py --porta 8080 --host 0.0.0.0
```

Teste local rápido:

```bash
curl -s localhost:8080/health
curl -s localhost:8080/webhook/falha -X POST -H 'Content-Type: application/json' \
  -d '{"evidencia": "POST /login [500 Internal Server Error, 12B, 4ms]"}'
```

Env opcionais:
- `WEBHOOK_TOKEN` — exige o cabeçalho `X-Webhook-Token` (recomendado em produção).
- `WEBHOOK_IA=1` — adiciona a análise de IA ao relato em todo payload.
- `WEBHOOK_PERSISTE=1` — grava a triagem no histórico (JSONL ou Supabase, via `persistencia.py`).

O webhook roda **fora** do Streamlit (VPS/Railway/Render) — o app Streamlit continua
na página Ferramenta; o relato gerado aqui pode ser colado direto nele.

## GitHub Actions

Em `.github/workflows/ci-falhas.yml`: sempre que o workflow **"CI - Testes (pytest)"**
terminar em falha, um passo monta a evidência (workflow/run/commit/jobs que falharam)
e envia `POST` para `WEBHOOK_URL`, autenticando com `WEBHOOK_TOKEN` quando existir.
Configure os secrets:

- `WEBHOOK_URL` — ex.: `https://seu-host/webhook/falha`
- `WEBHOOK_TOKEN` — opcional, usado no cabeçalho `X-Webhook-Token`

Sem `WEBHOOK_URL` a action apenas avisa (notice) e não faz nada.