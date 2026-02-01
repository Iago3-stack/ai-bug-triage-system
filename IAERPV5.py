# sistemaRH_final_v16_pdf_layout_organizado.py
# Versão final v16 — Correção: Layout do PDF para melhor organização (Espaçamento, 5 Colunas)

import os
import sys
import json
import datetime
import random
import traceback
import warnings
import shutil 
from pathlib import Path
import math
import io
import csv
from tkinter import messagebox, filedialog, ttk
import tkinter
import os 
import socket 
import threading 
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer 

from matplotlib import colors
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def centralizar_janela(janela, largura, altura):
    janela.update_idletasks()
    largura_tela = janela.winfo_screenwidth()
    altura_tela = janela.winfo_screenheight()
    x = (largura_tela // 2) - (largura // 2)
    y = (altura_tela // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")
    #janela.update()  # 🔥 força o posicionamento exato


# GUI libs
try:
    import customtkinter as ctk
except Exception as e:
    raise RuntimeError("Instale customtkinter: pip install customtkinter") from e

from PIL import Image, ImageDraw, ImageFont, ImageTk
try:
    RESAMPLING_NEAREST = Image.Resampling.NEAREST
except AttributeError:
    RESAMPLING_NEAREST = Image.NEAREST
    
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False
    
try:
    import qrcode
    from qrcode import constants as qrcode_constants
    QRCODE_AVAILABLE = True
except Exception:
    QRCODE_AVAILABLE = False

# ----------------------------
# Safety patches & warnings suppression
# ----------------------------
warnings.filterwarnings("ignore", category=UserWarning)

try:
    _tk_after = tkinter.Misc.after
    def _safe_after(self, ms, func=None, *args):
        try:
            if not getattr(self, "winfo_exists", lambda: True)():
                return None
        except Exception:
            return None
        try:
            return _tk_after(self, ms, func, *args)
        except Exception:
            return None
    tkinter.Misc.after = _safe_after
except Exception:
    pass

# ----------------------------
# Paths & config
# ----------------------------
ROOT = Path("dados_sistema")
PDFS = ROOT / "pdfs_compartilhados"
BACKUPS = ROOT / "backups"
DATA_FILE = ROOT / "colaboradores.json"
CONFIG_FILE = ROOT / "config.json"
QR_IMAGE = ROOT / "qr_relatorio.png"
ICON_LOGIN = ROOT / "icon_login.png" 
ICON_SPLASH = ROOT / "icon_splash.png" 
ROOT.mkdir(parents=True, exist_ok=True)
PDFS.mkdir(parents=True, exist_ok=True)
BACKUPS.mkdir(parents=True, exist_ok=True)

# ----------------------------
# Configuração do Servidor HTTP Local (QR Code)
# ----------------------------
SERVER_PORT = 8000
PDF_SERVER_NAME = "relatorio_bi.pdf" 

try:
    SERVER_IP = socket.gethostbyname(socket.gethostname())
    if SERVER_IP == "127.0.0.1": 
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        SERVER_IP = s.getsockname()[0]
        s.close()
except Exception:
    SERVER_IP = "127.0.0.1" 
    
PDF_URL_LOCAL = f"http://{SERVER_IP}:{SERVER_PORT}/{PDF_SERVER_NAME}"

class LocalFileHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PDFS), **kwargs)

    def log_message(self, format, *args):
        if "GET" in format and PDF_SERVER_NAME in args:
             print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] HTTP: Servido: {args[0]} - {args[1]}")
        pass 

class HTTPServerThread(threading.Thread):
    def __init__(self, host, port, handler_class):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.handler_class = handler_class
        self.httpd = None
        self.is_running = False

    def run(self):
        try:
            self.httpd = ThreadingHTTPServer(('0.0.0.0', self.port), self.handler_class)
            self.is_running = True
            print(f"🌐 Servidor HTTP iniciado em http://{self.host}:{self.port}")
            self.httpd.serve_forever()
        except OSError as e:
            if "Address already in use" in str(e):
                 print(f"ERRO: A porta {self.port} já está em uso. O servidor HTTP não pôde ser iniciado. O QR Code não funcionará. Tente fechar outros programas ou reiniciar o app.")
            else:
                 print(f"ERRO ao iniciar servidor HTTP: {e}")
            self.is_running = False
        except Exception as e:
            print(f"Erro inesperado no servidor HTTP: {e}")
            self.is_running = False

    def stop(self):
        if self.httpd:
            print("🌐 Servidor HTTP parado.")
            self.httpd.shutdown()
            self.httpd.server_close()
            self.is_running = False

# ----------------------------
# Funções de Dados e Config
# ----------------------------
def ensure_config():
    if not CONFIG_FILE.exists():
        default = {"users": {"admin": "1234"}, "theme": "dark"}
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return {"users": {"admin":"1234"}, "theme":"dark"}

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

def ensure_data():
    if not DATA_FILE.exists():
        sample = [
            {
                "Nome": "João Silva",
                "E-mail": "joao.silva@empresa.com",
                "Telefone": "(11) 98888-7777",
                "Cargo/Função": "Analista de RH",
                "TipoVinculo": "CLT",
                "Documento": "123.456.789-00",
                "Salario": "R$ 4.500,00",
                "Data de Admissão": "2022-03-14",
                "Observações": "",
                "Ausências": [{"Data": "2024-02-05", "Motivo": "Doença"}]
            }
        ]
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(sample, f, ensure_ascii=False, indent=2)
            
def load_data():
    ensure_data()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ----------------------------
# Appearance init & Utilities
# ----------------------------
cfg = ensure_config()
DEFAULT_THEME = cfg.get("theme", "dark")
ctk.set_appearance_mode(DEFAULT_THEME)
ctk.set_default_color_theme("green")


def ts():
    return datetime.datetime.now().strftime("%d%m%Y %H%M%S")

