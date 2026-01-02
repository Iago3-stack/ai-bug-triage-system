import flet as ft
from datetime import datetime
import json
import os

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
        "error": "#ff6b6b",
        "success": "#51cf66",
    }


# ==================== CLASSES DE DADOS ====================

class ColetorDeDados:
    """Classe para coletar e validar dados de RH/Folha."""
    
    def __init__(self):
        self.nome = None
        self.idade = None
        self.ano = None
        self.trabalho = None
        self.valor = None
        self.horas = None
        self.total = None
        self.data_criacao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.dados_file = "dados_rh.json"
    
    def validar_nome(self, nome):
        """Valida nome."""
        if not nome or not nome.strip():
            return False, "O campo Nome não pode ficar vazio."
        if len(nome) < 3:
            return False, "Nome deve ter pelo menos 3 caracteres."
        return True, "Válido"
    
    def validar_idade(self, idade):
        """Valida idade."""
        try:
            idade_int = int(idade)
            if idade_int < 18:
                return False, "Idade deve ser maior ou igual a 18 anos."
            if idade_int > 100:
                return False, "Idade deve ser menor que 100 anos."
            return True, "Válido"
        except ValueError:
            return False, "Idade deve ser um número inteiro válido."
    
    def validar_ano(self, ano):
        """Valida ano de nascimento."""
        try:
            ano_int = int(ano)
            if ano_int < 1900 or ano_int > 2025:
                return False, "Ano deve estar entre 1900 e 2025."
            return True, "Válido"
        except ValueError:
            return False, "Ano deve ser um número inteiro válido."
    
    def validar_trabalho(self, trabalho):
        """Valida empresa."""
        if not trabalho or not trabalho.strip():
            return False, "Campo empresa não pode ficar vazio."
        return True, "Válido"
    
    def validar_valor(self, valor):
        """Valida valor hora."""
        try:
            valor_float = float(valor.replace(',', '.'))
            if valor_float <= 0:
                return False, "Valor deve ser maior que zero."
            return True, "Válido"
        except ValueError:
            return False, "Valor deve ser um número válido."
    
    def validar_horas(self, horas):
        """Valida horas por mês."""
        try:
            horas_int = int(horas)
            if horas_int <= 0:
                return False, "Horas deve ser um valor positivo."
            if horas_int > 744:  # Máximo de horas em um mês
                return False, "Horas não pode ser maior que 744 (horas de um mês)."
            return True, "Válido"
        except ValueError:
            return False, "Horas deve ser um número inteiro válido."
    
    def calcular_salario(self):
        """Calcula o salário total."""
        if self.valor and self.horas:
            self.total = float(self.valor) * int(self.horas)
            return self.total
        return None
    
    def salvar_dados(self):
        """Salva os dados em JSON."""
        dados = {
            "nome": self.nome,
            "idade": self.idade,
            "ano": self.ano,
            "empresa": self.trabalho,
            "valor_hora": self.valor,
            "horas_mes": self.horas,
            "salario_total": self.total,
            "data_criacao": self.data_criacao
        }
        
        try:
            # Carregar dados existentes
            if os.path.exists(self.dados_file):
                with open(self.dados_file, 'r', encoding='utf-8') as f:
                    registros = json.load(f)
            else:
                registros = []
            
            # Adicionar novo registro
            registros.append(dados)
            
            # Salvar
            with open(self.dados_file, 'w', encoding='utf-8') as f:
                json.dump(registros, f, ensure_ascii=False, indent=2)
            
            return True, "Dados salvos com sucesso!"
        except Exception as e:
            return False, f"Erro ao salvar: {str(e)}"
    
    def carregar_dados(self):
        """Carrega dados salvos."""
        try:
            if os.path.exists(self.dados_file):
                with open(self.dados_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception:
            return []


# ==================== APLICAÇÃO FLET ====================

class ERPRHApp(ft.Column):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.coletor = ColetorDeDados()
        colors = get_dynamic_colors(page)
        
        # Estado
        self.fase_atual = 1  # 1 ou 2
        self.erro_message = None
        
        # ============= FASE 1: DADOS PESSOAIS =============
        
        self.nome_field = ft.TextField(
            label="👤 Nome Completo",
            bgcolor=colors["search_bg"],
            border_color=colors["border"],
            on_change=self.limpar_erro
        )
        
        self.idade_field = ft.TextField(
            label="🎂 Idade",
            bgcolor=colors["search_bg"],
            border_color=colors["border"],
            input_filter="0123456789",
            on_change=self.limpar_erro
        )
        
        self.ano_field = ft.TextField(
            label="📅 Ano de Nascimento",
            bgcolor=colors["search_bg"],
            border_color=colors["border"],
            input_filter="0123456789",
            on_change=self.limpar_erro
        )
        
        # ============= FASE 2: DADOS PROFISSIONAIS =============
        
        self.empresa_field = ft.TextField(
            label="🏢 Empresa",
            bgcolor=colors["search_bg"],
            border_color=colors["border"],
            on_change=self.limpar_erro
        )
        
        self.valor_field = ft.TextField(
            label="💰 Valor/Hora",
            bgcolor=colors["search_bg"],
            border_color=colors["border"],
            on_change=self.limpar_erro
        )
        
        self.horas_field = ft.TextField(
            label="⏰ Horas/Mês",
            bgcolor=colors["search_bg"],
            border_color=colors["border"],
            input_filter="0123456789",
            on_change=self.limpar_erro
        )
        
        # Resultado
        self.resultado_text = ft.Text(
            value="",
            size=14,
            color=colors["text_secondary"],
            selectable=True
        )
        
        # Mensagem de erro
        self.erro_text = ft.Text(
            value="",
            size=12,
            color=colors["error"],
        )
        
        # Mensagem de sucesso
        self.sucesso_text = ft.Text(
            value="",
            size=12,
            color=colors["success"],
        )
        
        # Botões
        self.btn_proximo = ft.ElevatedButton(
            "➡️ Próximo",
            on_click=self.proxima_fase,
            expand=True
        )
        
        self.btn_anterior = ft.ElevatedButton(
            "⬅️ Anterior",
            on_click=self.fase_anterior,
            expand=True,
            disabled=True
        )
        
        self.btn_salvar = ft.ElevatedButton(
            "💾 Salvar Dados",
            on_click=self.salvar_dados,
            expand=True
        )
        
        self.btn_limpar = ft.ElevatedButton(
            "🔄 Limpar Tudo",
            on_click=self.limpar_formulario,
            expand=True,
            style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_700)
        )
        
        # Histórico
        self.historico_list = ft.ListView(expand=True, spacing=5)
        self.abrir_historico_btn = ft.ElevatedButton(
            "📜 Ver Histórico",
            on_click=self.mostrar_historico,
            expand=True
        )
        
        # ============= LAYOUT =============
        
        self.fase1_content = ft.Column(
            controls=[
                ft.Text("📝 Fase 1: Dados Pessoais", size=20, weight="bold"),
                self.nome_field,
                ft.Row(
                    controls=[self.idade_field, self.ano_field],
                    spacing=10
                ),
                self.erro_text,
                self.sucesso_text,
                ft.Row(
                    controls=[self.btn_anterior, self.btn_proximo],
                    spacing=10
                ),
            ],
            spacing=15,
            visible=True
        )
        
        self.fase2_content = ft.Column(
            controls=[
                ft.Text("💼 Fase 2: Dados Profissionais", size=20, weight="bold"),
                self.empresa_field,
                self.valor_field,
                self.horas_field,
                ft.Divider(),
                ft.Text("📊 Resultado:", size=14, weight="bold"),
                self.resultado_text,
                self.erro_text,
                self.sucesso_text,
                ft.Row(
                    controls=[self.btn_anterior, self.btn_salvar],
                    spacing=10
                ),
                ft.Divider(),
                ft.Row(
                    controls=[self.btn_limpar, self.abrir_historico_btn],
                    spacing=10
                ),
            ],
            spacing=15,
            visible=False
        )
        
        # Layout principal - Usando apenas column com scroll
        self.main_column = ft.Column(
            controls=[
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Text("ERP RH", size=28, weight="bold"),
                            ft.Icon(ft.Icons.BUSINESS, size=32),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    padding=15,
                    bgcolor=colors["header_bg"],
                    border_radius=12,
                    border=ft.border.all(1, colors["border"]),
                ),
                
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.ProgressBar(
                                value=0.5,
                                color=colors["accent"],
                            ),
                            ft.Text("Fase 1 de 2", size=12, color=colors["text_secondary"]),
                        ],
                        spacing=6
                    ),
                    padding=10,
                ),
                
                ft.Container(
                    content=ft.Column(
                        controls=[self.fase1_content, self.fase2_content],
                        spacing=20,
                    ),
                    padding=20,
                    bgcolor=colors["card_bg"],
                    border_radius=12,
                    border=ft.border.all(1, colors["border"]),
                ),
            ],
            spacing=15,
            scroll=ft.ScrollMode.AUTO,
        )
        
        self.controls = [
            ft.Container(
                content=self.main_column,
                padding=15,
                expand=True
            )
        ]
        self.expand = True
    
    def limpar_erro(self, e):
        """Limpa mensagens de erro."""
        self.erro_text.value = ""
        self.sucesso_text.value = ""
        self.page.update()
    
    def mostrar_erro(self, mensagem):
        """Exibe mensagem de erro."""
        self.erro_text.value = f"❌ {mensagem}"
        self.sucesso_text.value = ""
        self.page.update()
    
    def mostrar_sucesso(self, mensagem):
        """Exibe mensagem de sucesso."""
        self.sucesso_text.value = f"✅ {mensagem}"
        self.erro_text.value = ""
        self.page.update()
    
    def proxima_fase(self, e):
        """Valida fase 1 e vai para fase 2."""
        # Validar nome
        valido, msg = self.coletor.validar_nome(self.nome_field.value)
        if not valido:
            self.mostrar_erro(msg)
            return
        
        self.coletor.nome = self.nome_field.value
        
        # Validar idade
        valido, msg = self.coletor.validar_idade(self.idade_field.value)
        if not valido:
            self.mostrar_erro(msg)
            return
        
        self.coletor.idade = int(self.idade_field.value)
        
        # Validar ano
        valido, msg = self.coletor.validar_ano(self.ano_field.value)
        if not valido:
            self.mostrar_erro(msg)
            return
        
        self.coletor.ano = int(self.ano_field.value)
        
        # Ir para fase 2
        self.fase_atual = 2
        self.fase1_content.visible = False
        self.fase2_content.visible = True
        self.btn_anterior.disabled = False
        self.mostrar_sucesso(f"Bem-vindo {self.coletor.nome}! Agora preencha os dados profissionais.")
        self.page.update()
    
    def fase_anterior(self, e):
        """Volta para fase 1."""
        if self.fase_atual == 2:
            self.fase_atual = 1
            self.fase1_content.visible = True
            self.fase2_content.visible = False
            self.btn_anterior.disabled = True
            self.limpar_erro(None)
            self.page.update()
    
    def salvar_dados(self, e):
        """Valida fase 2 e salva dados."""
        # Validar empresa
        valido, msg = self.coletor.validar_trabalho(self.empresa_field.value)
        if not valido:
            self.mostrar_erro(msg)
            return
        
        self.coletor.trabalho = self.empresa_field.value
        
        # Validar valor
        valido, msg = self.coletor.validar_valor(self.valor_field.value)
        if not valido:
            self.mostrar_erro(msg)
            return
        
        self.coletor.valor = float(self.valor_field.value.replace(',', '.'))
        
        # Validar horas
        valido, msg = self.coletor.validar_horas(self.horas_field.value)
        if not valido:
            self.mostrar_erro(msg)
            return
        
        self.coletor.horas = int(self.horas_field.value)
        
        # Calcular salário
        self.coletor.calcular_salario()
        
        # Exibir resultado
        resultado = (
            f"👤 Nome: {self.coletor.nome}\n"
            f"🎂 Idade: {self.coletor.idade} anos\n"
            f"📅 Nascimento: {self.coletor.ano}\n"
            f"🏢 Empresa: {self.coletor.trabalho}\n"
            f"💰 Valor/Hora: R$ {self.coletor.valor:.2f}\n"
            f"⏰ Horas/Mês: {self.coletor.horas}\n"
            f"💵 Salário Total: R$ {self.coletor.total:.2f}"
        )
        
        self.resultado_text.value = resultado
        
        # Salvar dados
        sucesso, msg = self.coletor.salvar_dados()
        if sucesso:
            self.mostrar_sucesso(msg)
        else:
            self.mostrar_erro(msg)
        
        self.page.update()
    
    def limpar_formulario(self, e):
        """Limpa todos os campos."""
        self.nome_field.value = ""
        self.idade_field.value = ""
        self.ano_field.value = ""
        self.empresa_field.value = ""
        self.valor_field.value = ""
        self.horas_field.value = ""
        self.resultado_text.value = ""
        
        self.coletor = ColetorDeDados()
        self.fase_atual = 1
        self.fase1_content.visible = True
        self.fase2_content.visible = False
        self.btn_anterior.disabled = True
        
        self.limpar_erro(None)
        self.page.update()
    
    def mostrar_historico(self, e):
        """Exibe histórico de dados salvos."""
        dados = self.coletor.carregar_dados()
        
        if not dados:
            self.mostrar_erro("Nenhum registro salvo ainda.")
            return
        
        # Criar tabela com histórico
        self.historico_list.controls.clear()
        
        for idx, registro in enumerate(dados, 1):
            card = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(f"#{idx} - {registro['nome']}", size=14, weight="bold"),
                        ft.Text(f"Empresa: {registro['empresa']}", size=12),
                        ft.Text(f"Salário: R$ {registro['salario_total']:.2f}", size=12, color="green"),
                        ft.Text(f"Data: {registro['data_criacao']}", size=10, color="gray"),
                    ],
                    spacing=5
                ),
                padding=10,
                bgcolor=ft.Colors.SURFACE_VARIANT,
                border_radius=8,
            )
            self.historico_list.controls.append(card)
        
        # Criar diálogo
        dlg = ft.AlertDialog(
            title=ft.Text(f"📜 Histórico ({len(dados)} registros)"),
            content=ft.Container(
                content=self.historico_list,
                height=400,
                width=500
            ),
            actions=[
                ft.TextButton("Fechar", on_click=lambda x: self.fechar_dialog(dlg))
            ]
        )
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()
    
    def fechar_dialog(self, dlg):
        """Fecha diálogo."""
        dlg.open = False
        self.page.update()


