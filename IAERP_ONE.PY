# Requer CustomTkinter: pip install customtkinter
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from collections import defaultdict
import csv
from datetime import datetime

# Define a aparência global do CustomTkinter
ctk.set_appearance_mode("System")  # Padrão: "Light", "Dark", "System"
ctk.set_default_color_theme("blue") # Temas: "blue", "green", "dark-blue"

# --- CONFIGURAÇÕES DE DADOS (Persistência JSON) ---
NOME_ARQUIVO = 'dados_usuarios.json'
CREDENCIAIS = {
    'admin': '1234',
    'user': '4321'
}

def carregar_dados():
    """Carrega os dados de usuários do arquivo JSON. Retorna lista vazia se falhar."""
    if os.path.exists(NOME_ARQUIVO):
        try:
            with open(NOME_ARQUIVO, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def salvar_dados(dados):
    """Salva a lista completa de dados no arquivo JSON."""
    with open(NOME_ARQUIVO, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

# ----------------------------------------------------------------------
# CLASSE DE LOGIN (Controlador para Transição de Tela)
# ----------------------------------------------------------------------

class LoginApp:
    def __init__(self, master):
        self.master = master
        master.title("Login - AI ERP")
        master.geometry("350x300")
        master.resizable(False, False) 

        self.user_role = None 

        self.frame = ctk.CTkFrame(master, corner_radius=10)
        self.frame.pack(expand=True, fill="both", padx=20, pady=20)

        ctk.CTkLabel(self.frame, text="Acesso ao Sistema ERP", font=ctk.CTkFont(family="Inter", size=18, weight="bold")).pack(pady=20)

        # Campos de Login
        ctk.CTkLabel(self.frame, text="Usuário:", font=ctk.CTkFont(family="Inter", size=12)).pack(pady=(10, 0), anchor='w', padx=10)
        self.user_entry = ctk.CTkEntry(self.frame, width=280, placeholder_text="Digite seu usuário")
        self.user_entry.pack(pady=5)

        ctk.CTkLabel(self.frame, text="Senha:", font=ctk.CTkFont(family="Inter", size=12)).pack(pady=(10, 0), anchor='w', padx=10)
        self.pass_entry = ctk.CTkEntry(self.frame, width=280, show="*", placeholder_text="Digite sua senha")
        self.pass_entry.pack(pady=5)

        ctk.CTkButton(self.frame, text="Entrar", command=self.do_login, font=ctk.CTkFont(family="Inter", size=13, weight="bold")).pack(pady=20)
        
        # Bind do Enter
        self.user_entry.bind('<Return>', lambda event: self.do_login())
        self.pass_entry.bind('<Return>', lambda event: self.do_login())


    def do_login(self):
        """Tenta autenticar o usuário e inicia o ERP na mesma janela se for bem-sucedido."""
        username = self.user_entry.get()
        password = self.pass_entry.get()

        if username in CREDENCIAIS and CREDENCIAIS[username] == password:
            self.user_role = 'Admin' if username == 'admin' else 'User'
            self.start_erp_app() 
        else:
            messagebox.showerror("Erro de Login", "Usuário ou senha inválidos.")
            self.pass_entry.delete(0, tk.END)

    def start_erp_app(self):
        """Limpa a janela e inicializa o ERPApp na mesma janela raiz."""
        for widget in self.master.winfo_children():
            widget.destroy()
        
        ERPApp(self.master, self.user_role)

# ----------------------------------------------------------------------
# CLASSE PRINCIPAL DO APLICATIVO TKINTER/CUSTOMTKINTER
# ----------------------------------------------------------------------

class ERPApp:
    def __init__(self, master, user_role):
        self.master = master
        self.user_role = user_role
        master.title(f"AI ERP - Gerenciamento Avançado (Perfil: {self.user_role})")
        master.geometry("1200x800")
        master.resizable(True, True) 

        self.dados_usuarios = carregar_dados()
        
        # Variáveis de Estado
        self.treeview_geral = None
        self.treeviews_modalidade = {} 
        self.editando_id = None
        self.entries = {}
        self.modalidade_var = ctk.StringVar(master, value='CLT')
        self.btn_salvar_cadastro = None
        self.btn_cancelar_edicao = None
        self.combo_ausencias_user = None 

        # Configurações do Notebook (Abas - Usamos o ttk para manter a funcionalidade de abas)
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(pady=10, padx=10, expand=True, fill="both")

        # Criação das Abas
        self.criar_aba_cadastro()
        self.criar_aba_listagem_geral()
        self.criar_aba_listagem_modalidade('CLT')
        self.criar_aba_listagem_modalidade('PJ')
        self.criar_aba_listagem_modalidade('ESTAGIÁRIO')
        self.criar_aba_ausencias() 
        
        if self.user_role == 'Admin':
            self.criar_aba_relatorios() 

        self.atualizar_todas_as_listas()
        
        self.notebook.bind("<<NotebookTabChanged>>", self.ao_mudar_aba)


    # --- 1. CRIAÇÃO DA ABA DE CADASTRO/EDIÇÃO ---
    def criar_aba_cadastro(self):
        """Cria e configura o formulário de cadastro/edição usando CTkFrame."""
        frame = ctk.CTkFrame(self.notebook, corner_radius=10) 
        self.notebook.add(frame, text='Cadastro / Edição', sticky='nsew')

        self.titulo_cadastro = ctk.CTkLabel(frame, text="Novo Cadastro de Colaborador", font=ctk.CTkFont(family="Inter", size=18, weight="bold"))
        self.titulo_cadastro.grid(row=0, column=0, columnspan=2, pady=15, sticky='w', padx=20)

        campos = ["Nome", "E-mail", "Telefone", "Salário (R$)", "Modalidade"]
        
        for i, campo in enumerate(campos):
            ctk.CTkLabel(frame, text=f"{campo}:", font=ctk.CTkFont(family="Inter", size=12)).grid(row=i + 1, column=0, sticky="w", pady=12, padx=20)
            
            if campo == "Salário (R$)":
                if self.user_role != 'Admin':
                    ctk.CTkLabel(frame, text="Acesso Negado", text_color="red", font=ctk.CTkFont(family="Inter", size=12, slant="italic")).grid(row=i + 1, column=1, sticky="w", pady=12, padx=5)
                    self.entries[campo] = None 
                    continue
            
            if campo == "Modalidade":
                modalidades = ['CLT', 'PJ', 'ESTAGIÁRIO']
                entry = ctk.CTkComboBox(frame, variable=self.modalidade_var, values=modalidades, width=400)
            else:
                self.entries[campo] = ctk.CTkEntry(frame, width=400, font=ctk.CTkFont(family="Inter", size=12))
                entry = self.entries[campo]
            
            entry.grid(row=i + 1, column=1, sticky="ew", pady=12, padx=20)
        
        button_frame = ctk.CTkFrame(frame, fg_color="transparent")
        button_frame.grid(row=len(campos) + 1, column=0, columnspan=2, pady=20, padx=20, sticky='w') 

        self.btn_salvar_cadastro = ctk.CTkButton(button_frame, text="Salvar Cadastro", command=self.salvar_ou_atualizar_usuario, width=180, font=ctk.CTkFont(family="Inter", size=13, weight="bold"))
        self.btn_salvar_cadastro.pack(side='left', padx=10)
        
        self.btn_cancelar_edicao = ctk.CTkButton(button_frame, text="Cancelar Edição", command=self.cancelar_edicao, fg_color="gray", hover_color="darkgray", width=180)
        
        frame.grid_columnconfigure(1, weight=1)

    def criar_aba_listagem_geral(self):
        """Cria a aba de listagem geral usando CTkFrame."""
        frame = ctk.CTkFrame(self.notebook, corner_radius=10) 
        self.notebook.add(frame, text='Listagem Geral', sticky='nsew')

        ctk.CTkLabel(frame, text="Todos os Registros", font=ctk.CTkFont(family="Inter", size=16, weight="bold")).pack(pady=15)

        colunas = ('ID', 'Nome', 'Modalidade', 'Email', 'Telefone')
        if self.user_role == 'Admin':
            colunas = ('ID', 'Nome', 'Modalidade', 'Salário', 'Email', 'Telefone') 
            
        self.treeview_geral = ttk.Treeview(frame, columns=colunas, show='headings')
        
        for col in colunas:
            self.treeview_geral.heading(col, text=col)
            largura = 150
            self.treeview_geral.column(col, width=largura, anchor='center')

        self.treeview_geral.pack(fill='both', expand=True, padx=20, pady=5)
        
        action_frame = ctk.CTkFrame(frame, fg_color="transparent")
        action_frame.pack(pady=20, fill='x', padx=20)

        self.btn_editar = ctk.CTkButton(action_frame, text="Editar Selecionado", command=self.abrir_edicao_selecionada, state='disabled')
        self.btn_editar.pack(side='left', padx=10)

        self.btn_deletar = ctk.CTkButton(action_frame, text="Deletar Selecionado", command=self.deletar_usuario_selecionado, fg_color="red", hover_color="darkred", state='disabled')
        self.btn_deletar.pack(side='left', padx=10)
        
        if self.user_role == 'Admin':
            self.btn_exportar = ctk.CTkButton(action_frame, text="Exportar Dados (CSV)", command=self.exportar_dados_csv)
            self.btn_exportar.pack(side='right', padx=10)
        
        self.treeview_geral.bind('<<TreeviewSelect>>', self.toggle_action_buttons)

    def criar_aba_listagem_modalidade(self, modalidade_nome):
        """Cria abas específicas por modalidade usando CTkFrame."""
        frame = ctk.CTkFrame(self.notebook, corner_radius=10) 
        self.notebook.add(frame, text=f'{modalidade_nome}', sticky='nsew')

        ctk.CTkLabel(frame, text=f"Registros de {modalidade_nome}", font=ctk.CTkFont(family="Inter", size=16, weight="bold")).pack(pady=15)

        colunas = ('ID', 'Nome', 'Email', 'Telefone')
        if self.user_role == 'Admin':
            colunas = ('ID', 'Nome', 'Salário', 'Email', 'Telefone')

        tree = ttk.Treeview(frame, columns=colunas, show='headings')
        
        for col in colunas:
            tree.heading(col, text=col)
            largura = 150
            tree.column(col, width=largura, anchor='center')
            
        tree.pack(fill='both', expand=True, padx=20, pady=5)
        
        self.treeviews_modalidade[modalidade_nome] = tree

    # --- 3. MÓDULO DE GESTÃO DE AUSÊNCIAS ---
    def criar_aba_ausencias(self):
        """Cria a aba para gerenciar e registrar ausências dos colaboradores usando CTkFrame."""
        frame = ctk.CTkFrame(self.notebook, corner_radius=10) 
        self.notebook.add(frame, text='Gestão de Ausências', sticky='nsew')

        ctk.CTkLabel(frame, text="Registro e Histórico de Ausências", font=ctk.CTkFont(family="Inter", size=16, weight="bold")).grid(row=0, column=0, columnspan=2, pady=15, padx=20, sticky='w')
        
        ctk.CTkLabel(frame, text="Colaborador:", font=ctk.CTkFont(family="Inter", size=12)).grid(row=1, column=0, sticky="w", pady=5, padx=20)
        self.combo_ausencias_user = ctk.CTkComboBox(frame, state="readonly", width=400, values=[])
        self.combo_ausencias_user.grid(row=1, column=1, sticky="ew", padx=20)
        
        ctk.CTkLabel(frame, text="Data (YYYY-MM-DD):", font=ctk.CTkFont(family="Inter", size=12)).grid(row=2, column=0, sticky="w", pady=5, padx=20)
        self.ausencia_data = ctk.CTkEntry(frame, width=400, placeholder_text="Ex: 2025-01-15")
        self.ausencia_data.grid(row=2, column=1, sticky="ew", padx=20)

        ctk.CTkLabel(frame, text="Tipo (Férias/Atestado/Outro):", font=ctk.CTkFont(family="Inter", size=12)).grid(row=3, column=0, sticky="w", pady=5, padx=20)
        self.ausencia_tipo = ctk.CTkEntry(frame, width=400, placeholder_text="Ex: FÉRIAS")
        self.ausencia_tipo.grid(row=3, column=1, sticky="ew", padx=20)
        
        ctk.CTkLabel(frame, text="Observação:", font=ctk.CTkFont(family="Inter", size=12)).grid(row=4, column=0, sticky="w", pady=5, padx=20)
        self.ausencia_obs = ctk.CTkEntry(frame, width=400)
        self.ausencia_obs.grid(row=4, column=1, sticky="ew", padx=20)
        
        ctk.CTkButton(frame, text="Registrar Ausência", command=self.registrar_ausencia, width=200).grid(row=5, column=0, columnspan=2, pady=15)

        ctk.CTkLabel(frame, text="Histórico de Ausências do Colaborador:", font=ctk.CTkFont(family="Inter", size=14, weight="bold")).grid(row=6, column=0, columnspan=2, pady=10, sticky='w', padx=20)
        
        colunas_hist = ('Data', 'Tipo', 'Observação')
        self.treeview_ausencias = ttk.Treeview(frame, columns=colunas_hist, show='headings', height=10)
        for col in colunas_hist:
            self.treeview_ausencias.heading(col, text=col)
            self.treeview_ausencias.column(col, width=200, anchor='center')
        self.treeview_ausencias.grid(row=7, column=0, columnspan=2, sticky='nsew', padx=20, pady=5)
        
        frame.grid_rowconfigure(7, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        
        self.combo_ausencias_user.bind('<<ComboboxSelected>>', self.atualizar_historico_ausencias)

    # --- 4. CRIAÇÃO DA ABA DE RELATÓRIOS ANALÍTICOS (RBAC) ---
    def criar_aba_relatorios(self):
        """
        Cria a aba para exibir métricas de BI (Apenas para Admin) usando CTkTextbox para evitar o bug visual.
        O CTkTextbox gerencia o tema e a rolagem automaticamente.
        """
        self.frame_relatorios = ctk.CTkFrame(self.notebook, corner_radius=10) 
        self.notebook.add(self.frame_relatorios, text='Relatórios BI', sticky='nsew')
        
        ctk.CTkLabel(self.frame_relatorios, text="Análise de Business Intelligence (BI)", font=ctk.CTkFont(family="Inter", size=16, weight="bold")).pack(pady=15)
        
        # V18 FIX: Usando CTkTextbox, que se integra perfeitamente com o tema.
        self.relatorio_texto = ctk.CTkTextbox(self.frame_relatorios, 
                                              height=550, # Altura ajustada
                                              font=("Courier", 12),
                                              corner_radius=8)
        self.relatorio_texto.pack(padx=20, pady=10, expand=True, fill='both')

    # ----------------------------------------------------------------------
    # Métodos de Lógica (Inalterados)
    # ----------------------------------------------------------------------

    def ao_mudar_aba(self, event):
        """Atualiza o conteúdo de abas dinâmicas (Relatórios e Ausências)."""
        tab_index = self.notebook.index(self.notebook.select())
        tab_title = self.notebook.tab(tab_index, "text")
        
        if tab_title == "Relatórios BI" and self.user_role == 'Admin':
            self.atualizar_relatorios()
        elif tab_title == "Gestão de Ausências":
            self.atualizar_combo_usuarios_ausencias()
            
    def atualizar_titulo_cadastro(self):
        """Atualiza o título da aba de cadastro para indicar se é uma edição ou novo cadastro."""
        if self.editando_id is not None:
            self.titulo_cadastro.configure(text=f"Editando Colaborador (ID: {self.editando_id})")
            self.btn_salvar_cadastro.configure(text="Salvar Alterações")
            self.btn_cancelar_edicao.pack(side='left', padx=10)
        else:
            self.titulo_cadastro.configure(text="Novo Cadastro de Colaborador")
            self.btn_salvar_cadastro.configure(text="Salvar Cadastro")
            self.btn_cancelar_edicao.pack_forget()

    def cancelar_edicao(self):
        """Limpa o formulário e retorna ao modo de novo cadastro."""
        campos_para_limpar = ["Nome", "E-mail", "Telefone"]
        
        for campo in campos_para_limpar:
            entry = self.entries.get(campo)
            if entry:
                entry.delete(0, tk.END)
                
        self.modalidade_var.set('CLT')
        self.editando_id = None
        messagebox.showinfo("Cancelado", "Modo de edição cancelado. Pronto para novo cadastro.")
        self.atualizar_titulo_cadastro()
    
    def salvar_ou_atualizar_usuario(self):
        """Coleta dados, valida e salva ou atualiza o usuário."""
        try:
            nome = self.entries["Nome"].get().strip().capitalize()
            email = self.entries["E-mail"].get().strip().lower()
            telefone = self.entries["Telefone"].get().strip() 
            
            salario_str = ''
            if self.user_role == 'Admin' and self.entries.get("Salário (R$)"):
                salario_str = self.entries["Salário (R$)"].get().replace(',', '.').strip()
            else:
                salario_str = '0' 
            
            modalidade = self.modalidade_var.get().strip().upper()
            
            if not all([nome, email, telefone]): 
                messagebox.showerror("Erro de Cadastro", "Campos Nome, E-mail e Telefone são obrigatórios.")
                return

            if self.user_role == 'Admin':
                try:
                    salario = float(salario_str)
                    if salario < 0: raise ValueError
                except ValueError:
                    messagebox.showerror("Erro de Cadastro", "O Salário deve ser um número válido e positivo.")
                    return
            else:
                 salario = 0.0

            novo_dados = {
                'nome': nome,
                'email': email,
                'telefone': telefone,
                'modalidade': modalidade,
                'salario': salario
            }
            
            if self.editando_id is None:
                proximo_id = 1
                if self.dados_usuarios:
                    proximo_id = max(user.get('id', 0) for user in self.dados_usuarios) + 1
                
                novo_dados['id'] = proximo_id
                novo_dados['historico_ausencias'] = [] 
                self.dados_usuarios.append(novo_dados)
                messagebox.showinfo("Sucesso", f"Usuário {nome} (ID: {proximo_id}) cadastrado com sucesso!")
            else:
                for user in self.dados_usuarios:
                    if user.get('id') == self.editando_id:
                        user.update(novo_dados)
                        messagebox.showinfo("Sucesso", f"Usuário ID: {self.editando_id} atualizado com sucesso!")
                        break
                self.editando_id = None
                self.atualizar_titulo_cadastro()
            
            salvar_dados(self.dados_usuarios)
            self.cancelar_edicao()
            self.atualizar_todas_as_listas()

        except Exception as e:
            messagebox.showerror("Erro Inesperado", f"Ocorreu um erro ao salvar/atualizar: {e}")

    def atualizar_combo_usuarios_ausencias(self, event=None):
        """Atualiza a Combobox de seleção de usuário no módulo de ausências."""
        nomes = [f"ID: {user['id']} - {user['nome']}" for user in self.dados_usuarios if user.get('id')]
        self.combo_ausencias_user.configure(values=nomes)
        self.combo_ausencias_user.set('')
        self.treeview_ausencias.delete(*self.treeview_ausencias.get_children()) 

    def registrar_ausencia(self):
        """Registra uma nova ausência para o colaborador selecionado."""
        selecao = self.combo_ausencias_user.get()
        data = self.ausencia_data.get()
        tipo = self.ausencia_tipo.get().upper()
        obs = self.ausencia_obs.get()

        if not selecao or not data or not tipo:
            messagebox.showerror("Erro", "Selecione o colaborador e preencha Data e Tipo.")
            return

        try:
            datetime.strptime(data, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("Erro", "Formato de Data inválido. Use YYYY-MM-DD.")
            return

        user_id = int(selecao.split(':')[1].split('-')[0].strip())
        
        for user in self.dados_usuarios:
            if user.get('id') == user_id:
                if 'historico_ausencias' not in user:
                    user['historico_ausencias'] = []
                    
                user['historico_ausencias'].append({
                    'data': data,
                    'tipo': tipo,
                    'observacao': obs,
                    'registro': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                salvar_dados(self.dados_usuarios)
                messagebox.showinfo("Sucesso", f"Ausência registrada para {user['nome']}.")
                self.atualizar_historico_ausencias()
                
                self.ausencia_data.delete(0, tk.END)
                self.ausencia_tipo.delete(0, tk.END)
                self.ausencia_obs.delete(0, tk.END)
                return

    def atualizar_historico_ausencias(self, event=None):
        """Exibe o histórico de ausências do colaborador selecionado."""
        selecao = self.combo_ausencias_user.get()
        self.treeview_ausencias.delete(*self.treeview_ausencias.get_children())
        
        if not selecao:
            return

        user_id = int(selecao.split(':')[1].split('-')[0].strip())
        
        usuario = next((user for user in self.dados_usuarios if user.get('id') == user_id), None)
        
        if usuario and 'historico_ausencias' in usuario:
            for ausencia in usuario['historico_ausencias']:
                valores = (
                    ausencia['data'],
                    ausencia['tipo'],
                    ausencia['observacao']
                )
                self.treeview_ausencias.insert('', tk.END, values=valores)

    def exportar_dados_csv(self):
        """Permite ao Admin exportar todos os dados para um arquivo CSV."""
        if self.user_role != 'Admin':
            messagebox.showerror("Acesso Negado", "Apenas administradores podem exportar dados.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Arquivos CSV", "*.csv")],
            title="Salvar Dados como CSV",
            initialfile="export_erp_data.csv"
        )

        if not filepath:
            return

        try:
            campos = ['id', 'nome', 'email', 'telefone', 'modalidade', 'salario', 'historico_ausencias']
            
            with open(filepath, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=campos, extrasaction='ignore', delimiter=';')
                
                writer.writeheader()
                for user in self.dados_usuarios:
                    temp_user = user.copy()
                    if 'historico_ausencias' in temp_user:
                        temp_user['historico_ausencias'] = json.dumps(temp_user['historico_ausencias'], ensure_ascii=False)
                    
                    writer.writerow(temp_user)
            
            messagebox.showinfo("Exportação Concluída", f"Dados exportados com sucesso para:\n{filepath}")

        except Exception as e:
            messagebox.showerror("Erro de Exportação", f"Não foi possível exportar os dados:\n{e}")

    def atualizar_todas_as_listas(self):
        """Limpa e preenche todos os Treeviews com os dados mais recentes."""
        self.dados_usuarios = carregar_dados()

        if self.treeview_geral:
            self.treeview_geral.delete(*self.treeview_geral.get_children())
            for tree in self.treeviews_modalidade.values():
                tree.delete(*tree.get_children())
            
            for user in self.dados_usuarios:
                salario = user.get('salario', 0.0)
                salario_formatado = f"R$ {salario:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')
                
                valores_gerais = [
                    user.get('id', 'N/A'),
                    user.get('nome', 'N/A'),
                    user.get('modalidade', 'N/A'),
                    salario_formatado if self.user_role == 'Admin' else '***', 
                    user.get('email', 'N/A'),
                    user.get('telefone', 'N/A') 
                ]
                
                if self.user_role != 'Admin':
                     valores_gerais.pop(3) 

                self.treeview_geral.insert('', tk.END, values=valores_gerais)

                modalidade = user.get('modalidade', 'OUTRO')
                if modalidade in self.treeviews_modalidade:
                    
                    valores_modalidade = [
                        user.get('id', 'N/A'),
                        user.get('nome', 'N/A'),
                        salario_formatado if self.user_role == 'Admin' else '***',
                        user.get('email', 'N/A'),
                        user.get('telefone', 'N/A') 
                    ]

                    if self.user_role != 'Admin':
                         valores_modalidade.pop(2) 

                    self.treeviews_modalidade[modalidade].insert('', tk.END, values=valores_modalidade)
            
    def atualizar_relatorios(self):
        """Recalcula e exibe os relatórios de BI na aba (Apenas Admin)."""
        if self.user_role != 'Admin': return
        
        # O CTkTextbox usa o método delete/insert, mas com o 'get' e 'insert' padrão do Tkinter
        self.relatorio_texto.delete('1.0', 'end') 
        
        dados = self.dados_usuarios
        dados_validos = [user for user in dados if user.get('salario') is not None and user.get('modalidade')]
        
        if not dados_validos:
            self.relatorio_texto.insert('1.0', "Dados insuficientes para gerar relatórios.")
            return

        total_salarios = 0
        analise_modalidade = defaultdict(lambda: {'soma': 0, 'count': 0})
        total_usuarios_validos = len(dados_validos)
        
        for user in dados_validos:
            salario = user['salario']
            modalidade = user['modalidade']
            total_salarios += salario
            analise_modalidade[modalidade]['soma'] += salario
            analise_modalidade[modalidade]['count'] += 1
            
        salario_medio_geral = total_salarios / total_usuarios_validos if total_usuarios_validos > 0 else 0
        
        total_salarios_f = f"R$ {total_salarios:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')
        salario_medio_geral_f = f"R$ {salario_medio_geral:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')

        report = "--- RELATÓRIOS ANALÍTICOS (BI) ---\n"
        report += f"\nTotal de Usuários na Análise: {total_usuarios_validos}"
        report += f"\nFolha de Pagamento Total: {total_salarios_f}"
        report += f"\nSalário Médio Geral: {salario_medio_geral_f}"
        report += "\n\n" + "="*40 + "\n"
        
        report += "--- Análise por Modalidade ---\n"
        for mod, data in analise_modalidade.items():
            media = data['soma'] / data['count'] if data['count'] > 0 else 0
            media_f = f"R$ {media:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')
            
            report += f"\n| Modalidade: {mod} ({data['count']} usuários)"
            report += f"\n|   > Salário Médio: {media_f}"
        
        self.relatorio_texto.insert('1.0', report)


    def toggle_action_buttons(self, event):
        """Habilita ou desabilita os botões de ação com base na seleção do Treeview."""
        selecionados = self.treeview_geral.selection()
        if selecionados:
            self.btn_editar.configure(state='normal')
            self.btn_deletar.configure(state='normal')
        else:
            self.btn_editar.configure(state='disabled')
            self.btn_deletar.configure(state='disabled')

    def abrir_edicao_selecionada(self):
        """Carrega os dados do usuário selecionado no formulário de cadastro/edição."""
        selecionados = self.treeview_geral.selection()
        if not selecionados: return

        item_id_treeview = selecionados[0]
        user_id_str = self.treeview_geral.item(item_id_treeview, 'values')[0]
        user_id = int(user_id_str)

        usuario_para_editar = next((user for user in self.dados_usuarios if user.get('id') == user_id), None)

        if usuario_para_editar:
            self.cancelar_edicao()
            
            self.entries["Nome"].insert(0, usuario_para_editar['nome'])
            self.entries["E-mail"].insert(0, usuario_para_editar['email'])
            self.entries["Telefone"].insert(0, usuario_para_editar['telefone'])
            
            if self.user_role == 'Admin' and self.entries.get("Salário (R$)"):
                 self.entries["Salário (R$)"].insert(0, str(usuario_para_editar.get('salario', 0.0)))
                 
            self.modalidade_var.set(usuario_para_editar['modalidade'])

            self.editando_id = user_id
            self.atualizar_titulo_cadastro()
            self.notebook.select(0)

    def deletar_usuario_selecionado(self):
        """Remove o usuário selecionado após confirmação."""
        selecionados = self.treeview_geral.selection()
        if not selecionados: return

        item_id_treeview = selecionados[0]
        user_id_str = self.treeview_geral.item(item_id_treeview, 'values')[0]
        user_id = int(user_id_str)
        user_nome = self.treeview_geral.item(item_id_treeview, 'values')[1]

        if messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja DELETAR o usuário:\n{user_nome} (ID: {user_id})?"):
            self.dados_usuarios = [user for user in self.dados_usuarios if user.get('id') != user_id]
            
            salvar_dados(self.dados_usuarios)
            self.atualizar_todas_as_listas()
            messagebox.showinfo("Sucesso", f"Usuário {user_nome} (ID: {user_id}) deletado.")
            self.toggle_action_buttons(None)

if __name__ == "__main__":
    root = ctk.CTk()
    login_app = LoginApp(root)
    root.mainloop()
