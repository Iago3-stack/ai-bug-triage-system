# -----------------------------------------------------------
# GESTÃO DE ESTOQUE AVANÇADA COM DICIONÁRIOS
# -----------------------------------------------------------

# Lista para armazenar VÁRIOS dicionários (os produtos)
estoque_produtos = []

# Um dicionário que representa UM ÚNICO produto
produto_exemplo = {
    "id_produto": 1,
    "nome": "Placa Gráfica RTX 4080",
    "preco": 6500.00,
    "quantidade": 15
}

# -----------------------------------------------------------
# FUNÇÕES DE CADASTRO
# -----------------------------------------------------------

def cadastrar_novo_produto(id_atual):
    """
    Função para coletar dados de um novo produto e criar um Dicionário.
    """
    print("\n--- CADASTRO DE NOVO PRODUTO ---")
    
    # 1. Coleta e validação da entrada (boa UX!)
    try:
        nome = input("Nome do produto: ").strip()
        # Usamos float() e int() protegidos pelo try/except para segurança
        preco = float(input("Preço de venda (ex: 6500.00): "))
        quantidade = int(input("Quantidade em estoque: "))
        
        # 2. Cria o Dicionário com os dados coletados (Chave: Valor)
        novo_produto = {
            "id_produto": id_atual,
            "nome": nome,
            "preco": preco,
            "quantidade": quantidade
        }
        
        # 3. Adiciona o Dicionário (o produto completo) à Lista de Estoque
        estoque_produtos.append(novo_produto)
        print(f"✅ Produto ID {id_atual} ('{nome}') cadastrado com sucesso.")
        return id_atual + 1 # Retorna o próximo ID
        
    except ValueError:
        print("\n❌ ERRO: Por favor, digite números válidos para Preço e Quantidade.")
        return id_atual # Retorna o ID sem incrementá-lo
        
def listar_estoque():
    """Lista todos os produtos (dicionários) no estoque."""
    print("\n========================================================")
    print("                 RELATÓRIO DE ESTOQUE                  ")
    print("========================================================")
    if not estoque_produtos:
        print("Estoque vazio.")
        return

    # Usamos o 'for' para percorrer a lista, onde cada item é um Dicionário
    for produto in estoque_produtos:
        # Acessamos os dados do Dicionário usando a Chave (ex: produto["nome"])
        print(f"ID: {produto['id_produto']} | NOME: {produto['nome']}")
        print(f"   Preço: R$ {produto['preco']:.2f} | Qtd: {produto['quantidade']}")
        print("--------------------------------------------------------")


# -----------------------------------------------------------
# INÍCIO DO PROGRAMA
# -----------------------------------------------------------
if __name__ == "__main__":
    
    proximo_id = 1
    
    # Adicionando um produto de exemplo manualmente (sem input)
    estoque_produtos.append({"id_produto": 0, "nome": "Processador Core i9", "preco": 3000.00, "quantidade": 5})
    
    # Cadastra o primeiro produto usando a função (com input)
    proximo_id = cadastrar_novo_produto(proximo_id)
    
    # Cadastra o segundo produto
    proximo_id = cadastrar_novo_produto(proximo_id)
    
    # Exibe o estoque completo
    listar_estoque()
