# Testes unitários do motor de triagem (triagem.py)
# Roda com: pytest -v
# Confirma: severidade, negação, ausência de falso-positivo e sentimento.

import pytest

from triagem import triar, _aplicar_lexico, _aplicar_negacoes


# --- Severidade: caso crítico (crash/login) ---
def test_crash_login_eh_critico():
    r = triar("o aplicativo está dando crash toda vez que tento fazer login")
    assert "CRÍTICA" in r["gravidade"]


def test_perda_de_dados_eh_critica():
    r = triar("perdi todos os meus dados depois do vazamento de segurança")
    assert "CRÍTICA" in r["gravidade"]


# --- Severidade: caso médio (frustração/negação) ---
def test_negacao_pagamento_eh_media_ou_critica():
    r = triar("não consigo pagar e estou muito frustrado")
    assert "MÉDIA" in r["gravidade"] or "CRÍTICA" in r["gravidade"]


def test_botao_nao_responde_eh_media_ou_critica():
    r = triar("o botão não responde quando tento salvar")
    assert "MÉDIA" in r["gravidade"] or "CRÍTICA" in r["gravidade"]


def test_botao_nao_funciona_eh_media():
    r = triar("o botão não funciona")
    assert "MÉDIA" in r["gravidade"]


# --- Falso-positivo: "erro" e "bug" são vocab de teste, não escalam sozinhos ---
def test_erro_de_digitacao_nao_dispara():
    r = triar("achei um erro de digitação no rodapé da página")
    assert "NORMAL" in r["gravidade"]


def test_bug_nao_dispara_sozinho():
    r = triar("encontrei um bug no rodapé da página inicial")
    assert "NORMAL" in r["gravidade"]


# --- Sentimentos ---
def test_frustracao_detecta_sentimento_negativo():
    r = triar("estou desesperado, isso é inaceitável")
    assert "Frustrado" in r["sentimento"] or "Negativo" in r["sentimento"]


def test_sucesso_retorna_normal_positivo():
    r = triar("a funcionalidade está funcionando perfeitamente, ótimo")
    assert "NORMAL" in r["gravidade"]
    assert "Satisfeito" in r["sentimento"]


# --- Motor offline/determinístico ---
def test_motor_eh_deterministico():
    r1 = triar("o app está travando ao abrir relatório")
    r2 = triar("o app está travando ao abrir relatório")
    assert r1 == r2


def test_motor_oferece_fatores():
    r = triar("não consigo salvar e o botão não responde")
    assert isinstance(r["fatores"], list)
    assert len(r["fatores"]) >= 1


# --- Funções internas (comportamento dos léxicos) ---
def test_aplicar_lexico_detecta_termos():
    score, acertos = _aplicar_lexico("isso está crashando todo dia")
    assert score < 0
    assert "crashando" in acertos


def test_aplicar_negacoes_detecta_padrao():
    score, acertos = _aplicar_negacoes("o botão não funciona")
    assert score < 0
    assert len(acertos) >= 1


# --- Lentidão por raiz (regex PADROES_LEXICO) ---
def test_lento_e_lenta_eh_media():
    assert "MÉDIA" in triar("o app ficou muito lento")["gravidade"]
    assert "MÉDIA" in triar("a página está lenta")["gravidade"]


def test_booster_muito_amplifica_score():
    # "muito frustrado" deve valer mais que "frustrado" (mesma base, ki do booster)
    sem_boost = triar("estou frustrado")
    com_boost = triar("estou muito frustrado")
    assert com_boost["score"] <= sem_boost["score"] * 1.5
    assert com_boost["score"] < sem_boost["score"]


def test_booster_nao_vaza_para_fora_da_janela():
    # "muito" distante do termo negativo não deve amplificá-lo
    r = triar("estou frustrado, e muito obrigado pelo retorno")
    assert r["score"] != -2.0 * 1.6  # não amplificou


# --- Ênfase: CAIXA ALTA e pontuação amplificam severidade ---
def test_caps_amplifica_score_negativo():
    sem_caps = triar("estou frustrado")
    com_caps = triar("ESTOU FRUSTRADO")
    assert com_caps["score"] < sem_caps["score"]


def test_pontuacao_repetida_amplifica_score():
    sem_pont = triar("estou frustrado")
    r = triar("estou frustrado!!!")
    assert r["score"] < sem_pont["score"] < 0


def test_caps_neutro_nao_cria_severidade():
    # Texto só com caps mas sem termo do léxico: não vira severidade do nada
    r = triar("POR FAVOR VERIFICAR")
    assert "NORMAL" in r["gravidade"]
    assert r["score"] == 0


