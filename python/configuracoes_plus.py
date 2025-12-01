# configure_plus_full.py
# Painel Configure+ embutível (CTkFrame) — compatível com IAERPV5.py (usa pasta dados_sistema)
import json
import shutil
from pathlib import Path
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox, filedialog, simpledialog

# Paths (compatível com IAERPV5.py)
ROOT = Path("dados_sistema")
ROOT.mkdir(parents=True, exist_ok=True)
CONFIG_PATH = ROOT / "config.json"
BACKUPS = ROOT / "backups"
BACKUPS.mkdir(parents=True, exist_ok=True)

# Chave que você define para liberar licença permanente (troque por sua chave)
ADMIN_LICENSE_KEY = "MINHA-CHAVE-PERMA"  # <--- Substitua por sua chave real

DEFAULT_CONFIG = {
    "theme": "dark",
    "language": "Português (BR)",
    "license": {"type": "trial", "until": "2026-12-31"},
    "email_smtp": {"sender": "", "password": ""},
    "company": {"name": "", "cnpj": "", "logo_path": ""}
}

MOCK_FLAGS = {
    "Português (BR)": "🇧🇷",
    "English (US)": "🇺🇸",
    "Español": "🇪🇸",
}

def load_or_create_config():
    if CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            # garante chaves
            for k, v in DEFAULT_CONFIG.items():
                if k not in cfg:
                    cfg[k] = v
            return cfg
        except Exception:
            pass
    # cria padrão
    CONFIG_PATH.write_text(json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=2), encoding="utf-8")
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    try:
        CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except Exception as e:
        print("Erro salvar config:", e)
        return False

