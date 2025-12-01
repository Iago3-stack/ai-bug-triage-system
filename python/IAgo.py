import customtkinter as ctk
from datetime import datetime
from tkinter import messagebox

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title('Gerenciador de Atividades')
        self.geometry("800x500")
        self.minsize(700, 400)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        # --- Estrutura de Dados ---
        self.atividades = {}  # Dicionário para guardar as atividades
        self.activity_id_counter = 0 # Contador para IDs únicos
        self.selected_activity_id = None

        # --- Layout Principal (2 colunas) ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # --- Coluna da Esquerda (Lista de Atividades) ---
        self.left_frame = ctk.CTkFrame(self, corner_radius=0)
        self.left_frame.grid(row=0, column=0, sticky="nsew")
        self.left_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self.left_frame, text="Atividades", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 10))
        self.activity_list_frame = ctk.CTkScrollableFrame(self.left_frame, fg_color="transparent")
        self.activity_list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # --- Coluna da Direita (Painel de Detalhes e Edição) ---
        self.right_frame = ctk.CTkFrame(self)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.right_frame.grid_rowconfigure(5, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_columnconfigure(1, weight=1)

        # --- Widgets do Painel Direito (inicialmente vazios) ---
        ctk.CTkLabel(self.right_frame, text="Detalhes da Atividade", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=2, pady=(10, 20))
        
        self.entry_edit_activity = ctk.CTkEntry(self.right_frame, placeholder_text="Selecione uma atividade para editar")
        self.entry_edit_activity.grid(row=1, column=0, columnspan=2, padx=20, pady=5, sticky="ew")

        self.label_date = ctk.CTkLabel(self.right_frame, text="Data: -")
        self.label_date.grid(row=2, column=0, columnspan=2, padx=20, pady=5, sticky="w")
        
        self.label_status_title = ctk.CTkLabel(self.right_frame, text="Status:")
        self.label_status_title.grid(row=3, column=0, padx=(20, 5), pady=10, sticky="w")
        
        self.label_status = ctk.CTkLabel(self.right_frame, text="-", font=ctk.CTkFont(size=14, weight="bold"))
        self.label_status.grid(row=3, column=1, padx=(5, 20), pady=10, sticky="w")
        
        # --- Radio Buttons para Status ---
        self.status_var = ctk.StringVar(value="Pendente")
        
        self.radio_button_done = ctk.CTkRadioButton(self.right_frame, text="Feito", variable=self.status_var, value="Feito", command=self.update_status_from_radio)
        self.radio_button_done.grid(row=4, column=0, padx=20, pady=10, sticky="w")

        self.radio_button_not_done = ctk.CTkRadioButton(self.right_frame, text="Não Feito", variable=self.status_var, value="Não Feito", command=self.update_status_from_radio)
        self.radio_button_not_done.grid(row=4, column=1, padx=20, pady=10, sticky="w")

        # Botões de Ação
        self.button_save = ctk.CTkButton(self.right_frame, text="Salvar Alterações", command=self.save_edit)
        self.button_save.grid(row=6, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        
        self.button_delete = ctk.CTkButton(self.right_frame, text="Excluir Atividade", fg_color="#D32F2F", hover_color="#B71C1C", command=self.delete_activity)
        self.button_delete.grid(row=7, column=0, columnspan=2, padx=20, pady=(10,20), sticky="ew")

        # --- Adicionar nova atividade (no frame esquerdo, abaixo da lista) ---
        self.add_frame = ctk.CTkFrame(self.left_frame)
        self.add_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        self.add_frame.grid_columnconfigure(0, weight=1)

        self.entry_new_activity = ctk.CTkEntry(self.add_frame, placeholder_text="Nova atividade")
        self.entry_new_activity.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="ew")
        self.entry_new_activity.bind("<Return>", self.add_activity) # Adicionar com Enter

        self.button_add = ctk.CTkButton(self.add_frame, text="Adicionar", width=80, command=self.add_activity)
        self.button_add.grid(row=0, column=1, pady=10)

        self.update_detail_panel_visibility()

    def add_activity(self, event=None):
        texto = self.entry_new_activity.get().strip()
        if not texto:
            return

        self.activity_id_counter += 1
        activity_id = self.activity_id_counter
        
        data_criacao = datetime.now().strftime("%d/%m/%Y")
        
        nova_atividade = {
            "texto": texto,
            "data": data_criacao,
            "status": "Pendente",
            "widget": None 
        }
        
        self.atividades[activity_id] = nova_atividade
        self.entry_new_activity.delete(0, 'end')
        self.render_activity_list()

    def render_activity_list(self):
        # Limpa a lista antiga
        for widget in self.activity_list_frame.winfo_children():
            widget.destroy()

        # Recria a lista com os dados atualizados
        for activity_id, atividade in self.atividades.items():
            btn = ctk.CTkButton(
                self.activity_list_frame, 
                text=atividade["texto"],
                fg_color="blue" if atividade["status"] == "Pendente" else ("green" if atividade["status"] == "Feito" else "red"),
                hover_color=None,
                anchor="w",
                command=lambda id=activity_id: self.select_activity(id)
            )
            btn.pack(fill="x", padx=5, pady=2)
            self.atividades[activity_id]["widget"] = btn

    def select_activity(self, activity_id):
        self.selected_activity_id = activity_id
        atividade_selecionada = self.atividades[activity_id]

        self.entry_edit_activity.delete(0, 'end')
        self.entry_edit_activity.insert(0, atividade_selecionada["texto"])

        self.label_date.configure(text=f'Data: {atividade_selecionada["data"]}')
        
        # Atualiza a variável dos radio buttons e o label de status
        self.status_var.set(atividade_selecionada["status"])
        self.update_status_label(atividade_selecionada["status"])
        
        self.update_detail_panel_visibility()

    def save_edit(self):
        if self.selected_activity_id is None:
            return
        
        novo_texto = self.entry_edit_activity.get().strip()
        if not novo_texto:
            messagebox.showwarning("Campo Vazio", "O nome da atividade não pode estar vazio.")
            return

        self.atividades[self.selected_activity_id]["texto"] = novo_texto
        
        # Chamar render_activity_list() para garantir que a cor do status e o texto sejam atualizados.
        self.render_activity_list()

        # Adiciona a mensagem de sucesso, como solicitado.
        messagebox.showinfo("Sucesso", "Alterações salvas com sucesso!")

    def update_status_from_radio(self):
        if self.selected_activity_id is None:
            return
        
        novo_status = self.status_var.get()
        self.atividades[self.selected_activity_id]["status"] = novo_status
        self.update_status_label(novo_status)
    
    def update_status_label(self, status):
        if status == "Feito":
            self.label_status.configure(text="✓ Feito", text_color="#2E7D32") # Verde
        elif status == "Não Feito":
            self.label_status.configure(text="✗ Não Feito", text_color="#D32F2F") # Vermelho
        else:
            self.status_var.set("Pendente")
            self.label_status.configure(text="Pendente", text_color="gray")

    def delete_activity(self):
        if self.selected_activity_id is None:
            return

        # Remove do dicionário de dados
        del self.atividades[self.selected_activity_id]
        
        # Limpa o painel de detalhes
        self.selected_activity_id = None
        self.entry_edit_activity.delete(0, 'end')
        self.entry_edit_activity.configure(placeholder_text="Selecione uma atividade para editar")
        self.label_date.configure(text="Data: -")
        self.update_status_label("Pendente")
        
        self.update_detail_panel_visibility()
        self.render_activity_list()

    def update_detail_panel_visibility(self):
        # Esconde ou mostra os widgets do painel de detalhes
        if self.selected_activity_id is None:
            # Limpa a seleção dos radio buttons
            self.status_var.set("Pendente")
            for widget in self.right_frame.winfo_children():
                if isinstance(widget, ctk.CTkLabel) and "Detalhes" in widget.cget("text"):
                    continue
                widget.grid_remove()
        else:
            for widget in self.right_frame.winfo_children():
                widget.grid()

if __name__ == "__main__":
    app = App()
    app.mainloop()