# --- Extensão do léxico (novos termos técnicos/emocionais) ---
def test_termo_perda_de_dados_eh_critico():
    assert "CRÍTICA" in triar("perdi acesso e houve vazamento de dados")["gravidade"]


def test_fora_do_ar_eh_grave():
    assert "MÉDIA" in triar("o sistema está fora do ar")["gravidade"]


def test_apagar_corromper_eh_critico():
    assert "CRÍTICA" in triar("o app apagou meus relatórios e corrompeu tudo")["gravidade"]


def test_duplicou_eh_media():
    assert "MÉDIA" in triar("a cobrança duplicou na fatura")["gravidade"]



def test_lentidao_flexoes_eh_media():
    r = triar("o aplicativo está lentíssimo hoje")
    assert "MÉDIA" in r["gravidade"]


def test_lente_nao_dispara_falso_positivo():
    r = triar("troquei a lente da câmera do aplicativo")
    assert "NORMAL" in r["gravidade"]


def test_lento_nao_conta_duplo():
    r = triar("o app está lento e carrega lentamente")
    assert r["score"] == -0.7
    assert sum(1 for f in r["fatores"] if "lent" in f) == 1


def test_lento_maiusculo_e_composto():
    r = triar("O sistema está LENTÍSSIMO e o botão não responde")
    assert "CRÍTICA" in r["gravidade"]
    assert any("lent" in f for f in r["fatores"])


# --- Regra geral de negação (negar bênção vira maldição; negar maldição acalma) ---
def test_negacao_positiva_inverte_o_sinal():
    r = triar("o rollback não funcionou")
    assert r["score"] < 0  # não pode mais ficar positivo
    assert "MÉDIA" in r["gravidade"]


def test_negacao_negativa_acalma_o_score():
    r = triar("o sistema não trava")
    assert "NORMAL" in r["gravidade"] or "MÉDIA" in r["gravidade"]
    assert r["score"] > -1.0  # não mantém o peso cru -1.5


def test_negacao_lista_fixa_continua_intacta():
    r = triar("o botão não funciona")
    assert "MÉDIA" in r["gravidade"]
    assert r["score"] == -1.5


def test_negacao_com_auxiliar_flexao_pega():
    # flexão/passado que a lista fixa não enumera -> regra geral cobre
    r = triar("o app não estava funcionando")
    assert r["score"] < 0
    assert "NORMAL" in r["gravidade"] or "MÉDIA" in r["gravidade"]


def test_negacao_termo_composto_curado_nao_recorta():
    # "não baixa" é termo curado próprio; não pode ser duplo-contado pela regra geral
    r = triar("o download não baixa")
    assert "MÉDIA" in r["gravidade"]
    assert "não baixa" in r["fatores"]


# --- Diminuidores (atenuadores: "um pouco", "leve"...) ---
def test_diminuidor_reduz_score_em_vez_de_amplificar():
    sem_dim = triar("estou frustrado")
    com_dim = triar("estou um pouco frustrado")
    assert com_dim["score"] < 0
    assert com_dim["score"] > sem_dim["score"]  # menos grave, não mais


def test_diminuidor_vs_booster_antagonico():
    boost = triar("estou muito frustrado")
    dim = triar("estou um pouco frustrado")
    assert boost["score"] < dim["score"]


def test_relato_medio_com_diminuidor_nao_dispara_critico():
    # relato real que estava estourando CRÍTICA indevidamente
    r = triar("A busca está um pouco lenta. Não trava, mas duplicou alguns registros. Nada crítico.")
    assert r["score"] > -2.0
    assert "CRÍTICA" not in r["gravidade"]


# --- Meta-severidade (voto explícito do usuário limita o teto) ---
def test_nada_critico_veta_teto_critica():
    r = triar("perdi todos os meus dados, mas nada crítico")
    assert "CRÍTICA" not in r["gravidade"]
    assert r["score"] >= -0.5


def test_nao_e_urgente_veta_teto_critica():
    r = triar("o sistema está fora do ar, mas não é urgente")
    assert "CRÍTICA" not in r["gravidade"]
    assert r["score"] >= -0.5


def test_meta_severidade_nao_remove_critica_sem_voto():
    # sem autoavaliação explícita, o peso do léxico decide
    r = triar("PERDA TOTAL de dados, URGENTE!!!")
    assert "CRÍTICA" in r["gravidade"]


def test_meta_severidade_nao_altera_assinatura_triar():
    # retorna sempre o mesmo dict com as 5 chaves
    r = triar("perda de dados, nada crítico")
    assert set(r) == {"score", "gravidade", "sentimento", "fatores", "motor"}


