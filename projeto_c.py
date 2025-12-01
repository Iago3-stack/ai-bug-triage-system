def cadastro_completo(): 
    """
    o programa conciste em cadastro de ususario coletando informações;
    sobre seu nome, idade, ano de nascimento sobre seu trabalho quanto ganha;
    sua , modalidade de trabalho etc.
    """
    while True:
        try:
            
            # vamos dar saudações ao (UX)
            print('**SEJA BEM VINDO AO SISTEMA DO (UX) V1.0**')
            print('\n---tudo bem com você !--- ')
            print('Precisamos Preencher suas Informções!')
            
            # VAMOS COMEÇAR COLETANDO INFORMAÇÕES PESSOAIS
            nome = input('Qual o seu nome ?')
            if not nome:
                raise ValueError('escreva um nome ex:(céu)')
            # o raise mostra o valor do erro e para! para que o (UX) corrija

            idade = int(input('Qual sua idade ?'))
            if idade <= 0:
                raise ValueError('O valor dever ser numero inteiro ex:(123!)')
            # o raise para! para que o (UX) coloque apenas numeros inteiros

            ano = int(input('Qual ano você nasceu ?'))
            if ano <= 0:
                raise ValueError('O valor dever ser um numero inteiro ex:(123!)')
            # vamos confirmar os inputs do (UX) estão corretos----
            # vamos exibir as informções do usuario seu inputs()
            print(f'\n *** Revisão de Dados ***')
            print(f'nome: {nome}')
            print(f'idade: {idade} anos')
            print(f'ano de nascimento: {ano}')
            print('------------------------\n')
            
            # confirmamos as informações e perguntamos ao usuario
            ux = input('Suas informacões estão corretas ? sim/não !').lower().strip() # metodos 
            if ux == 'sim':
                print('Cadastro Realizado com Sucesso')
                print('Obrigado por sua participação')
                break    
            # caso contrario o usuario precisa refazer o cadastro
            elif ux == 'não':
                print('Por favor cadastre-se novamente')
            
        except ValueError:
            print('\n *** ERROR por favor tente novamente !')
if __name__ == "__main__":
    cadastro_completo() 
# Importa a biblioteca 'time' para controlar o tempo de exibição (UX)
import time

def salario_mensal():
    """
    Função principal que coleta as horas e o ganho por hora,
    calcula o salário total e trata erros de digitação (ValueError).
    Utiliza um loop 'while True' para garantir a coleta correta dos dados.
    """
    
    # 1. Mensagens Iniciais (UX)
    print("\n ***SEGUNDO MÓDULO DO (UX) V1.0***")
    print(" Olá, tudo bem ! ")
    print("\n---------------")

    time.sleep(1) # Pausa de 1 segundo para efeito visual

    # --- COLETA SEGURA DE HORAS POR HORA (float) ---
    while True:
        try:
            # qual modelo de trabalho do usúario ? 
            print('\n **Escolha sua Modalidade**')
            print('OPÇÃO 1: PJ')
            print('OPÇÃO 2: CLT')
            print('OPÇÃO 3: AUTÔNOMO')
            print('\n-----------------')
            mod = input('Qual sua Modalidade Trabalhista ?').strip()
            if not mod:
                raise ValueError('Por favor Digite no campo indicado!')
            print(f'Entendido você trabalha como {mod}')
            #  mod2 = input('Qual o nome da empresa ?')

            # Tenta converter o input para float. Se falhar, vai para o 'except'.
            horas_valor = float(input('Quanto você ganha por hora? R$ '))
            break # Se a conversão for bem-sucedida, sai do loop 'while True'
        except ValueError:
            print('\n⚠️ ERRO: Por favor, digite o valor usando apenas números (ex: 25.50)')

    # --- COLETA SEGURA DE HORAS POR MÊS (int) ---
    while True:
        try:
            # Tenta converter o input para inteiro. Se falhar, vai para o 'except'.
            horas_mes_valor = int(input('Quantas horas você trabalha por mês? '))
            break # Se a conversão for bem-sucedida, sai do loop 'while True'
        except ValueError:
            print('\n⚠️ ERRO: Por favor, digite o total de horas apenas números inteiros (ex: 220)')

    # 2. ALGORITMO: Cálculo
    ganho_total = horas_valor * horas_mes_valor 

    # 3. Exibição dos Resultados (UX com formato de moeda  R$:.2f)
    print("\n--- Resumo de Ganhos ---")
    print(f'Você ganha R$ {horas_valor:.2f} por hora e trabalha {horas_mes_valor} horas por mês.')
    print(f'O valor do seu salário total na UNDB é de R$ {ganho_total:.2f} no mês.')
    print("-------------------------\n")

# Executa a função
if __name__ == "__main__":
    salario_mensal()
 
               
            
            
            
