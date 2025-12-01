# Importa tudo da biblioteca Tkinter
from tkinter import *

# --- FUNÇÕES ---

def somar_numeros():
    try:
        # Pega o valor dos campos de entrada
        numero1_str = campo_numero1.get()
        numero2_str = campo_numero2.get()
        
        # Converte os valores para números (inteiros)
        num1 = int(numero1_str)
        num2 = int(numero2_str)
        
        # Realiza a soma
        resultado = num1 + num2
        
        # Atualiza o texto da mensagem com o resultado
        mensagem_resultado["text"] = f"A soma é: {resultado}"
        
    except ValueError:
        # Lida com o erro se o usuário digitar algo que não é um número
        mensagem_resultado["text"] = "Erro: Digite apenas números inteiros."

# --- INTERFACE GRÁFICA ---

# Cria a janela principal do programa
janela = Tk()
janela.title("Calculadora de Soma")
janela.geometry("300x250")
janela.configure(bg="#f0f0f0") # Adiciona uma cor de fundo

# Cria um label para instruir o usuário
label_titulo = Label(janela, text="Calculadora Simples", font=("Arial", 16, "bold"), bg="#f0f0f0")
label_titulo.pack(pady=10)

# Cria um campo de entrada para o primeiro número
label_num1 = Label(janela, text="Primeiro número:", bg="#f0f0f0")
label_num1.pack()
campo_numero1 = Entry(janela)
campo_numero1.pack()

# Cria um campo de entrada para o segundo número
label_num2 = Label(janela, text="Segundo número:", bg="#f0f0f0")
label_num2.pack()
campo_numero2 = Entry(janela)
campo_numero2.pack()

# Cria um botão para somar os números
# O comando "somar_numeros" chama a função que criamos
botao_somar = Button(janela, text="Somar", command=somar_numeros)
botao_somar.pack(pady=10)

# Cria um label para exibir o resultado
mensagem_resultado = Label(janela, text="Aguardando...", bg="#f0f0f0")
mensagem_resultado.pack()

# Inicia o loop principal do programa
janela.mainloop()