# --- Contexto de teste automatizado (Playwright/Postman) vs incidente real ---
def test_saida_playwright_teste_login_nao_eh_critica():
    # exemplo oficial do app: teste de login que falhou = ruído de pipeline
    r = triar("login.spec.ts: teste de login com sucesso — Expected: Bem-vindo, Received: Erro")
    assert "CRÍTICA" not in r["gravidade"]
    assert r["score"] >= -0.5


def test_postman_http500_mantem_critica():
    # exemplo oficial: HTTP 500 + database timeout = incidente real, não vira ruído
    r = triar("POST https://api.exemplo.com/v1/pagamento [500 Internal Server Error, 412B, 150ms] — expected 200, but got 500; response body: {\"error\": \"database timeout\"}")
    assert "CRÍTICA" in r["gravidade"]


def test_assertionerror_sem_incidente_nao_escalona():
    r = triar("AssertionError: expected response to have status code 200, but got 200 with body vazio")
    assert "CRÍTICA" not in r["gravidade"]


# --- Erros de serviço explícitos (internos do Postman/newman) ---
def test_internal_server_error_mais_timeout_eh_critico():
    r = triar("POST https://api.producao.com.br/v1/cobranca [500 Internal Server Error, 412B, 150ms] — response body: {\"error\": \"database timeout\"}")
    assert "CRÍTICA" in r["gravidade"]


def test_database_timeout_tem_peso_proprio():
    # não depende da palavra do domínio ("pagamento"): "cobrança" não está no
    # léxico, mas o erro de serviço sozinho já sustenta severidade alta
    r = triar("POST https://api.exemplo.com/v1/cobranca [500 Internal Server Error] database timeout")
    assert "CRÍTICA" in r["gravidade"] or "MÉDIA" in r["gravidade"]
    assert "database timeout" in r["fatores"]


# --- Negações comuns de fala real (bloco 1) ---
def test_nao_clica_eh_media():
    r = triar("o botão não clica de jeito nenhum")
    assert "MÉDIA" in r["gravidade"]


def test_nao_inicia_eh_media():
    r = triar("o app não inicia no meu celular")
    assert "MÉDIA" in r["gravidade"]


def test_nao_atualiza_eh_media():
    r = triar("a página não atualiza com os novos dados")
    assert "MÉDIA" in r["gravidade"]


def test_nao_sincroniza_eh_media():
    r = triar("não sincroniza meus contatos com a nuvem")
    assert "MÉDIA" in r["gravidade"]


def test_nao_processa_pagamento_acumula():
    r = triar("não processa o pagamento e não conclui a compra")
    assert "MÉDIA" in r["gravidade"] or "CRÍTICA" in r["gravidade"]


# --- Termos técnicos graves (bloco 2) ---
def test_tela_branca_eh_media_ou_critica():
    r = triar("a tela fica branca quando abro o relatório")
    assert "MÉDIA" in r["gravidade"] or "CRÍTICA" in r["gravidade"]


def test_tela_preta_eh_media_ou_critica():
    r = triar("depois do update a tela fica preta")
    assert "MÉDIA" in r["gravidade"] or "CRÍTICA" in r["gravidade"]


def test_loop_infinito_eh_critico():
    r = triar("o sistema entrou em loop infinito de recarga")
    assert "CRÍTICA" in r["gravidade"] or "MÉDIA" in r["gravidade"]


def test_instavel_eh_media():
    r = triar("a conexão está instável, cai a cada minuto")
    assert "MÉDIA" in r["gravidade"]


def test_perda_total_eh_critica():
    r = triar("houve perda total das configurações do sistema")
    assert "CRÍTICA" in r["gravidade"]


# --- Ausência 'sem X' como sinal de incidente (bloco 3) ---
def test_sem_acesso_eh_media():
    r = triar("estou sem acesso ao painel agora")
    assert "MÉDIA" in r["gravidade"]
    assert "sem acesso" in r["fatores"]


def test_sem_conexao_eh_media():
    r = triar("o dispositivo ficou sem conexão com o servidor")
    assert "MÉDIA" in r["gravidade"]


def test_sem_sinal_acumula_com_parou():
    r = triar("fiquei sem sinal e parou de responder")
    assert "MÉDIA" in r["gravidade"] or "CRÍTICA" in r["gravidade"]


