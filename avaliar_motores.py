#!/usr/bin/env python3
"""Avalia os motores de triagem contra os 30 relatos de teste ROTULADOS.

Ground truth: severidade esperada da legenda de
~/Documentos/relatos-teste-dashboard-qa.md. "ALTA" da legenda foi mapeado
para CRÍTICA (o app tem 3 níveis: CRÍTICA/MÉDIA/NORMAL); os casos ambíguos
("MÉDIA ou ALTA", "NORMAL ou MÉDIA") aceitam qualquer um dos rótulos.

Compara: léxico (triagem.triar) x semântico (semantico.analisar) x ensemble
(média dos dois scores) e mostra acerto estrito (só casos sem ambiguidade) e
tolerante (aceita o conjunto).

Uso:
    python3 avaliar_motores.py            # resumo
    python3 avaliar_motores.py --detalhe  # + caso a caso
"""

import argparse

import semantico
import triagem
from casos_qa import CASOS


def avaliar(detalhe: bool = False) -> None:
    tem_semantico = semantico.garantir_modelo() and semantico.disponivel()
    if not tem_semantico:
        print("⚠️  Semântico indisponível — rode `python3 semantico.py` "
              "ou garanta o modelo (release/GitHub) para comparar os 3 motores.\n")

    acertos = {"léxico": 0, "semântico": 0, "ensemble": 0}
    estritos = {"léxico": 0, "semântico": 0, "ensemble": 0}
    n_estritos = 0
    divergencias = []

    for i, (texto, esperados) in enumerate(CASOS, start=1):
        lex = triagem.triar(texto)
        # gravidade do app vem com emoji ("CRÍTICA 🚨"); o ground truth não tem.
        prev = {"léxico": lex["gravidade"].split(" ")[0]}
        if tem_semantico:
            # mede exatamente o caminho de produção (semantico.ensemble)
            prev["semântico"] = semantico.analisar(texto)["gravidade"].split(" ")[0]
            prev["ensemble"] = semantico.ensemble(texto, lex)["gravidade"].split(" ")[0]

        estrito = len(esperados) == 1
        if estrito:
            n_estritos += 1
        for motor, p in prev.items():
            if p in esperados:
                acertos[motor] += 1
                if estrito:
                    estritos[motor] += 1

        if len(set(prev.values())) > 1:
            divergencias.append((i, prev, esperados))

        if detalhe:
            alvo = "/".join(sorted(esperados))
            marca = lambda m: "✓" if prev[m] in esperados else "✗"  # noqa: E731
            print(f"{i:>2}. esp={alvo:<18} | " + "  ".join(
                f"{m}={prev[m]}{marca(m)}" for m in prev))

    total = len(CASOS)
    print(f"\n=== {total} casos ({n_estritos} sem ambiguidade) ===")
    print(f"{'motor':<10} acerto tolerante   acerto estrito")
    for m in acertos:
        print(f"{m:<10} {acertos[m]:>2}/{total} ({acertos[m]/total:5.1%})   "
              f"{estritos[m]:>2}/{n_estritos} ({estritos[m]/n_estritos:5.1%})")

    if divergencias:
        print(f"\nDivergências ({len(divergencias)}):")
        for i, prev, esperados in divergencias:
            print(f"  {i:>2}. " + "  ".join(f"{m}={p}" for m, p in prev.items())
                  + f"  (esperado {'/'.join(sorted(esperados))})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--detalhe", action="store_true")
    args = ap.parse_args()
    avaliar(args.detalhe)