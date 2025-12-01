import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from collections import defaultdict
import uuid

# --- CONFIGURAÇÕES DE DADOS (Persistência JSON) ---
NOME_ARQUIVO = 'dados_usuarios.json'

def carregar_dados():
    """Carrega os dados de usuários do arquivo JSON. Retorna lista vazia se falhar."""
    if os.path.exists(NOME_ARQUIVO):
        try:
            with open(NOME_ARQUIVO, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            # Arquivo existe mas está vazio ou corrompido, retorna lista vazia
            return []
    return []

def salvar_dados(dados):
    """Salva a lista completa de dados no arquivo JSON."""
    with open(NOME_ARQUIVO, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

# ----------------------------------------------------------------------
# CLASSE PRINCIPAL DO APLICATIVO TKINTER
# ----------------------------------------------------------------------

class ERPApp:
    def __init__(self, master):
        self.master = master
        master.title("AI ERP - Sistema de Gerenciamento")
        master.geometry("1000x650")

        self.dados_usuarios = carregar_dados()
        
        # VARIÁVEIS DE ESTADO (CORREÇÃO DE ORDEM DE INICIALIZAÇÃO!)
        # Criadas ANTES de qualquer função que as utilize ser chamada
        self.treeview_geral = None
        self.treeviews_modalidade = {} 
        self.editando_id = None # Armazena o ID do usuário sendo editado (ou None)
        self.entries = {} # Armazena as referências dos campos de entrada
        self.modalidade_var = tk.StringVar(master)
        self.btn_salvar_cadastro = None
        self.btn_cancelar_edicao = None

        # Configurações do Notebook (Abas)
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(pady=10, padx=10, expand=True, fill="both")

        # Criação das Abas
        self.criar_aba_cadastro()
        self.criar_aba_listagem_geral()
        self.criar_aba_listagem_modalidade('CLT')
        self.criar_aba_listagem_modalidade('PJ')
        self.criar_aba_listagem_modalidade('ESTAGIÁRIO')
        self.criar_aba_relatorios()

        # Ao iniciar, garante que todas as listas exibam os dados
        self.atualizar_todas_as_listas()
        
        # Configura o evento para atualizar a aba de relatórios ao ser clicada
        self.notebook.bind("<<NotebookTabChanged>>", self.ao_mudar_aba)

    def ao_mudar_aba(self, event):
        """Atualiza o conteúdo da aba de Relatórios quando ela é selecionada."""
        tab_index = self.notebook.index(self.notebook.select())
        tab_title = self.notebook.tab(tab_index, "text")
        
        if tab_title == "Relatórios BI":
            self.atualizar_relatorios()

    # --- 1. CRIAÇÃO DA ABA DE CADASTRO ---
    def criar_aba_cadastro(self):
        """Cria e configura o formulário de cadastro/edição."""
        frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(frame, text='Cadastro / Edição')

        # Título principal (será atualizado via método self.atualizar_titulo_cadastro)
        self.titulo_cadastro = ttk.Label(frame, text="Novo Cadastro de Colaborador", font=("Inter", 18, "bold"))
        self.titulo_cadastro.grid(row=0, column=0, columnspan=2, pady=15, sticky='w')

        campos = ["Nome", "E-mail", "Telefone", "Salário (R$)", "Modalidade"]
        
        # Criação das labels e entradas de texto
        for i, campo in enumerate(campos):
            ttk.Label(frame, text=f"{campo}:", font=("Inter", 10)).grid(row=i + 1, column=0, sticky="w", pady=8, padx=5)
            
            if campo == "Modalidade":
                modalidades = ['CLT', 'PJ', 'ESTAGIÁRIO']
                self.modalidade_var.set(modalidades[0]) 
                entry = ttk.OptionMenu(frame, self.modalidade_var, self.modalidade_var.get(), *modalidades)
            else:
                self.entries[campo] = ttk.Entry(frame, width=40, font=("Inter", 10))
                entry = self.entries[campo]
            
            entry.grid(row=i + 1, column=1, sticky="ew", pady=8, padx=5)
        
        # Frame para botões de ação
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=len(campos) + 1, column=0, columnspan=2, pady=20)

        # Botão de Salvar/Atualizar
        self.btn_salvar_cadastro = ttk.Button(button_frame, text="Salvar Cadastro", command=self.salvar_ou_atualizar_usuario)
        self.btn_salvar_cadastro.pack(side='left', padx=10)
        
        # Botão de Cancelar Edição (Inicialmente escondido)
        self.btn_cancelar_edicao = ttk.Button(button_frame, text="Cancelar Edição", command=self.cancelar_edicao)
        # O botão é empacotado/desempacotado para aparecer apenas durante a edição
        
        # Configuração de expansão das colunas
        frame.grid_columnconfigure(1, weight=1)

    def atualizar_titulo_cadastro(self):
        """Atualiza o título da aba de cadastro para indicar se é uma edição ou novo cadastro."""
        if self.editando_id is not None:
            self.titulo_cadastro.config(text=f"Editando Colaborador (ID: {self.editando_id})")
            self.btn_salvar_cadastro.config(text="Salvar Alterações")
            self.btn_cancelar_edicao.pack(side='left', padx=10)
        else:
            self.titulo_cadastro.config(text="Novo Cadastro de Colaborador")
            self.btn_salvar_cadastro.config(text="Salvar Cadastro")
            self.btn_cancelar_edicao.pack_forget()

    def cancelar_edicao(self):
        """Limpa o formulário e retorna ao modo de novo cadastro."""
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self.modalidade_var.set('CLT')
        self.editando_id = None
        self.atualizar_titulo_cadastro()
        messagebox.showinfo("Cancelado", "Modo de edição cancelado. Pronto para novo cadastro.")
    
    # --- 2. CRIAÇÃO DAS ABAS DE LISTAGEM ---
    def criar_aba_listagem_geral(self):
        """Cria a aba de listagem geral para todos os usuários com botões de ação."""
        frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(frame, text='Listagem Geral')

        ttk.Label(frame, text="Todos os Registros", font=("Inter", 14, "bold")).pack(pady=10)

        # Definindo as colunas do Treeview
        colunas = ('ID', 'Nome', 'Modalidade', 'Salário', 'Email', 'Telefone')
        self.treeview_geral = ttk.Treeview(frame, columns=colunas, show='headings')
        
        # Configuração dos cabeçalhos
        for col in colunas:
            self.treeview_geral.heading(col, text=col)
            if col == 'ID':
                 self.treeview_geral.column(col, width=50, stretch=tk.NO, anchor='center')
            else:
                 self.treeview_geral.column(col, width=120, anchor='center')

        self.treeview_geral.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Adicionar Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.treeview_geral.yview)
        self.treeview_geral.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        # Frame para botões de Ação
        action_frame = ttk.Frame(frame)
        action_frame.pack(pady=10, fill='x')

        self.btn_editar = ttk.Button(action_frame, text="Editar Selecionado", command=self.abrir_edicao_selecionada, state='disabled')
        self.btn_editar.pack(side='left', padx=5)

        self.btn_deletar = ttk.Button(action_frame, text="Deletar Selecionado", command=self.deletar_usuario_selecionado, state='disabled')
        self.btn_deletar.pack(side='left', padx=5)
        
        # Vincular evento de seleção para habilitar/desabilitar botões
        self.treeview_geral.bind('<<TreeviewSelect>>', self.toggle_action_buttons)


    def criar_aba_listagem_modalidade(self, modalidade_nome):
        """Cria abas específicas para CLT, PJ, Estagiário com Treeview."""
        frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(frame, text=f'{modalidade_nome}')

        ttk.Label(frame, text=f"Registros de {modalidade_nome}", font=("Inter", 14, "bold")).pack(pady=10)

        colunas = ('ID', 'Nome', 'Salário', 'Email')
        tree = ttk.Treeview(frame, columns=colunas, show='headings')
        
        for col in colunas:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor='center')
            
        tree.pack(fill='both', expand=True)
        
        self.treeviews_modalidade[modalidade_nome] = tree

    # --- 3. CRIAÇÃO DA ABA DE RELATÓRIOS ANALÍTICOS ---
    def criar_aba_relatorios(self):
        """Cria a aba para exibir métricas de BI."""
        self.frame_relatorios = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(self.frame_relatorios, text='Relatórios BI')

        ttk.Label(self.frame_relatorios, text="Análise de Business Intelligence (BI)", font=("Inter", 16, "bold")).pack(pady=15)
        
        # Widget de texto para exibir os resultados do BI
        self.relatorio_texto = tk.Text(self.frame_relatorios, height=20, width=80, font=("Courier", 12))
        self.relatorio_texto.pack(padx=10, pady=10, expand=True, fill='both')


    # ----------------------------------------------------------------------
    # 4. LÓGICA DE AÇÕES (SALVAR/EDITAR/DELETAR)
    # ----------------------------------------------------------------------

    def salvar_ou_atualizar_usuario(self):
        """Coleta dados do formulário, valida e salva ou atualiza o usuário."""
        try:
            nome = self.entries["Nome"].get().strip().capitalize()
            email = self.entries["E-mail"].get().strip().lower()
            telefone = self.entries["Telefone"].get().strip()
            salario_str = self.entries["Salário (R$)"].get().replace(',', '.').strip()
            modalidade = self.modalidade_var.get().strip().upper()
            
            # 1. Validação Básica
            if not all([nome, email, telefone, salario_str]):
                messagebox.showerror("Erro de Cadastro", "Todos os campos devem ser preenchidos.")
                return
            
            if '@' not in email or '.' not in email:
                messagebox.showerror("Erro de Cadastro", "Formato de E-mail inválido.")
                return

            try:
                salario = float(salario_str)
                if salario < 0:
                     messagebox.showerror("Erro de Cadastro", "Salário deve ser positivo.")
                     return
            except ValueError:
                messagebox.showerror("Erro de Cadastro", "O Salário deve ser um número válido.")
                return
            
            # 2. Dados a serem salvos
            novo_dados = {
                'nome': nome,
                'email': email,
                'telefone': telefone,
                'modalidade': modalidade,
                'salario': salario
            }

            # 3. Lógica de Criação ou Atualização
            if self.editando_id is None:
                # MODO CRIAÇÃO
                proximo_id = 1
                if self.dados_usuarios:
                    proximo_id = max(user.get('id', 0) for user in self.dados_usuarios) + 1
                
                novo_dados['id'] = proximo_id
                self.dados_usuarios.append(novo_dados)
                messagebox.showinfo("Sucesso", f"Usuário {nome} (ID: {proximo_id}) cadastrado com sucesso!")
            else:
                # MODO ATUALIZAÇÃO
                for user in self.dados_usuarios:
                    if user.get('id') == self.editando_id:
                        user.update(novo_dados)
                        messagebox.showinfo("Sucesso", f"Usuário ID: {self.editando_id} atualizado com sucesso!")
                        break
                
                # Reseta o modo de edição
                self.editando_id = None
                self.atualizar_titulo_cadastro()
            
            # 4. Finalização
            salvar_dados(self.dados_usuarios)
            self.cancelar_edicao() # Limpa o formulário
            self.atualizar_todas_as_listas()

        except Exception as e:
            messagebox.showerror("Erro Inesperado", f"Ocorreu um erro ao salvar/atualizar: {e}")

    # ----------------------------------------------------------------------
    # 5. LÓGICA DE EDIÇÃO E DELEÇÃO (INTEGRAÇÃO COM TREEVIEW)
    # ----------------------------------------------------------------------

    def toggle_action_buttons(self, event):
        """Habilita ou desabilita os botões de ação com base na seleção do Treeview."""
        selecionados = self.treeview_geral.selection()
        if selecionados:
            self.btn_editar.config(state='normal')
            self.btn_deletar.config(state='normal')
        else:
            self.btn_editar.config(state='disabled')
            self.btn_deletar.config(state='disabled')

    def abrir_edicao_selecionada(self):
        """Carrega os dados do usuário selecionado no formulário de cadastro/edição."""
        selecionados = self.treeview_geral.selection()
        if not selecionados:
            return

        # Pega o primeiro item selecionado
        item_id_treeview = selecionados[0]
        # O ID real do usuário está no primeiro campo ('ID')
        user_id_str = self.treeview_geral.item(item_id_treeview, 'values')[0]
        user_id = int(user_id_str)

        # Encontra o objeto usuário real
        usuario_para_editar = next((user for user in self.dados_usuarios if user.get('id') == user_id), None)

        if usuario_para_editar:
            # 1. Limpa e preenche os campos
            self.cancelar_edicao() # Garante que o estado de edição anterior seja limpo
            
            self.entries["Nome"].insert(0, usuario_para_editar['nome'])
            self.entries["E-mail"].insert(0, usuario_para_editar['email'])
            self.entries["Telefone"].insert(0, usuario_para_editar['telefone'])
            self.entries["Salário (R$)"].insert(0, str(usuario_para_editar['salario']))
            self.modalidade_var.set(usuario_para_editar['modalidade'])

            # 2. Define o estado de edição
            self.editando_id = user_id
            self.atualizar_titulo_cadastro()
            
            # 3. Muda para a aba de Cadastro/Edição
            self.notebook.select(0) # A primeira aba (index 0) é a de Cadastro

    def deletar_usuario_selecionado(self):
        """Remove o usuário selecionado após confirmação."""
        selecionados = self.treeview_geral.selection()
        if not selecionados:
            return

        item_id_treeview = selecionados[0]
        user_id_str = self.treeview_geral.item(item_id_treeview, 'values')[0]
        user_id = int(user_id_str)
        user_nome = self.treeview_geral.item(item_id_treeview, 'values')[1]

        # Janela de confirmação
        if messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja DELETAR o usuário:\n{user_nome} (ID: {user_id})?"):
            
            # Cria uma nova lista sem o usuário a ser deletado
            self.dados_usuarios = [user for user in self.dados_usuarios if user.get('id') != user_id]
            
            # Salva, atualiza e notifica
            salvar_dados(self.dados_usuarios)
            self.atualizar_todas_as_listas()
            messagebox.showinfo("Sucesso", f"Usuário {user_nome} (ID: {user_id}) deletado.")
            self.toggle_action_buttons(None) # Desabilita botões de ação

    # ----------------------------------------------------------------------
    # 6. LÓGICA DE ATUALIZAÇÃO DE LISTAS E RELATÓRIOS
    # ----------------------------------------------------------------------

    def atualizar_todas_as_listas(self):
        """Limpa e preenche todos os Treeviews com os dados mais recentes."""
        self.dados_usuarios = carregar_dados()

        # 1. Limpa Treeviews
        self.treeview_geral.delete(*self.treeview_geral.get_children())
        for tree in self.treeviews_modalidade.values():
            tree.delete(*tree.get_children())
        
        # 2. Preenche os Treeviews
        for user in self.dados_usuarios:
            salario_formatado = f"R$ {user.get('salario', 0.0):,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')
            
            # Preenche Lista Geral
            valores_gerais = (
                user.get('id', 'N/A'),
                user.get('nome', 'N/A'),
                user.get('modalidade', 'N/A'),
                salario_formatado,
                user.get('email', 'N/A'),
                user.get('telefone', 'N/A')
            )
            self.treeview_geral.insert('', tk.END, values=valores_gerais)

            # Preenche Listas por Modalidade
            modalidade = user.get('modalidade', 'OUTRO')
            if modalidade in self.treeviews_modalidade:
                valores_modalidade = (
                    user.get('id', 'N/A'),
                    user.get('nome', 'N/A'),
                    salario_formatado,
                    user.get('email', 'N/A')
                )
                self.treeviews_modalidade[modalidade].insert('', tk.END, values=valores_modalidade)
            
    def atualizar_relatorios(self):
        """Recalcula e exibe os relatórios de BI na aba."""
        
        self.relatorio_texto.delete('1.0', tk.END) 
        
        dados = self.dados_usuarios
        dados_validos = [user for user in dados if user.get('salario') is not None and user.get('modalidade')]
        
        if not dados_validos:
            self.relatorio_texto.insert(tk.END, "Dados insuficientes para gerar relatórios.")
            return

        total_salarios = 0
        analise_modalidade = defaultdict(lambda: {'soma': 0, 'count': 0})
        total_usuarios_validos = len(dados_validos)
        
        # 1. Coleta de dados e soma total
        for user in dados_validos:
            salario = user['salario']
            modalidade = user['modalidade']
            
            total_salarios += salario
            analise_modalidade[modalidade]['soma'] += salario
            analise_modalidade[modalidade]['count'] += 1
            
        # 2. Geração de Métricas Globais
        salario_medio_geral = total_salarios / total_usuarios_validos if total_usuarios_validos > 0 else 0
        
        # Formatação
        total_salarios_f = f"R$ {total_salarios:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')
        salario_medio_geral_f = f"R$ {salario_medio_geral:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')

        report = "--- RELATÓRIOS ANALÍTICOS (BI) ---\n"
        report += f"\nTotal de Usuários na Análise: {total_usuarios_validos}"
        report += f"\nFolha de Pagamento Total: {total_salarios_f}"
        report += f"\nSalário Médio Geral: {salario_medio_geral_f}"
        report += "\n\n" + "="*40 + "\n"
        
        # 3. Geração de Métricas por Modalidade
        report += "--- Análise por Modalidade ---\n"
        for mod, data in analise_modalidade.items():
            media = data['soma'] / data['count'] if data['count'] > 0 else 0
            media_f = f"R$ {media:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')
            
            report += f"\n| Modalidade: {mod} ({data['count']} usuários)"
            report += f"\n|   > Salário Médio: {media_f}"
        
        self.relatorio_texto.insert(tk.END, report)


if __name__ == "__main__":
    root = tk.Tk()
    app = ERPApp(root)
    root.mainloop()