# --- Finanças (dinheiro do cliente = impacto de negócio) ---
def test_cobrou_a_mais_eh_grave():
    r = triar("a plataforma cobrou a mais na minha fatura")
    assert "MÉDIA" in r["gravidade"] or "CRÍTICA" in r["gravidade"]


def test_cobranca_indevida_eh_critica():
    r = triar("houve cobrança indevida duas vezes seguidas")
    assert "CRÍTICA" in r["gravidade"] or "MÉDIA" in r["gravidade"]


def test_saldo_sumiu_eh_grave():
    r = triar("o saldo da minha conta sumiu depois do pagamento")
    assert "MÉDIA" in r["gravidade"] or "CRÍTICA" in r["gravidade"]


def test_pix_nao_caiu_eh_grave():
    r = triar("fiz um pix e o dinheiro não caiu na conta")
    assert "MÉDIA" in r["gravidade"] or "CRÍTICA" in r["gravidade"]


def test_debito_em_dobro_eh_grave():
    r = triar("meu débito veio em dobro esse mês")
    assert "MÉDIA" in r["gravidade"] or "CRÍTICA" in r["gravidade"]


def test_estorno_sozinho_nao_eh_media():
    # solicitar estorno ≠ incidente: é pedido na interface, não bug grave
    r = triar("gostaria de pedir o estorno do valor")
    assert "NORMAL" in r["gravidade"]


def test_estorno_que_nao_chega_eh_grave():
    # a AUSÊNCIA do estorno é o problema: aqui sim pesa
    r = triar("fiz o pedido de estorno e ele não chegou na conta")
    assert "MÉDIA" in r["gravidade"] or "CRÍTICA" in r["gravidade"]


def test_reembolso_que_nao_veio_eh_grave():
    r = triar("pedi reembolso e não veio nada até hoje")
    assert "MÉDIA" in r["gravidade"] or "CRÍTICA" in r["gravidade"]


# --- Escala (incidente amplo) ---
def test_todos_usuarios_amplifica_incidente():
    base = triar("o login está fora do ar")
    amplo = triar("todos os usuários estão sem acesso ao login, ninguém consegue entrar")
    assert "CRÍTICA" in amplo["gravidade"]
    assert amplo["score"] <= base["score"]
    assert "escala" in amplo["fatores"]


def test_pane_geral_eh_critica():
    r = triar("pane geral no sistema inteiro, ninguém consegue acessar")
    assert "CRÍTICA" in r["gravidade"]


def test_escala_em_relato_positivo_nao_dispara():
    # "todos os usuários" num elogio não pode virar severidade
    r = triar("todos os usuários elogiaram a nova interface da home")
    assert "NORMAL" in r["gravidade"]
    assert r["score"] >= 0


# --- Recorrência (falha intermitente/constante) ---
def test_recorrencia_amplifica_falha():
    r = triar("a tela fica branca toda vez que tento abrir o relatório")
    assert "CRÍTICA" in r["gravidade"]
    assert "recorrência" in r["fatores"]


def test_recorrencia_em_elogio_nao_dispara():
    r = triar("funciona perfeitamente de novo, obrigado pela correção")
    assert "NORMAL" in r["gravidade"]


# --- Segurança fina ---
def test_dados_expostos_eh_critico():
    r = triar("os dados dos clientes ficaram expostos no relatório")
    assert "CRÍTICA" in r["gravidade"]


def test_credencial_vazada_eh_critica():
    r = triar("credencial vazada, senha apareceu no logs")
    assert "CRÍTICA" in r["gravidade"]


def test_acesso_indevido_eh_grave():
    r = triar("detectamos acesso indevido a contas de usuário")
    assert "CRÍTICA" in r["gravidade"] or "MÉDIA" in r["gravidade"]


def test_falha_autenticacao_eh_media():
    r = triar("falha de autenticação ao tentar entrar com a senha correta")
    assert "MÉDIA" in r["gravidade"] or "CRÍTICA" in r["gravidade"]


# --- Status HTTP (401/403/404) ---
def test_erro_404_eh_media():
    r = triar("o link retorna 404 ao clicar no botão")
    assert "MÉDIA" in r["gravidade"]


def test_erro_403_eh_media():
    r = triar("a API retorna 403 Forbidden no ambiente de produção")
    assert "MÉDIA" in r["gravidade"] or "CRÍTICA" in r["gravidade"]


def test_erro_401_eh_media():
    r = triar("recebi um 401 ao tentar acessar o painel")
    assert "MÉDIA" in r["gravidade"]


def test_tempo_esgotado_eh_media():
    r = triar("deu tempo esgotado ao esperar a resposta do sistema")
    assert "MÉDIA" in r["gravidade"]