class ConfigurePlusPanel(ctk.CTkFrame):
    """Painel embutido de configurações — use dentro do seu frame principal."""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.pack(expand=True, fill="both")
        self.cfg = load_or_create_config()

        # Variáveis
        self.theme_var = ctk.StringVar(value=self.cfg.get("theme", "dark").capitalize())
        self.lang_var = ctk.StringVar(value=self.cfg.get("language", "Português (BR)"))
        self.smtp_sender_var = ctk.StringVar(value=self.cfg.get("email_smtp", {}).get("sender", ""))
        self.smtp_password_var = ctk.StringVar(value=self.cfg.get("email_smtp", {}).get("password", ""))
        self.company_name_var = ctk.StringVar(value=self.cfg.get("company", {}).get("name", ""))
        self.company_cnpj_var = ctk.StringVar(value=self.cfg.get("company", {}).get("cnpj", ""))
        self.company_logo_path = self.cfg.get("company", {}).get("logo_path", "")

        self._build_ui()

    def _build_ui(self):
        header = ctk.CTkLabel(self, text="⚙ Configure+ — Configurações", font=("Segoe UI", 16, "bold"))
        header.pack(pady=(8,6))

        main = ctk.CTkFrame(self)
        main.pack(expand=True, fill="both", padx=8, pady=8)
        main.grid_columnconfigure(0, weight=0)
        main.grid_columnconfigure(1, weight=1)
        main.grid_rowconfigure(0, weight=1)

        # left nav
        left = ctk.CTkFrame(main, width=220)
        left.grid(row=0, column=0, sticky="ns", padx=(0,10), pady=6)
        sections = [
            ("🏢 Empresa", "company"),
            ("✨ Aparência & Idioma", "language"),
            ("👥 Usuários", "users"),
            ("✉️ Integrações (SMTP)", "integrations"),
            ("🔒 Licença", "license"),
            ("🧹 Cache / Backup", "cache"),
            ("📘 Guia (GuiaBot)", "chat"),
        ]
        self.nav_buttons = {}
        self.current_section = "company"
        for i, (txt, key) in enumerate(sections):
            def _make(k=key):
                self.current_section = k
                self._render_right(k)
            btn = ctk.CTkButton(left, text=txt, width=200, anchor="w", command=_make, fg_color="#2f8bdb")
            btn.pack(pady=6, padx=8)
            self.nav_buttons[key] = btn

        # right area
        self.right = ctk.CTkFrame(main)
        self.right.grid(row=0, column=1, sticky="nsew", padx=(8,0), pady=6)
        self._render_right(self.current_section)

    def _render_right(self, key):
        # limpa
        for w in self.right.winfo_children(): w.destroy()
        # nav highlight
        for k, b in self.nav_buttons.items():
            b.configure(fg_color="#2f8bdb" if k==key else "transparent")
        # dispatch
        getattr(self, f"_panel_{key}", self._panel_default)(self.right)

    # ---------- panels ----------
    def _panel_default(self, master):
        ctk.CTkLabel(master, text="Selecione uma seção à esquerda.", font=("Segoe UI", 14)).pack(pady=20)

    def _panel_company(self, master):
        ctk.CTkLabel(master, text="🏢 Dados da Empresa", font=("Segoe UI", 14, "bold")).pack(pady=(8,6), anchor="w", padx=12)
        frm = ctk.CTkFrame(master); frm.pack(fill="x", padx=12, pady=6)
        ctk.CTkLabel(frm, text="Nome:").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        ctk.CTkEntry(frm, textvariable=self.company_name_var).grid(row=0, column=1, sticky="ew", padx=6, pady=6)
        ctk.CTkLabel(frm, text="CNPJ:").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        ctk.CTkEntry(frm, textvariable=self.company_cnpj_var).grid(row=1, column=1, sticky="ew", padx=6, pady=6)
        frm.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(master, text="Logotipo (somente via Explorador):", anchor="w").pack(padx=12, pady=(10,0), anchor="w")
        btn = ctk.CTkButton(master, text="📁 Selecionar Logo", command=self._choose_logo)
        btn.pack(padx=12, pady=8, anchor="w")

        if self.company_logo_path:
            ctk.CTkLabel(master, text=f"Logo atual: {self.company_logo_path}", text_color="gray").pack(padx=12, pady=(0,8), anchor="w")

        ctk.CTkButton(master, text="💾 Salvar Dados da Empresa", command=self._save_company).pack(padx=12, pady=(8,12), anchor="w")

    def _choose_logo(self):
        p = filedialog.askopenfilename(filetypes=[("Imagem", "*.png;*.jpg;*.jpeg")])
        if not p:
            return
        self.company_logo_path = p
        messagebox.showinfo("Logo", f"Logo selecionado:\n{p}")
        self._render_right(self.current_section)

    def _save_company(self):
        self.cfg.setdefault("company", {})
        self.cfg["company"]["name"] = self.company_name_var.get().strip()
        self.cfg["company"]["cnpj"] = self.company_cnpj_var.get().strip()
        self.cfg["company"]["logo_path"] = self.company_logo_path
        if save_config(self.cfg):
            messagebox.showinfo("Sucesso", "Dados da empresa salvos.")
        else:
            messagebox.showerror("Erro", "Falha ao salvar.")

    def _panel_language(self, master):
        ctk.CTkLabel(master, text="✨ Aparência & Idioma", font=("Segoe UI", 14, "bold")).pack(pady=(8,6), anchor="w", padx=12)
        # Tema
        frm = ctk.CTkFrame(master); frm.pack(fill="x", padx=12, pady=6)
        ctk.CTkLabel(frm, text="Tema:").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        theme_menu = ctk.CTkOptionMenu(frm, values=["Dark", "Light", "System"], variable=self.theme_var, command=self._change_theme)
        theme_menu.grid(row=0, column=1, padx=6, pady=6, sticky="w")

        # Idioma (bandeiras emoji)
        ctk.CTkLabel(master, text="Idioma:", anchor="w").pack(padx=12, pady=(8,2), anchor="w")
        lang_frame = ctk.CTkFrame(master); lang_frame.pack(fill="x", padx=12, pady=6)
        col = 0
        for lang, flag in MOCK_FLAGS.items():
            rb = ctk.CTkRadioButton(lang_frame, text=f"{flag} {lang}", variable=self.lang_var, value=lang, command=lambda l=lang: self._change_language(l))
            rb.grid(row=0, column=col, padx=8, pady=6)
            col += 1

        ctk.CTkLabel(master, text="Obs: o idioma altera textos padrão do sistema (simulação).", text_color="gray").pack(padx=12, pady=(6,12), anchor="w")

    def _change_theme(self, theme):
        # grava e aplica (aplica apenas no painel; o app principal pode ler o config.json)
        self.cfg["theme"] = theme.lower()
        save_config(self.cfg)
        messagebox.showinfo("Tema", f"Tema salvo como: {theme}")

    def _change_language(self, lang):
        self.cfg["language"] = lang
        save_config(self.cfg)
        messagebox.showinfo("Idioma", f"Idioma salvo: {lang}")
        self._render_interactive_language_panel()

    def _panel_users(self, master):
        ctk.CTkLabel(master, text="👥 Usuários (lista simples)", font=("Segoe UI", 14, "bold")).pack(pady=(8,6), anchor="w", padx=12)
        # lista em texto (simples)
        users = self.cfg.get("users", {"admin": "1234"})
        txt = "\n".join([f"{u}" for u in users.keys()])
        tb = ctk.CTkTextbox(master, height=160); tb.pack(fill="x", padx=12, pady=6)
        tb.insert("0.0", txt); tb.configure(state="disabled")
        ctk.CTkLabel(master, text="Gerenciamento avançado: console ADM (fora deste painel).", text_color="gray").pack(padx=12, pady=(6,10), anchor="w")

    def _panel_integrations(self, master):
        ctk.CTkLabel(master, text="✉️ Integrações (SMTP)", font=("Segoe UI", 14, "bold")).pack(padx=12, pady=(8,6), anchor="w")
        frm = ctk.CTkFrame(master); frm.pack(fill="x", padx=12, pady=6)
        ctk.CTkLabel(frm, text="Remetente (SMTP):").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        ctk.CTkEntry(frm, textvariable=self.smtp_sender_var).grid(row=0, column=1, padx=6, pady=6, sticky="ew")
        ctk.CTkLabel(frm, text="Senha/Token:").grid(row=1, column=0, padx=6, pady=6, sticky="w")
        ctk.CTkEntry(frm, textvariable=self.smtp_password_var, show="*").grid(row=1, column=1, padx=6, pady=6, sticky="ew")
        frm.grid_columnconfigure(1, weight=1)
        btns = ctk.CTkFrame(master); btns.pack(fill="x", padx=12, pady=8)
        ctk.CTkButton(btns, text="✅ Testar Conexão (sim)", command=self._test_smtp).pack(side="right", padx=6)
        ctk.CTkButton(btns, text="💾 Salvar", command=self._save_smtp).pack(side="right", padx=6)

    def _test_smtp(self):
        s = self.smtp_sender_var.get()
        if "@" in s:
            messagebox.showinfo("SMTP", "Simulação: conexão SMTP OK.")
        else:
            messagebox.showerror("SMTP", "Remetente inválido.")

    def _save_smtp(self):
        self.cfg.setdefault("email_smtp", {})
        self.cfg["email_smtp"]["sender"] = self.smtp_sender_var.get().strip()
        self.cfg["email_smtp"]["password"] = self.smtp_password_var.get().strip()
        save_config(self.cfg)
        messagebox.showinfo("SMTP", "Credenciais salvas no config.json (backup disponível).")

    def _panel_license(self, master):
        ctk.CTkLabel(master, text="🔒 Licença", font=("Segoe UI", 14, "bold")).pack(pady=(8,6), anchor="w", padx=12)
        lic = self.cfg.get("license", {"type": "trial", "until": "2026-12-31"})
        t = lic.get("type", "trial")
        until = lic.get("until", "")
        ctk.CTkLabel(master, text=f"Status: {t.upper()} — Até: {until}", text_color="#10B981" if t=="permanent" else "#F59E0B").pack(padx=12, pady=6, anchor="w")
        btns = ctk.CTkFrame(master); btns.pack(padx=12, pady=8, anchor="w")
        ctk.CTkButton(btns, text="📅 Definir Data Expiração", command=self._definir_licenca_data).pack(side="left", padx=6)
        ctk.CTkButton(btns, text="♾️ Tornar Permanente (Chave)", command=self._tornar_permanente).pack(side="left", padx=6)

    def _definir_licenca_data(self):
        new = simpledialog.askstring("Data Expiração", "Informe nova data (YYYY-MM-DD):", parent=self)
        if not new: return
        self.cfg["license"] = {"type": "trial", "until": new}
        save_config(self.cfg)
        messagebox.showinfo("Licença", f"Licença atualizada até {new}")
        self._render_right(self.current_section)

    def _tornar_permanente(self):
        key = simpledialog.askstring("Chave Permanente", "Insira a chave de ativação:", parent=self)
        if not key:
            return
        if key.strip() == ADMIN_LICENSE_KEY:
            self.cfg["license"] = {"type": "permanent", "until": "Não Expira"}
            save_config(self.cfg)
            messagebox.showinfo("Licença", "Licença definida como PERMANENTE.")
            self._render_right(self.current_section)
        else:
            messagebox.showerror("Chave Inválida", "Chave fornecida inválida.")

    def _panel_cache(self, master):
        ctk.CTkLabel(master, text="🧹 Cache e Backup", font=("Segoe UI", 14, "bold")).pack(pady=(8,6), anchor="w", padx=12)
        ctk.CTkLabel(master, text=f"Local do config.json: {CONFIG_PATH}", text_color="gray").pack(padx=12, pady=6, anchor="w")
        ctk.CTkButton(master, text="🧹 Limpar Backups (dados_sistema/backups)", command=self._limpar_backups, fg_color="#DC2626").pack(padx=12, pady=6, anchor="w")
        ctk.CTkButton(master, text="💾 Criar Backup do config.json", command=self._criar_backup).pack(padx=12, pady=6, anchor="w")

    def _limpar_backups(self):
        removed = 0
        for f in BACKUPS.glob("*"):
            try:
                if f.is_file():
                    f.unlink()
                    removed += 1
            except Exception:
                pass
        messagebox.showinfo("Limpeza", f"Removidos {removed} arquivos de backup.")

    def _criar_backup(self):
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = BACKUPS / f"config_backup_{stamp}.json"
        try:
            shutil.copyfile(CONFIG_PATH, dst)
            messagebox.showinfo("Backup", f"Backup criado: {dst.name}")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao criar backup: {e}")

    def _panel_chat(self, master):
        ctk.CTkLabel(master, text="📘 GuiaBot — Assistente Rápido", font=("Segoe UI", 14, "bold")).pack(pady=(8,6), anchor="w", padx=12)
        chat_frame = ctk.CTkFrame(master)
        chat_frame.pack(expand=True, fill="both", padx=12, pady=8)
        self.chat_box = ctk.CTkTextbox(chat_frame, state="disabled")
        self.chat_box.pack(fill="both", expand=True, padx=6, pady=6)
        input_frame = ctk.CTkFrame(master, fg_color="transparent")
        input_frame.pack(fill="x", padx=12, pady=(0,12))
        self.chat_entry = ctk.CTkEntry(input_frame, placeholder_text="Pergunte algo sobre o sistema...")
        self.chat_entry.pack(side="left", fill="x", expand=True, padx=(0,8))
        ctk.CTkButton(input_frame, text="Perguntar", width=120, command=self._chat_send).pack(side="right")

        self._chat_insert("🤖 GuiaBot:", "Olá — digite uma pergunta ou escolha uma seção à esquerda.")

    # -------- simple chat ----------
    def _chat_send(self):
        q = self.chat_entry.get().strip()
        if not q:
            return
        self.chat_entry.delete(0, "end")
        self._chat_insert("👤 Você:", q)
        resp = self._chat_answer(q)
        self.after(300, lambda: self._chat_insert("🤖 GuiaBot:", resp))

    def _chat_insert(self, who, txt):
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", f"{who} {txt}\n\n")
        self.chat_box.configure(state="disabled")
        self.chat_box.see("end")

    def _chat_answer(self, q):
        ql = q.lower()
        if "usuário" in ql or "cadastrar" in ql:
            return "Use a aba '👥 Usuários' para ver a lista. Para criar/editar usuários use o Console ADM."
        if "smtp" in ql or "email" in ql:
            return "Defina remetente e token em '✉️ Integrações (SMTP)' e teste a conexão."
        if "licença" in ql:
            return "Em '🔒 Licença' você pode definir expiração ou inserir chave para permanente."
        if "backup" in ql or "cache" in ql:
            return "Use '🧹 Cache / Backup' para criar backup do config.json ou limpar backups."
        return "Desculpe, não tenho uma instrução específica. Tente outra pergunta."

    # ---------- helper renders ----------
    def _render_interactive_language_panel(self):
        # atualiza painel lateral em caso de necessidade (não obrigatório)
        pass
