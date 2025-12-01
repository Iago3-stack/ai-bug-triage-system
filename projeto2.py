# app_final.py - Versão Gemini Advanced com Splash Screen

import tkinter as tk
from tkinter import Frame, messagebox, filedialog, ttk
import customtkinter as ctk
import re
import os
import shutil
import json
from datetime import datetime
import csv
from collections import defaultdict
from io import StringIO
from PIL import Image, ImageTk
import threading
import time # NOVO: Importado para simular o tempo de carregamento

# --- Dependências para Servidor HTTP e Rede ---
import socket
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

# Tentativa de usar tkcalendar.DateEntry; se não estiver disponível, usamos um CTkEntry como fallback
try:
    from tkcalendar import DateEntry
    TKCALENDAR_AVAILABLE = True
except Exception:
    TKCALENDAR_AVAILABLE = False

# Tentativa de usar qrcode e reportlab; se não estiverem disponíveis, avisamos ao usuário quando necessário
try:
    import qrcode
    from qrcode.image.pil import PilImage
    QRCODE_AVAILABLE = True
except Exception:
    QRCODE_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False

# --- Constantes e Configurações ---
ctk.set_default_color_theme("green") 
NOME_ARQUIVO = "dados_colaboradores.json"
CREDENTIALS_FILE = "credentials.json"
PDF_RELATORIO = "relatorio_bi.pdf"
DEFAULT_CREDENTIALS = {
    "admin": "1234",
    "user": "1234",
    "theme": "System"
}

# --- Configurações do Servidor Local ---
SERVER_PORT = 8000
try:
    # Tenta obter o IP da máquina na rede local
    SERVER_IP = socket.gethostbyname(socket.gethostname())
except socket.gaierror:
    # Fallback para localhost, mas só funcionará no PC que está rodando o app
    SERVER_IP = "127.0.0.1"

# URL de acesso para o QR Code (via rede local)
PDF_URL_LOCAL = f"http://{SERVER_IP}:{SERVER_PORT}/{PDF_RELATORIO}"

def log_error(funcao, mensagem):
    """Simulação de log de error."""
    print(f"[ERRO] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {funcao}: {mensagem}")
# --- Funções de Manipulação de Dados ---
def carregar_dados():
    """Carrega dados mockados se o arquivo não existir. Garante compatibilidade com campos novos (cargo, data_admissao)."""
    if os.path.exists(NOME_ARQUIVO):
        try:
            with open(NOME_ARQUIVO, 'r', encoding='utf-8') as f:
                dados = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            log_error("carregar_dados", "Arquivo JSON inválido ou corrompido. Iniciando com dados vazios.")
            dados = []
    else:
        dados = [
            {"id": 1, "nome": "João Silva", "email": "joao@empresa.com", "telefone": "9999-1234", "modalidade": "CLT", "salario": 5000.00, "documento_fiscal": "11122233344", "historico_ausencias": [{"data": "2024-10-01", "tipo": "FERIAS", "observacao": ""}], "cargo": "Analista", "data_admissao": "2023-01-15"},
            {"id": 2, "nome": "Maria Souza", "email": "maria@empresa.com", "telefone": "9999-5678", "modalidade": "PJ", "salario": 8500.00, "documento_fiscal": "00000000000000", "historico_ausencias": [{"data": "2024-10-05", "tipo": "ATESTADO", "observacao": "Gripe"}], "cargo": "Consultora", "data_admissao": "2024-02-20"},
        ]
    # Garantir compatibilidade com dados antigos
    # O código original já faz isso. Mantido.
    for user in dados:
        user.setdefault('cargo', '—')
        user.setdefault('data_admissao', datetime.now().strftime('%d-%m-%Y'))
        user.setdefault('historico_ausencias', user.get('historico_ausencias', []))
        user.setdefault('salario', user.get('salario', 0.0))
        user.setdefault('documento_fiscal', user.get('documento_fiscal', ''))
    return dados

def salvar_dados(dados):
    """Salva dados no arquivo JSON."""
    try:
        with open(NOME_ARQUIVO, 'w', encoding='utf-8') as f:
            # O código original está recebendo uma lista de dicionários aqui, 
            # mas o fluxo de cadastro e deleção o trata como uma lista.
            # Se for uma lista, o salvamento é direto.
            # Se for um dicionário de IDs (estrutura do meu código anterior), 
            # isso pode causar um erro. Vou assumir que é uma lista como no código fornecido.
            json.dump(dados, f, indent=4, ensure_ascii=False)
    except Exception as e:
        log_error("salvar_dados", f"Falha ao salvar o arquivo: {e}")
        messagebox.showerror("Erro de Salvamento", "Não foi possível salvar os dados dos colaboradores.")
        
def load_credentials():
    """Carrega as credenciais e configurações (incluindo tema) dos usuários do arquivo JSON."""
    creds = DEFAULT_CREDENTIALS.copy()
    if os.path.exists(CREDENTIALS_FILE):
        try:
            with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
                saved_creds = json.load(f)
                creds.update(saved_creds)
                
        except (json.JSONDecodeError, FileNotFoundError):
            log_error("load_credentials", "Arquivo de credenciais inválido. Usando credenciais padrão.")
            # Salva as credenciais padrão se o arquivo estiver corrompido
            save_credentials(creds) 
    else:
        # Salva as credenciais padrão se o arquivo não existir
        save_credentials(creds)
        
    return creds

def save_credentials(creds):
    """Salva as credenciais e configurações (incluindo tema) dos usuários no arquivo JSON."""
    try:
        with open(CREDENTIALS_FILE, 'w', encoding='utf-8') as f:
            json.dump(creds, f, indent=4, ensure_ascii=False)
    except Exception as e:
        log_error("save_credentials", f"Falha ao salvar o arquivo de credenciais: {e}")
        messagebox.showerror("Erro de Salvamento", "Não foi possível salvar as credenciais.")

def string_para_float(valor_str):
    """Converte string de moeda BR (vírgula decimal) para float."""
    if isinstance(valor_str, (int, float)): return float(valor_str)
    # Garante que 'R$' e espaços sejam removidos, e o separador de milhar seja ignorado.
    limpo = valor_str.replace('R$', '').replace('.', '').replace(',', '.').strip()
    return float(limpo) if limpo else 0.0

def formatar_moeda(valor):
    """Formata float para string de moeda BR (ponto milhar, vírgula decimal)."""
    return f"R$ {valor:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')

def validar_data(data_str, formato='%d-%m-%Y'):
    """Valida se a string é uma data no formato correto."""
    if not data_str:
        raise ValueError("O campo Data é obrigatório.")
    try:
        datetime.strptime(data_str, formato)
    except ValueError:
        raise ValueError(f"Formato de data inválido. Use o formato DD/MM/AAAA (Ex: 10/10/2025).")
        
# Função para gerar PDF usando reportlab
def gerar_pdf_relatorio(path, texto_relatorio):
    if not REPORTLAB_AVAILABLE:
        raise ImportError("reportlab não disponível")
    try:
        c = canvas.Canvas(path, pagesize=A4)
        width, height = A4
        margin = 40
        y = height - margin
        c.setFont("Helvetica-Bold", 18)
        c.drawString(margin, y, "RELATÓRIO DE BUSINESS INTELLIGENCE (BI)")
        y -= 30
        c.setFont("Helvetica", 10)
        
        # Processa o texto com a nova formatação
        for linha in texto_relatorio.splitlines():
            # Pula linhas em branco, exceto as que são explicitamente separadores
            if not linha.strip() and not linha.startswith('---') and not linha.startswith('='):
                y -= 5 # Pequeno espaço
                continue

            # Quebra linhas longas
            partes = [linha[i:i+100] for i in range(0, len(linha), 100)]
            
            # Formatação de Tópicos (incluindo cabeçalhos '---') e Títulos ('=')
            if linha.startswith('===') or linha.startswith('---'):
                 c.setFont("Helvetica-Bold", 10 if linha.startswith('---') else 12)
                 y -= 10
                 c.drawString(margin, y, linha)
                 c.setFont("Helvetica", 10)
                 y -= 5
            else:
                for p in partes:
                    c.drawString(margin + 5, y, p)
                    y -= 18
                    
            if y < margin:
                c.showPage()
                y = height - margin
                c.setFont("Helvetica", 10)
                
        c.save()
        return True
    except Exception as e:
        log_error("gerar_pdf_relatorio", str(e))
        return False

class LateralApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # 1. Configurações Iniciais e Carregamento
        self.credentials = load_credentials()
        self.current_theme = self.credentials.get("theme", "System")
        ctk.set_appearance_mode(self.current_theme)

        self.title("Gerenciador de RH #")
        self.geometry("1200x700")
        self.minsize(900, 600)

        # 2. Variáveis de Estado
        self.user_role = None  # Definido após o login
        self.dados_usuarios = carregar_dados()
        self.editando_id = None
        self.user_map = {}
        self.qr_im_label = None
        self.qr_visible = False
        self.httpd = None # Servidor HTTP

        # 3. Configuração do Layout Principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Frames para Login e Aplicação Principal
        self.login_frame = ctk.CTkFrame(self)
        self.main_app_frame = ctk.CTkFrame(self)

        # 4. NOVO: Inicia com a Tela de Splash
        self.withdraw() # Oculta a janela principal
        self.show_splash_screen()

    # --- NOVO: Lógica da Animação Inicial (Splash Screen) ---
    def show_splash_screen(self):
        """Cria e exibe a tela de splash screen com animação."""
        self.splash_window = ctk.CTkToplevel(self)
        self.splash_window.title("Carregando Sistema RH...")
        self.splash_window.overrideredirect(True) # Remove bordas
        self.splash_window.lift()
        self.splash_window.attributes('-topmost', True) # Fica sempre no topo
        
        # Centralizar a tela de splash (tamanho fixo 500x300)
        splash_width = 500
        splash_height = 300
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (splash_width // 2)
        y = (screen_height // 2) - (splash_height // 2)
        self.splash_window.geometry(f"{splash_width}x{splash_height}+{x}+{y}")
        
        # Configuração da UI do Splash
        self.splash_window.grid_columnconfigure(0, weight=1)
        self.splash_window.grid_rowconfigure(0, weight=1)
        
        frame = ctk.CTkFrame(self.splash_window)
        frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(frame, text="Gerenciador RH +", 
                     font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(50, 5))
        
        self.splash_progress = ctk.CTkProgressBar(frame, orientation="horizontal", width=300, mode="indeterminate")
        self.splash_progress.pack(pady=20, padx=20)
        self.splash_progress.start()
        
        self.splash_label = ctk.CTkLabel(frame, text="Iniciando Sistema +...", font=ctk.CTkFont(size=14))
        self.splash_label.pack(pady=(5, 50))
        
        # Iniciar carregamento/animação em um thread
        threading.Thread(target=self.start_loading_process).start()

    def start_loading_process(self):
        """Simula um processo de carregamento com animação."""
        time.sleep(0.5)
        self.splash_label.configure(text="Carregando dados de usuários...")
        time.sleep(0.8)
        self.splash_label.configure(text="Verificando dependências...")
        
        # Simulação da animação de progressão
        for i in range(1, 101, 10):
            time.sleep(0.08)
            self.splash_label.configure(text=f"Preparando interface... ({i}%)")
        
        # Chama a próxima etapa na thread principal após a animação
        self.splash_window.after(100, self.setup_login_ui)

    def setup_login_ui(self):
        """Fecha a splash screen e inicia a tela de login."""
        self.splash_progress.stop()
        self.splash_window.destroy()
        self.show_login_frame()
        
    # --- FIM da Lógica da Animação Inicial ---

    def change_theme_event(self, new_selection):
        # O restante do método change_theme_event é mantido.
        theme_map = {"Claro": "Light", "Escuro": "Dark", "Sistema": "System"}
        mapped_mode = theme_map.get(new_selection, "System")
        ctk.set_appearance_mode(mapped_mode)
        self.credentials["theme"] = mapped_mode
        save_credentials(self.credentials)

    def start_http_server(self):
        # O restante do método start_http_server é mantido.
        Handler = SimpleHTTPRequestHandler
        try:
            self.httpd = ThreadingHTTPServer(("", SERVER_PORT), Handler)
            server_thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
            server_thread.start()
            print(f"Servidor HTTP iniciado em http://{SERVER_IP}:{SERVER_PORT}")
            return True
        except Exception as e:
            log_error("start_http_server", f"Não foi possível iniciar o servidor HTTP: {e}")
            messagebox.showwarning("Erro de Rede", f"Não foi possível iniciar o servidor HTTP na porta {SERVER_PORT}. O QR Code não funcionará por rede para dispositivos externos.")
            return False

    def on_closing(self):
        # O restante do método on_closing é mantido.
        if hasattr(self, 'httpd') and self.httpd:
            self.httpd.shutdown()
            print("Servidor HTTP parado.")
        self.destroy()

    def show_login_frame(self):
        # O restante do método show_login_frame é mantido.
        self.main_app_frame.grid_forget()
        self.create_login_frame()
        self.login_frame.grid(row=0, column=0, sticky="nsew")
        self.deiconify() # Mostra a janela principal após a splash screen

    def create_login_frame(self):
        # O restante do método create_login_frame é mantido.
        for widget in self.login_frame.winfo_children():
            widget.destroy()
        self.login_frame.grid_columnconfigure(0, weight=1)
        self.login_frame.grid_rowconfigure(0, weight=1)
        login_card = ctk.CTkFrame(self.login_frame, width=400, height=450, corner_radius=15)
        login_card.grid(row=0, column=0)
        login_card.pack_propagate(False)
        ctk.CTkLabel(login_card, text="🔐 Login Gerenciador RH +", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(40, 30))
        self.user_var = ctk.StringVar(value="")
        self.pass_var = ctk.StringVar(value="")
        ctk.CTkLabel(login_card, text="Usuário:", anchor="w").pack(fill='x', padx=50, pady=(5, 0))
        user_entry = ctk.CTkEntry(login_card, textvariable=self.user_var, placeholder_text="admin ou user")
        user_entry.pack(fill='x', padx=50, pady=(0, 15))
        ctk.CTkLabel(login_card, text="Senha:", anchor="w").pack(fill='x', padx=50, pady=(5, 0))
        pass_entry = ctk.CTkEntry(login_card, textvariable=self.pass_var, placeholder_text="1234")
        pass_entry.configure(show="*")
        pass_entry.pack(fill='x', padx=50, pady=(0, 30))
        ctk.CTkButton(login_card, text="🚪 Entrar", command=self.simulated_login, height=40).pack(fill='x', padx=50)
        ctk.CTkLabel(login_card, text="Versão: 1.0 / 2025 |™Desenvolvido por: Iago Nunes©", text_color="red").pack(pady=5)

    def simulated_login(self):
        # O restante do método simulated_login é mantido.
        username = self.user_var.get().strip().lower()
        password = self.pass_var.get().strip()
        self.credentials = load_credentials()
        credentials = self.credentials
        if username in credentials and credentials[username] == password:
            self.user_role = 'Admin' if username == 'admin' else 'User'
            self.login_frame.grid_forget()
            self.create_main_app_layout()
            messagebox.showinfo("Sucesso", f"Login efetuado como {self.user_role}.")
        else:
            messagebox.showerror("Erro de Login", "Credenciais inválidas. Verifique o usuário e a senha.")

    def logout(self):
        # O restante do método logout é mantido.
        if messagebox.askyesno("Sair", "Tem certeza que deseja fazer logout?"):
            if hasattr(self, 'httpd') and self.httpd:
                self.httpd.shutdown()
                self.httpd = None 
                print("Servidor HTTP parado.")
                
            self.user_role = None
            self.show_login_frame()
            messagebox.showinfo("Logout", "Sessão encerrada.")

    def create_main_app_layout(self):
        # O restante do método create_main_app_layout é mantido.
        self.main_app_frame.grid(row=0, column=0, sticky="nsew")
        self.main_app_frame.grid_columnconfigure(0, weight=0)
        self.main_app_frame.grid_columnconfigure(1, weight=1)
        self.main_app_frame.grid_rowconfigure(0, weight=1)
        
        self.create_sidebar_frame(self.main_app_frame)
        
        self.content_container = ctk.CTkFrame(self.main_app_frame, fg_color=self.main_app_frame.cget("fg_color"))
        self.content_container.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.content_container.grid_columnconfigure(0, weight=1)
        self.content_container.grid_rowconfigure(0, weight=1)
        
        self.content_frames = {}
        self.create_content_frames(self.content_container)
        self.atualizar_todas_as_listas()
        self.show_frame("geral")
        
        self.start_http_server()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_sidebar_frame(self, master):
        # O restante do método create_sidebar_frame é mantido.
        self.sidebar_frame = ctk.CTkFrame(master, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(8, weight=1)
        row_idx = 0
        ctk.CTkLabel(self.sidebar_frame, text="GERENCIADOR RH ➕", font=ctk.CTkFont(size=18, weight="bold")).grid(row=row_idx, column=0, padx=20, pady=(20, 10))
        row_idx += 1
        ctk.CTkLabel(self.sidebar_frame, text=f"Role: {self.user_role}", font=ctk.CTkFont(size=12, slant="italic")).grid(row=row_idx, column=0, padx=20, pady=(0, 20))
        row_idx += 1
        ctk.CTkButton(self.sidebar_frame, text="📅 Listagem", command=lambda: self.show_frame("geral")).grid(row=row_idx, column=0, padx=20, pady=10, sticky="ew")
        row_idx += 1
        ctk.CTkButton(self.sidebar_frame, text="Cadastro / Edição", command=lambda: self.show_frame("cadastro")).grid(row=row_idx, column=0, padx=20, pady=10, sticky="ew")
        row_idx += 1
        ctk.CTkButton(self.sidebar_frame, text="Ausências", command=lambda: self.show_frame("ausencias")).grid(row=row_idx, column=0, padx=20, pady=10, sticky="ew")
        row_idx += 1
        if self.user_role == 'Admin':
            ctk.CTkButton(self.sidebar_frame, text="Admin / BI", command=lambda: self.show_frame("admin_bi")).grid(row=row_idx, column=0, padx=20, pady=10, sticky="ew")
        row_idx += 1
        ctk.CTkLabel(self.sidebar_frame, text="🌓 Aparência:").grid(row=row_idx, column=0, padx=20, pady=(30, 0), sticky="sw")
        row_idx += 1
        saved_theme = self.credentials.get("theme", "System")
        theme_map_reverse = {"Light": "Claro", "Dark": "Escuro", "System": "Sistema"}
        initial_theme_pt = theme_map_reverse.get(saved_theme, "Sistema")
        self.theme_option_menu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Sistema", "Claro", "Escuro"], command=self.change_theme_event)
        self.theme_option_menu.set(initial_theme_pt)
        self.theme_option_menu.grid(row=row_idx, column=0, padx=20, pady=(5, 10), sticky="ew")
        row_idx += 1
        ctk.CTkButton(self.sidebar_frame, text="🔒 Alterar Senha", command=self.abrir_modal_alterar_senha, fg_color="#facc15", hover_color="#eab308").grid(row=row_idx, column=0, padx=20, pady=(10, 10), sticky="ew")
        ctk.CTkButton(self.sidebar_frame, text="🔴 Sair / Logout", command=self.logout, fg_color="#ef4444", hover_color="#dc2626").grid(row=9, column=0, padx=20, pady=(10, 20), sticky="s")


    def create_content_frames(self, master):
        # O restante do método create_content_frames é mantido.
        self.entries = {}
        self.ausencias_vars = {}
        self.content_frames["geral"] = self.criar_aba_geral(master)
        self.content_frames["cadastro"] = self.criar_aba_cadastro(master)
        self.content_frames["ausencias"] = self.criar_aba_ausencias(master)
        if self.user_role == 'Admin':
            self.content_frames["admin_bi"] = self.criar_aba_administracao(master)
        for name, frame in self.content_frames.items():
            frame.grid(row=0, column=0, sticky="nsew")

    def show_frame(self, frame_name):
        # O restante do método show_frame é mantido.
        if frame_name in self.content_frames:
            for frame in self.content_frames.values():
                frame.grid_remove()
            self.content_frames[frame_name].grid()
            if frame_name == "ausencias":
                self.atualizar_combo_usuarios_ausencias()
            elif frame_name == "cadastro":
                self.update_documento_label()
            elif frame_name == "admin_bi":
                if self.user_role == 'Admin':
                    self.atualizar_relatorios()
                    try:
                        texto = self.relatorio_texto.get("1.0", tk.END)
                        success = gerar_pdf_relatorio(PDF_RELATORIO, texto)
                        if success:
                            pass 
                        else:
                            messagebox.showwarning("PDF", "Não foi possível gerar o PDF do relatório. Verifique se 'reportlab' está instalado.")
                    except ImportError:
                        messagebox.showwarning("Dependência ausente", "A biblioteca 'reportlab' não está instalada. Para habilitar geração de PDF execute:\n\npip install reportlab")
                    except Exception as e:
                        log_error("show_frame_admin_pdf", str(e))
                        messagebox.showwarning("Erro", "Erro ao gerar PDF do relatório. Verifique o log.")


    def abrir_modal_alterar_senha(self):
        # O restante do método abrir_modal_alterar_senha é mantido.
        if hasattr(self, 'modal_senha') and self.modal_senha.winfo_exists():
            self.modal_senha.lift()
            return
        self.modal_senha = ctk.CTkToplevel(self)
        self.modal_senha.title(f"Alterar Senha ({self.user_role})")
        self.modal_senha.geometry("400x380")
        self.modal_senha.attributes('-topmost', 'true')
        self.modal_senha.resizable(False, False)
        x = self.winfo_x() + self.winfo_width() // 2 - 200
        y = self.winfo_y() + self.winfo_height() // 2 - 190
        self.modal_senha.geometry(f'+{x}+{y}')
        ctk.CTkLabel(self.modal_senha, text=f"ALTERAR SENHA PARA {self.user_role.upper()}", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=20)
        self.current_pass_var = ctk.StringVar()
        self.new_pass_var = ctk.StringVar()
        self.confirm_pass_var = ctk.StringVar()
        ctk.CTkLabel(self.modal_senha, text="Senha Atual:", anchor='w').pack(fill='x', padx=30, pady=(5, 0))
        ctk.CTkEntry(self.modal_senha, textvariable=self.current_pass_var, show="*").pack(fill='x', padx=30, pady=(0, 10))
        ctk.CTkLabel(self.modal_senha, text="Nova Senha:", anchor='w').pack(fill='x', padx=30, pady=(5, 0))
        ctk.CTkEntry(self.modal_senha, textvariable=self.new_pass_var, show="*").pack(fill='x', padx=30, pady=(0, 10))
        ctk.CTkLabel(self.modal_senha, text="Confirmar Nova Senha:", anchor='w').pack(fill='x', padx=30, pady=(5, 0))
        ctk.CTkEntry(self.modal_senha, textvariable=self.confirm_pass_var, show="*").pack(fill='x', padx=30, pady=(0, 20))
        ctk.CTkButton(self.modal_senha, text="Confirmar Alteração", command=self.process_alterar_senha, height=35).pack(fill='x', padx=30)
        self.modal_senha.protocol("WM_DELETE_WINDOW", self.modal_senha.destroy)

    def process_alterar_senha(self):
        # O restante do método process_alterar_senha é mantido.
        current_pass = self.current_pass_var.get()
        new_pass = self.new_pass_var.get()
        confirm_pass = self.confirm_pass_var.get()
        user_key = self.user_role.lower()
        if not all([current_pass, new_pass, confirm_pass]):
            messagebox.showerror("Erro de Senha", "Todos os campos de senha são obrigatórios.")
            return
        if new_pass != confirm_pass:
            messagebox.showerror("Erro de Senha", "A nova senha e a confirmação não coincidem.")
            return
        if len(new_pass) < 4:
            messagebox.showerror("Erro de Senha", "A nova senha deve ter pelo menos 4 caracteres.")
            return
        self.credentials = load_credentials()
        credentials = self.credentials
        if credentials.get(user_key) != current_pass:
            messagebox.showerror("Erro de Senha", "A Senha Atual informada está incorreta.")
            return
        credentials[user_key] = new_pass
        save_credentials(credentials)
        self.modal_senha.destroy()
        messagebox.showinfo("Sucesso", f"A senha para o usuário '{user_key}' foi alterada com sucesso!")


    def criar_aba_geral(self, master):
        # O restante do método criar_aba_geral é mantido.
        frame = ctk.CTkFrame(master)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(frame, text="LISTAGEM DE COLABORADORES", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, padx=10, pady=10)
        frame_listagem = ctk.CTkFrame(frame)
        frame_listagem.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        frame_listagem.grid_columnconfigure(0, weight=1)
        frame_listagem.grid_rowconfigure(0, weight=1)
        columns = ('ID', 'Nome', 'Cargo', 'E-mail', 'Modalidade', 'Salário (R$)')
        self.treeview_geral = ttk.Treeview(frame_listagem, columns=columns, show='headings')
        for col in columns:
            self.treeview_geral.heading(col, text=col)
            self.treeview_geral.column(col, anchor=tk.CENTER, width=150)
        style = ttk.Style()
        style.theme_use("default") 
        style.configure("Treeview.Heading", font=('Arial', 10, 'bold'), background="#3bf667", foreground="white")
        style.configure("Treeview", rowheight=25, font=('Arial', 10), fieldbackground="#fdfeff")
        self.treeview_geral.grid(row=0, column=0, sticky='nsew', padx=10, pady=5)
        self.treeview_geral.bind('<<TreeviewSelect>>', self.toggle_action_buttons)
        frame_botoes = ctk.CTkFrame(frame)
        frame_botoes.grid(row=2, column=0, sticky='ew', padx=10, pady=10)
        self.btn_editar = ctk.CTkButton(frame_botoes, text="Editar Selecionado", command=self.abrir_edicao_selecionada, state='disabled', fg_color="#facc15", hover_color="#eab308")
        self.btn_editar.pack(side='left', padx=10)
        self.btn_deletar = ctk.CTkButton(frame_botoes, text="Deletar Selecionado", command=self.deletar_usuario_selecionado, state='disabled', fg_color="#ef4444", hover_color="#dc2626")
        self.btn_deletar.pack(side='left', padx=10)
        return frame


    def update_documento_label(self, *args):
        # O restante do método update_documento_label é mantido.
        modalidade = self.modalidade_var.get()
        doc_entry = self.entries.get("Documento Fiscal")
        if modalidade == 'PJ':
            self.documento_label_var.set("Documento Fiscal (CNPJ):")
            if doc_entry: doc_entry.configure(placeholder_text="Ex: 00.000.000/0000-00")
        else:
            self.documento_label_var.set("Documento Fiscal (CPF):")
            if doc_entry: doc_entry.configure(placeholder_text="Ex: 000.000.000-00")

    def criar_aba_cadastro(self, master):
        # O restante do método criar_aba_cadastro é mantido.
        frame = ctk.CTkFrame(master)
        frame.grid_columnconfigure(0, weight=1)
        self.titulo_cadastro = ctk.CTkLabel(frame, text="Novo Cadastro de Colaborador", font=ctk.CTkFont(size=18, weight="bold"))
        self.titulo_cadastro.pack(pady=20)
        campos = ["Nome", "E-mail", "Telefone"]
        if self.user_role == 'Admin':
             campos.append("Salário (R$)")
        for i, campo in enumerate(campos):
            frame_campo = ctk.CTkFrame(frame, fg_color="green")
            frame_campo.pack(fill='x', padx=50, pady=5)
            ctk.CTkLabel(frame_campo, text=f"{campo}:", width=100, anchor='w').pack(side='left', padx=5)
            entry = ctk.CTkEntry(frame_campo)
            entry.pack(side='left', fill='x', expand=True, padx=5)
            self.entries[campo] = entry
        frame_documento = ctk.CTkFrame(frame, fg_color="blue")
        frame_documento.pack(fill='x', padx=50, pady=5)
        self.documento_label_var = tk.StringVar(value="Documento Fiscal (CPF):")
        ctk.CTkLabel(frame_documento, textvariable=self.documento_label_var, width=100, anchor='w').pack(side='left', padx=5)
        entry_doc = ctk.CTkEntry(frame_documento, placeholder_text="Ex: 000.000.000-00")
        entry_doc.pack(side='left', fill='x', expand=True, padx=5)
        self.entries["Documento Fiscal"] = entry_doc
        frame_modalidade = ctk.CTkFrame(frame, fg_color="green")
        frame_modalidade.pack(fill='x', padx=50, pady=5)
        ctk.CTkLabel(frame_modalidade, text="Modalidade:", width=100, anchor='w').pack(side='left', padx=5)
        self.modalidade_var = tk.StringVar(value='CLT')
        combo_modalidade = ctk.CTkComboBox(frame_modalidade, values=['CLT', 'PJ', 'ESTÁGIO'], variable=self.modalidade_var)
        combo_modalidade.pack(side='left', fill='x', expand=True, padx=5)
        self.modalidade_var.trace_add("write", self.update_documento_label)
        frame_cargo = ctk.CTkFrame(frame, fg_color="blue")
        frame_cargo.pack(fill='x', padx=50, pady=5)
        ctk.CTkLabel(frame_cargo, text="Cargo / Função:", width=100, anchor='w').pack(side='left', padx=5)
        entry_cargo = ctk.CTkEntry(frame_cargo, placeholder_text="Ex: Analista de RH")
        entry_cargo.pack(side='left', fill='x', expand=True, padx=5)
        self.entries["Cargo / Função"] = entry_cargo
        frame_data = ctk.CTkFrame(frame, fg_color="blue")
        frame_data.pack(fill='x', padx=50, pady=5)
        ctk.CTkLabel(frame_data, text="Data de Admissão (YYYY-MM-DD):", width=100, anchor='w').pack(side='left', padx=5)
        if TKCALENDAR_AVAILABLE:
            date_widget = DateEntry(frame_data, date_pattern='yyyy-mm-dd')
            date_widget.pack(side='left', fill='x', expand=True, padx=5)
            self.entries["Data de Admissão"] = date_widget
        else:
            entry_data = ctk.CTkEntry(frame_data, placeholder_text="Ex: 2025-10-17")
            entry_data.pack(side='left', fill='x', expand=True, padx=5)
            self.entries["Data de Admissão"] = entry_data
        frame_botoes = ctk.CTkFrame(frame, fg_color="blue")
        frame_botoes.pack(pady=20)
        self.btn_salvar_cadastro = ctk.CTkButton(frame_botoes, text="Salvar Cadastro", command=self.salvar_ou_atualizar_usuario)
        self.btn_salvar_cadastro.pack(side='left', padx=10)
        self.btn_cancelar_edicao = ctk.CTkButton(frame_botoes, text="Cancelar Edição", command=self.cancelar_edicao, fg_color="gray", hover_color="darkgray")
        self.update_documento_label()
        return frame

    def criar_aba_ausencias(self, master):
        # O restante do método criar_aba_ausencias é mantido.
        frame = ctk.CTkFrame(master)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        self.ausencia_tipo = tk.StringVar(value='')
        self.ausencia_data = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d")) # Corrigido o formato inicial para YYYY-MM-DD
        self.ausencia_obs = tk.StringVar(value='')
        frame_registro = ctk.CTkFrame(frame)
        frame_registro.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        ctk.CTkLabel(frame_registro, text="REGISTRAR NOVA AUSÊNCIA", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        frame_inputs = ctk.CTkFrame(frame_registro, fg_color="green")
        frame_inputs.pack(fill='x', padx=20, pady=5)
        ctk.CTkLabel(frame_inputs, text="Colaborador:").pack(side='left', padx=5)
        self.combo_ausencias_user = ctk.CTkComboBox(frame_inputs, command=self.atualizar_historico_ausencias, values=["Carregando..."], width=250)
        self.combo_ausencias_user.pack(side='left', padx=10)
        ctk.CTkLabel(frame_inputs, text="Data (YYYY-MM-DD):").pack(side='left', padx=5)
        ctk.CTkEntry(frame_inputs, textvariable=self.ausencia_data, width=120).pack(side='left', padx=5)
        ctk.CTkLabel(frame_inputs, text="Tipo:").pack(side='left', padx=5)
        ctk.CTkEntry(frame_inputs, textvariable=self.ausencia_tipo, width=150).pack(side='left', padx=5)
        ctk.CTkLabel(frame_inputs, text="Obs:").pack(side='left', padx=5)
        ctk.CTkEntry(frame_inputs, textvariable=self.ausencia_obs, width=200).pack(side='left', padx=5)
        frame_btn_container = ctk.CTkFrame(frame_registro, fg_color="green")
        frame_btn_container.pack(fill='x', padx=20, pady=(10,0))
        btn_registrar = ctk.CTkButton(frame_btn_container, text="Registrar Ausência", command=self.registrar_ausencia, fg_color="#3b82f6", width=200)
        btn_registrar.pack(pady=15)
        frame_historico = ctk.CTkFrame(frame)
        frame_historico.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        frame_historico.grid_columnconfigure(0, weight=1)
        frame_historico.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(frame_historico, text="HISTÓRICO DE AUSÊNCIAS", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=10, pady=10)
        columns = ('Data', 'Tipo', 'Observação')
        self.treeview_ausencias = ttk.Treeview(frame_historico, columns=columns, show='headings')
        self.treeview_ausencias.heading('Data', text='Data')
        self.treeview_ausencias.heading('Tipo', text='Tipo')
        self.treeview_ausencias.heading('Observação', text='Observação')
        self.treeview_ausencias.column('Data', width=100)
        self.treeview_ausencias.column('Tipo', width=150)
        self.treeview_ausencias.column('Observação', width=450)
        self.treeview_ausencias.grid(row=1, column=0, sticky='nsew', padx=10, pady=5)
        return frame

    def criar_aba_administracao(self, master):
        # O restante do método criar_aba_administracao é mantido.
        frame = ctk.CTkFrame(master)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        
        frame_botoes = ctk.CTkFrame(frame)
        frame_botoes.grid(row=0, column=0, sticky='ew', padx=10, pady=10)
        ctk.CTkLabel(frame_botoes, text="Exportação de Dados e Segurança:", font=ctk.CTkFont(weight="bold")).pack(side='left', padx=10)
        ctk.CTkButton(frame_botoes, text="Exportar Dados (Completo)", command=self.exportar_dados_csv).pack(side='left', padx=10)
        ctk.CTkButton(frame_botoes, text="Exportar Ausências (CSV Plano)", command=self.exportar_dados_ausencias_csv, fg_color="#facc15", hover_color="#eab308").pack(side='left', padx=10)
        ctk.CTkButton(frame_botoes, text="Fazer Backup", command=self.backup_dados).pack(side='left', padx=10)
        ctk.CTkButton(frame_botoes, text="Restaurar Backup", command=self.restaurar_dados).pack(side='left', padx=10)
        
        frame_relatorios = ctk.CTkFrame(frame)
        frame_relatorios.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        frame_relatorios.grid_columnconfigure(0, weight=1)
        frame_relatorios.grid_columnconfigure(1, weight=0)
        frame_relatorios.grid_rowconfigure(0, weight=1)

        frame_relatorio_txt = ctk.CTkFrame(frame_relatorios)
        frame_relatorio_txt.grid(row=0, column=0, sticky='nsew', padx=(10, 5), pady=10)
        frame_relatorio_txt.grid_rowconfigure(1, weight=1)
        frame_relatorio_txt.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frame_relatorio_txt, text="RELATÓRIOS E BI", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=10, pady=(0, 5), sticky='w')

        self.relatorio_texto = ctk.CTkTextbox(frame_relatorio_txt, wrap='word', activate_scrollbars=True)
        self.relatorio_texto.grid(row=1, column=0, sticky='nsew', padx=10, pady=(0, 10))

        frame_qr_area = ctk.CTkFrame(frame_relatorios)
        frame_qr_area.grid(row=0, column=1, sticky='ns', padx=(5, 10), pady=10)
        frame_qr_area.grid_columnconfigure(0, weight=1)
        
        self.btn_qr_toggle = ctk.CTkButton(frame_qr_area, text="Gerar QR Code", command=self.toggle_qr_code, fg_color="#10b981", height=40)
        self.btn_qr_toggle.grid(row=0, column=0, padx=10, pady=(10, 5), sticky='ew')

        self.qr_container = ctk.CTkFrame(frame_qr_area, width=170, height=170) 
        self.qr_container.grid(row=1, column=0, sticky='n', padx=10, pady=(5, 10))
        self.qr_container.grid_propagate(False)

        self.atualizar_relatorios()
        return frame

    def atualizar_todas_as_listas(self):
        # O restante do método atualizar_todas_as_listas é mantido.
        self.dados_usuarios = carregar_dados()
        if hasattr(self, 'treeview_geral') and self.treeview_geral:
            self.treeview_geral.delete(*self.treeview_geral.get_children())
            for user in self.dados_usuarios:
                salario_exibido = formatar_moeda(user.get('salario', 0.0))
                self.treeview_geral.insert('', tk.END, values=(
                    user.get('id'),
                    user.get('nome'),
                    user.get('cargo', '—'),
                    user.get('email'),
                    user.get('modalidade'),
                    salario_exibido
                ))
        if hasattr(self, 'combo_ausencias_user') and self.combo_ausencias_user:
            self.atualizar_combo_usuarios_ausencias(event=None)
        if self.user_role == 'Admin' and hasattr(self, 'relatorio_texto'):
            self.atualizar_relatorios()

    def atualizar_combo_usuarios_ausencias(self, event=None):
        # O restante do método atualizar_combo_usuarios_ausencias é mantido.
        if hasattr(self, 'combo_ausencias_user') and self.combo_ausencias_user:
            self.user_map = {
                f"{user.get('nome', 'N/A')} (ID: {user.get('id', 'N/A')})": user.get('id', None)
                for user in self.dados_usuarios
            }
            usuarios_nomes = list(self.user_map.keys())
            self.combo_ausencias_user.configure(values=usuarios_nomes)
            if usuarios_nomes:
                current_selection = self.combo_ausencias_user.get()
                if current_selection not in usuarios_nomes:
                    self.combo_ausencias_user.set(usuarios_nomes[0])
                self.atualizar_historico_ausencias()
            else:
                self.combo_ausencias_user.set("Nenhum Colaborador")
                if hasattr(self, 'treeview_ausencias') and self.treeview_ausencias:
                    self.treeview_ausencias.delete(*self.treeview_ausencias.get_children())

    def registrar_ausencia(self):
        # O restante do método registrar_ausencia é mantido.
        selected_user_text = self.combo_ausencias_user.get()
        ausencia_data = self.ausencia_data.get().strip()
        ausencia_tipo = self.ausencia_tipo.get().strip().upper()
        ausencia_obs = self.ausencia_obs.get().strip()
        if not selected_user_text or selected_user_text == "Nenhum Colaborador":
            messagebox.showerror("Erro de Ausência", "Selecione um colaborador.")
            return
        if not ausencia_tipo:
            messagebox.showerror("Erro de Ausência", "O campo 'Tipo' é obrigatório.")
            return
        try:
            validar_data(ausencia_data, formato='%Y-%m-%d')
        except ValueError as ve:
            messagebox.showerror("Erro de Data", str(ve))
            return
        user_id = self.user_map.get(selected_user_text)
        if user_id is None:
            messagebox.showerror("Erro", "Selecione um colaborador válido da lista.")
            return
        try:
            for user in self.dados_usuarios:
                if user.get('id') == user_id:
                    if 'historico_ausencias' not in user:
                        user['historico_ausencias'] = []
                    nova_ausencia = {'data': ausencia_data, 'tipo': ausencia_tipo, 'observacao': ausencia_obs}
                    user['historico_ausencias'].append(nova_ausencia)
                    salvar_dados(self.dados_usuarios)
                    nome = user.get('nome')
                    messagebox.showinfo("Sucesso", f"Ausência registrada para {nome}.")
                    self.ausencia_tipo.set("")
                    self.ausencia_obs.set("")
                    self.atualizar_historico_ausencias()
                    return
            messagebox.showerror("Erro", "Colaborador não encontrado para registro.")
        except Exception as e:
            log_error("registrar_ausencia", f"Erro inesperado no registro de ausência. Detalhes: {e}")
            messagebox.showerror("Erro Inesperado", f"Ocorreu um erro ao registrar a ausência.")

    def atualizar_historico_ausencias(self, event=None):
        # O restante do método atualizar_historico_ausencias é mantido.
        if hasattr(self, 'treeview_ausencias') and self.treeview_ausencias:
            self.treeview_ausencias.delete(*self.treeview_ausencias.get_children())
        selected_user_text = self.combo_ausencias_user.get()
        if not selected_user_text or selected_user_text == "Nenhum Colaborador":
            return
        user_id = self.user_map.get(selected_user_text)
        if user_id is None: return
        usuario = next((user for user in self.dados_usuarios if user.get('id') == user_id), None)
        if usuario and 'historico_ausencias' in usuario and len(usuario['historico_ausencias']) > 0:
            historico_ordenado = sorted(usuario['historico_ausencias'], key=lambda x: x['data'], reverse=True)
            for ausencia in historico_ordenado:
                self.treeview_ausencias.insert('', tk.END, values=(ausencia.get('data', 'N/A'), ausencia.get('tipo', 'N/A'), ausencia.get('observacao', '')))
        elif hasattr(self, 'treeview_ausencias') and self.treeview_ausencias:
            self.treeview_ausencias.insert('', tk.END, values=('N/A', 'NENHUM REGISTRO ENCONTRADO.', ''), tags=('placeholder'))

    def atualizar_titulo_cadastro(self):
        # O restante do método atualizar_titulo_cadastro é mantido.
        if self.editando_id is not None:
            self.titulo_cadastro.configure(text=f"Editando Colaborador (ID: {self.editando_id})")
            self.btn_salvar_cadastro.configure(text="Salvar Alterações")
            self.btn_cancelar_edicao.pack(side='left', padx=10)
        else:
            self.titulo_cadastro.configure(text="Novo Cadastro de Colaborador")
            self.btn_salvar_cadastro.configure(text="Salvar Cadastro")
            self.btn_cancelar_edicao.pack_forget()

    def limpar_formulario_cadastro(self):
        # O restante do método limpar_formulario_cadastro é mantido.
        campos_para_limpar = ["Nome", "E-mail", "Telefone", "Documento Fiscal", "Cargo / Função"]
        for campo in campos_para_limpar:
            entry = self.entries.get(campo)
            if entry:
                try:
                    entry.delete(0, tk.END)
                except Exception:
                    pass
                try:
                    entry.configure(placeholder_text="")
                except Exception:
                    pass
        if self.user_role == 'Admin' and self.entries.get("Salário (R$)"):
            try:
                self.entries["Salário (R$)"].delete(0, tk.END)
            except Exception:
                pass
        data_widget = self.entries.get("Data de Admissão")
        if data_widget:
            try:
                if TKCALENDAR_AVAILABLE and hasattr(data_widget, 'set_date'):
                    data_widget.set_date(datetime.now())
                else:
                    data_widget.delete(0, tk.END)
                    data_widget.insert(0, datetime.now().strftime('%Y-%m-%d'))
            except Exception:
                pass
        self.modalidade_var.set('CLT')
        self.update_documento_label()

    def cancelar_edicao(self):
        # O restante do método cancelar_edicao é mantido.
        self.limpar_formulario_cadastro()
        self.editando_id = None
        messagebox.showinfo("Cancelado", "Modo de edição cancelado. Pronto para novo cadastro.")
        self.atualizar_titulo_cadastro()
        self.toggle_action_buttons()

    def validar_documento_fiscal(self, documento, modalidade):
        # O restante do método validar_documento_fiscal é mantido.
        doc_limpo = re.sub(r'[^0-9]', '', documento)
        if not doc_limpo:
            raise ValueError(f"O campo Documento Fiscal ({modalidade}) é obrigatório.")
        if modalidade == 'PJ':
            if len(doc_limpo) != 14:
                raise ValueError("CNPJ inválido. Deve conter 14 dígitos numéricos.")
        else:
            if len(doc_limpo) != 11:
                raise ValueError("CPF inválido. Deve conter 11 dígitos numéricos.")
        return doc_limpo

    def validar_dados_usuario(self, nome, email, telefone, salario_str, modalidade):
        # O restante do método validar_dados_usuario é mantido.
        EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        TELEFONE_REGEX = r'^\+?[0-9\s()-]{8,20}$'
        if not all([nome, email, telefone, modalidade]):
            raise ValueError("Campos Nome, E-mail, Telefone e Modalidade são obrigatórios.")
        if not re.match(EMAIL_REGEX, email):
            raise ValueError("O E-mail fornecido não é válido.")
        if not re.match(TELEFONE_REGEX, telefone):
            raise ValueError("O Telefone fornecido não é válido. Use um formato aceitável.")
        salario = 0.0
        if self.user_role == 'Admin':
            try:
                salario = string_para_float(salario_str)
                if salario < 0: raise ValueError
            except ValueError:
                raise ValueError("O Salário deve ser um número válido e positivo.")
        return salario

    def salvar_ou_atualizar_usuario(self):
        # O restante do método salvar_ou_atualizar_usuario é mantido.
        try:
            nome = self.entries["Nome"].get().strip().capitalize()
            email = self.entries["E-mail"].get().strip().lower()
            telefone = self.entries["Telefone"].get().strip()
            modalidade = self.modalidade_var.get().strip().upper()
            salario_str = self.entries.get("Salário (R$)").get() if self.user_role == 'Admin' and self.entries.get("Salário (R$)") else '0'
            documento_str = self.entries.get("Documento Fiscal").get().strip()
            cargo = self.entries.get("Cargo / Função").get().strip() if self.entries.get("Cargo / Função") else '—'
            data_widget = self.entries.get("Data de Admissão")
            if data_widget:
                try:
                    if TKCALENDAR_AVAILABLE and hasattr(data_widget, 'get_date'):
                        data_admissao = data_widget.get_date().strftime('%Y-%m-%d')
                    else:
                        data_admissao = data_widget.get().strip()
                except Exception:
                    data_admissao = data_widget.get().strip() if hasattr(data_widget, 'get') else ''
            else:
                data_admissao = datetime.now().strftime('%Y-%m-%d')
            salario = self.validar_dados_usuario(nome, email, telefone, salario_str, modalidade)
            documento_fiscal_limpo = self.validar_documento_fiscal(documento_str, modalidade)
            try:
                validar_data(data_admissao, formato='%Y-%m-%d')
            except ValueError as ve:
                raise ValueError(f"Data de Admissão inválida: {ve}")
            for user in self.dados_usuarios:
                if user.get('email', '').lower() == email and user.get('id') != self.editando_id:
                    raise ValueError(f"O E-mail '{email}' já está sendo usado por outro colaborador (ID: {user.get('id')}).")
            novo_dados = {'nome': nome, 'email': email, 'telefone': telefone, 'modalidade': modalidade, 'salario': salario if self.user_role == 'Admin' else 0.0, 'documento_fiscal': documento_fiscal_limpo, 'cargo': cargo, 'data_admissao': data_admissao}
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
                        historico = user.get('historico_ausencias', [])
                        user.update(novo_dados)
                        user['historico_ausencias'] = historico
                        messagebox.showinfo("Sucesso", f"Usuário ID: {self.editando_id} atualizado com sucesso!")
                        break
                self.editando_id = None
                self.atualizar_titulo_cadastro()
            salvar_dados(self.dados_usuarios)
            self.limpar_formulario_cadastro()
            self.atualizar_todas_as_listas()
        except ValueError as ve:
            messagebox.showerror("Erro de Cadastro", str(ve))
        except Exception as e:
            messagebox.showerror("Erro Inesperado", f"Ocorreu um erro ao salvar/atualizar: {e}. Verifique o log de erros.")

    def toggle_action_buttons(self, event=None):
        # O restante do método toggle_action_buttons é mantido.
        if self.editando_id is not None:
            self.btn_editar.configure(state='disabled')
            self.btn_deletar.configure(state='disabled')
            return
        if self.treeview_geral.selection():
            self.btn_editar.configure(state='normal')
            self.btn_deletar.configure(state='normal')
        else:
            self.btn_editar.configure(state='disabled')
            self.btn_deletar.configure(state='disabled')

    def abrir_edicao_selecionada(self):
        # O restante do método abrir_edicao_selecionada é mantido.
        selecao = self.treeview_geral.selection()
        if not selecao:
            messagebox.showerror("Erro", "Nenhum colaborador selecionado para edição.")
            return
        try:
            item_id = self.treeview_geral.item(selecao[0], 'values')[0]
            user_id = int(item_id)
        except (IndexError, ValueError) as e:
            messagebox.showerror("Erro", "ID de usuário inválido ou linha de lista vazia.")
            return
        usuario = next((user for user in self.dados_usuarios if user.get('id') == user_id), None)
        if usuario:
            self.editando_id = user_id
            self.show_frame("cadastro")
            self.atualizar_titulo_cadastro()
            self.toggle_action_buttons()
            self.limpar_formulario_cadastro()
            campos_map = {"Nome": 'nome', "E-mail": 'email', "Telefone": 'telefone', "Documento Fiscal": 'documento_fiscal', "Cargo / Função": 'cargo', "Data de Admissão": 'data_admissao'}
            for campo_ui, campo_data in campos_map.items():
                entry = self.entries.get(campo_ui)
                if entry and campo_data in usuario:
                    value = usuario.get(campo_data, '')
                    try:
                        if TKCALENDAR_AVAILABLE and campo_ui == "Data de Admissão" and hasattr(entry, 'set_date'):
                            try:
                                entry.set_date(datetime.strptime(value, '%Y-%m-%d'))
                            except Exception:
                                try:
                                    entry.set_date(value)
                                except Exception:
                                    pass
                        else:
                            entry.insert(0, value)
                    except Exception:
                        try:
                            entry.insert(0, value)
                        except Exception:
                            pass
            if self.user_role == 'Admin' and self.entries.get("Salário (R$)"):
                salario_entry = self.entries["Salário (R$)"]
                salario_entry.insert(0, f"{usuario.get('salario', 0.0):.2f}".replace('.', ','))
            self.modalidade_var.set(usuario.get('modalidade', 'CLT'))

    def deletar_usuario_selecionado(self):
        # O restante do método deletar_usuario_selecionado é mantido.
        selecao = self.treeview_geral.selection()
        if not selecao:
            messagebox.showerror("Erro", "Nenhum colaborador selecionado para deletar.")
            return
        try:
            item_data = self.treeview_geral.item(selecao[0], 'values')
            user_id = int(item_data[0])
            nome_usuario = item_data[1] if len(item_data) > 1 else f"ID {user_id}"
        except (IndexError, ValueError):
            messagebox.showerror("Erro", "ID de usuário inválido ou linha de lista corrompida.")
            return
        if messagebox.askyesno("Confirmação de Deleção", f"Tem certeza que deseja deletar o usuário {nome_usuario} (ID: {user_id})?"):
            self.dados_usuarios = [user for user in self.dados_usuarios if user.get('id') != user_id]
            salvar_dados(self.dados_usuarios)
            messagebox.showinfo("Sucesso", f"Usuário {nome_usuario} deletado.")
            self.atualizar_todas_as_listas()
            self.toggle_action_buttons()

    def atualizar_relatorios(self):
        # O restante do método atualizar_relatorios é mantido.
        if self.user_role != 'Admin': return
        self.relatorio_texto.configure(state='normal')
        self.relatorio_texto.delete("1.0", tk.END)
        
        total_funcionarios = len(self.dados_usuarios)
        
        salarios_validos = [user.get('salario', 0) for user in self.dados_usuarios if user.get('salario', 0) is not None and user.get('salario', 0) > 0]
        total_salario = sum(salarios_validos)
        count_com_salario = len(salarios_validos)
        
        contagem_modalidade = defaultdict(int)
        for user in self.dados_usuarios:
            contagem_modalidade[user.get('modalidade', 'N/A').upper()] += 1
            
        relatorio_str = "=================================================\n"
        relatorio_str += "    RELATÓRIO DE BUSINESS INTELLIGENCE (BI)      \n"
        relatorio_str += "=================================================\n\n\n"
        
        relatorio_str += "--- 1. DADOS GERAIS DO QUADRO ---\n"
        relatorio_str += f"Total de Colaboradores Registrados: {total_funcionarios}\n"
        
        relatorio_str += "\n\n\n"

        relatorio_str += "--- 2. CUSTO SALARIAL ---\n"
        
        salario_formatado = formatar_moeda(total_salario)
        relatorio_str += f"Custo Salarial Total (registrado): {salario_formatado}\n"
        
        salario_medio = total_salario / count_com_salario if count_com_salario > 0 else 0
        salario_medio_formatado = formatar_moeda(salario_medio)
        relatorio_str += f"Salário Médio (base de {count_com_salario} registros): {salario_medio_formatado}\n"
        
        relatorio_str += "\n\n\n"

        relatorio_str += "--- 3. DISTRIBUIÇÃO POR MODALIDADE ---\n"
        for mod, count in sorted(contagem_modalidade.items()):
            percentual = (count / total_funcionarios) * 100 if total_funcionarios > 0 else 0
            relatorio_str += f"- {mod}: {count} colaboradores ({percentual:.1f}%)\n"
            
        relatorio_str += "\n\n\n"
        
        relatorio_str += "--- 4. ANÁLISE DE AUSÊNCIAS (CONTAGEM DE OCORRÊNCIAS) ---\n"
        contagem_ausencias = defaultdict(int)
        for user in self.dados_usuarios:
            for ausencia in user.get('historico_ausencias', []):
                contagem_ausencias[ausencia.get('tipo', 'OUTRO').upper()] += 1
                
        if contagem_ausencias:
            for tipo, count in sorted(contagem_ausencias.items(), key=lambda item: item[1], reverse=True):
                relatorio_str += f"- Total de registros de {tipo}: {count}\n"
        else:
            relatorio_str += "Nenhum registro de ausência encontrado.\n"
        
        self.relatorio_texto.insert("1.0", relatorio_str)
        self.relatorio_texto.configure(state='disabled')

    def exportar_dados_csv(self):
        # O restante do método exportar_dados_csv é mantido.
        if self.user_role != 'Admin':
             messagebox.showwarning("Acesso Negado", "Você não tem permissão de Administrador para exportar dados.")
             return
        if not self.dados_usuarios:
            messagebox.showwarning("Exportar", "Não há dados para exportar.")
            return
        try:
            filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Arquivos CSV", "*.csv")], initialfile="colaboradores_completo.csv")
            if not filepath: return
            headers = ['id', 'nome', 'cargo', 'data_admissao', 'email', 'telefone', 'modalidade', 'salario', 'documento_fiscal', 'historico_ausencias']
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore', delimiter=';')
                writer.writeheader()
                dados_para_csv = []
                for user in self.dados_usuarios:
                    user_copy = user.copy()
                    user_copy['historico_ausencias'] = json.dumps(user_copy.get('historico_ausencias', []))
                    dados_para_csv.append(user_copy)
                writer.writerows(dados_para_csv)
            messagebox.showinfo("Sucesso na Exportação", f"Dados exportados com sucesso para:\\n{filepath}")
        except Exception as e:
            messagebox.showerror("Erro de Exportação", f"Não foi possível exportar os dados:\\n{e}. Verifique o log de erros.")

    def exportar_dados_ausencias_csv(self):
        # O restante do método exportar_dados_ausencias_csv é mantido.
        if self.user_role != 'Admin':
            messagebox.showwarning("Acesso Negado", "Você não tem permissão de Administrador para exportar dados.")
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Arquivos CSV", "*.csv")], initialfile="ausencias_plano.csv")
        if not filepath: return
        try:
            output = StringIO()
            writer = csv.writer(output, delimiter=';', lineterminator='\n')
            headers = ['ID_Colaborador', 'Nome', 'Data_Ausencia', 'Tipo_Ausencia', 'Observacao']
            writer.writerow(headers)
            for user in self.dados_usuarios:
                user_id = user.get('id')
                user_nome = user.get('nome', 'N/A')
                historico = user.get('historico_ausencias', [])
                for ausencia in historico:
                    writer.writerow([user_id, user_nome, ausencia.get('data', 'N/A'), ausencia.get('tipo', 'N/A'), ausencia.get('observacao', '').replace('\n', ' ')])
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                f.write(output.getvalue())
            messagebox.showinfo("Sucesso na Exportação", f"CSV Plano de Ausências exportado com sucesso para:\\n{filepath}")
        except Exception as e:
            log_error("exportar_dados_ausencias_csv", f"Falha na exportação CSV Plano. Detalhes: {e}")
            messagebox.showerror("Erro de Exportação", f"Não foi possível exportar o CSV Plano:\\n{e}.")

    def backup_dados(self):
        # O restante do método backup_dados é mantido.
        if self.user_role != 'Admin':
             messagebox.showwarning("Acesso Negado", "Você não tem permissão de Administrador para backup.")
             return
        if not os.path.exists(NOME_ARQUIVO):
            messagebox.showwarning("Backup", f"Arquivo de dados '{NOME_ARQUIVO}' não encontrado.")
            return
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_nome = f"backup_{timestamp}_{NOME_ARQUIVO}"
        try:
            shutil.copyfile(NOME_ARQUIVO, backup_nome)
            messagebox.showinfo("Backup Concluído", f"Backup criado com sucesso:\\n{backup_nome}")
        except Exception as e:
            messagebox.showerror("Erro de Backup", f"Não foi possível criar o backup: {e}. Verifique o log de erros.")

    def restaurar_dados(self):
        # O restante do método restaurar_dados é mantido.
        if self.user_role != 'Admin':
             messagebox.showwarning("Acesso Negado", "Você não tem permissão de Administrador para restaurar dados.")
             return
        if not messagebox.askyesno("Confirmação de Restauração", "ATENÇÃO: Isso irá sobrescrever todos os dados atuais. Deseja continuar?"):
            return
        try:
            filepath = filedialog.askopenfilename(defaultextension=".json", filetypes=[("Arquivos JSON", "*.json")])
            if not filepath: return
            with open(filepath, 'r', encoding='utf-8') as f:
                novos_dados = json.load(f)
            if not isinstance(novos_dados, list) or not all(isinstance(item, dict) for item in novos_dados):
                messagebox.showerror("Erro de Restauração", "O arquivo JSON não parece ser um formato de lista de colaboradores válido.")
                return
            salvar_dados(novos_dados)
            self.atualizar_todas_as_listas()
            messagebox.showinfo("Restauração Concluída", f"Dados restaurados com sucesso a partir de:\\n{filepath}")
        except json.JSONDecodeError:
            messagebox.showerror("Erro de Restauração", "O arquivo selecionado não é um JSON válido.")
        except Exception as e:
            messagebox.showerror("Erro de Restauração", f"Não foi possível restaurar os dados: {e}. Verifique o log de erros.")

    def toggle_qr_code(self):
        # O restante do método toggle_qr_code é mantido.
        if self.qr_visible:
            for widget in self.qr_container.winfo_children():
                widget.destroy()
            self.qr_visible = False
            self.btn_qr_toggle.configure(text="Gerar QR Code")
            return
        if not QRCODE_AVAILABLE:
            messagebox.showwarning("Dependência ausente", "A biblioteca 'qrcode' não está instalada. Para habilitar QR Code execute:\n\npip install qrcode[pil]")
            return
            
        uri = PDF_URL_LOCAL 

        try:
            qr = qrcode.make(uri)
            qr = qr.resize((200, 200))
            qr_tk = ImageTk.PhotoImage(qr)
            
            for widget in self.qr_container.winfo_children():
                widget.destroy()
            
            lbl = tk.Label(self.qr_container, image=qr_tk)
            lbl.image = qr_tk
            lbl.pack(pady=10) 
            
            self.qr_visible = True
            self.btn_qr_toggle.configure(text="Esconder QR Code (Gerado)")
        except Exception as e:
            log_error("toggle_qr_code", str(e))
            messagebox.showerror("Erro QR", "Não foi possível gerar o QR Code. Verifique dependências e permissões. Tente iniciar o servidor manualmente se necessário.")

if __name__ == "__main__":
    if not os.path.exists(NOME_ARQUIVO):
        salvar_dados(carregar_dados())
    if not REPORTLAB_AVAILABLE:
        pass
        
    # Assegura que o arquivo de credenciais exista
    load_credentials() 
    
    app = LateralApp()
    app.mainloop()