import random

def mutar_cromossomo(cromossomo, taxa_mutacao):
    """
    Simula o processo de mutação em um cromossomo.
    """
    cromossomo_mutado = []
    # Itera sobre cada gene do cromossomo
    for gene in cromossomo:
        # Gera um número aleatório entre 0.0 e 1.0
        if random.random() < taxa_mutacao:
            # Se o número aleatório for menor que a taxa de mutação,
            # o gene é alterado (mutação).
            cromossomo_mutado.append(1 - gene)
        else:
            # Caso contrário, o gene permanece o mesmo.
            cromossomo_mutado.append(gene)
    return cromossomo_mutado

# Exemplo de cromossomo (problema da mochila)
cromossomo_original = [1, 0, 1, 1, 0]

# Taxa de mutação de 100% para garantir a alteração
taxa_mutacao = 1.0

# Aplica a mutação
cromossomo_final = mutar_cromossomo(cromossomo_original, taxa_mutacao)

print(f"Cromossomo Original: {cromossomo_original}")
print(f"Cromossomo Mutado:   {cromossomo_final}")
