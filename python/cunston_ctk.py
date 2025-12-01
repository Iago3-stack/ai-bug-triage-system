import customtkinter as ctk
import re
from tkinter import messagebox

# --- Configurações básicas do CTk ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class SistemaRH(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🗂️Arquivos Pessoais")
        self.geometry("600x400")
        self.minsize(500, 300)
        self.eval('tk::PlaceWindow . center')

        self.dados_usuario = {} # Armazena o usuário atual
        self.modo_edicao = False # Flag para saber se estamos editando ou cadastrando

        self.criar_widgets()

    def criar_widgets(self):
        # ... (Frame e Labels/Entries são os mesmos do código anterior) ...
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(pady=20, padx=20, fill="both", expand=True)
       
        # campo para nome 
        ctk.CTkLabel(self.main_frame, text="Nome:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.entrada_nome = ctk.CTkEntry(self.main_frame, width=250, placeholder_text="Digite seu nome completo")
        self.entrada_nome.grid(row=0, column=1, padx=10, pady=10)
        # campo para idade
        ctk.CTkLabel(self.main_frame, text="Idade:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.entrada_idade = ctk.CTkEntry(self.main_frame, width=250, placeholder_text="Apenas números (ex: 30)")
        self.entrada_idade.grid(row=1, column=1, padx=10, pady=10)
        # campo para cpf
        ctk.CTkLabel(self.main_frame, text="CPF:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.entrada_cpf = ctk.CTkEntry(self.main_frame, width=250, placeholder_text="Somente 11 dígitos")
        self.entrada_cpf.grid(row=2, column=1, padx=10, pady=10)
        # campo para email
        ctk.CTkLabel(self.main_frame, text="Email:").grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.entrada_email = ctk.CTkEntry(self.main_frame, width=250, placeholder_text="exemplo@dominio.com")
        self.entrada_email.grid(row=3, column=1, padx=10, pady=10)
        
        # Botões
        # Este botão verde agora alterna entre Cadastrar e Salvar Edição
        self.botao_principal = ctk.CTkButton(self.main_frame, text="Cadastrar Usuário", command=self.cadastrar_usuario)
        self.botao_principal.grid(row=4, column=0, pady=20, padx=10, sticky="e") 
        
        # Botão para entrar no modo de edição
        self.botao_modo_edicao = ctk.CTkButton(self.main_frame, text="Modo Edição", command=self.entrar_modo_edicao, fg_color="dark blue", hover_color="blue")
        self.botao_modo_edicao.grid(row=4, column=1, pady=20, padx=10, sticky="w")
        self.botao_modo_edicao.configure(state="enable") # Começa desativado

    def limpar_campos(self):
        """Função auxiliar para limpar todas as entradas."""
        self.entrada_nome.delete(0, ctk.END)
        self.entrada_idade.delete(0, ctk.END)
        self.entrada_cpf.delete(0, ctk.END)
        self.entrada_email.delete(0, ctk.END)

    def validar_campos(self, nome, idade_str, cpf_raw, email):
        """Função auxiliar para validar os dados e retornar um dicionário ou None em caso de erro."""
        try:
            if not nome: raise ValueError("O campo Nome não pode estar vazio.")
            
            idade = int(idade_str)
            if idade < 18: raise ValueError("Você deve ser maior de idade.")

            cpf = re.sub(r'[^0-9]', '', cpf_raw)
            if len(cpf) != 11: raise ValueError("O CPF deve ter 11 dígitos numéricos.")

            if '@' not in email or '.' not in email: raise ValueError("Por favor, insira um e-mail válido.")
            
            return {'Nome': nome, 'Idade': idade, 'CPF': cpf, 'Email': email}
        
        except ValueError as e:
            messagebox.showerror("Erro de Validação", str(e))
            return None

    def cadastrar_usuario(self):
        """Lógica para cadastrar um novo usuário."""
        if self.modo_edicao:
            # Se o botão foi clicado no modo errado, ignora
            return 

        dados = self.validar_campos(
            self.entrada_nome.get().strip().title(),
            self.entrada_idade.get().strip(),
            self.entrada_cpf.get().strip(),
            self.entrada_email.get().strip().lower()
        )
        
        if dados:
            self.dados_usuario = dados
            messagebox.showinfo("Sucesso", f"Usuário {dados['Nome']} cadastrado!")
            self.botao_modo_edicao.configure(state="normal") # Ativa o botão de edição
            self.limpar_campos()
            # TODO: Chamar funções de salvar TXT/JSON aqui.
            
    def entrar_modo_edicao(self):
        """Preenche os campos com os dados existentes e muda o botão principal para 'Salvar'."""
        if not self.dados_usuario:
            messagebox.showwarning("Atenção", "Nenhum usuário cadastrado para editar.")
            return

        self.modo_edicao = True
        
        # Mudar a aparência do botão principal para indicar que está salvando edição
        self.botao_principal.configure(
            text="Salvar Alterações", 
            command=self.salvar_edicao,
            fg_color="green",
            hover_color="dark green"
        )
        self.botao_modo_edicao.configure(state="disabled") # Desativa o botão de edição enquanto edita

        # Preenche os campos com os dados atuais
        self.limpar_campos()
        self.entrada_nome.insert(0, self.dados_usuario['Nome'])
        self.entrada_idade.insert(0, str(self.dados_usuario['Idade']))
        self.entrada_cpf.insert(0, self.dados_usuario['CPF'])
        self.entrada_email.insert(0, self.dados_usuario['Email'])
        
        messagebox.showinfo("Modo Edição", "Campos preenchidos. Altere os dados e clique em 'Salvar Alterações'.")

    def salvar_edicao(self):
        """Salva os dados editados nos campos."""
        if not self.modo_edicao:
            return

        dados_editados = self.validar_campos(
            self.entrada_nome.get().strip().title(),
            self.entrada_idade.get().strip(),
            self.entrada_cpf.get().strip(),
            self.entrada_email.get().strip().lower()
        )

        if dados_editados:
            self.dados_usuario = dados_editados
            messagebox.showinfo("Sucesso", f"Dados de {dados_editados['Nome']} atualizados!")

            # Retorna ao modo de cadastro normal
            self.modo_edicao = False
            self.botao_principal.configure(
                text="Cadastrar Usuário", 
                command=self.cadastrar_usuario,
                fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"], # Cor padrão azul
                hover_color=ctk.ThemeManager.theme["CTkButton"]["hover_color"]
            )
            self.botao_modo_edicao.configure(state="normal") # Reativa o botão de edição
            self.limpar_campos()
            # TODO: Chamar funções de salvar TXT/JSON aqui COM OS DADOS ATUALIZADOS.


if __name__ == "__main__":
    app = SistemaRH()
    app.mainloop()
