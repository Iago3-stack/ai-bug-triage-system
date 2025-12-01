import customtkinter as ctk
from tkinter import messagebox

# Configurações iniciais do CustomTkinter
ctk.set_appearance_mode("dark")  # Define o modo inicial como "dark"
ctk.set_default_color_theme("blue")

class criar_janela(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('Gerenciador')
        self.geometry("700x500")
        self.minsize(600, 450)
        
        # Estrutura para armazenar os dados do usuário
        self.dados_usuario = {}
        
        self.criar_widgets()

    def criar_widgets(self):
        # Frame principal que se expande com a janela
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        # Configura o grid para que a segunda coluna (onde ficam as entradas) se expanda
        self.main_frame.grid_columnconfigure(1, weight=1)

        # --- Campos de Dados ---
        # campo para nome 
        ctk.CTkLabel(self.main_frame, text="Nome:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.entrada_nome = ctk.CTkEntry(self.main_frame, placeholder_text="Digite o nome completo")
        self.entrada_nome.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        # campo para idade
        ctk.CTkLabel(self.main_frame, text="Idade:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.entrada_idade = ctk.CTkEntry(self.main_frame, placeholder_text="Apenas números (ex: 30)")
        self.entrada_idade.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        # campo para email
        ctk.CTkLabel(self.main_frame, text="Email:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.entrada_email = ctk.CTkEntry(self.main_frame, placeholder_text="exemplo@email.com")
        self.entrada_email.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        # campo para telefone
        ctk.CTkLabel(self.main_frame, text="Telefone:").grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.entrada_telefone = ctk.CTkEntry(self.main_frame, placeholder_text="(XX) XXXXX-XXXX")
        self.entrada_telefone.grid(row=3, column=1, padx=10, pady=10, sticky="ew")

        # --- Frame para organizar os botões ---
        self.botoes_frame = ctk.CTkFrame(self.main_frame)
        self.botoes_frame.grid(row=4, column=0, columnspan=2, pady=20, sticky="ew")
        self.botoes_frame.grid_columnconfigure((0, 1), weight=1) # Faz os botões se espaçarem

        # --- Botões de Ação ---
        self.botao_salvar = ctk.CTkButton(self.botoes_frame, text="Salvar Novo", command=self.salvar_dados)
        self.botao_salvar.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        #--- botaõ de editar 
        self.botao_carregar = ctk.CTkButton(self.botoes_frame, text="Carregar para Editar", command=self.carregar_dados)
        self.botao_carregar.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        # --- Interruptor para Mudar o Tema ---
        self.theme_switch = ctk.CTkSwitch(self.main_frame, text="Modo Escuro", command=self.change_theme)
        self.theme_switch.grid(row=5, column=0, columnspan=2, pady=10, padx=20, sticky="w")
        self.theme_switch.select() # Deixa o switch ativado por padrão, pois começamos em modo escuro
    # função de alterna entre modo claro/escuro
    def change_theme(self):
        """Alterna entre o modo claro e escuro."""
        if self.theme_switch.get() == 1:
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")

    def carregar_dados(self):
        """Carrega os dados do dicionário para os campos de entrada, permitindo a edição."""
        if not self.dados_usuario:
            messagebox.showwarning("Aviso", "Nenhum dado salvo para carregar.")
            return
       # Limpa os campos antes de carregar
        self.entrada_nome.delete(0, 'end')
        self.entrada_idade.delete(0, 'end')
        self.entrada_email.delete(0, 'end')
        self.entrada_telefone.delete(0, 'end')

        # Insere os dados salvos nos campos
        self.entrada_nome.insert(0, self.dados_usuario.get('nome', ''))
        self.entrada_idade.insert(0, self.dados_usuario.get('idade', ''))
        self.entrada_email.insert(0, self.dados_usuario.get('email', ''))
        self.entrada_telefone.insert(0, self.dados_usuario.get('telefone', ''))
        
        messagebox.showinfo("Sucesso", "Dados carregados nos campos. Agora você pode editar e salvar as alterações.")

    def salvar_dados(self):
        """Salva ou atualiza os dados dos campos de entrada no dicionário."""
        nome = self.entrada_nome.get()
        idade = self.entrada_idade.get()
        email = self.entrada_email.get()
        telefone = self.entrada_telefone.get()
        
        # Validação simples para garantir que os campos principais não estão vazios
        if nome and idade:
            self.dados_usuario['nome'] = nome
            self.dados_usuario['idade'] = idade
            self.dados_usuario['email'] = email
            self.dados_usuario['telefone'] = telefone
            
            messagebox.showinfo("Sucesso", f"Dados para '{nome}' foram salvos com sucesso!")
            
            # Limpa os campos após salvar um novo registro
            self.entrada_nome.delete(0, 'end')
            self.entrada_idade.delete(0, 'end')
            self.entrada_email.delete(0, 'end')
            self.entrada_telefone.delete(0, 'end')
        else:
            # Exibe a mensagem de erro se a validação falhar
            messagebox.showerror("Erro", "Os campos 'Nome' e 'Idade' são obrigatórios.")

if __name__ == "__main__":
    app = criar_janela()
    app.mainloop()
