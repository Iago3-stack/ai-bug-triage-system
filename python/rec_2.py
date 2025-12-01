import re # Biblioteca para trabalhar com expressões regulares (limpeza de texto)

# --- FUNÇÃO 1: Limpeza (Remove caracteres especiais) ---
def limpar_texto(texto_bruto):
    """
    Função A: Limpa o texto, removendo pontuações e caracteres indesejados.
    O resultado desta função será a entrada da próxima.
    """
    print(f"-> Função A (Limpar) Recebe: '{texto_bruto}'")
    # Usa a biblioteca 're' para substituir qualquer coisa que não seja letra ou espaço por nada.
    texto_limpo = re.sub(r'[^\w\s]', '', texto_bruto)
    return texto_limpo.strip()

# --- FUNÇÃO 2: Transformação (Converte para maiúsculas) ---
def transformar_maiusculas(texto_limpo):
    """
    Função B: Converte o texto para maiúsculas.
    A entrada desta função veio da Função A.
    """
    print(f"-> Função B (Maiúsculas) Recebe: '{texto_limpo}'")
    texto_maiusculo = texto_limpo.upper()
    return texto_maiusculo

# --- FUNÇÃO 3: Adicionar Selo (Finaliza o texto) ---
def adicionar_selo(texto_final):
    """
    Função C: Adiciona uma etiqueta de finalização.
    A entrada desta função veio da Função B.
    """
    print(f"-> Função C (Selo) Recebe: '{texto_final}'")
    texto_com_selo = f"[PROCESSADO] - {texto_final} - [FIM]"
    return texto_com_selo

# ----------------------------------------------------
# O ALGORITMO DE COMPOSIÇÃO
# ----------------------------------------------------

# Nosso texto de entrada, com sujeira
entrada_bruta = "   aQui eSta o tExTo!! para: ser proceSSado.  "

# Primeira forma: Passos Sequenciais (Mais fácil de ler)
print("--- MÉTODO 1: PASSOS SEQUENCIAIS ---")
texto_passo_1 = limpar_texto(entrada_bruta)
texto_passo_2 = transformar_maiusculas(texto_passo_1)
texto_passo_3 = adicionar_selo(texto_passo_2)

print(f"\nResultado Final (Sequencial): {texto_passo_3}")

print("\n" + "="*40 + "\n")

# Segunda forma: Composição Encadeada (Mais compacto, mais comum em ML)
# O resultado da função mais interna (limpar_texto) vira o parâmetro da próxima.
print("--- MÉTODO 2: COMPOSIÇÃO ENCADEADA ---")

resultado_encadeado = adicionar_selo(
    transformar_maiusculas(
        limpar_texto(entrada_bruta)
    )
)

print(f"\nResultado Final (Encadeado): {resultado_encadeado}")
