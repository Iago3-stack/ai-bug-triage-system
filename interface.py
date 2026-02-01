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
            print(f"Servidor HTTP iniciado em http://{self.host}:{self.port}")
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
            print("Servidor HTTP parado.")
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
ctk.set_default_color_theme("blue")

def ts():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

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
        self.on_finish = on_finish
        self.theme = theme
        self.title("Gerenciador RH ➕ — Inicializando")
        self.geometry("560x420")
        self.resizable(False, False)
        try:
            self.eval('tk::PlaceWindow . center')
        except Exception:
            pass
        self.configure(fg_color="#1E3A8A" if theme=="dark" else "#FFFFFF")

        self.canvas_label = ctk.CTkLabel(self, text="")
        self.canvas_label.pack(pady=(20,10))

        self.title_label = ctk.CTkLabel(self, text="Gerenciador RH — BI", font=("Segoe UI", 20, "bold"),
                                        text_color="white" if theme=="dark" else "black")
        self.title_label.pack(pady=(4,10))

        self.progress = ctk.CTkProgressBar(self, width=420)
        self.progress.pack(pady=(8,6))
        self.progress.set(0.0)

        self.msg_label = ctk.CTkLabel(self, text="Preparando visualização...", text_color="#DDE6FF")
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
        self.title("Gerenciador RH ➕ — Sistema")
        self.geometry("1240x780")
        self.minsize(1000, 620)
        try:
            self.eval('tk::PlaceWindow . center')
        except Exception:
            pass

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
        style.map('Treeview', background=[('selected', select_color)])
        style.configure("Treeview.Heading", 
                        background=header_color, 
                        foreground=header_fg, 
                        font=("Segoe UI", 10, "bold"))
    
    def _show_frame(self, frame_name):
        for widget in self.content.winfo_children():
            widget.destroy()
            
        self.lista_tree = None
        self.qr_label_widget = None

        if frame_name == "cadastro":
            self._frame_cadastro()
        elif frame_name == "lista_edicao":
            self._setup_treeview_style() 
            self._frame_lista_edicao()
        elif frame_name == "ausencias":
            self._frame_ausencias()
        elif frame_name == "ferias":  # ✅ Adicione esta linha
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
        title = ctk.CTkLabel(frame, text="🔐 Acesso — Gerenciador RH ➕", font=("Segoe UI", 20, "bold"))
        title.pack(pady=(6,8))
        self.login_user = ctk.CTkEntry(frame, placeholder_text="Usuário", width=380)
        self.login_user.pack(pady=(8,6))
        self.login_pass = ctk.CTkEntry(frame, placeholder_text="Senha", show="*", width=380)
        self.login_pass.pack(pady=(6,8))
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(pady=(8,6))
        ctk.CTkButton(btn_frame, text="Entrar", width=160, command=self._do_login).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="Alterar senha", width=160, command=self._open_change_password_modal).pack(side="left", padx=8)
        self.login_msg = ctk.CTkLabel(frame, text="", text_color="red")
        self.login_msg.pack(pady=(6,10))
    def _do_login(self):
        u = self.login_user.get().strip(); p = self.login_pass.get().strip()
        if u in self.users and self.users[u] == p:
            self.current_user = u
            self._build_main_ui() 
        else:
            self.login_msg.configure(text="Usuário ou senha incorretos ❌")
    def _open_change_password_modal(self):
        top = ctk.CTkToplevel(self); top.title("Alterar Senha"); top.geometry("420x240")
        try: top.eval('tk::PlaceWindow . center')
        except Exception: pass
        top.transient(self); top.grab_set()
        ctk.CTkLabel(top, text="Alterar senha do usuário", font=("Segoe UI", 14, "bold")).pack(pady=(12,8))
        user_ent = ctk.CTkEntry(top, placeholder_text="Usuário", width=340); user_ent.pack(pady=6)
        pass_ent = ctk.CTkEntry(top, placeholder_text="Nova senha", show="*", width=340); pass_ent.pack(pady=6)
        def do_change():
            u = user_ent.get().strip(); p = pass_ent.get().strip()
            if not u or not p: messagebox.showwarning("Atenção", "Informe usuário e nova senha."); return
            self.users[u] = p; self.config["users"] = self.users; save_config(self.config)
            messagebox.showinfo("Sucesso", f"Senha do usuário '{u}' atualizada.")
            try: top.grab_release(); top.destroy()
            except Exception: pass
        ctk.CTkButton(top, text="Salvar", width=160, command=do_change).pack(pady=(12,14))

    # ----------------------------
    # Main UI (Menu Lateral)
    # ----------------------------
    def _build_main_ui(self):
        for w in self.winfo_children(): w.destroy()
        self._setup_treeview_style() 
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=8); self.sidebar.pack(side="left", fill="y", padx=(12,10), pady=12)
        theme_color = self.config.get("theme", "dark")
        brand_text_color = "white" if theme_color == "dark" else "black"
        brand = ctk.CTkLabel(self.sidebar, text="Gerenciador RH ➕", font=("Segoe UI",18,"bold"), text_color=brand_text_color); brand.pack(pady=(16,8))
        ctk.CTkButton(self.sidebar, text="➕ Cadastro", command=lambda:self._show_frame("cadastro"), width=220, fg_color="#2563EB").pack(pady=(10,8))
        ctk.CTkButton(self.sidebar, text="📋 Lista / Edição", command=lambda:self._show_frame("lista_edicao"), width=220, fg_color="#2563EB").pack(pady=8)
        ctk.CTkButton(self.sidebar, text="📅 Ausências", command=lambda:self._show_frame("ausencias"), width=220, fg_color="#2563EB").pack(pady=8)
        ctk.CTkButton(self.sidebar, text="⛱️ Férias", command=lambda:self._show_frame("ferias"), width=220, fg_color="#2563EB").pack(pady=8)
        ctk.CTkButton(self.sidebar, text="📊 Admin / BI", command=lambda:self._show_frame("admin_bi"), width=220, fg_color="#2563EB").pack(pady=8)
        spacer = ctk.CTkLabel(self.sidebar, text=""); spacer.pack(expand=True, fill="y")
        self.theme_var.set(self.theme.capitalize()) 
        ctk.CTkLabel(self.sidebar, text="🌓 Modo de Aparência:").pack(pady=(12, 0))
        ctk.CTkOptionMenu(self.sidebar, values=["Dark", "Light"], command=self._change_theme_option_menu, variable=self.theme_var, width=220).pack(pady=(0, 15))
        ctk.CTkButton(self.sidebar, text="🚪 Sair / Logout", command=self._logout_to_login, width=220, fg_color="#DC2626").pack(pady=(6,18))
        self.content = ctk.CTkFrame(self, corner_radius=8); self.content.pack(side="right", expand=True, fill="both", padx=(6,12), pady=12)
        self._show_frame("cadastro")

    def _change_theme_option_menu(self, new_theme_value):
        new_theme = new_theme_value.lower()
        if new_theme != self.theme:
            ctk.set_appearance_mode(new_theme)
            self.config["theme"] = new_theme
            self.theme = new_theme
            save_config(self.config)
            self._build_main_ui()

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
        header = ctk.CTkLabel(root, text="Cadastro de Novo Colaborador / Edição", font=("Segoe UI",16,"bold")); header.pack(pady=(6,10))
        topico1 = ctk.CTkFrame(root); topico1.pack(fill="x", padx=6, pady=(6,2))
        ctk.CTkLabel(topico1, text="1. Identificação", font=("Segoe UI", 12, "bold"), fg_color=("gray80", "gray20"), corner_radius=6).pack(fill="x", pady=(4,6), padx=4)
        row1 = ctk.CTkFrame(topico1, fg_color="transparent"); row1.pack(fill="x", pady=(2,6))
        ctk.CTkLabel(row1, text="Nome", width=160, anchor="w").pack(side="left", padx=(6,12))
        self.e_nome = ctk.CTkEntry(row1); self.e_nome.pack(side="left", fill="x", expand=True, padx=(0,6))
        ctk.CTkLabel(row1, text="E-mail", width=140, anchor="w").pack(side="left", padx=(6,12))
        self.e_email = ctk.CTkEntry(row1, width=240); self.e_email.pack(side="left", padx=(0,6))
        row2 = ctk.CTkFrame(topico1, fg_color="transparent"); row2.pack(fill="x", pady=(2,6))
        ctk.CTkLabel(row2, text="Telefone", width=160, anchor="w").pack(side="left", padx=(6,12))
        self.e_telefone = ctk.CTkEntry(row2); self.e_telefone.pack(side="left", fill="x", expand=True, padx=(0,6))
        ctk.CTkLabel(row2, text="Cargo/Função", width=140, anchor="w").pack(side="left", padx=(6,12))
        self.e_cargo = ctk.CTkEntry(row2, width=240); self.e_cargo.pack(side="left", padx=(0,6))
        topico2 = ctk.CTkFrame(root); topico2.pack(fill="x", padx=6, pady=6)
        ctk.CTkLabel(topico2, text="2. Vínculo e Admissão", font=("Segoe UI", 12, "bold"), fg_color=("gray80", "gray20"), corner_radius=6).pack(fill="x", pady=(4,6), padx=4)
        row3 = ctk.CTkFrame(topico2, fg_color="transparent"); row3.pack(fill="x", pady=(2,6))
        ctk.CTkLabel(row3, text="Tipo de vínculo", width=160, anchor="w").pack(side="left", padx=(6,12))
        self.tipo_var = ctk.StringVar(value="CLT")
        self.tipo_menu = ctk.CTkOptionMenu(row3, values=["CLT","Pessoa Jurídica","Freelancer", "Estágio"], variable=self.tipo_var, command=self._on_tipo_change); self.tipo_menu.pack(side="left", padx=(0,6))
        row4 = ctk.CTkFrame(topico2, fg_color="transparent"); row4.pack(fill="x", pady=(2,6))
        self.lbl_documento = ctk.CTkLabel(row4, text="CPF", width=160, anchor="w"); self.lbl_documento.pack(side="left", padx=(6,12))
        self.e_documento = ctk.CTkEntry(row4); self.e_documento.pack(side="left", fill="x", expand=True, padx=(0,6))
        ctk.CTkLabel(row4, text="Salário/Valor (R$)", width=140, anchor="w").pack(side="left", padx=(6,12))
        self.e_salario = ctk.CTkEntry(row4, width=200); self.e_salario.pack(side="left", padx=(0,6))
        row5 = ctk.CTkFrame(topico2, fg_color="transparent"); row5.pack(fill="x", pady=(2,6))
        ctk.CTkLabel(row5, text="Data de admissão/início (AAAA-MM-DD)", width=320, anchor="w").pack(side="left", padx=(6,12))
        self.e_data = ctk.CTkEntry(row5, width=260); self.e_data.pack(side="left", padx=(0,6))
        topico3 = ctk.CTkFrame(root); topico3.pack(fill="x", padx=6, pady=6)
        ctk.CTkLabel(topico3, text="3. Observações Adicionais", font=("Segoe UI", 12, "bold"), fg_color=("gray80", "gray20"), corner_radius=6).pack(fill="x", pady=(4,6), padx=4)
        row6 = ctk.CTkFrame(topico3, fg_color="transparent"); row6.pack(fill="both", pady=(2,6))
        self.e_obs = ctk.CTkTextbox(row6, height=100); self.e_obs.pack(side="left", fill="both", expand=True, padx=6, pady=6)
        btns = ctk.CTkFrame(root, fg_color="transparent"); btns.pack(pady=(8,12))
        ctk.CTkButton(btns, text="➕ Adicionar / Atualizar", command=self._salvar_colaborador, width=220, fg_color="#2563EB").pack(side="left", padx=8)
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
        header = ctk.CTkLabel(root, text="Lista de Colaboradores Cadastrados", font=("Segoe UI",16,"bold")); header.pack(pady=(6,10))
        list_frame = ctk.CTkFrame(root); list_frame.pack(fill="both", expand=True, padx=8, pady=8)
        columns = ("Nome", "Tipo", "Cargo", "Salario")
        self.lista_tree = tkinter.ttk.Treeview(list_frame, columns=columns, show="headings", style="Treeview")
        self.lista_tree.heading("Nome", text="NOME DO COLABORADOR", anchor="w"); self.lista_tree.heading("Tipo", text="TIPO VÍNCULO", anchor="center")
        self.lista_tree.heading("Cargo", text="CARGO/FUNÇÃO", anchor="w"); self.lista_tree.heading("Salario", text="SALÁRIO/VALOR", anchor="e")
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

    # ----------------------------
    # Ausências 
    # ----------------------------
    def _frame_ausencias(self):
        root = ctk.CTkFrame(self.content); root.pack(expand=True, fill="both", padx=10, pady=10)
        header = ctk.CTkLabel(root, text="Registro de Ausências", font=("Segoe UI", 16, "bold")); header.pack(pady=(6,10))
        self.colaboradores = load_data()
        nomes_cadastrados = sorted([c.get("Nome", "") for c in self.colaboradores if c.get("Nome", "")])
        form = ctk.CTkFrame(root, fg_color="transparent"); form.pack(fill="x", padx=6, pady=6)
        ctk.CTkLabel(form, text="Nome do colaborador", width=180, anchor="w").pack(side="left", padx=(6,8))
        self.f_nome = ctk.CTkComboBox(form, values=nomes_cadastrados, state="readonly")
        if nomes_cadastrados: self.f_nome.set(nomes_cadastrados[0])
        else: self.f_nome.set("")
        self.f_nome.pack(side="left", fill="x", expand=True, padx=(0,6))
        ctk.CTkLabel(form, text="Data (AAAA-MM-DD)", width=160, anchor="w").pack(side="left", padx=(6,8))
        self.f_data = ctk.CTkEntry(form, width=160); self.f_data.pack(side="left", padx=(0,6))
        ctk.CTkLabel(root, text="Motivo:").pack(anchor="w", padx=10, pady=(10,4))
        self.f_motivo = ctk.CTkEntry(root); self.f_motivo.pack(fill="x", padx=10, pady=(0,8))
        ctk.CTkButton(root, text="✅ Confirmar Ausência", command=self._confirmar_ausencia, width=220).pack(pady=(8,10))

    def _confirmar_ausencia(self):
        n = self.f_nome.get().strip(); d = self.f_data.get().strip(); m = self.f_motivo.get().strip()
        if not n or not d or not m: messagebox.showwarning("Atenção", "Preencha todos os campos."); return
        try: datetime.date.fromisoformat(d)
        except ValueError: messagebox.showerror("Erro de Data", "Formato de data inválido. Use AAAA-MM-DD."); return
        encontrado = False
        for c in self.colaboradores:
            if c.get("Nome","").lower() == n.lower():
                if "Ausências" not in c: c["Ausências"] = []
                c["Ausências"].append({"Data": d, "Motivo": m})
                encontrado = True; break
        if encontrado:
            save_data(self.colaboradores); messagebox.showinfo("Sucesso", f"Ausência de '{n}' na data {d} registrada.")
            self.f_data.delete(0, "end"); self.f_motivo.delete(0, "end")
        else: messagebox.showerror("Erro", f"Colaborador '{n}' não encontrado.")

    def _frame_ferias(self):
        root = ctk.CTkFrame(self.content); root.pack(expand=True, fill="both", padx=10, pady=10)
        header = ctk.CTkLabel(root, text="Registro de Férias", font=("Segoe UI", 16, "bold")); header.pack(pady=(6,10))

        self.colaboradores = load_data()
        nomes_cadastrados = sorted([c.get("Nome", "") for c in self.colaboradores if c.get("Nome", "")])
                
                # === Formulário de Registro ===
        form1 = ctk.CTkFrame(root, fg_color="transparent") 
        form1.pack(fill="x", padx=6, pady=4)

        ctk.CTkLabel(form1, text="Nome do colaborador", width=180, anchor="w").pack(side="left", padx=(6,8))
        self.f_ferias_nome = ctk.CTkComboBox(form1, values=nomes_cadastrados, state="readonly", width=220)
        if nomes_cadastrados: 
            self.f_ferias_nome.set(nomes_cadastrados[0])
        self.f_ferias_nome.pack(side="left", padx=(0,6))

        ctk.CTkLabel(form1, text="Início (DD/MM/AAAA)", width=160, anchor="w").pack(side="left", padx=(6,8))
        self.f_ferias_inicio = ctk.CTkEntry(form1, width=140) 
        self.f_ferias_inicio.pack(side="left", padx=(0,6))

        form2 = ctk.CTkFrame(root, fg_color="transparent")
        form2.pack(fill="x", padx=6, pady=4)

        ctk.CTkLabel(form2, text="Término (DD/MM/AAAA)", width=160, anchor="w").pack(side="left", padx=(6,8))
        self.f_ferias_fim = ctk.CTkEntry(form2, width=140) 
        self.f_ferias_fim.pack(side="left", padx=(0,6))


        ctk.CTkLabel(form2, text="Valor:(R$)", width=100, anchor="w").pack(side="left", padx=(6,8))
        self.f_ferias_valor = ctk.CTkEntry(form2, width=140)
        self.f_ferias_valor.pack(side="left", padx=(0,6))

        btns = ctk.CTkFrame(root, fg_color="transparent"); btns.pack(pady=(8,12))
        ctk.CTkButton(btns, text="💾 Salvar / Registrar Férias", command=self._salvar_ferias, width=220, fg_color="#2563EB").pack(side="left", padx=8)
        ctk.CTkButton(btns, text="✏️ Editar Selecionado", command=self._editar_ferias, width=180, fg_color="#F59E0B").pack(side="left", padx=8)

        hist_frame = ctk.CTkFrame(root); hist_frame.pack(fill="both", expand=True, padx=10, pady=(4,10))
        ctk.CTkLabel(hist_frame, text="Histórico de Férias Registradas", font=("Segoe UI", 14, "bold")).pack(pady=(4,8))

        columns = ("Colaborador", "Início", "Término", "Valor")
        self.tree_ferias = ttk.Treeview(hist_frame, columns=columns, show="headings", style="Treeview")
        for col in columns:
            self.tree_ferias.heading(col, text=col, anchor="center")
            self.tree_ferias.column(col, anchor="center", width=160)
        scrollbar = ctk.CTkScrollbar(hist_frame, command=self.tree_ferias.yview); self.tree_ferias.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y", padx=(0,6), pady=6); self.tree_ferias.pack(fill="both", expand=True, padx=(6,0), pady=6)

        self._atualizar_historico_ferias()

    def _salvar_ferias(self):
        n = self.f_ferias_nome.get().strip(); inicio = self.f_ferias_inicio.get().strip()
        fim = self.f_ferias_fim.get().strip(); valor = self.f_ferias_valor.get().strip()
        if not n or not inicio or not fim or not valor:
            messagebox.showwarning("Atenção", "Preencha todos os campos."); return

        # valida formato DD/MM/YYYY
        for d in (inicio, fim):
            try:
                datetime.datetime.strptime(d, "%d/%m/%Y")
            except Exception:
                messagebox.showerror("Erro de Data", f"Data inválida: {d}. Use DD/MM/AAAA."); return

        for c in self.colaboradores:
            if c.get("Nome","").lower() == n.lower():
                if "Ferias" not in c: c["Ferias"] = []
                c["Ferias"].append({"Inicio": inicio, "Termino": fim, "Valor": valor})
                save_data(self.colaboradores)
                messagebox.showinfo("Sucesso", f"Férias de '{n}' registradas.")
                self._limpar_campos_ferias(); self._atualizar_historico_ferias()
                return
        messagebox.showerror("Erro", f"Colaborador '{n}' não encontrado.")

    def _editar_ferias(self):
        sel = self.tree_ferias.focus()
        if not sel: messagebox.showwarning("Atenção", "Selecione um registro para editar."); return
        vals = self.tree_ferias.item(sel, "values")
        if not vals: return
        nome, inicio, fim, valor = vals
        self.f_ferias_nome.set(nome)
        self.f_ferias_inicio.delete(0,"end"); self.f_ferias_inicio.insert(0, inicio)
        self.f_ferias_fim.delete(0,"end"); self.f_ferias_fim.insert(0, fim)
        self.f_ferias_valor.delete(0,"end"); self.f_ferias_valor.insert(0, valor)

        # remove registro antigo para evitar duplicidade (será re-salvo ao salvar)
        for c in self.colaboradores:
            if c.get("Nome","").lower() == nome.lower() and "Ferias" in c:
                c["Ferias"] = [f for f in c["Ferias"] if not (f.get("Inicio")==inicio and f.get("Termino")==fim)]
                save_data(self.colaboradores)
                self._atualizar_historico_ferias()
                break

    def _atualizar_historico_ferias(self):
        if not hasattr(self, "tree_ferias"): return
        for item in self.tree_ferias.get_children(): self.tree_ferias.delete(item)
        self.colaboradores = load_data()
        for c in self.colaboradores:
            nome = c.get("Nome","")
            for f in c.get("Ferias", []):
                self.tree_ferias.insert("", "end", values=(nome, f.get("Inicio",""), f.get("Termino",""), f.get("Valor","")))

    def _limpar_campos_ferias(self):
        try:
            self.f_ferias_inicio.delete(0,"end"); self.f_ferias_fim.delete(0,"end"); self.f_ferias_valor.delete(0,"end")
        except Exception:
            pass

    # ----------------------------
    # Funções Admin/BI (Layout PDF Corrigido)
    # ----------------------------
    def _gerar_relatorio_pdf(self):
        if not REPORTLAB_AVAILABLE:
            messagebox.showerror("Erro", "A biblioteca 'reportlab' não está instalada. Instale com: pip install reportlab")
            return
            
        filename_server = PDFS / PDF_SERVER_NAME
        pdf_name_archive = f"Relatorio_RH_{ts()}.pdf"
        filename_archive = PDFS / pdf_name_archive
        
        try:
            c = canvas.Canvas(str(filename_server), pagesize=A4)
            width, height = A4
            
            # --- Configurações de Layout ---
            HEADER_FONT_SIZE = 15
            DATA_FONT_SIZE = 8
            # Aumentei o line_height para garantir espaço entre as linhas
            LINE_HEIGHT = 25 
            # Margem superior do conteúdo
            Y_START_MARGIN = height - 80 
            X_START = 30
            
            # Headers e larguras das 5 colunas (ajustado para caber na página A4)
            headers = ["Nome", "Cargo/Função", "Tipo Vínculo", "Salário", "Data Admissão"]
            # Larguras: (200 + 100 + 100 + 80 + 80) = 560 (A4 tem cerca de 595 de largura)
            col_widths = [180, 100, 100, 80, 80] 
            
            # --- Funções de Desenho ---
            def draw_page_header(canvas, y_position):
                canvas.setFont("Helvetica-Bold", HEADER_FONT_SIZE)
                canvas.drawString(X_START, y_position, "Relatório Geral de Colaboradores - Gerenciador RH")
                y_position -= 15
                canvas.setFont("Helvetica", 10)
                canvas.drawString(X_START, y_position, f"Gerado em: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
                y_position -= 25 # Espaço antes do cabeçalho da tabela
                return y_position

            def draw_table_header(canvas, y_position, headers, col_widths, x_start):
                canvas.setFont("Helvetica-Bold", DATA_FONT_SIZE + 1)
                x = x_start
                # Desenha os títulos com espaço extra
                for i, header in enumerate(headers):
                    canvas.drawString(x, y_position - 8, header)
                    x += col_widths[i]
                
                # Linha separadora do cabeçalho
                y_position -= 12 
                canvas.line(x_start, y_position, x_start + sum(col_widths), y_position)
                
                # Espaço após a linha
                return y_position - 10 
            
            # --- Início do Desenho ---
            y_pos = draw_page_header(c, height - 30)
            y_pos = draw_table_header(c, y_pos, headers, col_widths, X_START)
            
            c.setFont("Helvetica", DATA_FONT_SIZE)
            
            for colaborador in self.colaboradores:
                # Se a linha estiver muito baixa, cria uma nova página e desenha o cabeçalho
                if y_pos < 40:
                    c.showPage()
                    y_pos = height - 30
                    y_pos = draw_page_header(c, y_pos)
                    y_pos = draw_table_header(c, y_pos, headers, col_widths, X_START)
                    c.setFont("Helvetica", DATA_FONT_SIZE)

                x = X_START
                data = [
                    colaborador.get("Nome", "N/A"),
                    colaborador.get("Cargo/Função", "N/A"),
                    colaborador.get("TipoVinculo", "N/A"),
                    colaborador.get("Salario", "N/A"),
                    colaborador.get("Data de Admissão", "N/A")
                ]
                
                # Desenha a linha de dados
                for i, d in enumerate(data):
                    # Desenhar com um pequeno recuo vertical (por exemplo, 8 pontos)
                    c.drawString(x, y_pos - 8, d) 
                    x += col_widths[i]
                
                # Ajusta a posição vertical para a próxima linha
                y_pos -= LINE_HEIGHT 

            c.save()
            
            # Copia o arquivo gerado para o arquivo de backup/arquivamento
            shutil.copy(filename_server, filename_archive)

            self.last_pdf_path = str(filename_server) 
            
            messagebox.showinfo("PDF Gerado", f"Relatório PDF salvo (e atualizado para acesso via QR Code) em:\n{filename_archive}")
            
            if self.qr_label_widget: self._toggle_qr_code()
            
        except Exception as e:
            messagebox.showerror("Erro PDF", f"Não foi possível gerar o PDF. Erro: {e}")

    def _exportar_csv(self):
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")], initialfile="Colaboradores_Export_"+ts()+".csv")
        if not filename: return
        try:
            fieldnames = ["Nome", "E-mail", "Telefone", "Cargo/Função", "TipoVinculo", "Documento", "Salario", "Data de Admissão", "Observações"]
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
                writer.writeheader()
                export_data = []
                for c in self.colaboradores:
                    row = {k: c.get(k, '') for k in fieldnames}
                    row['Observações'] = row['Observações'].replace('\n', ' ').replace('\r', ' ')
                    export_data.append(row)
                writer.writerows(export_data)
            messagebox.showinfo("Exportado", f"Dados exportados para CSV com sucesso em:\n{filename}")
        except Exception as e:
            messagebox.showerror("Erro CSV", f"Não foi possível exportar para CSV. Erro: {e}")
            
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
            messagebox.showerror("Erro", "A biblioteca 'qrcode' não está instalada. Instale com: pip install qrcode[pil]")
            return
        try:
            if not self.qr_label_widget or not self.qr_label_widget.winfo_exists():
                messagebox.showwarning("Atenção", "O container do QR Code não foi inicializado. Tente reabrir a aba Admin/BI.")
                return
            for widget in self.qr_label_widget.winfo_children(): widget.destroy()

            is_pdf_ready = os.path.exists(PDFS / PDF_SERVER_NAME)
            is_server_running = self.http_server_thread.is_running
            
            if not is_pdf_ready or not is_server_running:
                qr_content = "https://gererelatorio.primeiro"
                display_url = "⚠️ Servidor Offline / PDF Ausente!"
                text_color = "red"
            else:
                qr_content = PDF_URL_LOCAL 
                display_url = f"URL NO QR: {PDF_URL_LOCAL}"
                text_color = "#2563EB"

            qr_maker = qrcode.QRCode(version=None, error_correction=qrcode_constants.ERROR_CORRECT_H, box_size=5, border=4)
            qr_maker.add_data(qr_content); qr_maker.make(fit=True)
            qr_img = qr_maker.make_image(fill_color="black", back_color="white").convert("RGBA")
            qr_img = qr_img.resize((200, 200), RESAMPLING_NEAREST)
            qr_ctk_img = ctk.CTkImage(qr_img, size=(200, 200))
            
            lbl = ctk.CTkLabel(self.qr_label_widget, image=qr_ctk_img, text=""); lbl.image = qr_ctk_img
            lbl.pack(padx=10, pady=10) 
            ctk.CTkLabel(self.qr_label_widget, text=display_url, font=("Segoe UI", 10)).pack(pady=(0, 2))
            
            ctk.CTkLabel(self.qr_label_widget, 
                         text=f"Acesso via rede local: Servidor rodando em {SERVER_IP}:{SERVER_PORT}",
                         text_color=text_color, 
                         justify="center").pack(pady=(0, 5))
                         
            if is_server_running and is_pdf_ready:
                 messagebox.showinfo("QR Code", f"QR Code gerado. Aponte o celular para {SERVER_IP}:{SERVER_PORT} e o relatório será aberto.")
            elif not is_server_running:
                 messagebox.showwarning("Atenção", "O Servidor HTTP não está rodando! O QR Code não funcionará. Verifique se a porta 8000 está livre ou reinicie o aplicativo.")

        except Exception as e:
             messagebox.showerror("Erro QR Code", f"Erro ao gerar QR Code: {e}.")
             
    # ----------------------------
    # Admin / BI (Layout e Funções)
    # ----------------------------
    def _frame_admin_bi(self):
        root = ctk.CTkFrame(self.content); root.pack(expand=True, fill="both", padx=10, pady=10)
        header = ctk.CTkLabel(root, text="Administração, BI e Ferramentas", font=("Segoe UI", 16, "bold")); header.pack(pady=(6,10))
        metrics_group = ctk.CTkFrame(root); metrics_group.pack(fill="x", padx=6, pady=(6,2))
        ctk.CTkLabel(metrics_group, text="1. Análise Rápida", font=("Segoe UI", 12, "bold"), fg_color=("gray80", "gray20"), corner_radius=6).pack(fill="x", pady=(4,6), padx=4)
        metrics_frame = ctk.CTkFrame(metrics_group, fg_color="transparent"); metrics_frame.pack(fill="x", padx=10, pady=8)
        total_colabs = len(self.colaboradores); clt_count = sum(1 for c in self.colaboradores if c.get("TipoVinculo") == "CLT")
        aus_count = sum(len(c.get("Ausências", [])) for c in self.colaboradores)
        ctk.CTkLabel(metrics_frame, text=f"Total de Colaboradores: {total_colabs}", font=("Segoe UI", 14, "bold")).pack(side="left", padx=15, pady=4)
        ctk.CTkLabel(metrics_frame, text=f"Vínculo CLT: {clt_count}", font=("Segoe UI", 14, "bold")).pack(side="left", padx=15, pady=4)
        ctk.CTkLabel(metrics_frame, text=f"Total de Ausências Registradas: {aus_count}", font=("Segoe UI", 14, "bold")).pack(side="left", padx=15, pady=4)
        tools_group = ctk.CTkFrame(root); tools_group.pack(fill="x", padx=6, pady=6)
        ctk.CTkLabel(tools_group, text="2. Ferramentas e Exportação", font=("Segoe UI", 12, "bold"), fg_color=("gray80", "gray20"), corner_radius=6).pack(fill="x", pady=(4,6), padx=4)
        tools_frame = ctk.CTkFrame(tools_group, fg_color="transparent"); tools_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(tools_frame, text="📄 Gerar Relatório PDF", command=self._gerar_relatorio_pdf, width=220).pack(side="left", padx=8)
        ctk.CTkButton(tools_frame, text="📥 Exportar CSV", command=self._exportar_csv, width=220).pack(side="left", padx=8)
        ctk.CTkButton(tools_frame, text="💾 Fazer Backup Rápido", command=self._backup_rapido, width=220).pack(side="left", padx=8)
        ctk.CTkButton(tools_frame, text="🔄 Restaurar Backup", command=self._restaurar_backup, width=220, fg_color="#F59E0B").pack(side="left", padx=8)
        qr_group = ctk.CTkFrame(root); qr_group.pack(fill="x", padx=6, pady=6)
        ctk.CTkLabel(qr_group, text="3. QR Code para Acesso Rápido ao Relatório", font=("Segoe UI", 12, "bold"), fg_color=("gray80", "gray20"), corner_radius=6).pack(fill="x", pady=(4,6), padx=4)
        qr_control_frame = ctk.CTkFrame(qr_group, fg_color="transparent"); qr_control_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(qr_control_frame, text="🔗 Gerar/Atualizar QR Code", command=self._toggle_qr_code, width=220).pack(side="left", padx=8, pady=8)
        ctk.CTkLabel(qr_control_frame, text=f"O QR aponta para: {PDF_URL_LOCAL}").pack(side="left", padx=10)
        self.qr_label_widget = ctk.CTkFrame(qr_group, height=250); self.qr_label_widget.pack(fill="both", padx=10, pady=10)
        ctk.CTkLabel(self.qr_label_widget, text="Gere o PDF e depois clique em 'Gerar/Atualizar QR Code'.\n(Servidor HTTP deve estar rodando em segundo plano)").pack(pady=50)

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