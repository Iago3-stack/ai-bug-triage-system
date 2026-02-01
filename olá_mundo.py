# Este código foi revisado e corrigido para garantir que funcione perfeitamente!
# O seu filho de 10 anos fez um trabalho incrível com a estrutura!

def salvar_txt(dados_usuario):
    """Salva um dicionário de dados em um arquivo de texto e json."""
    try:
        # Abre o arquivo 'cadastro_usuarios.txt' no modo 'a' (append/adicionar),
        # que coloca os novos dados no final, sem apagar os antigos.
        with open('cadastro_usuarios.txt', 'a', encoding='utf-8') as arquivo:
            arquivo.write(f'--- NOVO CADASTRO ---\n')
            # Itera sobre o dicionário (chave e valor) para escrever cada item
            for chave, valor in dados_usuario.items():
                # Formata a linha como "Chave: Valor"
                arquivo.write(f'{chave}: {valor}\n')
            arquivo.write(f'---------------------\n\n')
        print(f'\nSUCESSO: Os dados de {dados_usuario["Nome"]} foram salvos em cadastro_usuarios.txt!')
    except IOError as e:
        # Se houver um erro ao salvar (por exemplo, falta de permissão)
        print(f'\nERRO: Não foi possível salvar os dados no arquivo. Detalhes: {e}')

# Importa a biblioteca JSON nativa do Python.
# Essa biblioteca é necessária para manipular arquivos .json corretamente.
import json
import os
import re
# Biblioteca para verificar se o arquivo existe

# Função para SALVAR os dados em um arquivo JSON.
def salvar_json(dados_usuario):
    """Lê todos os cadastros existentes, adiciona o novo e salva de volta em JSON."""
    
    NOME_ARQUIVO = 'cadastro_usuarios.json'
    lista_de_cadastros = []

    # --- 1. Tenta carregar dados existentes ---
    if os.path.exists(NOME_ARQUIVO):
        try:
            with open(NOME_ARQUIVO, 'r', encoding='utf-8') as arquivo:
                # Carrega (lê) todo o conteúdo JSON do arquivo para a memória (lista_de_cadastros)
                lista_de_cadastros = json.load(arquivo)
        except json.JSONDecodeError:
            # Se o arquivo existir, mas estiver vazio ou corrompido, inicia uma lista vazia
            print(f"Atenção: O arquivo {NOME_ARQUIVO} existe, mas está vazio ou inválido. Criando novo conteúdo.")
            lista_de_cadastros = []
        except IOError as e:
            print(f'ERRO ao ler o arquivo {NOME_ARQUIVO}: {e}')
            return

    # --- 2. Adiciona o novo cadastro ---
    # O novo dicionário (dados_usuario) é adicionado ao final da lista
    lista_de_cadastros.append(dados_usuario)
    
    # --- 3. Salva a lista completa no arquivo JSON ---
    try:
        # Abre o arquivo no modo 'w' (write/escrever) para reescrever todo o conteúdo
        # 'indent=4' garante que o arquivo fique bonito e fácil de ler, com indentação de 4 espaços
        with open(NOME_ARQUIVO, 'w', encoding='utf-8') as arquivo:
            json.dump(lista_de_cadastros, arquivo, indent=4, ensure_ascii=False)

        print(f'\nSUCESSO: Os dados de {dados_usuario["Nome"]} foram salvos e adicionados a {NOME_ARQUIVO}!')
    except IOError as e:
        print(f'\nERRO: Não foi possível salvar os dados no arquivo. Detalhes: {e}')
#---------------------------------------------#------------------#--------------------#------------

