import flet as ft
from datetime import datetime, timedelta
import json
import os
import csv
import time
from collections import defaultdict

# ==================== CORES DINÂMICAS ====================

def get_dynamic_colors(page):
    """Retorna cores que se adaptam ao tema atual com tons equilibrados."""
    is_dark = page.theme_mode == ft.ThemeMode.DARK
    return {
        "header_bg": "#1e1e1e" if is_dark else "#ffffff",
        "search_bg": "#2d2d2d" if is_dark else "#f5f5f5",
        "container_bg": "#121212" if is_dark else "#fafafa",
        "card_bg": "#252525" if is_dark else "#ffffff",
        "text_primary": "#ffffff" if is_dark else "#1a1a1a",
        "text_secondary": "#b3b3b3" if is_dark else "#666666",
        "divider": "#3a3a3a" if is_dark else "#e0e0e0",
        "accent": "#2196F3",
        "border": "#404040" if is_dark else "#e0e0e0",
    }

# ==================== MODELOS DE DADOS ====================

class ActivityItem(ft.Container):
    def __init__(self, activity_id, activity_data, app):
        super().__init__()
        self.activity_id = activity_id
        self.activity_data = activity_data
        self.app = app

        # Exibir atividade com informações completas de forma compacta
        priority_icon = self.get_priority_icon(activity_data.get("prioridade", "Baixa"))
        status_icon = self.get_status_icon(activity_data["status"])
        
        # Calcular dias até vencimento
        vencimento_info = ""
        if activity_data.get("data_vencimento"):
            try:
                venc_date = datetime.strptime(activity_data["data_vencimento"], "%d/%m/%Y")
                dias_diff = (venc_date - datetime.now()).days
                if dias_diff < 0:
                    vencimento_info = f" ⏰ Atrasado ({abs(dias_diff)}d)"
                elif dias_diff == 0:
                    vencimento_info = " ⏰ Vence hoje!"
                elif dias_diff <= 3:
                    vencimento_info = f" ⏰ {dias_diff}d"
            except:
                pass
        
        self.content = ft.Row(
            controls=[
                ft.Text(priority_icon, size=14),
                ft.Text(status_icon, size=14),
                ft.Column(
                    controls=[
                        ft.Text(
                            self.activity_data["texto"][:50],
                            size=13,
                            weight="w500",
                            expand=True,
                            color="white" if self.app.page.theme_mode == ft.ThemeMode.DARK else "black"
                        ),
                        ft.Row(
                            controls=[
                                ft.Text(
                                    self.activity_data.get("categoria", "Sem categoria"),
                                    size=10,
                                    color="#888888" if self.app.page.theme_mode == ft.ThemeMode.DARK else "#666666",
                                ),
                                ft.Text(vencimento_info, size=10, color="red" if "Atrasado" in vencimento_info else "orange"),
                            ],
                            spacing=5
                        ),
                    ],
                    spacing=2,
                    expand=True
                ),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )
        self.bgcolor = self.get_status_color(self.activity_data["status"])
        self.padding = 12
        self.border_radius = 8
        self.shadow = ft.BoxShadow(blur_radius=2, color=ft.Colors.BLACK26)
        self.on_click = self.select_clicked

    def get_status_color(self, status):
        """Retorna a cor baseada no status da atividade."""
        if status == "Feito":
            return "#d4edda"  # Verde muito suave
        elif status == "Não Feito":
            return "#f8d7da"  # Vermelho muito suave
        return "#d1ecf1"  # Azul muito suave

    def get_priority_icon(self, priority):
        """Retorna ícone baseado na prioridade."""
        if priority == "Alta":
            return "🔴"
        elif priority == "Média":
            return "🟡"
        return "🟢"
    
    def get_status_icon(self, status):
        """Retorna ícone baseado no status."""
        if status == "Feito":
            return "✅"
        elif status == "Não Feito":
            return "❌"
        return "⏳"

    def select_clicked(self, e):
        """Seleciona a atividade ao ser clicada."""
        self.app.select_activity(self)


# ==================== GERENCIADOR DE TAREFAS ====================

class TaskManager(ft.Column):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.atividades = {}
        self.activity_id_counter = 0
        self.selected_activity = None
        self.historico = []  # Histórico de alterações
        self.usuario_atual = None
        self.data_file = "atividades.json"
        self.historico_file = "historico.json"
        
        # Carregar dados salvos
        self.load_atividades()
        self.load_historico()
        
        # Obter cores dinâmicas
        colors = get_dynamic_colors(page)
        
        # --- Barra de Busca Compacta ---
        self.search_field = ft.TextField(
            hint_text="🔍 Buscar atividades...",
            expand=True,
            on_change=self.filtrar_atividades,
            prefix_icon=ft.Icons.SEARCH,
            border_radius=10,
            bgcolor=colors["search_bg"],
            border_color=colors["border"],
            focused_border_color=colors["accent"],
        )
        
        self.filter_status = ft.Dropdown(
            label="Status",
            options=[
                ft.dropdown.Option("Todos"),
                ft.dropdown.Option("Pendente"),
                ft.dropdown.Option("Feito"),
                ft.dropdown.Option("Não Feito"),
            ],
            value="Todos",
            on_change=self.filtrar_atividades,
            width=150
        )
        
        self.filter_priority = ft.Dropdown(
            label="Prioridade",
            options=[
                ft.dropdown.Option("Todos"),
                ft.dropdown.Option("Alta"),
                ft.dropdown.Option("Média"),
                ft.dropdown.Option("Baixa"),
            ],
            value="Todos",
            on_change=self.filtrar_atividades,
            width=150
        )
        
        self.filter_category = ft.Dropdown(
            label="Categoria",
            options=[ft.dropdown.Option("Todos")],
            value="Todos",
            on_change=self.filtrar_atividades,
            width=150
        )
        
        # Barra de filtros
        filters_row = ft.Row(
            controls=[
                self.filter_status,
                self.filter_priority,
                self.filter_category,
            ],
            spacing=5,
            scroll=ft.ScrollMode.AUTO
        )
        
        # --- Seção de Novo Item ---
        self.new_activity = ft.TextField(
            hint_text="Escreva uma nova atividade aqui...",
            expand=True,
            on_submit=self.add_clicked,
            min_lines=2,
            max_lines=3,
            bgcolor=colors["search_bg"],
            border_color=colors["border"],
            focused_border_color=colors["accent"],
        )
        
        add_button = ft.IconButton(
            ft.Icons.ADD_CIRCLE,
            icon_size=32,
            on_click=self.add_clicked,
            tooltip="Adicionar atividade"
        )
        
        new_activity_container = ft.Container(
            content=ft.Row(
                controls=[self.new_activity, add_button],
                vertical_alignment=ft.CrossAxisAlignment.START
            ),
            padding=15,
            bgcolor=colors["card_bg"],
            border_radius=12,
            border=ft.border.all(1, colors["border"]),
        )
        
        # --- Lista de Atividades ---
        self.activity_list = ft.ListView(
            expand=True,
            spacing=8,
            padding=0
        )
        
        # --- Painel de Edição (Modal) ---
        self.edit_activity_text = ft.TextField(
            label="Atividade",
            multiline=True,
            min_lines=2,
            bgcolor=colors["search_bg"],
            label_style=ft.TextStyle(color=colors["text_secondary"]),
        )
        self.date_label = ft.Text(color=colors["text_primary"])
        self.due_date_field = ft.TextField(
            label="Data de Vencimento (DD/MM/YYYY)",
            bgcolor=colors["search_bg"],
            label_style=ft.TextStyle(color=colors["text_secondary"]),
        )
        
        self.priority_radio = ft.RadioGroup(
            content=ft.Row(
                controls=[
                    ft.Radio(value="Alta", label="🔴 Alta"),
                    ft.Radio(value="Média", label="🟡 Média"),
                    ft.Radio(value="Baixa", label="🟢 Baixa"),
                ]
            )
        )
        
        self.status_radio = ft.RadioGroup(
            content=ft.Row(
                controls=[
                    ft.Radio(value="Pendente", label="⏳ Pendente"),
                    ft.Radio(value="Feito", label="✅ Feito"),
                    ft.Radio(value="Não Feito", label="❌ Não Feito"),
                ]
            ),
            on_change=self.status_changed
        )
        
        self.category_field = ft.TextField(
            label="Categoria",
            bgcolor=colors["search_bg"],
            label_style=ft.TextStyle(color=colors["text_secondary"]),
        )
        self.tags_field = ft.TextField(
            label="Tags (separadas por vírgula)",
            bgcolor=colors["search_bg"],
            label_style=ft.TextStyle(color=colors["text_secondary"]),
        )
        
        self.save_button = ft.ElevatedButton(
            "💾 Salvar",
            on_click=self.save_clicked,
            expand=True
        )
        self.delete_button = ft.ElevatedButton(
            "🗑️ Deletar",
            color="white",
            bgcolor=ft.Colors.RED_700,
            on_click=self.delete_clicked,
            expand=True
        )
        self.history_button = ft.IconButton(
            ft.Icons.HISTORY,
            tooltip="Ver histórico",
            on_click=self.show_history
        )
        self.export_button = ft.IconButton(
            ft.Icons.DOWNLOAD,
            tooltip="Exportar CSV",
            on_click=self.export_csv
        )
        
        self.edit_panel = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("Editar Atividade", size=18, weight="bold", color=colors["text_primary"]),
                            ft.IconButton(
                                ft.Icons.CLOSE,
                                on_click=self.close_edit_panel
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Divider(color=colors["divider"]),
                    self.edit_activity_text,
                    self.date_label,
                    ft.Text("📅 Data de Vencimento:", color=colors["text_primary"]),
                    self.due_date_field,
                    ft.Text("⭐ Prioridade:", color=colors["text_primary"]),
                    self.priority_radio,
                    ft.Text("📌 Status:", color=colors["text_primary"]),
                    self.status_radio,
                    ft.Text("🏷️ Categoria:", color=colors["text_primary"]),
                    self.category_field,
                    ft.Text("🏷️ Tags:", color=colors["text_primary"]),
                    self.tags_field,
                    ft.Row(
                        controls=[
                            self.save_button,
                            self.delete_button,
                        ],
                        spacing=10
                    ),
                    ft.Row(
                        controls=[
                            self.history_button,
                            self.export_button,
                        ],
                        spacing=10
                    ),
                ],
                spacing=10,
                scroll=ft.ScrollMode.AUTO
            ),
            padding=20,
            bgcolor=colors["card_bg"],
            border_radius=12,
            border=ft.border.all(1, colors["border"]),
            visible=False
        )
        
        # --- Configuração do Layout Principal ---
        self.controls = [
            # Header com título e informações
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text("Suas Atividades", size=24, weight="bold", color=colors["text_primary"]),
                        ft.Icon(ft.Icons.TASK_ALT, size=32),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                padding=15,
                bgcolor=colors["header_bg"],
                border_radius=12,
                border=ft.border.all(1, colors["border"]),
            ),
            
            # Barra de busca
            ft.Container(
                content=self.search_field,
                padding=10,
                bgcolor=colors["search_bg"],
                border_radius=12,
                border=ft.border.all(1, colors["border"]),
            ),
            
            # Filtros
            ft.Container(
                content=filters_row,
                padding=10,
                bgcolor=colors["card_bg"],
                border_radius=12,
                border=ft.border.all(1, colors["border"]),
            ),
            
            # Nova atividade
            new_activity_container,
            
            # Lista de atividades
            ft.Container(
                content=self.activity_list,
                expand=True,
                padding=10,
                bgcolor=colors["container_bg"],
            ),
            
            # Painel de edição
            self.edit_panel,
        ]
        
        self.expand = True
        self.spacing = 10
        self.padding = 15
        self.scroll = ft.ScrollMode.AUTO
        self.bgcolor = colors["container_bg"]
    
    def close_edit_panel(self, e):
        """Fecha o painel de edição."""
        self.edit_panel.visible = False
        self.selected_activity = None
        self.page.update()
    
    def refresh_colors(self):
        """Atualiza as cores baseado no tema atual."""
        colors = get_dynamic_colors(self.page)
        
        # Atualizar cores dos TextFields
        self.search_field.bgcolor = colors["search_bg"]
        self.new_activity.bgcolor = colors["search_bg"]
        self.edit_activity_text.bgcolor = colors["search_bg"]
        self.due_date_field.bgcolor = colors["search_bg"]
        self.category_field.bgcolor = colors["search_bg"]
        self.tags_field.bgcolor = colors["search_bg"]
        
        # Atualizar cores dos containers
        self.edit_panel.bgcolor = colors["card_bg"]
        
        self.page.update()

    # ==================== PERSISTÊNCIA DE DADOS ====================

    def load_atividades(self):
        """Carrega atividades do arquivo JSON."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.atividades = data.get("atividades", {})
                self.activity_id_counter = data.get("activity_id_counter", 0)
            except Exception as e:
                self.atividades = {}
                self.activity_id_counter = 0
        else:
            self.atividades = {}
            self.activity_id_counter = 0

    def save_atividades(self):
        """Salva atividades no arquivo JSON."""
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "atividades": self.atividades,
                        "activity_id_counter": self.activity_id_counter
                    },
                    f,
                    ensure_ascii=False,
                    indent=2
                )
        except Exception as e:
            pass

    def load_historico(self):
        """Carrega histórico de alterações."""
        if os.path.exists(self.historico_file):
            try:
                with open(self.historico_file, "r", encoding="utf-8") as f:
                    self.historico = json.load(f)
            except Exception:
                self.historico = []
        else:
            self.historico = []

    def save_historico(self):
        """Salva histórico de alterações."""
        try:
            with open(self.historico_file, "w", encoding="utf-8") as f:
                json.dump(self.historico, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def registrar_historico(self, acao, activity_id, detalhes):
        """Registra ação no histórico."""
        self.historico.append({
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "acao": acao,
            "activity_id": activity_id,
            "detalhes": detalhes,
            "usuario": self.usuario_atual or "Anônimo"
        })
        self.save_historico()

    # ==================== OPERAÇÕES DE ATIVIDADES ====================

    def add_clicked(self, e):
        """Adiciona uma nova atividade."""
        texto = self.new_activity.value.strip()
        if not texto:
            self.show_snackbar("⚠️ Por favor, digite uma atividade!")
            return

        self.activity_id_counter += 1
        activity_id = self.activity_id_counter
        
        nova_atividade = {
            "texto": texto,
            "data": datetime.now().strftime("%d/%m/%Y"),
            "status": "Pendente",
            "prioridade": "Baixa",
            "categoria": "Sem categoria",
            "tags": [],
            "data_vencimento": "",
        }
        
        self.atividades[activity_id] = nova_atividade
        self.registrar_historico("CRIADA", activity_id, f"Atividade: {texto}")
        self.save_atividades()
        self.new_activity.value = ""
        self.update_activity_list()
        self.update_categories()
        self.new_activity.focus()
        self.show_snackbar("✅ Atividade adicionada com sucesso!")
        self.page.update()

    def update_activity_list(self):
        """Atualiza a lista de atividades com base nos filtros."""
        self.activity_list.controls.clear()
        
        search_text = self.search_field.value.lower()
        filter_status = self.filter_status.value
        filter_priority = self.filter_priority.value
        filter_category = self.filter_category.value
        
        for activity_id, activity_data in sorted(self.atividades.items(), reverse=True):
            # Aplicar filtros
            if search_text and search_text not in activity_data["texto"].lower():
                continue
            if filter_status != "Todos" and activity_data["status"] != filter_status:
                continue
            if filter_priority != "Todos" and activity_data.get("prioridade", "Baixa") != filter_priority:
                continue
            if filter_category != "Todos" and activity_data.get("categoria", "Sem categoria") != filter_category:
                continue
            
            self.activity_list.controls.append(ActivityItem(activity_id, activity_data, self))
        
        self.page.update()

    def filtrar_atividades(self, e):
        """Atualiza a lista ao mudar filtros."""
        self.update_activity_list()

    def update_categories(self):
        """Atualiza dropdown de categorias."""
        categorias = set(["Todos"])
        for activity in self.atividades.values():
            categorias.add(activity.get("categoria", "Sem categoria"))
        
        self.filter_category.options = [ft.dropdown.Option(cat) for cat in sorted(categorias)]
        self.page.update()

    def select_activity(self, activity_control: ActivityItem):
        """Seleciona uma atividade para edição."""
        if self.selected_activity:
            self.selected_activity.border = None
        
        self.selected_activity = activity_control
        self.selected_activity.border = ft.border.all(3, ft.Colors.PRIMARY)
        
        self.edit_activity_text.value = activity_control.activity_data["texto"]
        self.date_label.value = f"📅 Data de criação: {activity_control.activity_data['data']}"
        self.status_radio.value = activity_control.activity_data["status"]
        self.priority_radio.value = activity_control.activity_data.get("prioridade", "Baixa")
        self.category_field.value = activity_control.activity_data.get("categoria", "Sem categoria")
        self.tags_field.value = ", ".join(activity_control.activity_data.get("tags", []))
        self.due_date_field.value = activity_control.activity_data.get("data_vencimento", "")
        self.edit_panel.visible = True
        self.page.update()

    def save_clicked(self, e):
        """Salva alterações na atividade selecionada."""
        if self.selected_activity:
            activity_id = self.selected_activity.activity_id
            old_data = self.atividades[activity_id].copy()
            
            self.atividades[activity_id]["texto"] = self.edit_activity_text.value
            self.atividades[activity_id]["status"] = self.status_radio.value
            self.atividades[activity_id]["prioridade"] = self.priority_radio.value or "Baixa"
            self.atividades[activity_id]["categoria"] = self.category_field.value or "Sem categoria"
            self.atividades[activity_id]["tags"] = [tag.strip() for tag in self.tags_field.value.split(",") if tag.strip()]
            self.atividades[activity_id]["data_vencimento"] = self.due_date_field.value
            
            detalhes = f"Alterações: Texto, Status={self.status_radio.value}, Prioridade={self.priority_radio.value}"
            self.registrar_historico("EDITADA", activity_id, detalhes)
            self.save_atividades()
            self.update_activity_list()
            self.update_categories()
            self.edit_panel.visible = False
            self.selected_activity = None
            self.show_snackbar("✅ Atividade salva com sucesso!")
            self.page.update()

    def status_changed(self, e):
        """Atualiza cor ao mudar status."""
        if self.selected_activity:
            self.selected_activity.bgcolor = self.selected_activity.get_status_color(e.control.value)
            self.page.update()

    def delete_clicked(self, e):
        """Deleta a atividade selecionada."""
        if self.selected_activity:
            activity_id = self.selected_activity.activity_id
            activity_text = self.atividades[activity_id]["texto"]
            
            del self.atividades[activity_id]
            self.registrar_historico("DELETADA", activity_id, f"Atividade: {activity_text}")
            self.save_atividades()
            self.edit_panel.visible = False
            self.selected_activity = None
            self.update_activity_list()
            self.update_categories()
            self.show_snackbar("✅ Atividade excluída com sucesso!")
            self.page.update()

    # ==================== EXPORTAÇÃO E HISTÓRICO ====================

    def export_csv(self, e):
        """Exporta atividades para arquivo CSV."""
        try:
            filename = f"atividades_export_{datetime.now().strftime('%d%m%Y_%H%M%S')}.csv"
            with open(filename, "w", newline="", encoding="utf-8") as csvfile:
                fieldnames = ["ID", "Texto", "Data Criação", "Status", "Prioridade", "Categoria", "Tags", "Data Vencimento"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for activity_id, activity_data in self.atividades.items():
                    writer.writerow({
                        "ID": activity_id,
                        "Texto": activity_data["texto"],
                        "Data Criação": activity_data["data"],
                        "Status": activity_data["status"],
                        "Prioridade": activity_data.get("prioridade", "Baixa"),
                        "Categoria": activity_data.get("categoria", "Sem categoria"),
                        "Tags": ", ".join(activity_data.get("tags", [])),
                        "Data Vencimento": activity_data.get("data_vencimento", ""),
                    })
            
            self.show_snackbar(f"✅ Exportado para {filename}")
        except Exception as ex:
            self.show_snackbar(f"❌ Erro ao exportar: {str(ex)}")

    def show_history(self, e):
        """Exibe histórico de alterações."""
        if not self.selected_activity:
            self.show_snackbar("⚠️ Selecione uma atividade para ver o histórico!")
            return
        
        activity_id = self.selected_activity.activity_id
        history_items = [h for h in self.historico if h["activity_id"] == activity_id]
        
        history_text = "📜 Histórico de Alterações:\n\n"
        for item in history_items:
            history_text += f"[{item['timestamp']}] {item['acao']}: {item['detalhes']}\n"
        
        # Criar um diálogo para exibir o histórico
        dlg = ft.AlertDialog(
            title=ft.Text("Histórico de Alterações"),
            content=ft.Text(history_text, selectable=True),
            actions=[ft.TextButton("Fechar", on_click=lambda x: self.close_dialog(dlg))]
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def close_dialog(self, dlg):
        """Fecha um diálogo."""
        dlg.open = False
        self.page.update()

    def show_snackbar(self, message):
        """Exibe uma notificação tipo snackbar."""
        snack = ft.SnackBar(ft.Text(message))
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()


# ==================== TELA DE LOGIN ====================

class LoginScreen(ft.Container):
    def __init__(self, page: ft.Page, on_login_callback):
        super().__init__()
        self.page = page
        self.on_login_callback = on_login_callback
        
        colors = get_dynamic_colors(page)
        
        self.username_field = ft.TextField(
            label="👤 Usuário",
            width=350,
            border_radius=10,
            bgcolor=colors["search_bg"],
            label_style=ft.TextStyle(color=colors["text_secondary"]),
        )
        self.password_field = ft.TextField(
            label="🔐 Senha",
            password=True,
            width=350,
            border_radius=10,
            bgcolor=colors["search_bg"],
            label_style=ft.TextStyle(color=colors["text_secondary"]),
        )
        
        self.login_button = ft.ElevatedButton(
            "🔓 Entrar",
            on_click=self.login_clicked,
            width=350,
            height=50,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
        )
        
        self.content = ft.Column(
            controls=[
                ft.Icon(ft.Icons.TASK_ALT, size=80, color=ft.Colors.PRIMARY),
                ft.Text("IAgo", size=40, weight="bold"),
                ft.Text("Gerenciador de Atividades", size=16, color=colors["text_secondary"]),
                ft.Container(height=30),
                ft.Text("🔐 Login", size=22, weight="bold"),
                self.username_field,
                self.password_field,
                self.login_button,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15
        )
        self.alignment = ft.alignment.center
        self.expand = True
        self.bgcolor = colors["container_bg"]

    def login_clicked(self, e):
        """Verifica credenciais e faz login."""
        username = self.username_field.value.strip()
        password = self.password_field.value.strip()
        
        if not username or not password:
            snack = ft.SnackBar(ft.Text("⚠️ Preencha todos os campos!"))
            self.page.overlay.append(snack)
            snack.open = True
            self.page.update()
            return
        
        # Aceita qualquer usuário com senha (demo)
        self.on_login_callback(username)


# ==================== FUNÇÃO PRINCIPAL ====================

def main(page: ft.Page):
    page.title = "IAgo - 🗃️ Gerenciador de Atividades"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.window_min_width = 600
    page.window_min_height = 700
    page.theme_mode = ft.ThemeMode.DARK
    
    # --- Splash Screen ---
    colors = get_dynamic_colors(page)
    splash_content = ft.Column(
        [
            ft.Icon(ft.Icons.TASK_ALT, size=80, color=ft.Colors.PRIMARY),
            ft.Text("IAgo", size=40, weight="bold"),
            ft.Container(height=20),
            ft.ProgressRing(width=50, height=50, stroke_width=4),
            ft.Text("Carregando suas atividades...", size=14),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True
    )
    page.add(splash_content)
    page.update()
    time.sleep(1.5)
    page.clean()

    # --- Tema ---
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
        if app:
            app.refresh_colors()
        page.update()

    theme_icon = ft.IconButton(
        ft.Icons.BRIGHTNESS_3_OUTLINED,
        tooltip="Mudar tema",
        on_click=change_theme,
    )

    # --- Login ---
    app = None
    login_screen = None
    
    def on_login(username):
        nonlocal app, login_screen
        page.clean()
        
        app = TaskManager(page)
        app.usuario_atual = username
        
        colors = get_dynamic_colors(page)
        
        page.appbar = ft.AppBar(
            title=ft.Text(f"IAgo - {username}"),
            center_title=False,
            bgcolor=colors["header_bg"],
            actions=[
                ft.Text(f"👤 {username}", size=12),
                theme_icon,
            ],
        )
        
        page.add(app)
        page.update()

    login_screen = LoginScreen(page, on_login)
    page.add(login_screen)
    page.update()


# Inicia a aplicação Flet
ft.app(target=main)