# ----------------------------
# Vector icons generation 
# ----------------------------
def create_login_padlock(size=180, bg=(30,58,138), fg=(255,255,255)):
    img = Image.new("RGBA", (size, size), bg + (255,))
    draw = ImageDraw.Draw(img)
    w, h = size, size
    body_w = int(w*0.52); body_h = int(h*0.38)
    body_x = (w - body_w)//2; body_y = int(h*0.34)
    draw.rounded_rectangle([body_x, body_y, body_x+body_w, body_y+body_h], radius=int(body_w*0.08), fill=fg)
    inner_w = int(body_w*0.16)
    inner_x = (w - inner_w)//2
    inner_y = body_y + int(body_h*0.2)
    draw.ellipse([inner_x, inner_y, inner_x+inner_w, inner_y+inner_w], fill=bg)
    draw.rectangle([inner_x + inner_w//2 - inner_w//10, inner_y+inner_w, inner_x + inner_w//2 + inner_w//10, inner_y+inner_w + int(body_h*0.22)], fill=bg)
    sh_w = int(body_w*0.92); sh_h = int(body_h*0.9)
    sh_x = (w - sh_w)//2; sh_y = body_y - int(sh_h*0.6)
    outer = Image.new("RGBA",(w,h),(0,0,0,0)); od = ImageDraw.Draw(outer)
    od.rounded_rectangle([sh_x, sh_y, sh_x+sh_w, sh_y+sh_h], radius=int(sh_w*0.5), fill=fg)
    inner = Image.new("RGBA",(w,h),(0,0,0,0)); idraw = ImageDraw.Draw(inner)
    margin = int(sh_w*0.20)
    idraw.rounded_rectangle([sh_x+margin, sh_y+margin//2, sh_x+sh_w-margin, sh_y+sh_h-margin], radius=int((sh_w-margin)*0.5), fill=bg)
    img = Image.alpha_composite(img, outer)
    img = Image.alpha_composite(img, inner)
    k_w = int(w*0.28); k_h = int(h*0.08)
    kx = body_x + body_w - int(k_w*0.6); ky = body_y + body_h - int(k_h*0.9)
    draw.rectangle([kx, ky, kx+int(k_w*0.6), ky+k_h], fill=bg)
    draw.ellipse([kx+int(k_w*0.6)-int(k_h*0.5), ky-int(k_h*0.7), kx+k_w, ky+k_h+int(k_h*0.7)], fill=bg)
    tooth_x = kx + int(k_w*0.08); tooth_y = ky + int(k_h*0.22)
    draw.rectangle([tooth_x, tooth_y, tooth_x + int(k_w*0.12), tooth_y + int(k_h*0.5)], fill=bg)
    draw.rectangle([tooth_x + int(k_w*0.18), tooth_y, tooth_x + int(k_w*0.3), tooth_y + int(k_h*0.5)], fill=bg)
    try:
        img.save(str(ICON_LOGIN))
    except Exception:
        pass
    return img

def create_splash_graphics(size=220, bg=(28,30,36), fg=(255,255,255)):
    img = Image.new("RGBA",(size,size),(bg[0],bg[1],bg[2],255))
    draw = ImageDraw.Draw(img)
    w,h = size,size
    bar_w = int(w*0.12)
    spacing = int(w*0.06)
    start_x = int(w*0.12)
    base_y = int(h*0.72)
    heights = [int(h*0.35), int(h*0.55), int(h*0.7)]
    for i, ht in enumerate(heights):
        x0 = start_x + i*(bar_w+spacing)
        x1 = x0 + bar_w
        y0 = base_y - ht
        draw.rounded_rectangle([x0, y0, x1, base_y], radius=max(3, bar_w//6), fill=fg)
    cx = int(w*0.74); cy = int(h*0.38); r = int(w*0.18)
    start = -90
    arcs = [75, 120, 165]
    colors = [(255,255,255),(200,220,255),(140,170,255)]
    acc = start
    for i,a in enumerate(arcs):
        draw.pieslice([cx-r, cy-r, cx+r, cy+r], start=acc, end=acc+a, fill=colors[i])
        acc += a
    draw.ellipse([cx-int(r*0.4), cy-int(r*0.4), cx+r, cy+r], fill=bg)
    try:
        img.save(str(ICON_SPLASH))
    except Exception:
        pass
    return img

try:
    if not ICON_LOGIN.exists():
        create_login_padlock(size=200)
    if not ICON_SPLASH.exists():
        create_splash_graphics(size=220)
except Exception:
    pass

# ----------------------------
# Splash 
# ----------------------------
class Splash(ctk.CTk):
    def __init__(self, on_finish, theme="dark"):
        super().__init__()
        self.withdraw()
        self.on_finish = on_finish
        self.theme = theme
        self.title("Gerenciador RH ➕ — Inicializando...")
        
        largura, altura = 800, 500
        self.geometry(f"{largura}x{altura}")
        self.resizable(False, False)

        self.after(100, lambda: (centralizar_janela(self, largura, altura), self.deiconify(), self.lift()))

        #self.after(100, lambda: centralizar_janela(self, largura, altura))

        #try:
           # self.eval('tk::PlaceWindow . centro')
        #except Exception:
          #  pass
        self.configure(fg_color="#3362E2" if theme=="dark" else "#3362E2")

        self.canvas_label = ctk.CTkLabel(self, text="")
        self.canvas_label.pack(pady=(20,10))

        self.title_label = ctk.CTkLabel(self, text="Gerenciador RH — BI", font=("Segoe UI", 20, "bold"),
                                        text_color="white" if theme=="dark" else "black")
        self.title_label.pack(pady=(4,10))

        self.progress = ctk.CTkProgressBar(self, width=420)
        self.progress.pack(pady=(8,6))
        self.progress.set(0.0)

        self.msg_label = ctk.CTkLabel(self, text="Preparando Ambiente 🏢...", text_color="#DDE6FF")
        self.msg_label.pack(pady=(6,8))

        self.anim_step = 0
        self.max_steps = 60
        self.bars_current = [5,5,5]
        self.target_bars = [int(220*0.35), int(220*0.55), int(220*0.7)]
        self.circle_angle = 0

        try:
            base = Image.open(str(ICON_SPLASH)).convert("RGBA").resize((220,220))
        except Exception:
            base = create_splash_graphics(size=220)
        self.base_img = base
        self._anim_frame()

    def _anim_frame(self):
        if not self.winfo_exists():
            return
        try:
            t = self.anim_step
            cur = self.progress.get()
            if cur < 1.0:
                self.progress.set(min(1.0, cur + 0.015))
            ratio = (t / self.max_steps)
            heights = [int(h * ratio) for h in self.target_bars]
            img = self.base_img.copy()
            draw = ImageDraw.Draw(img)
            w,h = img.size
            bar_w = int(w*0.12)
            spacing = int(w*0.06)
            start_x = int(w*0.12)
            base_y = int(h*0.72)
            for i, ht in enumerate(heights):
                x0 = start_x + i*(bar_w+spacing)
                x1 = x0 + bar_w
                y0 = base_y - ht
                draw.rounded_rectangle([x0, y0, x1, base_y], radius=max(3, bar_w//6), fill=(230,240,255))
            
            cx = int(w*0.74); cy = int(h*0.38); r = int(w*0.18)
            start_angle = -90 + int(self.circle_angle)
            end_angle = start_angle + 60
            draw.pieslice([cx-r, cy-r, cx+r, cy+r], start=start_angle, end=end_angle, fill=(255,255,255,220))

            try:
                ctk_img = ctk.CTkImage(img, size=(220,220))
                self.canvas_label.configure(image=ctk_img, text="")
                self.canvas_label.image = ctk_img
            except Exception:
                tkimg = ImageTk.PhotoImage(img)
                self.canvas_label.configure(image=tkimg, text="")
                self.canvas_label.image = tkimg
            self.anim_step += 1
            self.circle_angle = (self.circle_angle + 12) % 360
            if self.anim_step < self.max_steps:
                self.after(45, self._anim_frame)
            else:
                self.after(300, self._finish)
        except Exception:
            pass

    def _finish(self):
        if not self.winfo_exists():
            return
        try:
            self.destroy()
        except Exception:
            pass
        if callable(self.on_finish):
            try:
                self.on_finish()
            except Exception:
                traceback.print_exc()

# ----------------------------
# Main application
# ----------------------------
class SistemaRH(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.withdraw()
        self.title("🗂️ Gerenciador RH ➕")
        
        largura, altura = 1200, 700
        self.geometry(f"{largura}x{altura}")
        self.minsize(900, 600)

        self.after(100, lambda: (centralizar_janela(self, largura, altura), self.deiconify(), self.lift()))



        # ⏱️ Centraliza com leve atraso para garantir posição real
        #self.after(100, lambda: centralizar_janela(self, largura, altura))


        # 👉 Se quiser abrir automaticamente maximizada:
        self.after(100, lambda: self.state('zoomed'))

        #try:
            #self.eval('tk::PlaceWindow . centro')
        #except Exception:
          #  pass

        self.config = ensure_config()
        self.users = self.config.get("users", {"admin":"1234"})
        self.theme = self.config.get("theme", "dark")
        ctk.set_appearance_mode(self.theme)
        self.colaboradores = load_data()
        self.current_user = None
        
        self.theme_var = ctk.StringVar(value=self.theme.capitalize())

        self._setup_treeview_style()

        self.lista_tree = None        
        self.qr_label_widget = None  
        self.last_pdf_path = None 
        
        self.http_server_thread = HTTPServerThread(SERVER_IP, SERVER_PORT, LocalFileHandler)
        self.http_server_thread.start()
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing) 
        
        self.e_nome = None
        self.e_email = None
        self.e_telefone = None
        self.e_cargo = None
        self.tipo_var = None
        self.tipo_menu = None
        self.lbl_documento = None
        self.e_documento = None
        self.e_salario = None
        self.e_data = None
        self.e_obs = None
        
        self._build_login()
        
    def on_closing(self):
        if self.http_server_thread and self.http_server_thread.is_running:
            self.http_server_thread.stop()
        try:
            save_config(self.config)
            self.destroy()
        except Exception:
            pass
            
    def _get_ctk_color(self, key, color_property):
        DEFAULT_LIGHT_BG = "#f0f0f0"
        DEFAULT_DARK_BG = "#2b2b2b"
        DEFAULT_DARK_FG = "#ffffff"
        DEFAULT_ACCENT = "#1F6AA5" 
        def get_fallback():
            if color_property in ("fg_color", "fieldbackground"):
                 return DEFAULT_DARK_BG if self.theme == "dark" else DEFAULT_LIGHT_BG
            if color_property == "text_color":
                 return DEFAULT_DARK_FG if self.theme == "dark" else "#000000"
            return DEFAULT_ACCENT
        try:
            theme_dict = ctk.ThemeManager.theme
            component_dict = theme_dict.get(key)
            if not component_dict: return get_fallback()
            color_value = component_dict.get(color_property)
            if isinstance(color_value, tuple):
                idx = 0 if self.theme == 'light' else 1
                return color_value[idx]
            elif isinstance(color_value, str):
                return color_value
            return get_fallback()
        except Exception:
            return get_fallback()
            
    def _setup_treeview_style(self):
        style = ttk.Style()
        theme_bg = self._get_ctk_color("CTkFrame", "fg_color")
        theme_fg = self._get_ctk_color("CTkLabel", "text_color")
        select_color = self._get_ctk_color("CTkButton", "fg_color")
        header_color = self._get_ctk_color("CTkButton", "fg_color")
        header_fg = self._get_ctk_color("CTkButton", "text_color")
        style.theme_use("default")
        style.configure("Treeview", 
                        background=theme_bg, 
                        foreground=theme_fg, 
                        fieldbackground=theme_bg,
                        borderwidth=0,
                        rowheight=25) 
        style.map('Treeview', background=[('selected', "#0078D7")])
        style.configure("Treeview.Heading", 
                        background=header_color, 
                        foreground=header_fg, 
                        font=("Segoe UI", 10, "bold"))
# aqui definimos o conteudo interno de cada aba após abrir    
    def _show_frame(self, frame_name):
    # Cancela eventos pendentes de animações ou atualizações automáticas
        try:
            if hasattr(self, "_after_id"):
                self.after_cancel(self._after_id)
        except Exception:
            pass
        self.current_frame = frame_name  # <<< correção aqui
 # <<< adiciona aqui
        # Limpa o conteúdo da área principal antes de carregar o novo frame
        for widget in self.content.winfo_children():
            widget.destroy()

        # Reseta referências internas
        self.lista_tree = None
        self.qr_label_widget = None

        # Exibe o frame correspondente
        if frame_name == "cadastro":
            self._frame_cadastro()
        elif frame_name == "lista_edicao":
            self._setup_treeview_style()
            self._frame_lista_edicao()
        elif frame_name == "ausencias":
            self._frame_ausencias()
        elif frame_name == "ferias":
            self._frame_ferias()
        elif frame_name == "admin_bi":
            self._frame_admin_bi()
        else:
            ctk.CTkLabel(self.content, text="Página não encontrada.", font=("Segoe UI", 20)).pack(pady=50)

    # ----------------------------
    # Login 
    # ----------------------------
    def _build_login(self):
        for w in self.winfo_children(): w.destroy()
        frame = ctk.CTkFrame(self, corner_radius=12, width=520, height=460)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        try:
            pil_icon = Image.open(str(ICON_LOGIN)).convert("RGBA")
            icon_img = ctk.CTkImage(pil_icon, size=(120,120))
            lbl_icon = ctk.CTkLabel(frame, image=icon_img, text="")
            lbl_icon.image = icon_img
            lbl_icon.pack(pady=(12,6))
        except Exception:
            pass
        title = ctk.CTkLabel(frame, text="🔐 Login: — Gerenciador RH ➕", font=("Segoe UI", 20, "bold"))
        title.pack(pady=(6,8))
        self.login_user = ctk.CTkEntry(frame, placeholder_text="👤 Usuário:", width=330)
        self.login_user.pack(pady=(8,6))
       
        self.login_pass = ctk.CTkEntry(frame, placeholder_text="🔐 Senha:", show="*", width=330)
        self.login_pass.pack(pady=(6,8))
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(pady=(8,6))
        # botão de login entrar , alterar senha e rodapé
        ctk.CTkButton(btn_frame, text="🚪Entrar:", width=160, command=self._do_login).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="🔐 Alterar senha:", width=160, command=self._open_change_password_modal).pack(side="left", padx=8)
        ctk.CTkLabel(frame, text="🚀 Versão: 1.0 / 2025 | ™ Desenvolvido por: Iago Nunes ©", text_color="green").pack(pady=5)

        self.login_msg = ctk.CTkLabel(frame, text="", text_color="red")
        self.login_msg.pack(pady=(6,10))
    def _do_login(self):
        u = self.login_user.get().strip(); p = self.login_pass.get().strip()
        if u in self.users and self.users[u] == p:
            self.current_user = u
            self._build_main_ui() 
        else:
            self.login_msg.configure(text="👤 Usuário ou 🔐 senha incorretos ❌")
    def _open_change_password_modal(self):
        top = ctk.CTkToplevel(self); top.title("🔐 Alterar Senha"); top.geometry("420x240")
        try: top.eval('tk::PlaceWindow . center')
        except Exception: pass
        top.transient(self); top.grab_set()
        ctk.CTkLabel(top, text="🔐 Alterar senha do usuário:", font=("Segoe UI", 14, "bold")).pack(pady=(12,8))
        user_ent = ctk.CTkEntry(top, placeholder_text="👤 Usuário:", width=340); user_ent.pack(pady=6)
        pass_ent = ctk.CTkEntry(top, placeholder_text="🔐 Nova senha:", show="*", width=340); pass_ent.pack(pady=6)
        def do_change():
            u = user_ent.get().strip(); p = pass_ent.get().strip()
            if not u or not p: messagebox.showwarning("Atenção", "Informe usuário e nova senha."); return
            self.users[u] = p; self.config["users"] = self.users; save_config(self.config)
            messagebox.showinfo("Sucesso", f"Senha do usuário '{u}' atualizada.")
            try: top.grab_release(); top.destroy()
            except Exception: pass
        ctk.CTkButton(top, text="💾 Salvar", width=160, command=do_change).pack(pady=(12,14))

    # ----------------------------
    # Main UI (Menu Lateral)
    # ----------------------------
    def _build_main_ui(self):
        for w in self.winfo_children(): w.destroy()
        self._setup_treeview_style() 
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=8); self.sidebar.pack(side="left", fill="y", padx=(12,10), pady=12)
        theme_color = self.config.get("theme", "dark")
        brand_text_color = "white" if theme_color == "dark" else "black"
        brand = ctk.CTkLabel(self.sidebar, text="🗂️ Menu RH ➕", font=("Segoe UI",18,"bold"), text_color=brand_text_color); brand.pack(pady=(16,8))
       # Botão do menu lateral painel princinpal esquerdo
        ctk.CTkButton(self.sidebar, text="➕ Cadastro:", command=lambda:self._show_frame("cadastro"), width=220, fg_color="#2563EB").pack(pady=(10,8))
        ctk.CTkButton(self.sidebar, text="📋 Lista / Edição:", command=lambda:self._show_frame("lista_edicao"), width=220, fg_color="#2563EB").pack(pady=8)
        ctk.CTkButton(self.sidebar, text="📅 Ausências:", command=lambda:self._show_frame("ausencias"), width=220, fg_color="#2563EB").pack(pady=8)
        ctk.CTkButton(self.sidebar, text="⛱️ Férias:", command=lambda:self._show_frame("ferias"), width=220, fg_color="#2563EB").pack(pady=8)
        ctk.CTkButton(self.sidebar, text="📊 Admin / BI:", command=lambda:self._show_frame("admin_bi"), width=220, fg_color="#2563EB").pack(pady=8)
        ctk.CTkButton(self.sidebar, text="⚙️ Configure➕ / Configurações", command=lambda:self._show_frame("config_plus"), width=220, fg_color="#2563EB").pack(pady=8)

        spacer = ctk.CTkLabel(self.sidebar, text=""); spacer.pack(expand=True, fill="y")
        self.theme_var.set(self.theme.capitalize()) 
        ctk.CTkLabel(self.sidebar, text="🌛/🌝 Tema:").pack(pady=(12, 0))
        ctk.CTkOptionMenu(self.sidebar, values=["Dark", "Light"], command=self._change_theme_option_menu, variable=self.theme_var, width=220).pack(pady=(0, 15))
        ctk.CTkButton(self.sidebar, text="🚪 Sair / Logout:", command=self._logout_to_login, width=220, fg_color="#DC2626").pack(pady=(6,18))
        self.content = ctk.CTkFrame(self, corner_radius=8); self.content.pack(side="right", expand=True, fill="both", padx=(6,12), pady=12)
        if not hasattr(self, "current_frame") or self.current_frame is None:
            self._show_frame("cadastro")
        else:
            self._show_frame(self.current_frame)

           
    def _change_theme_option_menu(self, new_theme_value):
        new_theme = new_theme_value.lower()
        if new_theme != self.theme:
            # Guarda a aba (frame) atual antes da troca
            current_frame = getattr(self, "current_frame", "cadastro")

            # Aplica o novo tema
            ctk.set_appearance_mode(new_theme)
            self.config["theme"] = new_theme
            self.theme = new_theme
            save_config(self.config)

            # Reconstroi a interface
            self._build_main_ui()

            # Restaura o frame em que o usuário estava
            try:
                if current_frame:
                    self._show_frame(current_frame)
            except Exception:
                self._show_frame("cadastro")
            

    def _logout_to_login(self):
        save_config(self.config)
        self.current_user = None
        self._build_login()

    # ----------------------------
    # Funções de suporte (Documento e Limpeza)
    # ----------------------------
    def _on_tipo_change(self, v):
        if self.lbl_documento:
            if v == "CLT" or v == "Estágio": self.lbl_documento.configure(text="CPF")
            elif v == "Pessoa Jurídica": self.lbl_documento.configure(text="CNPJ")
            else: self.lbl_documento.configure(text="CPF / CNPJ")
    def _limpar_campos(self):
        if self.e_nome:
            for w in (self.e_nome, self.e_email, self.e_telefone, self.e_cargo, self.e_documento, self.e_salario, self.e_data):
                try: w.delete(0, "end")
                except Exception: pass
            try: self.e_obs.delete("1.0", "end")
            except Exception: pass
            if self.tipo_var:
                 self.tipo_var.set("CLT"); self._on_tipo_change("CLT")
    def _carregar_colaborador_internamente(self, nome):
        self.colaboradores = load_data(); self._limpar_campos()
        for c in self.colaboradores:
            if c.get("Nome","").lower() == nome.lower():
                self.e_nome.insert(0, c.get("Nome","")); self.e_email.insert(0, c.get("E-mail",""))
                self.e_telefone.insert(0, c.get("Telefone","")); self.e_cargo.insert(0, c.get("Cargo/Função",""))
                if self.tipo_var:
                    self.tipo_var.set(c.get("TipoVinculo","CLT")); self._on_tipo_change(c.get("TipoVinculo","CLT")) 
                self.e_documento.insert(0, c.get("Documento","")); self.e_salario.insert(0, c.get("Salario",""))
                self.e_data.insert(0, c.get("Data de Admissão","")); self.e_obs.insert("1.0", c.get("Observações",""))
                return True
        messagebox.showerror("Erro", f"Colaborador '{nome}' não encontrado."); return False

    # ----------------------------
    # Cadastro 
    # ----------------------------
    def _frame_cadastro(self):
        root = ctk.CTkFrame(self.content); root.pack(expand=True, fill="both", padx=10, pady=10)
        header = ctk.CTkLabel(root, text="📝 Cadastro de Colaborador / Edição:", font=("Segoe UI",16,"bold")); header.pack(pady=(6,10))
        topico1 = ctk.CTkFrame(root); topico1.pack(fill="x", padx=6, pady=(6,2))
        
        ctk.CTkLabel(topico1, text="1. Identificação:🔭", font=("Segoe UI", 12, "bold"), fg_color=("blue", "blue"), corner_radius=6).pack(fill="x", pady=(4,6), padx=4)
        row1 = ctk.CTkFrame(topico1, fg_color="green"); row1.pack(fill="x", pady=(2,6))
        ctk.CTkLabel(row1, text="👤Nome:", width=160, anchor="w").pack(side="left", padx=(6,12))
        
        self.e_nome = ctk.CTkEntry(row1); self.e_nome.pack(side="left", fill="x", expand=True, padx=(0,6))
        
        ctk.CTkLabel(row1, text="📧 E-mail:", width=140, anchor="w").pack(side="left", padx=(6,12))
        self.e_email = ctk.CTkEntry(row1, width=240); self.e_email.pack(side="left", padx=(0,6))
        
        row2 = ctk.CTkFrame(topico1, fg_color="green"); row2.pack(fill="x", pady=(2,6))
        ctk.CTkLabel(row2, text="📞 Telefone:", width=160, anchor="w").pack(side="left", padx=(6,12))
        
        self.e_telefone = ctk.CTkEntry(row2); self.e_telefone.pack(side="left", fill="x", expand=True, padx=(0,6))
        ctk.CTkLabel(row2, text="💼 Cargo/Função:", width=140, anchor="w").pack(side="left", padx=(6,12))
        
        self.e_cargo = ctk.CTkEntry(row2, width=240); self.e_cargo.pack(side="left", padx=(0,6))
        topico2 = ctk.CTkFrame(root); topico2.pack(fill="x", padx=6, pady=6)
        ctk.CTkLabel(topico2, text="2. Vínculo e Admissão:🤝", font=("Segoe UI", 12, "bold"), fg_color=("blue", "blue"), corner_radius=6).pack(fill="x", pady=(4,6), padx=4)
        row3 = ctk.CTkFrame(topico2, fg_color="green"); row3.pack(fill="x", pady=(2,6))
        
        ctk.CTkLabel(row3, text="🤝 Tipo de vínculo:", width=160, anchor="w").pack(side="left", padx=(6,12))
        self.tipo_var = ctk.StringVar(value="CLT")
        self.tipo_menu = ctk.CTkOptionMenu(row3, values=["CLT","Pessoa Jurídica","Freelancer", "Estágio"], variable=self.tipo_var, command=self._on_tipo_change); self.tipo_menu.pack(side="left", padx=(0,6))

        row4 = ctk.CTkFrame(topico2, fg_color="green"); row4.pack(fill="x", pady=(2,6))
        self.lbl_documento = ctk.CTkLabel(row4, text="CPF:", width=160, anchor="w"); self.lbl_documento.pack(side="left", padx=(6,12))
        self.e_documento = ctk.CTkEntry(row4); self.e_documento.pack(side="left", fill="x", expand=True, padx=(0,6))
        
        ctk.CTkLabel(row4, text="Salário/Valor:(R$)", width=140, anchor="w").pack(side="left", padx=(6,12))
        self.e_salario = ctk.CTkEntry(row4, width=200); self.e_salario.pack(side="left", padx=(0,6))
        row5 = ctk.CTkFrame(topico2, fg_color="green"); row5.pack(fill="x", pady=(2,6))
        
        ctk.CTkLabel(row5, text="📅 Data de admissão/início(DD/MM/AAAA):", width=320, anchor="w").pack(side="left", padx=(6,12))
        self.e_data = ctk.CTkEntry(row5, width=260); self.e_data.pack(side="left", padx=(0,6))
        topico3 = ctk.CTkFrame(root); topico3.pack(fill="x", padx=6, pady=6)
        
        ctk.CTkLabel(topico3, text="3. Observações Adicionais:👓", font=("Segoe UI", 12, "bold"), fg_color=("blue", "blue"), corner_radius=6).pack(fill="x", pady=(4,6), padx=4)
        row6 = ctk.CTkFrame(topico3, fg_color="green"); row6.pack(fill="both", pady=(2,6))
        self.e_obs = ctk.CTkTextbox(row6, height=100); self.e_obs.pack(side="left", fill="both", expand=True, padx=6, pady=6)
        
        btns = ctk.CTkFrame(root, fg_color="white"); btns.pack(pady=(8,12))
        ctk.CTkButton(btns, text="💾 Adicionar / Atualizar", command=self._salvar_colaborador, width=220, fg_color="#2563EB").pack(side="left", padx=8)
        ctk.CTkButton(btns, text="🧹 Limpar Campos", command=self._limpar_campos, width=150, fg_color="#F59E0B").pack(side="left", padx=8)
        self._on_tipo_change("CLT")

    def _salvar_colaborador(self):
        nome = self.e_nome.get().strip(); updated = False
        if not nome: messagebox.showwarning("Atenção", "Nome é obrigatório."); return
        item = {"Nome": nome, "E-mail": self.e_email.get().strip(), "Telefone": self.e_telefone.get().strip(), "Cargo/Função": self.e_cargo.get().strip(), "TipoVinculo": self.tipo_var.get(), "Documento": self.e_documento.get().strip(), "Salario": self.e_salario.get().strip(), "Data de Admissão": self.e_data.get().strip(), "Observações": self.e_obs.get("1.0", "end").strip(), "Ausências": []}
        for c in self.colaboradores:
            if c.get("Nome","").lower() == nome.lower():
                if "Ausências" in c: item["Ausências"] = c["Ausências"]
                c.update(item); updated = True; break
        if not updated: self.colaboradores.append(item)
        save_data(self.colaboradores)
        messagebox.showinfo("Sucesso", f"Colaborador '{nome}' salvo/atualizado.")
        self._limpar_campos()
        if self.lista_tree: self._exibir_lista_para_edicao()

    # ----------------------------
    # Lista / Edição (Treeview)
    # ----------------------------
    def _get_selected_colaborador_name(self):
        if not self.lista_tree or not self.lista_tree.winfo_exists(): return None
        selecionado = self.lista_tree.focus()
        if not selecionado: return None
        values = self.lista_tree.item(selecionado, 'values')
        return values[0] if values else None

    def _frame_lista_edicao(self):
        root = ctk.CTkFrame(self.content); root.pack(expand=True, fill="both", padx=10, pady=10)
        header = ctk.CTkLabel(root, text="📋 Colaboradores Cadastrados:", font=("Segoe UI",16,"bold")); header.pack(pady=(6,10))
        list_frame = ctk.CTkFrame(root); list_frame.pack(fill="both", expand=True, padx=8, pady=8)
        columns = ("Nome", "Tipo", "Cargo", "Salario")
        
        self.lista_tree = tkinter.ttk.Treeview(list_frame, columns=columns, show="headings", style="Treeview")
        self.lista_tree.heading("Nome", text="🧑‍💼COLABORADOR(a):", anchor="w"); self.lista_tree.heading("Tipo", text="TIPO VÍNCULO:🤝", anchor="center")
        self.lista_tree.heading("Cargo", text="💼 CARGO/FUNÇÃO:", anchor="w"); self.lista_tree.heading("Salario", text="SALÁRIO/VALOR:(💲)", anchor="e")
        
        self.lista_tree.column("Nome", width=300, minwidth=200, anchor="w"); self.lista_tree.column("Tipo", width=150, minwidth=100, anchor="center")
        self.lista_tree.column("Cargo", width=250, minwidth=150, anchor="w"); self.lista_tree.column("Salario", width=150, minwidth=100, anchor="e")
        scrollbar = ctk.CTkScrollbar(list_frame, command=self.lista_tree.yview); self.lista_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y", padx=(0, 6), pady=6); self.lista_tree.pack(fill="both", expand=True, padx=(6, 0), pady=6)
        
        self.lista_tree.bind("<Double-1>", lambda event: self._carregar_e_mudar_para_cadastro())
        control_frame = ctk.CTkFrame(root, fg_color="transparent"); control_frame.pack(fill="x", padx=8, pady=(4,12))
        ctk.CTkButton(control_frame, text="🔍 Carregar para Edição", command=self._carregar_e_mudar_para_cadastro, width=280, fg_color="#2563EB").pack(side="left", padx=8, fill="x", expand=True)
        ctk.CTkButton(control_frame, text="❌ Excluir Selecionado", command=self._excluir_selecionado, width=280, fg_color="#DC2626").pack(side="left", padx=8, fill="x", expand=True)
        self._exibir_lista_para_edicao()

    def _exibir_lista_para_edicao(self):
        self.colaboradores = load_data()
        if not self.lista_tree or not self.lista_tree.winfo_exists(): return
        for item in self.lista_tree.get_children(): self.lista_tree.delete(item)
        for i, c in enumerate(self.colaboradores):
            self.lista_tree.insert(parent='', index='end', iid=f'colab_{i}', 
                values=(c.get('Nome', ''), c.get('TipoVinculo', 'N/A'), c.get('Cargo/Função', 'N/A'), c.get('Salario', 'N/A')))
            
    def _carregar_e_mudar_para_cadastro(self):
        nome = self._get_selected_colaborador_name()
        if not nome: messagebox.showwarning("Atenção", "Selecione um colaborador na lista para carregar."); return
        self._show_frame("cadastro") 
        if self._carregar_colaborador_internamente(nome):
            messagebox.showinfo("Pronto para Edição", f"Dados de '{nome}' carregados na aba **Cadastro**. Altere os campos e clique em '➕ Adicionar / Atualizar' para salvar.")
            
    def _excluir_selecionado(self):
        nome = self._get_selected_colaborador_name()
        if not nome: messagebox.showwarning("Atenção", "Selecione um colaborador na lista para excluir."); return
        if not messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja EXCLUIR o colaborador '{nome}'? Esta ação é irreversível."): return
        original_len = len(self.colaboradores)
        self.colaboradores = [c for c in self.colaboradores if c.get("Nome","").lower() != nome.lower()]
        if len(self.colaboradores) < original_len:
            save_data(self.colaboradores); messagebox.showinfo("Removido", f"Colaborador '{nome}' removido.")
            self._limpar_campos(); self._exibir_lista_para_edicao()
        else: messagebox.showerror("Erro", f"Colaborador '{nome}' não encontrado para exclusão.")


# ============================
# ABA 1 — AUSÊNCIAS
# ============================
    def _frame_ausencias(self):
        root = ctk.CTkFrame(self.content)
        root.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(root, text="📋 Controle de Ausências:", font=("Segoe UI", 18, "bold")).pack(pady=(10, 20))

        form = ctk.CTkFrame(root)
        form.pack(fill="x", pady=5)

        # ComboBox de colaborador
        ctk.CTkLabel(form, text="👤 Colaborador:").grid(row=0, column=0, padx=10, pady=8, sticky="e")
        nomes_colaboradores = [c["Nome"] for c in self.colaboradores]
        self.combo_colab_aus = ctk.CTkComboBox(form, values=nomes_colaboradores, width=220)
        self.combo_colab_aus.grid(row=0, column=1, padx=10, pady=8, sticky="w")

        # Campo de data início
        ctk.CTkLabel(form, text="📅 Data Início:").grid(row=0, column=2, padx=10, pady=8, sticky="e")
        self.e_data_aus = ctk.CTkEntry(form, placeholder_text="DD/MM/AAAA", width=160)
        self.e_data_aus.grid(row=0, column=3, padx=10, pady=8, sticky="w")

        # Campo de data de retorno
        ctk.CTkLabel(form, text="📅 Data de Retorno:").grid(row=1, column=2, padx=10, pady=8, sticky="e")
        self.e_data_retorno = ctk.CTkEntry(form, placeholder_text="DD/MM/AAAA", width=160)
        self.e_data_retorno.grid(row=1, column=3, padx=10, pady=8, sticky="w")

        # ComboBox de motivo
        ctk.CTkLabel(form, text="🎯 Motivo:").grid(row=1, column=0, padx=10, pady=8, sticky="e")
        self.combo_motivo_aus = ctk.CTkComboBox(form, values=["Doença", "Férias", "Pessoal", "Outro"], width=220)
        self.combo_motivo_aus.grid(row=1, column=1, padx=10, pady=8, sticky="w")

        # Campo de observação
        ctk.CTkLabel(form, text="🗒️ Observação:").grid(row=2, column=0, padx=10, pady=8, sticky="e")
        self.e_obs_aus = ctk.CTkEntry(form, placeholder_text="Opcional", width=300)
        self.e_obs_aus.grid(row=2, column=1, columnspan=3, padx=10, pady=8, sticky="w")

        # Botões
        btn_frame = ctk.CTkFrame(root, fg_color="orange")
        btn_frame.pack(pady=10)

        ctk.CTkButton(btn_frame, text="💾 Salvar", width=130, command=self._salvar_ausencia).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="✏️ Editar", width=130, command=self._editar_ausencia).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="❌ Excluir", width=130, command=self._excluir_ausencia).pack(side="left", padx=5)

        # Histórico com Scroll
        hist_frame = ctk.CTkFrame(root)
        hist_frame.pack(fill="both", expand=True, pady=15)

        ctk.CTkLabel(hist_frame, text="📜 Histórico de Ausências:", font=("Segoe UI", 14, "bold")).pack(pady=10)

        tree_frame = ctk.CTkFrame(hist_frame)
        tree_frame.pack(fill="both", expand=True)

        self.tree_aus = ttk.Treeview(tree_frame, columns=("Nome", "Data Início", "Data Retorno", "Motivo", "Obs"), show="headings", height=10)
        self.tree_aus.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_aus.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree_aus.configure(yscrollcommand=scrollbar.set)

        for col in ("Nome", "Data Início", "Data Retorno", "Motivo", "Obs"):
            self.tree_aus.heading(col, text=col)
            self.tree_aus.column(col, width=150)

        self._atualizar_tree_ausencias()

    # ----------------------------
    def _salvar_ausencia(self):
        nome = self.combo_colab_aus.get().strip()
        data = self.e_data_aus.get().strip()
        retorno = self.e_data_retorno.get().strip()
        motivo = self.combo_motivo_aus.get().strip()
        obs = self.e_obs_aus.get().strip()
        if not nome or not data:
            messagebox.showwarning("Atenção", "Informe colaborador e data de início.")
            return
        for c in self.colaboradores:
            if c["Nome"] == nome:
                if "Ausências" not in c:
                    c["Ausências"] = []

                # Verifica se o mesmo registro já existe (edição)
                editou = False
                for a in c["Ausências"]:
                    if a["Data"] == data:
                        a["Retorno"] = retorno
                        a["Motivo"] = motivo
                        a["Obs"] = obs
                        editou = True
                        break

                    # Se não encontrou um existente, adiciona novo
                if not editou:
                    c["Ausências"].append({"Data": data, "Retorno": retorno, "Motivo": motivo, "Obs": obs})

                save_data(self.colaboradores)
                msg = "Ausência atualizada." if editou else "Ausência registrada."
                messagebox.showinfo("Sucesso", msg)
                break

        self._atualizar_tree_ausencias()

    # ----------------------------
    def _editar_ausencia(self):
        try:
            item = self.tree_aus.selection()[0]
        except IndexError:
            messagebox.showwarning("Selecione", "Selecione uma ausência para editar.")
            return
        valores = self.tree_aus.item(item, "values")
        nome, data, retorno, motivo, obs = valores
        self.combo_colab_aus.set(nome)
        self.e_data_aus.delete(0, "end"); self.e_data_aus.insert(0, data)
        self.e_data_retorno.delete(0, "end"); self.e_data_retorno.insert(0, retorno)
        self.combo_motivo_aus.set(motivo)
        self.e_obs_aus.delete(0, "end"); self.e_obs_aus.insert(0, obs)

    # ----------------------------
    def _excluir_ausencia(self):
        try:
            item = self.tree_aus.selection()[0]
        except IndexError:
            messagebox.showwarning("Selecione", "Selecione uma ausência para excluir.")
            return
        nome, data, retorno, motivo, obs = self.tree_aus.item(item, "values")
        for c in self.colaboradores:
            if c["Nome"] == nome and "Ausências" in c:
                c["Ausências"] = [a for a in c["Ausências"] if not (a["Data"] == data and a["Retorno"] == retorno and a["Motivo"] == motivo)]
                save_data(self.colaboradores)
                break
        self._atualizar_tree_ausencias()

    # ----------------------------
    def _atualizar_tree_ausencias(self):
        for i in self.tree_aus.get_children():
            self.tree_aus.delete(i)
        for c in self.colaboradores:
            if "Ausências" in c:
                for a in c["Ausências"]:
                    self.tree_aus.insert("", "end", values=(c["Nome"], a.get("Data", ""), a.get("Retorno", ""), a.get("Motivo", ""), a.get("Obs", "")))

# ============================
    def _frame_ferias(self):
        root = ctk.CTkFrame(self.content)
        root.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(root, text="⛱️ Controle de Férias:", font=("Segoe UI", 18, "bold")).pack(pady=(10, 20))

        form = ctk.CTkFrame(root)
        form.pack(fill="x", pady=5)

        # ComboBox colaborador
        ctk.CTkLabel(form, text="👤 Colaborador(a):").grid(row=0, column=0, padx=10, pady=8, sticky="e")
        nomes_colaboradores = [c["Nome"] for c in self.colaboradores]
        self.combo_colab_ferias = ctk.CTkComboBox(form, values=nomes_colaboradores, width=220, command=self._preencher_salario)
        self.combo_colab_ferias.grid(row=0, column=1, padx=10, pady=8, sticky="w")

        # Campos de datas
        ctk.CTkLabel(form, text="📆 Início:").grid(row=0, column=2, padx=10, pady=8, sticky="e")
        self.e_inicio_ferias = ctk.CTkEntry(form, placeholder_text="DD/MM/AAAA", width=160)
        self.e_inicio_ferias.grid(row=0, column=3, padx=10, pady=8, sticky="w")

        ctk.CTkLabel(form, text="📅 Retorno:").grid(row=1, column=2, padx=10, pady=8, sticky="e")
        self.e_retorno_ferias = ctk.CTkEntry(form, placeholder_text="DD/MM/AAAA", width=160)
        self.e_retorno_ferias.grid(row=1, column=3, padx=10, pady=8, sticky="w")

        # Campo salário e valor final
        ctk.CTkLabel(form, text="💰 Salário:").grid(row=1, column=0, padx=10, pady=8, sticky="e")
        self.e_salario_ferias = ctk.CTkEntry(form, placeholder_text="R$", width=160)
        self.e_salario_ferias.grid(row=1, column=1, padx=10, pady=8, sticky="w")

        ctk.CTkLabel(form, text="🏖️ Valor Final:").grid(row=2, column=0, padx=10, pady=8, sticky="e")
        self.e_valor_final_ferias = ctk.CTkEntry(form, placeholder_text="R$", width=160)
        self.e_valor_final_ferias.grid(row=2, column=1, padx=10, pady=8, sticky="w")

        # Botões
        btn_frame = ctk.CTkFrame(root, fg_color="orange")
        btn_frame.pack(pady=10)

        ctk.CTkButton(btn_frame, text="🧮 Calcular Valor", width=150, command=self._calcular_valor_ferias).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="💾 Salvar", width=150, command=self._salvar_ferias).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="✏️ Editar", width=150, command=self._editar_ferias).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="❌ Excluir", width=150, command=self._excluir_ferias).pack(side="left", padx=5)

        # Histórico com Scroll
        hist_frame = ctk.CTkFrame(root)
        hist_frame.pack(fill="both", expand=True, pady=15)

        ctk.CTkLabel(hist_frame, text="📜 Histórico de Férias:", font=("Segoe UI", 14, "bold")).pack(pady=10)

        tree_frame = ctk.CTkFrame(hist_frame)
        tree_frame.pack(fill="both", expand=True)


        self.tree_ferias = ttk.Treeview(tree_frame, columns=("Nome", "Início", "Retorno", "Salário", "Valor Final"), show="headings", height=10)
        self.tree_ferias.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_ferias.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree_ferias.configure(yscrollcommand=scrollbar.set)

        for col in ("Nome", "Início", "Retorno", "Salário", "Valor Final"):
            self.tree_ferias.heading(col, text=col)
            self.tree_ferias.column(col, width=150)

        self._atualizar_tree_ferias()

    # ----------------------------
    def _preencher_salario(self, *_):
        nome = self.combo_colab_ferias.get().strip()
        for c in self.colaboradores:
            if c["Nome"] == nome:
                self.e_salario_ferias.delete(0, "end")
                self.e_salario_ferias.insert(0, c.get("Salario", ""))
                break

    # ----------------------------
    def _calcular_valor_ferias(self):
    # Pega o valor do Entry de salário
        salario_txt = self.e_salario_ferias.get().strip()
        
        # Remove tudo que não seja número ou vírgula/ponto
        import re
        salario_txt = re.sub(r"[^\d,\.]", "", salario_txt)

        # Se houver vírgula, converte para ponto (padronizando para float)
        if "," in salario_txt and "." in salario_txt:
            # Caso haja milhar e decimal, remove os milhares
            salario_txt = salario_txt.replace(".", "")
            salario_txt = salario_txt.replace(",", ".")
        elif "," in salario_txt:
            salario_txt = salario_txt.replace(",", ".")

        try:
            salario = float(salario_txt)
            valor = salario + (salario / 3)  # cálculo padrão férias
            # Formata para R$ 2.500,00
            valor_str = f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            self.e_valor_final_ferias.delete(0, "end")
            self.e_valor_final_ferias.insert(0, valor_str)
        except ValueError:
            messagebox.showwarning("Erro", "Informe um salário válido.")

            
    # ----------------------------
    def _salvar_ferias(self):
        nome = self.combo_colab_ferias.get().strip()
        inicio = self.e_inicio_ferias.get().strip()
        retorno = self.e_retorno_ferias.get().strip()
        salario = self.e_salario_ferias.get().strip()
        valor_final = self.e_valor_final_ferias.get().strip()

        if not nome or not inicio:
            messagebox.showwarning("Atenção", "Informe colaborador e data de início.")
            return

        for c in self.colaboradores:
            if c["Nome"] == nome:
                if "Férias" not in c:
                    c["Férias"] = []

                # 🔁 Verifica se já existe férias com as mesmas datas para substituir
                existente = next((f for f in c["Férias"] if f["Início"] == inicio), None)
                if existente:
                    existente.update({"Retorno": retorno, "Salário": salario, "Valor Final": valor_final})
                    messagebox.showinfo("Atualizado", "Férias atualizadas com sucesso.")
                else:
                    c["Férias"].append({"Início": inicio, "Retorno": retorno, "Salário": salario, "Valor Final": valor_final})
                    messagebox.showinfo("Sucesso", "Férias registradas com sucesso.")

                save_data(self.colaboradores)
                break

        self._atualizar_tree_ferias()


    # ----------------------------
    def _editar_ferias(self):
        try:
            item = self.tree_ferias.selection()[0]
        except IndexError:
            messagebox.showwarning("Selecione", "Selecione um registro para editar.")
            return
        nome, inicio, retorno, salario, valor_final = self.tree_ferias.item(item, "values")
        self.combo_colab_ferias.set(nome)
        self.e_inicio_ferias.delete(0, "end"); self.e_inicio_ferias.insert(0, inicio)
        self.e_retorno_ferias.delete(0, "end"); self.e_retorno_ferias.insert(0, retorno)
        self.e_salario_ferias.delete(0, "end"); self.e_salario_ferias.insert(0, salario)
        self.e_valor_final_ferias.delete(0, "end"); self.e_valor_final_ferias.insert(0, valor_final)

    # ----------------------------
    def _excluir_ferias(self):
        try:
            item = self.tree_ferias.selection()[0]
        except IndexError:
            messagebox.showwarning("Selecione", "Selecione um registro para excluir.")
            return
        nome, inicio, retorno, salario, valor_final = self.tree_ferias.item(item, "values")
        for c in self.colaboradores:
            if c["Nome"] == nome and "Férias" in c:
                c["Férias"] = [f for f in c["Férias"] if not (f["Início"] == inicio and f["Retorno"] == retorno)]
                save_data(self.colaboradores)
                break
        self._atualizar_tree_ferias()

    # ----------------------------
    def _atualizar_tree_ferias(self):
        for i in self.tree_ferias.get_children():
            self.tree_ferias.delete(i)
        for c in self.colaboradores:
            if "Férias" in c:
                for f in c["Férias"]:
                    self.tree_ferias.insert("", "end", values=(c["Nome"], f.get("Início", ""), f.get("Retorno", ""), f.get("Salário", ""), f.get("Valor Final", "")))

    # ferias ok ===============
    # ----------------------------
    # Funções Admin/BI (Layout PDF Corrigido)
    # ----------------------------
    def _gerar_relatorio_pdf(self, *_):
        if not REPORTLAB_AVAILABLE:
            messagebox.showerror("Erro", "A biblioteca 'reportlab' não está instalada. Instale com: pip install reportlab")
            return

        try:
            # === Escolha de local para salvar o PDF ===
            user_filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("Arquivos PDF", "*.pdf")],
                initialfile=f"Relatorio_RH_{ts()}.pdf",
                title="Salvar Relatório PDF em..."
            )
            if not user_filename:
                return  # cancelado

            # === Caminhos internos ===
            filename_server = PDFS / PDF_SERVER_NAME
            pdf_name_archive = Path(user_filename).name
            filename_archive = PDFS / pdf_name_archive

            # === Criação do PDF ===
            c = canvas.Canvas(user_filename, pagesize=A4)
            width, height = A4

            # --- Estilos visuais ---
            from reportlab.lib import colors
            TITLE_COLOR = colors.HexColor("#2563EB")  # Azul institucional
            HEADER_FONT = "Helvetica-Bold"
            TEXT_FONT = "Helvetica"
            TITLE_SIZE = 16
            TEXT_SIZE = 9
            LINE_HEIGHT = 12
            BLOCK_MARGIN = 30 

            # --- Cabeçalho centralizado ---
            def draw_header():
                c.setFont(HEADER_FONT, TITLE_SIZE)
                c.setFillColor(TITLE_COLOR)
                c.drawCentredString(width / 2, height - 60, "📘 Relatório Geral de Colaboradores")
                c.setFont(TEXT_FONT, 9)
                c.setFillColor(colors.black)
                c.drawCentredString(width / 2, height - 75, f"Gerado em {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
                c.setStrokeColor(colors.lightgrey)
                c.line(50, height - 85, width - 50, height - 85)

            # --- Rodapé ---
            def draw_footer():
                c.setFont("Helvetica-Oblique", 8)
                c.setFillColor(colors.grey)
                c.drawRightString(width - 30, 25, f"Total de colaboradores: {len(self.colaboradores)}")

            # --- Bloco visual de colaborador ---
            def draw_colaborador_block(x, y, colab):
                c.setStrokeColor(colors.lightgrey)
                c.setLineWidth(0.5)

                # Retângulo maior para dar mais espaço interno (altura aumentada)
                block_height = 160  
                c.rect(x, y - block_height + 10, 250, block_height, stroke=1, fill=0)

                # Fundo azul atrás do nome (não sobreposto)
                c.setFillColor(TITLE_COLOR)
                c.rect(x, y + 2, 250, 15, fill=True, stroke=False)

                # Nome centralizado e com margem
                c.setFillColor(colors.white)
                c.setFont(HEADER_FONT, 10)
                c.drawString(x + 10, y + 5, colab.get("Nome", "N/A"))

                # Volta para o texto normal preto
                c.setFillColor(colors.black)
                c.setFont(TEXT_FONT, TEXT_SIZE)


                c.setFont(TEXT_FONT, TEXT_SIZE)
                c.setFillColor(colors.black)
                linhas = [
                    f"💼 {colab.get('Cargo/Função', 'N/A')}",
                    f"🏢 Vínculo: {colab.get('TipoVinculo', 'N/A')}",
                    f"💰 Salário: {colab.get('Salario', 'N/A')}",
                    f"📅 Admissão: {colab.get('Data de Admissão', 'N/A')}",
                    f"📞 Tel: {colab.get('Telefone', 'N/A')}",
                    f"📧 Email: {colab.get('Email', 'N/A')}",
                    f"🧾 CPF/CNPJ: {colab.get('CPF', colab.get('CNPJ', 'N/A'))}",
                    f"🗒️ Obs: {colab.get('Observações', 'N/A')}",
                ]
                offset_y = y - 10
                for linha in linhas:
                    c.drawString(x + 10, offset_y, linha)
                    offset_y -= LINE_HEIGHT

                # --- Ausências ---
                if colab.get("Ausências"):
                    c.setFillColor(TITLE_COLOR)
                    c.drawString(x + 10, offset_y - 3, "📋 Ausências:")
                    c.setFillColor(colors.black)
                    offset_y -= LINE_HEIGHT
                    for a in colab["Ausências"]:
                        c.drawString(x + 20, offset_y, f"- {a.get('Data', 'N/A')} → {a.get('Retorno', 'N/A')} ({a.get('Motivo', 'N/A')})")
                        offset_y -= LINE_HEIGHT

                # --- Férias ---
                if colab.get("Férias"):
                    c.setFillColor(TITLE_COLOR)
                    c.drawString(x + 10, offset_y - 3, "🌴 Férias:")
                    c.setFillColor(colors.black)
                    offset_y -= LINE_HEIGHT
                    for f in colab["Férias"]:
                        c.drawString(x + 20, offset_y, f"- {f.get('Início', 'N/A')} → {f.get('Retorno', 'N/A')} | Valor: {f.get('Valor Final', 'N/A')}")
                        offset_y -= LINE_HEIGHT

            # --- Desenho geral ---
            draw_header()
            y = height - 120
            x_positions = [60, 315]
            col_index = 0

            for colab in self.colaboradores:
                draw_colaborador_block(x_positions[col_index], y, colab)
                col_index += 1

                if col_index >= 2:
                    col_index = 0
                    y -= 150 + BLOCK_MARGIN
                    if y < 150:
                        draw_footer()
                        c.showPage()
                        draw_header()
                        y = height - 120

            draw_footer()
            c.save()

            # === Copia automática para servidor e backup ===
            shutil.copy(user_filename, filename_server)
            shutil.copy(user_filename, filename_archive)

            self.last_pdf_path = str(user_filename)
            messagebox.showinfo("PDF Gerado", f"Relatório PDF salvo em:\n{user_filename}\n\nCópia feita para:\n{filename_archive}")

            if self.qr_label_widget:
                self._toggle_qr_code()

        except Exception as e:
            messagebox.showerror("Erro PDF", f"Não foi possível gerar o PDF. Erro: {e}")




    def _exportar_csv(self):
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("Arquivo CSV", "*.csv")],
                initialfile=f"Colaboradores_Export_{ts()}.csv"
            )
            if not filename:
                return

            with open(filename, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=';')

                # Cabeçalho
                writer.writerow([
                    "Nome", "Cargo/Função", "Tipo de Vínculo", "Salário", "Data de Admissão",
                    "Telefone", "E-mail", "CPF/CNPJ", "Observações", "Ausências", "Férias"
                ])

                for c in self.colaboradores:
                    # Monta resumo das ausências
                    ausencias = ""
                    if "Ausências" in c and c["Ausências"]:
                        ausencias = "; ".join([
                            f"{a.get('Data', '')} até {a.get('Retorno', '')} ({a.get('Motivo', '')})"
                            for a in c["Ausências"]
                        ])

                    # Monta resumo das férias
                    ferias = ""
                    if "Férias" in c and c["Férias"]:
                        ferias = "; ".join([
                            f"{f.get('Início', '')} até {f.get('Retorno', '')} (R$ {f.get('Valor Final', '')})"
                            for f in c["Férias"]
                        ])

                    writer.writerow([
                        c.get("Nome", ""),
                        c.get("Cargo/Função", ""),
                        c.get("TipoVinculo", ""),
                        c.get("Salario", ""),
                        c.get("Data de Admissão", ""),
                        c.get("Telefone", ""),
                        c.get("E-mail", ""),
                        c.get("CPF", c.get("CNPJ", "")),
                        c.get("Observações", "").replace("\n", " ").replace("\r", " "),
                        ausencias,
                        ferias
                    ])

                # Rodapé (data e contagem)
                writer.writerow([])
                writer.writerow([
                    f"Relatório gerado em {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
                    f"Total de colaboradores: {len(self.colaboradores)}"
                ])

            messagebox.showinfo("Exportado", f"Relatório CSV gerado com sucesso em:\n{filename}")

        except Exception as e:
            messagebox.showerror("Erro CSV", f"Falha ao exportar CSV:\n{e}")
