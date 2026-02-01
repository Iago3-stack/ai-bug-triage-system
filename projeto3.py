def demonstrar_strip():
    # A entrada simulada do usuário. Note os espaços antes e depois.
    entrada_suja = "   usuario_exemplo@email.com   "
    
    print("Entrada Bruta Simulada:", f"'{entrada_suja}'")
    
    # 1. Aplicando .strip() FORA (CORRETO) - ENCADAMENTO
    # Simula: nome = input(...).strip()
    nome_limpo = entrada_suja.strip()
    print("-" * 30)
    print("1. Encadeamento (.strip() fora):")
    print(f"Resultado: '{nome_limpo}'")
    print("Tamanho (antes/depois):", len(entrada_suja), "->", len(nome_limpo))
    
    # 2. Aplicando .strip() DENTRO (INCORRETO/INÚTIL)
    # Simula: nome = input(prompt.strip())
    # Aqui, a string de prompt é 'Qual seu nome? '
    prompt_sujo = "    Qual seu nome?    "
    prompt_limpo = prompt_sujo.strip()
    
    # Observe que o .strip() não tem efeito na entrada do usuário.
    nome_sujo_resultado = entrada_suja 

    print("-" * 30)
    print("2. Aplicação Errada (.strip() no prompt):")
    print(f"Prompt Original:   '{prompt_sujo}'")
    print(f"Prompt Limpo:      '{prompt_limpo}'") # Isso é o que é limpo
    print(f"Resultado Sujo:    '{nome_sujo_resultado}'") # A entrada do usuário continua suja
    print("Tamanho (limpo/sujo):", len(prompt_limpo), "/", len(nome_sujo_resultado))


if __name__ == "__main__":
    demonstrar_strip()
