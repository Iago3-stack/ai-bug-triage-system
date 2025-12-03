import flet as ft
from datetime import datetime
import copy
import time

# Classe para representar um item de atividade na lista
class ActivityItem(ft.Container):
    def __init__(self, activity_id, activity_data, app):
        super().__init__()
        self.activity_id = activity_id
        self.activity_data = activity_data
        self.app = app

        # Configuração do Container
        self.content=ft.Row(
            controls=[
                ft.Text(self.activity_data["texto"], expand=True),
            ]
        )
        self.bgcolor=self.get_status_color(self.activity_data["status"])
        self.padding=10
        self.border_radius=5
        self.on_click=self.select_clicked

    def get_status_color(self, status):
        """Retorna a cor baseada no status da atividade."""
        if status == "Feito":
            return ft.Colors.GREEN_200
        elif status == "Não Feito":
            return ft.Colors.RED_200
        return ft.Colors.BLUE_GREY_200

    def select_clicked(self, e):
        """Seleciona a atividade ao ser clicada."""
        self.app.select_activity(self)

# Classe principal da aplicação
class TaskManager(ft.Row):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.atividades = {}
        self.activity_id_counter = 0
        self.selected_activity = None
        
        # --- Coluna da Esquerda (Lista e Adicionar) ---
        self.new_activity = ft.TextField(hint_text="Nova atividade", expand=True, on_submit=self.add_clicked)
        self.activity_list = ft.ListView(expand=True, spacing=5)
        self.left_panel = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        self.new_activity,
                        ft.IconButton(ft.Icons.ADD, on_click=self.add_clicked, tooltip="Adicionar"),
                    ]
                ),
                ft.Text("Atividades", size=20),
                self.activity_list,
            ],
            expand=True,
            spacing=10
        )

        # --- Coluna da Direita (Detalhes) ---
        self.edit_activity_text = ft.TextField(label="Editar Atividade")
        self.date_label = ft.Text()
        self.status_radio = ft.RadioGroup(
            content=ft.Row(
                controls=[
                    ft.Radio(value="Pendente", label="Pendente"),
                    ft.Radio(value="Feito", label="Feito"),
                    ft.Radio(value="Não Feito", label="Não Feito"),
                ]
            ),
            on_change=self.status_changed
        )
        self.save_button = ft.ElevatedButton("Salvar Alterações", on_click=self.save_clicked)
        self.delete_button = ft.ElevatedButton("Excluir Atividade", color="white", bgcolor=ft.Colors.RED_700, on_click=self.delete_clicked)
        
        self.right_panel_content = ft.Column(
            controls=[
                ft.Text("Detalhes da Atividade", size=20),
                self.edit_activity_text,
                self.date_label,
                ft.Text("Status:"),
                self.status_radio,
                self.save_button,
                self.delete_button,
            ],
            expand=True,
            visible=False, # Começa invisível
            spacing=10
        )
        
        self.right_panel = ft.Container(
            content=self.right_panel_content,
            padding=10,
            expand=True
        )

        # Configuração do Row principal
        self.controls=[
            ft.Container(
                content=self.left_panel, 
                width=300, 
                padding=10, 
                border=ft.border.only(right=ft.border.BorderSide(1, ft.Colors.BLACK12))
            ),
            self.right_panel,
        ]
        self.expand=True

    def add_clicked(self, e):
        texto = self.new_activity.value.strip()
        if not texto:
            return

        self.activity_id_counter += 1
        activity_id = self.activity_id_counter
        
        nova_atividade = {
            "texto": texto,
            "data": datetime.now().strftime("%d/%m/%Y"),
            "status": "Pendente",
        }
        
        self.atividades[activity_id] = nova_atividade
        self.save_atividades()
        self.new_activity.value = ""
        self.update_activity_list()
        self.new_activity.focus()
        self.page.update()

    def update_activity_list(self):
        self.activity_list.controls.clear()
        for activity_id, activity_data in sorted(self.atividades.items()):
            self.activity_list.controls.append(ActivityItem(activity_id, activity_data, self))
        self.page.update()

    def select_activity(self, activity_control: ActivityItem):
        # Desseleciona o item anterior se houver
        if self.selected_activity:
            self.selected_activity.border = None
        
        self.selected_activity = activity_control
        self.selected_activity.border = ft.border.all(2, ft.Colors.PRIMARY) # Destaque visual
        
        self.edit_activity_text.value = activity_control.activity_data["texto"]
        self.date_label.value = f"Data: {activity_control.activity_data['data']}"
        self.status_radio.value = activity_control.activity_data["status"]
        self.right_panel_content.visible = True
        self.page.update()

    def save_clicked(self, e):
        if self.selected_activity:
            activity_id = self.selected_activity.activity_id
            self.atividades[activity_id]["texto"] = self.edit_activity_text.value
            self.atividades[activity_id]["status"] = self.status_radio.value
            self.save_atividades()
            self.update_activity_list()
            self.right_panel_content.visible = False
            self.selected_activity = None # Limpa a seleção
            self.page.update()

    def status_changed(self, e):
        if self.selected_activity:
            self.selected_activity.bgcolor = self.selected_activity.get_status_color(e.control.value)
            self.page.update()

    def delete_clicked(self, e):
        if self.selected_activity:
            del self.atividades[self.selected_activity.activity_id]
            self.save_atividades()
            self.right_panel_content.visible = False
            self.selected_activity = None # Limpa a seleção
            self.update_activity_list()

    def save_atividades(self):
        pass

def main(page: ft.Page):
    page.title = "IAgo - 🗃️ Gerenciador de Atividades"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    
    # --- Lógica da Tela de Splash ---
    page.add(
        ft.Column(
            [
                ft.Text("Bem-vindo ao IAgo...🌏!", size=30, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                ft.ProgressRing(),
                ft.Text("Carregando..."),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True
        )
    )
    page.update()
    time.sleep(2.5) # Atraso para simular carregamento
    page.clean() # Limpa a tela de splash

    # --- Função para alternar o tema ---
    def change_theme(e):
        page.theme_mode = (
            ft.ThemeMode.DARK
            if page.theme_mode == ft.ThemeMode.LIGHT
            else ft.ThemeMode.LIGHT
        )
        theme_icon.name = (
            ft.Icons.WB_SUNNY_OUTLINED
            if page.theme_mode == ft.ThemeMode.LIGHT
            else ft.Icons.BRIGHTNESS_3_OUTLINED
        )
        page.update()

    theme_icon = ft.IconButton(
        ft.Icons.BRIGHTNESS_3_OUTLINED,
        tooltip="Mudar tema",
        on_click=change_theme,
    )

    # --- Configuração da AppBar ---
    page.appbar = ft.AppBar(
        leading=ft.Icon(ft.Icons.TASK_ALT_ROUNDED),
        leading_width=40,
        title=ft.Text("IAgo - Gerenciador de Atividades"),
        center_title=False,
        bgcolor="surface_variant",
        actions=[theme_icon],
    )
    
    # Define o tema inicial
    page.theme_mode = ft.ThemeMode.DARK
    
    # Cria e adiciona a instância da aplicação à página
    app = TaskManager(page)
    page.add(app)
    page.update()

# Inicia a aplicação Flet
ft.app(target=main)