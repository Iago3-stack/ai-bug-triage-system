import pyautogui # resposavel por automação de processos 
print("olá, mundo desde de 21/09/1997 eu serei um progamador ainda em 2025") # sim 
# passo 1 clicar no botão (win11)
# passo 2 digitar  o (google) 
pyautogui.PAUSE = 0.5 # resposavel por pausar por segundos ou minutos

pyautogui.press("win")  # aperta uma tecla 
pyautogui.write("google chorme")  # fazer pesquisa e digitar     
pyautogui.press("enter") 
pyautogui.write("https://dlp.hashtagtreinamentos.com/python/intensivao/login")
pyautogui.press("enter")

import time # dar tempo para a execução acontecer
time.sleep(1) 
# passo 5 logar com email iagojunio321@gmail.com  

pyautogui.click(x=685, y=451) # localiza o scroll da tela em x e y 
pyautogui.write("iagojunio321@gmail.com")
# passo 6 enserir senha 

pyautogui.press("tab")
pyautogui.write("32354678")
# botão logar 

pyautogui.press("tab")
pyautogui.press("enter")
# prencher formulário 

import pandas # resposavel por analises de dados 
tabela = pandas.read_csv("produtos.csv")
# proximo passo prencher o campo da tabela

print(tabela, ["produtos.csv"])