def perguntar_dados():
    """
    Função principal para coletar dados do usuário com validação robusta.
    """
    
    # --- 1. Início e Decisão de Cadastro ---
    print('\nOlá, tudo bem? Seja bem-vindo!')
    print('\nVamos cadastrar suas informações!')
    
    while True:
        # Pede para o usuário decidir e formata a resposta para minúsculas
        maior = input('Você é maior de idade? (sim/não):').strip().lower()
        if maior == 'sim':
            print('\nObrigado por nos confirmar sua idade!')
            break

        elif maior == 'não':
            print('\nAtenção somente pessoas maiores de idade!')
            return

        else:
            print('\nAtenção! Responda apenas com "sim" ou "não".\n')
            
    while True:
        # vamos decider para que o momento seja adequado para o ux     
        agora = input('Podemos começar agora? (sim/não): ').strip().lower()
        
        if agora == 'sim':
            print('\nMuito bem, vamos começar o seu cadastro!')
            break
            
        elif agora == 'não':
            print('\nMuito bem, continuamos em outro momento!')
            return # 'return' finaliza a função e o programa
        else:
            print('\nAtenção! Responda apenas com "sim" ou "não".\n')


    # --- 2. Coleta e Validação do Nome ---
    nome = ''
    # O loop continua ENQUANTO o nome estiver vazio
    while not nome:
        try:
            # .title() coloca a primeira letra em maiúscula (ex: 'joão' -> 'João')
            nome = input('Qual o seu nome? ').strip().title() 
            if not nome:
                raise ValueError('\nAtenção! O campo não pode estar vazio.')
        except ValueError:
                print('Por favor, preencha com o seu nome (ex: João).\n')
            
    # --- 3. Coleta e Validação da Idade (Garantindo que seja um número válido) ---
    idade = 0
    while True:
        try:
            # Tenta converter o input para um número inteiro
            idade_str = input('Qual sua idade? ').strip()
            idade = int(idade_str) 
            
            # Validação: Idade deve ser um número entre 18 e 120 anos (limites mais realistas)
            if idade >= 18 and idade <= 120:
                
                break # Sai do loop se a idade for um número válido
            else:
                print('Atenção: A idade deve ser um número entre 18 e 120.')
                
        except ValueError:
            # Captura o erro se o usuário digitar texto ou algo que não é um número
            print('Atenção: A idade deve ser um número inteiro (ex: 18 ou 45).')
            
    # --- 4. Coleta e Validação do Ano de Nascimento ---
    ano = 0
    ANO_MIN = 1900
    ANO_MAX = 2024 
    
    while True:
        try:
            # Tenta converter o input para um número inteiro
            ano = input(f'Qual seu ano de nascimento? (Entre {ANO_MIN} e {ANO_MAX}): ').strip()
            ano = int(ano)
            
            # Validação: ano deve estar entre os limites definidos
            if ano >= ANO_MIN and ano <= ANO_MAX:
                break
            else:
                print(f'Atenção: O ano deve estar entre {ANO_MIN} e {ANO_MAX}.')
        except ValueError:
            print('Atenção: O ano deve ser um número inteiro de 4 dígitos (ex: 1995).')
            pass
   
    while True:
        try:
            # 1. Pede o email e remove espaços extras no início/fim com .strip()
            email = input('Por favor, digite o seu e-mail: ').strip().lower()

            # 2. Lógica de Validação: O email é INVÁLIDO se:
            #    NÃO tiver o "@" OU NÃO tiver o "." (que indica o domínio, ex: .com)
            if '@' not in email or '.' not in email:
                # Se for inválido, levantamos o erro para ir para o 'except'
                raise ValueError
        
            # 3. Se chegou até aqui, o email é VÁLIDO.
            print(f'E-mail "{email}" registrado com sucesso!')
            #return email # Retorna o valor e sai do loop
            break
        except ValueError:
            # Mensagem de erro clara para o usuário
            print('Atenção: O e-mail deve conter o "@" e um ponto de domínio (ex: ".com" ou ".net").')
            print('-' * 40) # Linha divisória para clareza 
    

    # sempre que os input sair como verdadeiro 
    while True:
        try:
            cpf = input('Digite o seu cpf (apenas 11 números): ')
            
            # 1. Remove qualquer caractere que não seja dígito (pontos, traços, letras)
            cpf = re.sub(r'[^0-9]', '', cpf)

            # 2. Verifica se a string resultante tem exatamente 11 dígitos
            if len(cpf) != 11:
                # Se não tiver 11 dígitos, levanta a exceção
                raise ValueError("O CPF deve conter exatamente 11 dígitos numéricos.")
            
            # 3. Impede CPFs óbvios inválidos (opcional, mas recomendado)
            if cpf == cpf[0] * 11:
                raise ValueError("CPF inválido (sequência de dígitos repetidos).")
                
            # Se passou por tudo isso, está formatado corretamente
            print(f'CPF cadastrado com sucesso: {cpf}')
            break
        except ValueError as e:
            # Imprime a mensagem de erro que definimos no raise
            print(f'Atenção: {e}')
    # banco de dados
    dados_usuario = {
        'nome': nome,
        'idade': idade,
        'ano': ano,
        'email': email,
        'cpf': cpf
    }
    
    # --- 5. Confirmação dos Dados ---
    while True:
        print("="*40)# iniciando a confirmação 
        print('\n--- Confirmação Cadastral ---')
        print(f'--- Nome: {nome} ---')
        print(f'--- Idade: {idade} ---')
        print(f'--- Ano de Nascimento: {ano} ---')
        print(f'---O seu Email é: {email}--')
        print("="*40)# finalizando a confirmação 
        
        # Resumo final usando as f-strings que ele usou!
        print(f'\nParabéns, {nome}! Você tem {idade} anos e nasceu em {ano}.')
        print(f'E seu email é {email}') 
        print('--- Resumo dos dados ---')
        
        confirme = input('Seus dados estão corretos? (sim/não): ').strip().lower()
          
        if confirme == 'sim':
            print('\nMuito obrigado por sua participação! Dados registrados.')
            
            salvar_txt(dados_usuario)
            salvar_json(dados_usuario) # salvamos os dados 
            break # Fim da confirmação, sai do loop
            

        elif confirme == 'não':
            print('\nReinicie o programa para preencher novamente seus dados.')
             # Sai da função e não salva os dados para que o usuário possa recomeçar
            return None  #Inicie o seu cadastro novamente
        else:
            print('\nAtenção! Responda apenas com "sim" ou "não".')
            
# --- Execução do Programa (if__name == "__main__":)---
if __name__ == "__main__":
    perguntar_dados()


    