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

# (texto, {severidades aceitáveis})
CASOS = [
    ("o aplicativo está crashando toda vez que tento fazer login, aparece tela azul e perco tudo na sessão", {"CRÍTICA"}),
    ("perdi todos os meus dados depois do vazamento de segurança, não consigo acessar minha conta", {"CRÍTICA"}),
    ("não consigo pagar a assinatura, o pagamento falha na hora de confirmar e ainda fica cobrando duas vezes", {"CRÍTICA"}),
    ("estou muito frustrado, o botão salvar não responde e perco o que escrevo toda vez", {"MÉDIA", "CRÍTICA"}),
    ("o site ficou extremamente lento depois da última atualização, tudo demora demais para carregar", {"MÉDIA"}),
    ("não consigo entrar na minha conta, o login não funciona e diz que minhas credenciais estão erradas", {"MÉDIA", "CRÍTICA"}),
    ("encontrei um erro de digitação no rodapé da página inicial", {"NORMAL"}),
    ("a funcionalidade está funcionando perfeitamente hoje, tudo ótimo", {"NORMAL"}),
    ("o aplicativo congela ao abrir o relatório financeiro, trava todo o sistema", {"CRÍTICA"}),
    ("deu erro 500 na hora de salvar o formulário de cadastro, perdi tudo que digitei", {"CRÍTICA"}),
    ("o carrinho de compras não atualiza quando adiciono um produto, o valor fica errado", {"MÉDIA"}),
    ("estou desesperado, não consigo acessar meu extrato bancário pelo app há três dias", {"CRÍTICA"}),
    ("o aplicativo não instala no meu celular, dá erro de instalação toda vez", {"MÉDIA"}),
    ("a busca não retorna resultado nenhum, mesmo digitando o nome certo do cliente", {"MÉDIA", "CRÍTICA"}),
    ("a notificação push não chega no celular depois que atualizo o cadastro", {"MÉDIA"}),
    ("o envio do relatório trava no meio e diz que a conexão caiu", {"CRÍTICA"}),
    ("a tabela de pedidos aparece duplicada quando filtro por data de hoje", {"MÉDIA"}),
    ("o chat de suporte não abre, fica na tela de carregamento para sempre", {"MÉDIA", "CRÍTICA"}),
    ("o aplicativo fecha sozinho quando tento anexar uma imagem de erro", {"CRÍTICA"}),
    ("a senha de recuperação nunca chega no e-mail e não consigo redefinir", {"MÉDIA", "CRÍTICA"}),
    ("o modo escuro não é aplicado quando abro o aplicativo de madrugada", {"NORMAL"}),
    ("a importação de dados ficou mais rápida, funcionou muito bem hoje", {"NORMAL"}),
    ("o relatório PDF vem com a logo cortada e as margens erradas", {"MÉDIA"}),
    ("a sincronização entre celular e computador não funciona, os dados ficam desatualizados", {"MÉDIA", "CRÍTICA"}),
    ("o gráfico de vendas não mostra o mês de junho, pula de maio para julho", {"MÉDIA"}),
    ("o botão de enviar não responde quando tento finalizar o pedido, trava tudo", {"CRÍTICA"}),
    ("encontrei um comportamento estranho: o aplicativo reinicia sozinho ao abrir o menu de configurações", {"NORMAL", "MÉDIA"}),
    ("o valor do imposto calculado está errado, cobra a mais em todas as notas", {"CRÍTICA"}),
    ("o aplicativo funciona normal de dia, mas à noite a consulta de clientes demora muito", {"MÉDIA"}),
    ("tentei exportar para PDF e deu erro inesperado, o arquivo saiu com a página em branco", {"CRÍTICA"}),
]


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