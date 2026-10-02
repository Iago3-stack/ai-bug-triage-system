#!/usr/bin/env python3
"""Ground truth dos 30 relatos de teste de triagem (fonte única da verdade).

Vem da legenda do corpus de 30 relatos de teste do Dashboard de QA (documento
local do dono, fora do repo): a severidade esperada de cada relato. "ALTA" da legenda foi mapeado para CRÍTICA, porque o
app tem 3 níveis (CRÍTICA / MÉDIA / NORMAL) e a IA 4 (CRÍTICA/ALTA/MÉDIA/BAIXA,
com ALTA e CRÍTICA se equivalentes e BAIXA ≈ NORMAL).

Casos ambíguos ("MÉDIA ou ALTA") aceitam qualquer um dos rótulos listados — por
isso existem duas métricas: tolerante (30 casos) e estrita (23 sem ambiguidade).

Fica num módulo próprio (e não dentro de um harness) porque é a referência de
qualquer motor novo: `avaliar_lexico.py` (o léxico de produção) e
`avaliar_embeddings.py` (brazembed x classificadores simples, guardado como evidência
do experimento descartado) medem exatamente estes casos, com estas definições.

⚠️ Estes 30 casos são sintéticos (texto de QA, não relato de cliente) — servem
para filtrar candidatos, não para aprovar um motor. O histórico dessa decisão
está na memória local do dono (fora do repo).
"""

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

N_CASOS = len(CASOS)
# Só estes contam para a métrica estrita: rótulo único, sem ambiguidade.
CASOS_ESTRITOS = [(t, e) for t, e in CASOS if len(e) == 1]
N_ESTRITOS = len(CASOS_ESTRITOS)


def conferir(caso: tuple[str, set[str]]) -> None:
    """Valida o ground truth: 3 níveis conônicos e casos não vazios."""
    texto, esperados = caso
    assert texto and texto.strip(), "caso sem texto"
    assert esperados, f"caso sem rótulo: {texto[:40]}"
    fora = esperados - {"CRÍTICA", "MÉDIA", "NORMAL"}
    assert not fora, f"rótulo fora dos 3 canônicos: {fora} ({texto[:40]})"


for _caso in CASOS:
    conferir(_caso)
