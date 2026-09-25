"""Verificador do Pix automático (PagBank) — NUNCA imprime segredos.

Checa, com a configuração do .env/secrets:
  1. se o PagBank está configurado e em qual ambiente (prod/sandbox);
  2. se o TOKEN é aceito pela API (GET /orders);
  3. cria um pedido de teste no sandbox (CPF falso válido) e guarda o
     order_id/copia-e-cola em /tmp para a simulação do pagamento.

Uso:  python verificar_pagbank.py [--criar-pedido]
"""
import sys

import pagbank

_MASCA = "••••••••••••"


def _marcar(valor: str) -> str:
    v = str(valor)
    return _MASCA if v else "(vazio)"


def _ambiente() -> str:
    base = pagbank.base_url()
    return "SANDBOX" if "sandbox" in base else "PRODUÇÃO"


def verificar_credencial() -> bool:
    base = pagbank.base_url()
    resposta = None
    try:
        resposta = pagbank.requests.get(
            f"{base}/orders",
            headers=pagbank._cabecalhos(),
            params={"limit": "1"},
            timeout=20,
        )
    except Exception as ex:
        print(f"  falha de rede: {type(ex).__name__}: {ex}")
        return False
    # auth real = qualquer resposta ≠ 401 ("Invalid credential"); 400/422 =
    # endpoint pediu parâmetro, o que prova que o token foi aceito.
    ok = resposta.status_code != 401
    print(f"  GET {base}/orders -> HTTP {resposta.status_code} "
          f"({'✓ token aceito' if ok else '✗ token inválido/ambiente errado'})")
    return ok


def criar_pedido_teste() -> dict | None:
    print("\n2) Criando pedido de teste no sandbox (Pix, CPF falso)...")
    try:
        cobranca = pagbank.criar_cobranca(
            19.99,
            "verif-teste-" + str(sys.hash_info.width),
            cpf="52998224725",
            nome="Cliente Teste Sandbox",
            email="teste-sandbox@example.com",
        )
    except Exception as ex:
        print(f"  ERRO: {ex}")
        return None
    print(f"  ✓ pedido criado: order_id={cobranca.get('order_id')}")
    print(f"  ✓ copia-e-cola (truncado): {cobranca.get('pix_copia', '')[:24]}…")
    with open("/tmp/verif_pagbank.txt", "w", encoding="utf-8") as f:
        f.write(f"order_id={cobranca.get('order_id')}\npix={cobranca.get('pix_copia')}\n")
    return cobranca


def main() -> int:
    print("== Verificador PagBank (sem expor segredos) ==")
    print(f"1) configurado: {'SIM' if pagbank.configurado() else 'NÃO'} "
          f"| ambiente: {_ambiente()} | webhook: {pagbank.webhook_url() or '(vazio)'}")
    print(f"   token: {_marcar(pagbank.token())[:11]}({len(pagbank.token())} chars)")

    if not pagbank.configurado():
        print("\nPendente: defina PAGBANK_TOKEN no .env/secrets.")
        return 1

    ok = verificar_credencial()
    if not ok:
        print("\nDica: confira PAGBANK_API (sandbox != produção) e se o token é do mesmo ambiente.")
        return 2

    if "--criar-pedido" in sys.argv:
        pedido = criar_pedido_teste()
        if not pedido:
            return 3
        print("\nPróximo passo (no painel sandbox): em 'Transações' simule o pagamento do Pix")
        print("e o webhook /webhook/pagamento confirmará sozinho (consulte /tmp/verif_pagbank.txt).")

    print("\n✓ Verificação concluída.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())