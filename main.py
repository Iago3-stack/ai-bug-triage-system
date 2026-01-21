# Mini-Ferramenta de IA para QA
# Objetivo: Classificar a gravidade de um Bug automaticamente

def classificador_ia_de_bugs(descricao_erro):
    # Lista de palavras que indicam um desastre no sistema
    palavras_criticas = ["crash", "erro 500", "fechando", "parou de funcionar", "segurança", "login"]
    
    # Transformando o texto em letras minúsculas para a IA não se confundir
    descricao = descricao_erro.lower()
    
    # A "Lógica de Construção"
    for palavra in palavras_criticas:
        if palavra in descricao:
            return "🚨 ALTA PRIORIDADE: Este bug precisa de um Engenheiro agora!"
    
    return "✅ BAIXA PRIORIDADE: Erro leve ou de interface."

# --- TESTANDO A CONSTRUÇÃO ---
report_do_usuario = "O aplicativo está dando crash toda vez que tento fazer login"
resultado = classificador_ia_de_bugs(report_do_usuario)

print(f"Relatório: {report_do_usuario}")
print(f"Decisão da IA: {resultado}")

# Instalação necessária (no terminal: pip install textblob)
from textblob import TextBlob

def analise_inteligente_qa(descricao_bug):
    # Criamos o objeto de IA
    analise = TextBlob(descricao_bug)
    
    # A polaridade vai de -1 (muito irritado/negativo) a 1 (feliz/positivo)
    # Se for menor que -0.3, o usuário está frustrado com um erro
    sentimento = analise.sentiment.polarity
    
    print(f"Análise de Sentimento (Polaridade): {sentimento}")
    
    if sentimento < -0.2:
        return "🚨 PRIORIDADE MÁXIMA: Usuário frustrado detectado. Possível bug impeditivo!"
    elif "erro" in descricao_bug.lower() or "falha" in descricao_bug.lower():
        return "⚠️ PRIORIDADE MÉDIA: Verificar funcionalidade."
    else:
        return "✅ PRIORIDADE BAIXA: Sugestão ou feedback neutro."

# --- SIMULANDO O MUNDO REAL ---
bugs = [
    "I am very angry, the payment button is not working!", # Muito negativo
    "The background color could be a bit darker.",         # Neutro/Sugestão
    "Found a small typo in the footer."                    # Neutro
]

for bug in bugs:
    print(f"\nRelato: {bug}")
    print(f"Decisão da IA: {analise_inteligente_qa(bug)}")