# ==================== FUNÇÃO PRINCIPAL ====================

def main(page: ft.Page):
    page.title = "ERP RH - Gerenciador de Folha"
    page.window_min_width = 600
    page.window_min_height = 700
    page.theme_mode = ft.ThemeMode.DARK
    
    # Splash
    splash = ft.Column(
        [
            ft.Icon(ft.Icons.BUSINESS, size=80, color=ft.Colors.PRIMARY),
            ft.Text("ERP RH", size=40, weight="bold"),
            ft.Container(height=20),
            ft.ProgressRing(width=50, height=50, stroke_width=4),
            ft.Text("Carregando...", size=14),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True
    )
    page.add(splash)
    page.update()
    
    import time
    time.sleep(1)
    page.clean()
    
    # Tema
    def change_theme(e):
        page.theme_mode = (
            ft.ThemeMode.DARK
            if page.theme_mode == ft.ThemeMode.LIGHT
            else ft.ThemeMode.LIGHT
        )
        page.update()
    
    theme_btn = ft.IconButton(
        ft.Icons.BRIGHTNESS_3_OUTLINED,
        on_click=change_theme,
        tooltip="Alternar tema"
    )
    
    # AppBar
    page.appbar = ft.AppBar(
        title=ft.Text("ERP RH - Folha de Pagamento"),
        actions=[theme_btn],
    )
    
    # App
    app = ERPRHApp(page)
    page.add(app)
    page.update()


if __name__ == "__main__":
    ft.app(target=main)