#       ate e referente ao csv para relatorio
           
    def _backup_rapido(self):
        try:
            nome = f"backup_{ts()}.json"; destino = BACKUPS / nome
            with open(destino, "w", encoding="utf-8") as f:
                json.dump(self.colaboradores, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Backup", f"Backup salvo em:\n{destino}")
        except Exception as e:
            messagebox.showerror("Erro Backup", str(e))

    def _restaurar_backup(self):
        filename = filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")], initialdir=BACKUPS)
        if not filename: return
        if not messagebox.askyesno("Confirmar Restauração", "ATENÇÃO: A restauração irá SUBSTITUIR TODOS os dados atuais. Deseja continuar?"): return
        try:
            with open(filename, "r", encoding="utf-8") as f: backup_data = json.load(f)
            if isinstance(backup_data, list):
                self.colaboradores = backup_data; save_data(self.colaboradores)
                messagebox.showinfo("Sucesso", "Dados restaurados com sucesso a partir do backup.")
            else: messagebox.showerror("Erro", "O arquivo selecionado não contém o formato de dados esperado (lista de colaboradores).")
        except FileNotFoundError: messagebox.showerror("Erro", "Arquivo não encontrado.")
        except json.JSONDecodeError: messagebox.showerror("Erro", "O arquivo não é um JSON válido.")
        except Exception as e: messagebox.showerror("Erro Restauração", str(e))
            
    def _toggle_qr_code(self):
        if not QRCODE_AVAILABLE:
            messagebox.showerror("Erro", "A biblioteca 'qrcode' não está instalada.\nInstale com: pip install qrcode[pil]")
            return

        try:
            if not self.qr_label_widget or not self.qr_label_widget.winfo_exists():
                messagebox.showwarning("Atenção", "O container do QR Code não foi inicializado.\nTente reabrir a aba Admin/BI.")
                return

            for widget in self.qr_label_widget.winfo_children():
                widget.destroy()

            pdf_path = PDFS / PDF_SERVER_NAME
            is_pdf_ready = pdf_path.exists()
            is_server_running = hasattr(self, "http_server_thread") and getattr(self.http_server_thread, "is_running", False)

            # 🔄 Força uma tentativa de atualização de status antes de definir o QR
            if not is_server_running:
                try:
                    sock = socket.create_connection((SERVER_IP, SERVER_PORT), timeout=1)
                    sock.close()
                    is_server_running = True
                except Exception:
                    is_server_running = False

            # Define o conteúdo e cor da mensagem
            if not is_server_running:
                qr_content = "Servidor não disponível no momento"
                display_url = "⚠️ Servidor offline — tente novamente"
                text_color = "red"
            elif not is_pdf_ready:
                qr_content = PDF_URL_LOCAL
                display_url = "⚠️ Relatório ainda não gerado — gere o PDF para ativar o acesso"
                text_color = "#EAB308"
            else:
                qr_content = PDF_URL_LOCAL
                display_url = f"✅ QR Code ativo: {PDF_URL_LOCAL}"
                text_color = "#2563EB"

            # Gera o QR Code sempre, independente do status
            qr_maker = qrcode.QRCode(
                version=None,
                error_correction=qrcode_constants.ERROR_CORRECT_H,
                box_size=5,
                border=4
            )
            qr_maker.add_data(qr_content)
            qr_maker.make(fit=True)
            qr_img = qr_maker.make_image(fill_color="blue", back_color="black").convert("RGBA")
            qr_img = qr_img.resize((300, 300), RESAMPLING_NEAREST)

            qr_ctk_img = ctk.CTkImage(qr_img, size=(250, 250))
            lbl = ctk.CTkLabel(self.qr_label_widget, image=qr_ctk_img, text="")
            lbl.image = qr_ctk_img
            lbl.pack(padx=10, pady=10)

            ctk.CTkLabel(
                self.qr_label_widget,
                text=display_url,
                font=("Segoe UI", 10),
                text_color=text_color
            ).pack(pady=(0, 2))

            ctk.CTkLabel(
                self.qr_label_widget,
                text=f"Acesso via rede local: {SERVER_IP}:{SERVER_PORT}",
                text_color=text_color,
                justify="center"
            ).pack(pady=(0, 5))

            # Mensagem final ao usuário
            if is_pdf_ready and is_server_running:
                messagebox.showinfo("QR Code Ativo", f"📱 Escaneie o QR para abrir o relatório:\n{PDF_URL_LOCAL}")
            elif not is_pdf_ready:
                messagebox.showinfo("QR Code Gerado", "⚠️ QR criado, mas ainda não há relatório PDF.\nGere o relatório para ativar o acesso.")
            else:
                messagebox.showwarning("Servidor Offline", "⚠️ O servidor HTTP ainda não está ativo.")

        except Exception as e:
            messagebox.showerror("Erro QR Code", f"Erro ao gerar QR Code:\n{e}")


             
    # ----------------------------
    # Admin / BI (Layout e Funções)
    # ----------------------------
    def _frame_admin_bi(self):
        """Painel Admin/BI com gráfico e integração PDF + QR Code"""
        root = ctk.CTkFrame(self.content)
        root.pack(expand=True, fill="both", padx=10, pady=10)

        header = ctk.CTkLabel(root, text="📊 Administração, BI e Ferramentas: 🛠️",
                            font=("Segoe UI", 16, "bold"))
        header.pack(pady=(6, 10))

        # ===== 1. Métricas Rápidas =====
        metrics_group = ctk.CTkFrame(root)
        metrics_group.pack(fill="x", padx=6, pady=(6, 2))
        ctk.CTkLabel(metrics_group, text="1. Análise Rápida:📄",
                    font=("Segoe UI", 12, "bold"),
                    fg_color=("green", "green"), corner_radius=6).pack(fill="x", pady=(4, 6), padx=4)
        metrics_frame = ctk.CTkFrame(metrics_group, fg_color="orange")
        metrics_frame.pack(fill="x", padx=10, pady=8)

        total_colabs = len(self.colaboradores)
        clt_count = sum(1 for c in self.colaboradores if c.get("TipoVinculo") == "CLT")
        aus_count = sum(len(c.get("Ausências", [])) for c in self.colaboradores)
        ferias_count = sum(len(c.get("Férias", [])) for c in self.colaboradores)



        ctk.CTkLabel(metrics_frame, text=f"👥 Total de Colaboradores: {total_colabs}",
                 font=("Segoe UI", 14, "bold")).pack(side="left", padx=15)
        
        ctk.CTkLabel(metrics_frame, text=f"📑 Vínculo CLT: {clt_count}",
                 font=("Segoe UI", 14, "bold")).pack(side="left", padx=15)
        
        ctk.CTkLabel(metrics_frame, text=f"📆 Total de Ausências: {aus_count}",
                 font=("Segoe UI", 14, "bold")).pack(side="left", padx=15)

        ctk.CTkLabel(metrics_frame, text=f"📆 Total de Férias: {ferias_count}",
                 font=("Segoe UI", 14, "bold")).pack(side="left", padx=15)




        # ===== 2. Ferramentas e Exportação =====
        tools_group = ctk.CTkFrame(root)
        tools_group.pack(fill="x", padx=6, pady=6)
        ctk.CTkLabel(tools_group, text="2. Ferramentas e Exportação:📥",
                    font=("Segoe UI", 12, "bold"),
                    fg_color=("green", "green"), corner_radius=6).pack(fill="x", pady=(4, 6), padx=4)
        tools_frame = ctk.CTkFrame(tools_group, fg_color="blue")
        tools_frame.pack(fill="x", padx=10, pady=5)

        # ✅ Novo comportamento: o usuário escolhe onde salvar o PDF
        def gerar_pdf_interativo():
            try:
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".pdf",
                    filetypes=[("Arquivo PDF", "*.pdf")],
                    title="Salvar Relatório PDF como..."
                )
                if not file_path:
                    return
                self._gerar_relatorio_pdf(file_path)
                messagebox.showinfo("Relatório Gerado", f"Relatório salvo com sucesso em:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Erro ao Gerar PDF", str(e))

        ctk.CTkButton(tools_frame, text="📄 Gerar Relatório PDF", command=gerar_pdf_interativo, width=220).pack(side="left", padx=8)
        ctk.CTkButton(tools_frame, text="📥 Exportar CSV", command=self._exportar_csv, width=220).pack(side="left", padx=8)
        ctk.CTkButton(tools_frame, text="💾 Fazer Backup Rápido", command=self._backup_rapido, width=220).pack(side="left", padx=8)
        ctk.CTkButton(tools_frame, text="🔄 Restaurar Backup", command=self._restaurar_backup, width=220, fg_color="#F59E0B").pack(side="left", padx=8)

        # ===== 3. Visual (QR à esquerda / Gráfico à direita) =====
        main_frame = ctk.CTkFrame(root)
        main_frame.pack(fill="both", expand=True, padx=6, pady=6)

        # === QR Code ===
        qr_frame = ctk.CTkFrame(main_frame)
        qr_frame.pack(side="left", fill="both", expand=True, padx=(0, 3), pady=3)

        qr_control_frame = ctk.CTkFrame(qr_frame, fg_color="blue")
        qr_control_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(qr_control_frame, text="🔗 Gerar/Atualizar QR Code",
                    command=self._toggle_qr_code, width=220).pack(side="left", padx=8, pady=8)
        ctk.CTkLabel(qr_control_frame, text=f"O QR aponta para: {PDF_URL_LOCAL}").pack(side="left", padx=10)

        self.qr_label_widget = ctk.CTkFrame(qr_frame, height=250)
        self.qr_label_widget.pack(fill="both", expand=True, padx=10, pady=10)
        ctk.CTkLabel(self.qr_label_widget, text="Gere o PDF e depois clique em 'Gerar/Atualizar QR Code'.\n(Servidor HTTP deve estar rodando em segundo plano)").pack(pady=50)

       # self.qr_label_widget = ctk.CTkFrame(qr_frame, height=250)
        #self.qr_label_widget.pack(fill="both", expand=True, padx=10, pady=10)
        #ctk.CTkLabel(self.qr_label_widget, text="Gere o PDF e depois clique em 'Gerar/Atualizar QR Code'.\n(Servidor HTTP deve estar rodando em segundo plano)").pack(pady=50)

        # === Gráfico ===
        chart_frame = ctk.CTkFrame(main_frame)
        chart_frame.pack(side="right", fill="both", expand=True, padx=(3, 0), pady=3)

        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(4, 3))
        labels = ['CLT', 'PJ', 'Ausências', 'Férias']
        counts = [
            sum(1 for c in self.colaboradores if c.get("TipoVinculo") == "CLT"),
            sum(1 for c in self.colaboradores if c.get("TipoVinculo") == "Pessoa Jurídica"),
            sum(1 for c in self.colaboradores if c.get("TipoVinculo") == "Ausências"),
            sum(1 for c in self.colaboradores if c.get("TipoVinculo") == "Férias")
        ]
        ax.bar(labels, counts, color='#2563EB')
        ax.set_title("Colaboradores por Tipo:", fontsize=10)
        ax.set_ylabel("Quantidade:")
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
    # ----------------------------
    # Geração de QR Code para o PDF
    def _gerar_qrcode_relatorio(self):
        import qrcode
        from PIL import Image, ImageTk
        import os

        pdf_path = "dados_sistema/relatorio.pdf"
        if not os.path.exists(pdf_path):
            messagebox.showwarning("⚠️ Aviso", "Nenhum relatório encontrado. Gere o PDF antes.")
            return

        # Criação do QR
        qr = qrcode.QRCode(version=1, box_size=8, border=3)
        qr.add_data(pdf_path)
        qr.make(fit=True)
        img = qr.make_image(fill_color="blue", back_color="white")
        qr_path = "dados_sistema/qr_relatorio.png"
        img.save(qr_path)

        # Mostra QR na interface
        pil_img = Image.open(qr_path).resize((250, 250))
        self.qr_img_tk = ImageTk.PhotoImage(pil_img)
        self.qr_label_widget.configure(image=self.qr_img_tk, text="")
        messagebox.showinfo("QR Code", "Aponte a câmera do celular para acessar o PDF.")


# ----------------------------
# Entrypoint 
# ----------------------------
def start_app():
    app = SistemaRH()
    app.mainloop()

if __name__ == "__main__":
    ensure_data()
    cfg = ensure_config()
    try:
        if not ICON_LOGIN.exists():
            create_login_padlock(size=200)
        if not ICON_SPLASH.exists():
            create_splash_graphics(size=220)
    except Exception:
        pass
        
    def start_main():
        start_app()

    splash = Splash(start_main, theme=DEFAULT_THEME)
    splash.mainloop()