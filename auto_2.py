# Importa as bibliotecas necessárias
import pyautogui
import time
import pandas as pd

# Define um pequeno atraso para cada comando do PyAutoGUI
# Isso evita que a automação seja muito rápida e cause erros
pyautogui.PAUSE = 0.5

# ---- Passo 1: Acessar a página de login ----
print("Abrindo o navegador e acessando a página de login...")
pyautogui.press("win")
pyautogui.write("chrome")
pyautogui.press("enter")
time.sleep(1) # Aguarda o navegador abrir
pyautogui.write("https://dlp.hashtagtreinamentos.com/python/intensivao/login")
pyautogui.press("enter")
time.sleep(3) # Aguarda a página carregar completamente

# ---- Passo 2: Fazer o login ----
print("Fazendo o login...")
# Clica no campo de e-mail e digita o endereço
pyautogui.click(x=685, y=451)
pyautogui.write("iagojunio321@gmail.com")

# Pressiona TAB para ir para o campo de senha e digita a senha
pyautogui.press("tab")
pyautogui.write("32354678")

# Pressiona TAB e ENTER para clicar no botão de login
pyautogui.press("tab")
pyautogui.press("enter")
time.sleep(3) # Aguarda a página carregar após o login

# ---- Passo 3: Preencher o formulário com dados do CSV ----
print("Lendo a tabela de dados e preenchendo o formulário...")
try:
    # Lê a tabela de produtos.csv usando a biblioteca pandas
    tabela = pd.read_csv("produtos.csv")

    # Itera sobre cada linha da tabela (tabela.index é o índice de cada linha)
    for linha in tabela.index:
        # Extrai os dados de cada linha
        codigo = tabela.loc[linha, "codigo"]
        marca = tabela.loc[linha, "marca"]
        tipo = tabela.loc[linha, "tipo"]
        categoria = tabela.loc[linha, "categoria"]
        preco = tabela.loc[linha, "preco_unitario"]
        custo = tabela.loc[linha, "custo"]
        obs = tabela.loc[linha, "obs"]

        # Clica no primeiro campo do formulário (código do produto)
        # As coordenadas (x,y) podem variar. Sugiro usar o comando 'pyautogui.position()' para descobrir as corretas.
        pyautogui.click(x=685, y=242)

        # Preenche os campos do formulário
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

        # Verifica se há uma observação para preencher
        if not pd.isna(obs):
            pyautogui.write(str(obs))
        pyautogui.press("tab")

        # Clica no botão de enviar (cadastrar)
        pyautogui.press("enter")
        time.sleep(1) # Pequena pausa entre cada envio

    print("Processo de preenchimento de formulário concluído com sucesso!")

except FileNotFoundError:
    print("Erro: O arquivo 'produtos.csv' não foi encontrado. Certifique-se de que ele está na mesma pasta que o script.")
except Exception as e:
    print(f"Ocorreu um erro inesperado: {e}")
