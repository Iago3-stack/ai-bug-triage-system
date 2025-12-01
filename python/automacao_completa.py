# Importa as bibliotecas necessárias
from tkinter import *
from tkinter import ttk  # Importa ttk para a barra de progresso
import pyautogui
import time
import pandas as pd
import threading # Importa threading para rodar a automação em segundo plano

# --- FUNÇÕES ---

def atualizar_status(mensagem, cor="black"):
    """Função para atualizar a mensagem de status na interface."""
    mensagem_status.config(text=mensagem, fg=cor)

def iniciar_automacao():
    """Função que executa toda a automação em uma nova thread."""
    # Desabilita o botão para evitar cliques múltiplos
    botao_iniciar.config(state=DISABLED)
    
    # Inicia a automação em uma nova thread para não travar a interface
    # Isso é crucial para que a barra de progresso e o status continuem funcionando
    thread_automacao = threading.Thread(target=executar_automacao_thread)
    thread_automacao.start()

def executar_automacao_thread():
    """Função que contém a lógica de automação para ser executada na thread."""
    pyautogui.PAUSE = 0.5
    
    try:
        # Pega os dados dos campos da interface
        email = campo_email.get()
        senha = campo_senha.get()
        
        atualizar_status("Iniciando a automação...", "blue")
        barra_progresso.start()

        # ---- Passo 1: Acessar a página de login ----
        atualizar_status("Abrindo o navegador...", "blue")
        pyautogui.press("win")
        pyautogui.write("chrome")
        pyautogui.press("enter")
        time.sleep(2)
        pyautogui.write("https://dlp.hashtagtreinamentos.com/python/intensivao/login")
        pyautogui.press("enter")
        time.sleep(3)

        # ---- Passo 2: Fazer o login ----
        atualizar_status("Fazendo o login...", "blue")
        pyautogui.click(x=685, y=451)
        pyautogui.write(email)
        pyautogui.press("tab")
        pyautogui.write(senha)
        pyautogui.press("tab")
        pyautogui.press("enter")
        time.sleep(3)

        # ---- Passo 3: Preencher o formulário com dados do CSV ----
        atualizar_status("Lendo a tabela de dados...", "blue")
        tabela = pd.read_csv("produtos.csv")
        total_linhas = len(tabela.index)
        
        for i, linha in enumerate(tabela.index):
            atualizar_status(f"Preenchendo linha {i + 1} de {total_linhas}...", "green")
            barra_progresso['value'] = (i + 1) / total_linhas * 100
            janela.update_idletasks() # Força a atualização da interface

            codigo = tabela.loc[linha, "codigo"]
            marca = tabela.loc[linha, "marca"]
            tipo = tabela.loc[linha, "tipo"]
            categoria = tabela.loc[linha, "categoria"]
            preco = tabela.loc[linha, "preco_unitario"]
            custo = tabela.loc[linha, "custo"]
            obs = tabela.loc[linha, "obs"]

            pyautogui.click(x=685, y=242)
            pyautogui.write(str(codigo))
            pyautogui.press("tab")
            pyautogui.write(str(marca))
            pyautogui.press("tab")
            pyautogui.write(str(tipo))
            pyautogui.press("tab")
            pyautogui.write(str(categoria))
            pyautogui.press("tab")
            pyautogui.write(str(preco))
            pyautogui.press("tab")
            pyautogui.write(str(custo))
            pyautogui.press("tab")

            if not pd.isna(obs):
                pyautogui.write(str(obs))
            pyautogui.press("tab")
            pyautogui.press("enter")
            time.sleep(1)

        atualizar_status("Automação concluída com sucesso!", "green")
        barra_progresso.stop()
        botao_iniciar.config(state=NORMAL)

    except FileNotFoundError:
        atualizar_status("Erro: O arquivo 'produtos.csv' não foi encontrado.", "red")
        barra_progresso.stop()
        botao_iniciar.config(state=NORMAL)
    except Exception as e:
        atualizar_status(f"Ocorreu um erro inesperado: {e}", "red")
        barra_progresso.stop()
        botao_iniciar.config(state=NORMAL)

# --- INTERFACE GRÁFICA ---

# Cria a janela principal
janela = Tk()
janela.title("Automação de Formulários")
janela.geometry("450x300")
janela.configure(bg="#f0f0f0")

# Cria um Frame para organizar os campos
frame_campos = Frame(janela, bg="#f0f0f0")
frame_campos.pack(pady=20)

# Campo de E-mail
Label(frame_campos, text="E-mail:", bg="#f0f0f0").pack()
campo_email = Entry(frame_campos, width=40)
campo_email.pack(pady=5)
campo_email.insert(0, "iagojunio321@gmail.com") # Preenche com seu e-mail padrão

# Campo de Senha
Label(frame_campos, text="Senha:", bg="#f0f0f0").pack()
campo_senha = Entry(frame_campos, width=40, show="*") # show="*" esconde a senha
campo_senha.pack(pady=5)
campo_senha.insert(0, "32354678") # Preenche com sua senha padrão

# Botão de Iniciar
botao_iniciar = Button(janela, text="Iniciar Automação", command=iniciar_automacao)
botao_iniciar.pack(pady=10)

# Barra de progresso
barra_progresso = ttk.Progressbar(janela, orient="horizontal", length=300, mode="determinate")
barra_progresso.pack(pady=10)

# Mensagem de status
mensagem_status = Label(janela, text="Aguardando...", bg="#f0f0f0")
mensagem_status.pack()

# Inicia o loop da janela
janela.mainloop()
