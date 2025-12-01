# Importa as bibliotecas necessárias
from tkinter import *
import pyautogui
import time
import pandas as pd

# --- FUNÇÕES ---

def iniciar_automacao():
    """Função que executa toda a automação de preenchimento de formulário."""
    # Define um pequeno atraso para cada comando do PyAutoGUI
    pyautogui.PAUSE = 0.5

    try:
        # ---- Passo 1: Acessar a página de login ----
        print("Abrindo o navegador e acessando a página de login...")
        pyautogui.press("win")
        pyautogui.write("chrome")
        pyautogui.press("enter")
        time.sleep(1)
        pyautogui.write("https://dlp.hashtagtreinamentos.com/python/intensivao/login")
        pyautogui.press("enter")
        time.sleep(3)

        # ---- Passo 2: Fazer o login ----
        print("Fazendo o login...")
        pyautogui.click(x=685, y=451)
        pyautogui.write("iagojunio321@gmail.com")
        pyautogui.press("tab")
        pyautogui.write("32354678")
        pyautogui.press("tab")
        pyautogui.press("enter")
        time.sleep(3)

        # ---- Passo 3: Preencher o formulário com dados do CSV ----
        print("Lendo a tabela de dados e preenchendo o formulário...")
        tabela = pd.read_csv("produtos.csv")

        for linha in tabela.index:
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

        print("Processo de preenchimento de formulário concluído com sucesso!")
        mensagem_status["text"] = "Automação concluída!"

    except FileNotFoundError:
        print("Erro: O arquivo 'produtos.csv' não foi encontrado.")
        mensagem_status["text"] = "Erro: 'produtos.csv' não encontrado."
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
        mensagem_status["text"] = f"Erro: {e}"

# --- INTERFACE GRÁFICA ---

# Cria a janela principal
janela = Tk()
janela.title("Automação com Interface")
janela.geometry("400x150")

# Cria um label para exibir o status da automação
mensagem_status = Label(janela, text="Clique no botão para iniciar a automação.")
mensagem_status.pack(pady=20)

# Cria um botão para iniciar a automação
# O "command" chama a função que faz toda a mágica
botao_iniciar = Button(janela, text="Iniciar Automação", command=iniciar_automacao)
botao_iniciar.pack()

# Inicia o loop da janela
janela.mainloop()
