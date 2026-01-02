# O uso de classes em Python (Programação Orientada a Objetos - POO)
# é ideal para agrupar funcionalidades e dados de forma lógica.

class ColetorDeDados:
    """
    Esta classe agrupa métodos responsáveis por coletar e validar 
    dados de um usuário (Nome, Idade, Ano de Nascimento).
    """
    def __init__(self):
        """Inicializa os atributos da classe (onde os dados serão armazenados)."""
        self.nome = None
        self.idade = None
        self.ano = None
        self.trabalho = None 
        self.valor = None
        self.horas = None
        self.total = None
        print("🗂️  -Coletor de Dados inicializado...")

    def perguntar_ux(self):
        """
        Método que gerencia a interface de perguntas e a validação das entradas.
        """
        print("\n--- INÍCIO DO CADASTRO ---")
        
        # 1. PERGUNTA DO NOME (String)
        while self.nome is None:
            try:
                # Recebe o input e remove espaços extras no início/fim
                entrada_nome = input('Qual o seu nome? ').strip()
                
                # Validação: Se a string estiver vazia (após o strip), levanta um erro
                if not entrada_nome:
                    raise ValueError('O campo Nome não pode ficar vazio. Por favor, preencha.')
                
                # Se a validação passar, armazena e sai do loop
                self.nome = entrada_nome
            
            except ValueError as e:
                # Imprime a mensagem de erro específica do 'raise'
                print(f'\nATENÇÃO (Nome): {e}')

        # 2. PERGUNTA DA IDADE (Inteiro)
        while self.idade is None:
            try:
                # Recebe o input (string) e TENTA converter para inteiro
                entrada_idade = input('Qual sua idade? ').strip()
                idade = int(entrada_idade)
                
                # Validação: Idade mínima de 18 anos
                if idade < 18:
                    raise ValueError('Idade deve ser maior ou igual a 18 anos.')
                
                # Se a validação passar, armazena e sai do loop
                self.idade = idade
            
            except ValueError as e:
                # Trata tanto o erro da validação (raise) quanto o erro de conversão (int())
                print(f'\nATENÇÃO (Idade): {e}. Certifique-se de que digitou um número inteiro válido.')

        # 3. PERGUNTA DO ANO DE NASCIMENTO (Inteiro)
        while self.ano is None:
            try:
                # Recebe o input (string) e TENTA converter para inteiro
                entrada_ano = input('Qual seu ano de nascimento? ').strip()
                ano = int(entrada_ano)

                # Validação: Ano deve ser 1990 ou posterior (>=)
                if ano < 1900 or ano > 2025: # Adicionando limite mínimo para melhor UX
                    raise ValueError('O ano deve estar entre 1900 e 2025.')
                
                # Se a validação passar, armazena e sai do loop
                self.ano = ano
            
            except ValueError as e:
                # Trata tanto o erro da validação (raise) quanto o erro de conversão (int())
                print(f'\nATENÇÃO (Ano): {e}. Certifique-se de que digitou um número inteiro válido.')
                
        print("\n--- CADASTRO CONCLUÍDO COM SUCESSO ---")
        print(f"Nome: {self.nome}, Idade: {self.idade} anos, Ano de Nasc.: {self.ano}")
        
    # Exemplo de outro método que usa os dados coletados
    def mostrar_resumo(self):
        """Exibe um resumo dos dados coletados."""
        if self.nome and self.idade and self.ano:
            print(f"\nResumo: {self.nome} tem {self.idade} anos e nasceu em {self.ano}.")
        else:
            print("\nOs dados ainda não foram completamente coletados.")

    def segunda_fase(self):
        """
        aqui vou iniciar uma segunda fase dentro dessa classe
        """
        print("\n-- BEM VINDO A SEGUNDA FASE--\n")

        while self.trabalho is None:
            try:
                trabalho = input('Qual empresa você trabalha ?').strip().capitalize()
                if not trabalho:
                    raise ValueError('O campo não pode ser vazio por favor preencha')
                
                self.trabalho = trabalho

            except ValueError as e:
                print(f'Atenção (trabalho): {e}')

        while self.valor is None:
            try:
                valor = input('Quanto você ganha por hora ?').strip().replace(',','.')
                valor = float(valor)
                
                self.valor = valor

            except ValueError as e:
                print(f'Atençao (horas): {e} o valor dever ser um numero inteiro')

        while self.horas is None:
            try:
                horas = input('Quantas horas você trabalha por mês ?').strip()
                horas = int(horas)
                if horas == 0:
                    raise ValueError('Atenção o numero dever ser um valor inteiro')
                
                self.horas = horas
                

            except ValueError as e:
                print(f'Atençao (horas): {e}')
        
        while self.total is None:
            total = self.valor * self.horas
            self.total = total

        print('\n--CADASTRO DA SEGUNDA FASE REALIZADO COM SUCESSO--\n')
        print(f'Você trabalha na {self.trabalho} Ganha {self.valor} por horas e trabalha {self.horas} horas por mes e seu salario e de {total}')        

    def resumo_dois(self):
        """
        Vamos exibir o resumo da segunda fase.
        """
        if self.trabalho and self.valor and self.horas and self.total:
            print(f'Resumo: você trabalha na {self.trabalho} ganha {self.valor} por horas e trabalha {self.horas} horas por mes e seu salario e de {self.total}')
        else:
            print('Por favor verifique se todos os campos estão preenchidos corretamente')
            return None

# Bloco principal de execução
if __name__ == "__main__":
    # 1. Cria uma INSTÂNCIA da classe (um objeto)
    meu_formulario = ColetorDeDados()
    
    # 2. Chama o MÉTODO da instância para começar a coleta
    meu_formulario.perguntar_ux()
    
    # 3. Chama outro método para usar os dados
    meu_formulario.mostrar_resumo()
    
    meu_formulario.segunda_fase()

    meu_formulario.resumo_dois()
