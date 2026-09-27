#!/usr/bin/env python3
"""Mede o léxico de produção (triagem.py) contra os 30 relatos ROTULADOS.

Este é o instrumento de trabalho para evoluir o léxico: rode depois de mexer em
`triagem.py` e ele diz o que melhorou, o que regrediu e — no `--detalhe` — o
score e os fatores de cada caso, para ver qual padrão disparou.

Ground truth e métricas vêm de `casos_qa.py` (fonte única da verdade):
  - tolerante: acerto nos 30 casos, aceitando o conjunto de rótulos de cada um
  - estrito:    acerto nos 23 casos sem ambiguidade
  - referência atual: 29/30 (96,7%) tolerante e 22/23 (95,7%) estrito

Uso:
    python3 avaliar_lexico.py                  # resumo + erros
    python3 avaliar_lexico.py --detalhe        # todos os 30, com score e fatores
    python3 avaliar_lexico.py --falhar-abaixo 95  # sai com código 1 se cair abaixo
"""

import argparse
import sys

import triagem
from casos_qa import CASOS, N_CASOS, N_ESTRITOS

ROTULOS = ("CRÍTICA", "MÉDIA", "NORMAL")
# Referência medida no v3.2.0 (commit 528b818) — se cair, algo regrediu.
REFERENCIA = {"tolerante": 29, "estrito": 22}


def avaliar(detalhe: bool = False) -> tuple[int, int]:
    """Roda o léxico nos 30 casos. Devolve (acertos tolerantes, acertos estritos)."""
    linhas = []
    for i, (texto, esperados) in enumerate(CASOS, start=1):
        r = triagem.triar(texto)
        # a gravidade do app vem com emoji ("CRÍTICA 🚨"); o ground truth não tem.
        previsto = r["gravidade"].split(" ")[0]
        linhas.append({
            "i": i, "texto": texto, "esperados": esperados,
            "previsto": previsto, "score": round(r["score"], 2),
            "fatores": r.get("fatores") or [], "acertou": previsto in esperados,
            "estrito": len(esperados) == 1,
        })

    tolerante = sum(1 for l in linhas if l["acertou"])
    estrito = sum(1 for l in linhas if l["acertou"] and l["estrito"])
    erros = [l for l in linhas if not l["acertou"]]

    print(f"\n=== {N_CASOS} casos ({N_ESTRITOS} sem ambiguidade) ===")
    print(f"{'léxico (produção)':<20}{'acerto tolerante':<22}{'acerto estrito'}")
    print(f"{'':<20}{f'{tolerante}/{N_CASOS} ({tolerante/N_CASOS:5.1%})':<22}"
          f"{f'{estrito}/{N_ESTRITOS} ({estrito/N_ESTRITOS:5.1%})'}")

    print("\nConfiabilidade por severidade prevista:")
    for rotulo in ROTULOS:
        do_rotulo = [l for l in linhas if l["previsto"] == rotulo]
        if not do_rotulo:
            continue
        certos = sum(1 for l in do_rotulo if l["acertou"])
        print(f"  {rotulo:<9}{certos:>2}/{len(do_rotulo)} corretos")

    if erros:
        print(f"\n{len(erros)} erro(s) — é aqui que o léxico evolui:")
        for l in erros:
            alvo = "/".join(sorted(l["esperados"]))
            print(f"  {l['i']:>2}. prev={l['previsto']:<8} esp={alvo:<18} "
                  f"score={l['score']:>6}  {l['texto'][:52]}")
            print(f"      fatores: {', '.join(l['fatores']) or 'NENHUM (léxico não disparou)'}")

    if detalhe:
        print("\nTodos os casos:")
        for l in linhas:
            alvo = "/".join(sorted(l["esperados"]))
            marca = "✓" if l["acertou"] else "✗"
            print(f"  {l['i']:>2}. {marca} prev={l['previsto']:<8} esp={alvo:<18} "
                  f"score={l['score']:>6}  {l['texto'][:46]}")

    regressou = (tolerante < REFERENCIA["tolerante"] or estrito < REFERENCIA["estrito"])
    if regressou:
        print(f"\n⚠️  Abaixo da referência v3.2.0 ({REFERENCIA['tolerante']}/{N_CASOS} "
              f"e {REFERENCIA['estrito']}/{N_ESTRITOS}): REGRESSÃO.")
    return tolerante, estrito


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--detalhe", action="store_true", help="lista os 30 casos")
    ap.add_argument("--falhar-abaixo", type=float, metavar="PCT",
                    help="sai com código 1 se o acerto estrito cair abaixo de PCT (ex.: 95)")
    args = ap.parse_args()

    _, estrito = avaliar(args.detalhe)

    if args.falhar_abaixo is not None:
        pct = estrito / N_ESTRITOS * 100
        if pct < args.falhar_abaixo:
            print(f"FALHA: acerto estrito {pct:.1f}% < limite de {args.falhar_abaixo}%")
            return 1
        print(f"OK: acerto estrito {pct:.1f}% >= limite de {args.falhar_abaixo}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
