# Solução para o Problema das N-Rainhas usando Backtracking

def solve_n_queens(n):
    """
    Função principal para resolver o problema das N-Rainhas.
    
    Args:
        n (int): O tamanho do tabuleiro (N x N) e o número de rainhas.
    """
    # Lista para armazenar todas as soluções encontradas.
    solutions = []
    
    # Lista para representar o tabuleiro. O índice da lista representa
    # a linha (row) e o valor em cada índice representa a coluna (col).
    # Exemplo: board[0] = 3 significa que a rainha na linha 0 está na coluna 3.
    board = [-1] * n
    
    # Chama a função de backtracking para iniciar a busca.
    backtrack(board, 0, n, solutions)
    
    # Retorna todas as soluções encontradas.
    return solutions

def backtrack(board, row, n, solutions):
    """
    Função recursiva de backtracking para encontrar as soluções.
    
    Args:
        board (list): A representação atual do tabuleiro.
        row (int): A linha atual onde a rainha será posicionada.
        n (int): O tamanho total do tabuleiro.
        solutions (list): A lista para armazenar as soluções completas.
    """
    # Caso base: Se todas as rainhas foram posicionadas,
    # uma solução válida foi encontrada.
    if row == n:
        # Adiciona uma cópia da solução atual para a lista de soluções.
        solutions.append(list(board))
        return
    
    # Tenta posicionar a rainha em cada coluna da linha atual.
    for col in range(n):
        # Verifica se a posição (row, col) é segura.
        if is_safe(board, row, col):
            # Se for segura, posiciona a rainha.
            board[row] = col
            # Chama recursivamente para a próxima linha.
            backtrack(board, row + 1, n, solutions)
            
            # Não é necessário "remover" a rainha explicitamente
            # porque a linha é sobrescrita na próxima iteração do loop.
            # O backtracking ocorre naturalmente quando a recursão retorna.

def is_safe(board, row, col):
    """
    Verifica se a posição (row, col) é segura para colocar uma rainha,
    ou seja, se ela não está sendo atacada por outras rainhas.
    
    Args:
        board (list): O tabuleiro com as rainhas já posicionadas.
        row (int): A linha da nova rainha.
        col (int): A coluna da nova rainha.
        
    Returns:
        bool: True se a posição for segura, False caso contrário.
    """
    # Itera sobre as rainhas já posicionadas (linhas anteriores).
    for prev_row in range(row):
        prev_col = board[prev_row]
        
        # Verifica se há ataque na mesma coluna.
        if prev_col == col:
            return False
        
        # Verifica se há ataque na diagonal principal.
        # A diferença absoluta entre as linhas deve ser igual à diferença
        # absoluta entre as colunas para que estejam na mesma diagonal.
        if abs(prev_row - row) == abs(prev_col - col):
            return False
            
    # Se não houver nenhum ataque, a posição é segura.
    return True

# --- EXECUTAR O ALGORITMO ---

# Define o tamanho do problema.
n = 8

# Resolve o problema das 8 rainhas.
solutions = solve_n_queens(n)

# Imprime o número total de soluções encontradas.
print(f"Número de soluções encontradas para o problema das {n} rainhas: {len(solutions)}\n")

# Imprime as primeiras 5 soluções encontradas para demonstração.
if solutions:
    print("Primeiras 5 soluções (representação de colunas por linha):")
    for i in range(min(5, len(solutions))):
        print(f"Solução {i+1}: {solutions[i]}")

    print("\nExemplo de como visualizar a primeira solução em um tabuleiro:")
    primeira_solucao = solutions[0]
    for row in range(n):
        linha = ["□"] * n
        linha[primeira_solucao[row]] = "■"
        print(" ".join(linha))
