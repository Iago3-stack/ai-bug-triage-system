#!/usr/bin/env python3
"""Seed do histórico persistido para o Dashboard de QA.

Reproduz os 30 textos de ~/Documentos/relatos-teste-dashboard-qa.md (mais 1
duplicado = 32 registros) usando EXATAMENTE o mesmo motor que o app
(triagem.triar) e o mesmo formato de snapshot do home.py, mas com timestamps
sintéticos espalhados em dias recentes (para o Dashboard demonstrar a
distribuição de volume por dia).

Nenhum dos textos contém credenciais/PII. Uso:

    python3 seed_historico.py            # só roda se o arquivo estiver vazio
    python3 seed_historico.py --forcar   # sobrescreve e gera os 32 de novo
"""

import argparse
import pathlib
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

import triagem
import persistencia

RELATOS = [
    "o aplicativo está crashando toda vez que tento fazer login, aparece tela azul e perco tudo na sessão",
    "perdi todos os meus dados depois do vazamento de segurança, não consigo acessar minha conta",
    "não consigo pagar a assinatura, o pagamento falha na hora de confirmar e ainda fica cobrando duas vezes",
    "estou muito frustrado, o botão salvar não responde e perco o que escrevo toda vez",
    "o site ficou extremamente lento depois da última atualização, tudo demora demais para carregar",
    "não consigo entrar na minha conta, o login não funciona e diz que minhas credenciais estão erradas",
    "encontrei um erro de digitação no rodapé da página inicial",
    "a funcionalidade está funcionando perfeitamente hoje, tudo ótimo",
    "o aplicativo congela ao abrir o relatório financeiro, trava todo o sistema",
    "deu erro 500 na hora de salvar o formulário de cadastro, perdi tudo que digitei",
    "o carrinho de compras não atualiza quando adiciono um produto, o valor fica errado",
    "estou desesperado, não consigo acessar meu extrato bancário pelo app há três dias",
    "o aplicativo não instala no meu celular, dá erro de instalação toda vez",
    "a busca não retorna resultado nenhum, mesmo digitando o nome certo do cliente",
    "a notificação push não chega no celular depois que atualizo o cadastro",
    "o envio do relatório trava no meio e diz que a conexão caiu",
    "a tabela de pedidos aparece duplicada quando filtro por data de hoje",
    "o chat de suporte não abre, fica na tela de carregamento para sempre",
    "o aplicativo fecha sozinho quando tento anexar uma imagem de erro",
    "a senha de recuperação nunca chega no e-mail e não consigo redefinir",
    "o modo escuro não é aplicado quando abro o aplicativo de madrugada",
    "a importação de dados ficou mais rápida, funcionou muito bem hoje",
    "o relatório PDF vem com a logo cortada e as margens erradas",
    "a sincronização entre celular e computador não funciona, os dados ficam desatualizados",
    "o gráfico de vendas não mostra o mês de junho, pula de maio para julho",
    "o botão de enviar não responde quando tento finalizar o pedido, trava tudo",
    "encontrei um comportamento estranho: o aplicativo reinicia sozinho ao abrir o menu de configurações",
    "o valor do imposto calculado está errado, cobra a mais em todas as notas",
    "o aplicativo funciona normal de dia, mas à noite a consulta de clientes demora muito",
    "tentei exportar para PDF e deu erro inesperado, o arquivo saiu com a página em branco",
]


def _montar_registro(relato: str, data_hora: str, fuso: str) -> dict:
    r = triagem.triar(relato)
    descricao_limpa = relato.strip().strip('"\'')
    relatorio = f"""### 🛡️ Relatório de Triagem Técnica
**Resumo:** {descricao_limpa[:100]}...
**Prioridade:** {r['gravidade']}
**Análise de Sentimento:** {r['sentimento']} (Score: {r['score']:.2f})
**Motor de análise:** {r['motor']}
**Fatores identificados:** {', '.join(r['fatores']) or 'Nenhum (relato neutro)'}

**Cenário Gherkin:**
- DADO QUE o sistema recebeu um relato de erro
- QUANDO o agente processa a entrada: "{descricao_limpa[:50]}..."
- ENTÃO a prioridade deve ser definida como {r['gravidade']}."""
    return {
        "id": uuid.uuid4().hex[:12],
        "data_hora": data_hora,
        "data": data_hora[:10],
        "resumo": descricao_limpa[:100],
        "descricao": descricao_limpa,
        "motor": r["motor"],
        "gravidade": r["gravidade"],
        "score": round(r["score"], 2),
        "sentimento": r["sentimento"],
        "fatores": r["fatores"],
        "usou_ia": False,
        "erro_ia": None,
        "relatorio_completo": relatorio,
    }


def _grade_data_hora(fuso: ZoneInfo) -> list[str]:
    # Espalha os 32 registros em 4 dias recentes, com horário crescente por dia.
    distribuicao = [
        ("2026-09-03", 4), ("2026-09-04", 8),
        ("2026-09-05", 12), ("2026-09-06", 8),
    ]
    grade, acumulador = [], 0
    for dia, n in distribuicao:
        for i in range(n):
            minutos = 480 + acumulador * 9
            hora = f"{minutos // 60:02d}:{minutos % 60:02d}"
            data_hora = f"{dia}T{hora}:00"
            grade.append(datetime.fromisoformat(data_hora).replace(tzinfo=fuso).isoformat(timespec="seconds"))
            acumulador += 1
    return grade


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed do histórico persistido (Dashboard de QA).")
    parser.add_argument("--forcar", action="store_true", help="sobrescreve o arquivo e gera os 32 de novo")
    args = parser.parse_args()

    fuso = ZoneInfo("America/Sao_Paulo")
    caminho = persistencia._caminho()
    caminho.parent.mkdir(parents=True, exist_ok=True)
    existentes = persistencia.carregar_registros()
    if existentes and not args.forcar:
        print(f"⚠️  {caminho.name} já tem {len(existentes)} registro(s). Use --forcar para sobrescrever.")
        return

    grades = _grade_data_hora(fuso)
    relatos = RELATOS[:]
    i = 0
    while len(relatos) < len(grades):
        relatos.append(RELATOS[i])
        i += 1
    registros = [_montar_registro(rl, dh, fuso) for rl, dh in zip(relatos, grades)]

    if existentes and args.forcar:
        caminho.unlink(missing_ok=True)
    with caminho.open("a", encoding="utf-8") as f:
        for registro in registros:
            f.write(persistencia._linha(registro) + "\n")

    severidades = [r["gravidade"].split(" ")[0] for r in registros]
    total = len(registros)
    print(f"✅ Seed concluído: {total} registros em {caminho.relative_to(pathlib.Path(__file__).resolve().parent)}")
    print(f"   Distribuição: CRÍTICA={severidades.count('CRÍTICA')} | "
          f"MÉDIA={severidades.count('MÉDIA')} | NORMAL={severidades.count('NORMAL')}")


if __name__ == "__main__":
    main()