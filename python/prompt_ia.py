# Importa as bibliotecas necessárias
from tkinter import *
from tkinter import ttk
import threading
import time
import requests # Necessário para fazer a requisição HTTP (API Call)
import json # Necessário para formatar o JSON do payload

# --- CONFIGURAÇÃO DA API (ATENÇÃO: Use uma chave real para uso externo) ---
API_KEY = "SUA_CHAVE_DE_API_GEMINI" # Substitua pela sua chave real
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
#--------------------------------------------------------------------------

# --- FUNÇÕES ---

def atualizar_status(mensagem, cor="black"):
    """Função para atualizar a mensagem de status na interface."""
    mensagem_status.config(text=mensagem, fg=cor)
    janela.update_idletasks()

def gerar_prompt_e_executar():
    """
    Função principal que pega a entrada, gera o prompt e chama a thread de execução.
    """
    botao_executar.config(state=DISABLED)
    # Roda a execução em uma thread para não travar a interface
    thread_execucao = threading.Thread(target=executar_algoritmo)
    thread_execucao.start()

def executar_algoritmo():
    """
    Este é o ALGORITMO COMPLETO. Ele gera o prompt E simula a chamada da API.
    """
    
    # 1. Pega os valores dos campos de entrada
    topico = campo_topico.get()
    tom = combo_tom.get()
    formato = combo_formato.get()
    
    atualizar_status("Gerando o Prompt...", "blue")
    
    # 2. Inicia o prompt com a instrução principal
    prompt_base = f"Gere um conteúdo sobre o seguinte tópico: {topico}. "
    
    # 3. Adiciona a regra de FORMATO
    if formato == "Email":
        instrucao_formato = "O conteúdo deve ser formatado como um email conciso. Comece com 'Assunto: ' e 'Caro(a) [Nome],'."
    elif formato == "Parágrafo":
        instrucao_formato = "O conteúdo deve ser um único parágrafo bem estruturado e com no máximo 100 palavras."
    elif formato == "Lista de 5 Tópicos":
        instrucao_formato = "O conteúdo deve ser uma lista com 5 tópicos detalhados em formato markdown."
    else:
        instrucao_formato = ""

    # 4. Adiciona a regra de TOM
    instrucao_tom = f"Utilize um tom {tom} e certifique-se de que a resposta esteja em Português do Brasil."

    # 5. Concatena (junta) todas as partes para formar o prompt final (O ALGORITMO!)
    prompt_final = f"{prompt_base}{instrucao_formato} {instrucao_tom}"
    
    # 6. Atualiza a interface com o prompt gerado
    campo_resultado.config(state=NORMAL)
    campo_resultado.delete(1.0, END)
    campo_resultado.insert(END, f"--- PROMPT ENVIADO ---\n{prompt_final}\n\n")
    
    # 7. CHAMA A API GEMINI (Lógica da Requisição)
    atualizar_status("Enviando prompt para a IA (simulando 3s de espera)...", "orange")
    
    # --- Estrutura do Payload (O que seria enviado via requests.post) ---
    payload = {
        "contents": [{"parts": [{"text": prompt_final}]}],
    }
    
    # SIMULAÇÃO DE RESPOSTA (Já que não temos a chave de API real no ambiente)
    # Esta linha simula o tempo que a rede levaria para responder:
    time.sleep(3) 

    # Simulação da resposta que a IA retornaria:
    resultado_simulado = f"A lógica de programação é a base de todo o desenvolvimento de software. Ela permite que você crie algoritmos eficientes, resolva problemas complexos e se comunique com o computador de forma clara. Investir tempo no aprendizado da lógica é o passo mais **motivacional** para transformar ideias em realidade digital, e você está dominando essa arte!"

    
    # 8. Atualiza a interface com a RESPOSTA da IA
    campo_resultado.insert(END, f"--- RESPOSTA DA IA ---\n{resultado_simulado}")
    campo_resultado.config(state=DISABLED)
    
    atualizar_status("Execução e resposta da IA concluídas!", "green")
    botao_executar.config(state=NORMAL)


# --- INTERFACE GRÁFICA ---

janela = Tk()
janela.title("Gerador e Executor de Prompt (LLM)")
janela.geometry("600x550")
janela.configure(bg="#f0f0f0")

# --- Frame para os campos de entrada ---
frame_campos = Frame(janela, bg="#f0f0f0")
frame_campos.pack(pady=15, padx=20, fill=X)

# Rótulo e Campo Tópico
Label(frame_campos, text="Tópico Principal:", bg="#f0f0f0", anchor="w").pack(fill=X)
campo_topico = Entry(frame_campos, width=50, font=("Arial", 10))
campo_topico.pack(fill=X, pady=5)
campo_topico.insert(0, "A importância da lógica de programação")

# Rótulo e Combo Tom
Label(frame_campos, text="Tom de Voz:", bg="#f0f0f0", anchor="w").pack(fill=X, pady=(10, 0))
tom_opcoes = ["Profissional", "Casual", "Motivacional", "Técnico"]
combo_tom = ttk.Combobox(frame_campos, values=tom_opcoes, state="readonly", font=("Arial", 10))
combo_tom.current(0)
combo_tom.pack(fill=X, pady=5)

# Rótulo e Combo Formato
Label(frame_campos, text="Formato de Saída:", bg="#f0f0f0", anchor="w").pack(fill=X, pady=(10, 0))
formato_opcoes = ["Parágrafo", "Lista de 5 Tópicos", "Email"]
combo_formato = ttk.Combobox(frame_campos, values=formato_opcoes, state="readonly", font=("Arial", 10))
combo_formato.current(0)
combo_formato.pack(fill=X, pady=5)

# Botão Executar Prompt
botao_executar = Button(janela, text="EXECUTAR PROMPT NA IA", command=gerar_prompt_e_executar, bg="#008CBA", fg="white", font=("Arial", 12, "bold"))
botao_executar.pack(pady=20, padx=20, fill=X)

# Área de Resultado (Prompt Gerado + Resposta da IA)
Label(janela, text="Prompt Gerado e Resposta da IA:", bg="#f0f0f0").pack()
campo_resultado = Text(janela, height=10, width=60, padx=10, pady=10, wrap=WORD, font=("Arial", 10))
campo_resultado.pack(padx=20, fill=X, expand=True)
campo_resultado.config(state=DISABLED)

# Mensagem de Status
mensagem_status = Label(janela, text="Aguardando as instruções...", bg="#f0f0f0")
mensagem_status.pack(pady=10)

janela.mainloop()
