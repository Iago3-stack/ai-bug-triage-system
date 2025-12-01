# app.py
import flet as ft
import os
import json
import re

# --- FUNÇÕES DE SALVAR DADOS (MANTIDAS DO SEU CÓDIGO ORIGINAL) ---

def salvar_txt(dados_usuario):
    """Salva um dicionário de dados em um arquivo de texto."""
    NOME_ARQUIVO = 'cadastro_usuarios.txt'
    try:
        with open(NOME_ARQUIVO, 'a', encoding='utf-8') as arquivo:
            arquivo.write(f'--- NOVO CADASTRO ---\n')
            for chave, valor in dados_usuario.items():
                arquivo.write(f'{chave}: {valor}\n')
            arquivo.write(f'---------------------\n\n')
        print(f'\nSUCESSO: Dados salvos em {NOME_ARQUIVO}!')
    except IOError as e:
        print(f'\nERRO ao salvar TXT: {e}')

def salvar_json(dados_usuario):
    """Lê todos os cadastros existentes, adiciona o novo e salva de volta em JSON."""
    NOME_ARQUIVO = 'cadastro_usuarios.json'
    lista_de_cadastros = []

    if os.path.exists(NOME_ARQUIVO):
        try:
            with open(NOME_ARQUIVO, 'r', encoding='utf-8') as arquivo:
                lista_de_cadastros = json.load(arquivo)
        except json.JSONDecodeError:
            print(f"Atenção: Arquivo {NOME_ARQUIVO} vazio ou inválido. Criando novo conteúdo.")
            lista_de_cadastros = []
        except IOError as e:
            print(f'ERRO ao ler JSON: {e}')
            return

    lista_de_cadastros.append(dados_usuario)
    
    try:
        with open(NOME_ARQUIVO, 'w', encoding='utf-8') as arquivo:
            json.dump(lista_de_cadastros, arquivo, indent=4, ensure_ascii=False)
        print(f'\nSUCESSO: Dados adicionados a {NOME_ARQUIVO}!')
    except IOError as e:
        print(f'\nERRO ao salvar JSON: {e}')

# --- APLICAÇÃO FLET (Substitui a função 'perguntar_dados()') ---

def main(page: ft.Page):
    # Configurações iniciais da página web
    page.title = "Cadastro de Usuários com Flet"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.LIGHT

    # Campos de entrada de texto (substituem input())
    txt_nome = ft.TextField(label="Nome Completo", width=300)
    # CORRIGIDO: Sintaxe do InputFilter agora está correta
    txt_idade = ft.TextField(label="Idade (18+)", width=300, input_filter=ft.InputFilter(r"[0-9]"))
    txt_email = ft.TextField(label="E-mail", width=300)
    # CORRIGIDO: Sintaxe do InputFilter agora está correta aqui também
    txt_cpf = ft.TextField(label="CPF (apenas números)", width=300, input_filter=ft.InputFilter(r"[0-9]"), max_length=11)
    
    # Campo para feedback do usuário na interface
    status_text = ft.Text("")

    def cadastrar_click(e):
        """Função chamada quando o botão 'Cadastrar' é clicado."""
        nome = txt_nome.value.strip().title()
        idade_str = txt_idade.value.strip()
        email = txt_email.value.strip().lower()
        cpf = re.sub(r'[^0-9]', '', txt_cpf.value) # Usa sua lógica de regex

        # --- Validação dos dados (Lógica adaptada do seu código) ---
        if not nome or not idade_str or not email or len(cpf) != 11:
            status_text.value = "ERRO: Por favor, preencha todos os campos corretamente."
            status_text.Color = ft.Colors.RED_500
            page.update()
            return

        try:
            idade = int(idade_str)
            if idade < 18 or idade > 120:
                raise ValueError("Idade inválida.")
            
            if '@' not in email or '.' not in email:
                 raise ValueError("Email inválido.")

        except ValueError as ve:
            status_text.value = f"ERRO na validação: {ve}"
            status_text.Color = ft.Colors.RED_500
            page.update()
            return
        
        # --- Se a validação passar, salva os dados ---
        dados_usuario = {
            "Nome": nome,
            "Idade": idade,
            "Email": email,
            "CPF": cpf
        }

        salvar_txt(dados_usuario)
        salvar_json(dados_usuario)

        status_text.value = f"SUCESSO: Cadastro de {nome} realizado e salvo!"
        status_text.color = ft.Colors.GREEN_500
        
        # Limpa os campos após o cadastro
        txt_nome.value = ""
        txt_idade.value = ""
        txt_email.value = ""
        txt_cpf.value = ""

        page.update() # Atualiza a interface para mostrar o resultado

    # Adiciona os componentes visuais na página, organizados em uma coluna centralizada
    page.add(
        ft.Text("Formulário de Cadastro", size=24, weight=ft.FontWeight.BOLD),
        txt_nome,
        txt_idade,
        txt_email,
        txt_cpf,
        ft.ElevatedButton(text="Cadastrar Usuário", on_click=cadastrar_click),
        status_text
    )

# --- Como rodar o aplicativo ---
ft.app(target=main) # Roda como desktop/app nativo por padrão
# Use o terminal para rodar como web: flet run app.py --web
