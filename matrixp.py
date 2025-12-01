import random
import time
import sys

# === Configurações da Chuva ===

# Frases e Nomes para misturar com os números.
# O gênio pode customizar esta lista como quiser!
CONTEUDO_GENIAL = [
'0000000000000000++++0000000000000000=  ==========   ++++++++++++++++++++++++++++++++ !-----------------!',
'0000000000000000++++0000000000000000=  ==========      +++++++++++++++++++++++         !-------------!',
'0000000000000000++++0000000000000000=  ==========           ++++++++++++++++             !----------!',
'0000000000000000++++0000000000000000=  ==========               ++++++++                   !-------!',
'iniciando o programa! rastreando o sistema de arquivos!'
'1... 2... 3... 4... 5... 6... 7... 8... 9... 10... 11... 12... 13... 14... 15...'
'Atenção seus sitema estar sendo acessado remotamente!'
'==9(copiando arquivos para o destino final HTTPS://www.google.com.br/LOCAL:)',
'👽 olá amigo estou invandindo seu sistema...', '🌏servidor iniciado atraves da porta local 8888:0',
'transferencia iniciada... ',
'movendo informações para um banco de dados...'
'transferencia concluida com sucesso...'
'modificando as chaves do sistema...'
'chave criptografada com sucesso...'

]

# Atraso em segundos. Este é o controle de velocidade!
# 0.15 é um bom ponto de partida, mais lento que o original.
# Se quiser mais rápido, diminua (ex: 0.05). Se quiser mais lento, aumente (ex: 0.3).
ATRASO_ENTRE_LINHAS = 0.5

# Códigos ANSI para a cor verde (como o 'color 0a' do Batch)
COR_VERDE = '\033[92m'  # Verde brilhante
RESET_COR = '\033[0m'  # Reseta a cor para o padrão do terminal

# === Função Principal do Loop ===
def iniciar_chuva_genial():
    """
    Inicia o loop infinito que simula a chuva de códigos no terminal.
    """
    print(COR_VERDE) # Aplica a cor verde no início

    try:
        while True:
            # 1. Monta a linha de caracteres
            linha_de_dados = []
            
            # O número de colunas (itens) a ser exibido em cada linha.
            # O 'random.randint(10, 20)' garante que a largura da linha mude um pouco, 
            # simulando o efeito de "queda" de caracteres.
            num_colunas = random.randint(15, 30) 
            
            for _ in range(num_colunas):
                # Escolhe um item (número ou frase) aleatoriamente
                item = random.choice(CONTEUDO_GENIAL)
                linha_de_dados.append(item)

            # Junta os itens com espaços para formar a linha completa
            linha_final = " ".join(linha_de_dados)

            # 2. Imprime a linha
            print(linha_final)
            
            # 3. Controla a velocidade
            time.sleep(ATRASO_ENTRE_LINHAS)

    except KeyboardInterrupt: 
        # Permite que o usuário pare a execução pressionando CTRL+C
        print(f"\n{RESET_COR}Chuva de Códigos Parada. Gênio em Pausa.")
    finally:
        # Garante que a cor do terminal volte ao normal no final
        print(RESET_COR, end="")

# Inicia o programa
if __name__ == "__main__":
    # Esta é a maneira padrão de iniciar o script Python
    iniciar_chuva_genial()