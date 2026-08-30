import streamlit as st

CSS = """
<style>
@keyframes float_item {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-7px); }
}
@keyframes pulse_dot {
  0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(37,211,102,.7); }
  50% { opacity: .65; box-shadow: 0 0 0 9px rgba(37,211,102,0); }
}
@keyframes grad_move {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
@keyframes marquee_move {
  0% { transform: translateX(100%); }
  100% { transform: translateX(-100%); }
}
.hero-card {
  border: 1px solid rgba(46,124,246,.4);
  border-radius: 16px;
  padding: 18px 12px 14px;
  background: linear-gradient(135deg, rgba(46,124,246,.09), rgba(139,92,246,.12));
  text-align: center;
  animation: float_item 4s ease-in-out infinite;
  box-shadow: 0 6px 26px rgba(46,124,246,.18);
}
.hero-grad {
  background: linear-gradient(90deg, #2E7CF6, #F6821D, #25D366, #2E7CF6);
  background-size: 300% 100%;
  font-weight: 800;
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  animation: grad_move 6s linear infinite;
}
.hero-dot {
  display: inline-block;
  width: 10px; height: 10px; border-radius: 50%;
  background: #25D366;
  animation: pulse_dot 1.6s infinite;
}
.hero-pill {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 999px;
  margin: 3px;
  font-size: 12px;
  font-weight: 600;
  animation: float_item 5s ease-in-out infinite;
}
.hero-marquee {
  overflow: hidden;
  white-space: nowrap;
  border-radius: 12px;
  padding: 6px 0;
  background: rgba(46,124,246,.06);
  margin-top: 10px;
}
.hero-marquee span {
  display: inline-block;
  animation: marquee_move 9s linear infinite;
}
.hero-line {
  height: 4px;
  border-radius: 2px;
  margin: 4px 0 10px 0;
  background: linear-gradient(90deg, #2E7CF6, #F6821D, #25D366, #2E7CF6);
  background-size: 300% 100%;
  animation: grad_move 6s linear infinite;
}
</style>
"""

MARQUEE_TEXT = "QA • IA • NLP • Gemini • Streamlit • Python • Linux • "

def linha():
    st.markdown('<div class="hero-line"></div>', unsafe_allow_html=True)

def _css():
    st.markdown(CSS, unsafe_allow_html=True)

def linha():
    _css()
    st.markdown('<div class="hero-line"></div>', unsafe_allow_html=True)

def render():
    _css()
    st.markdown("""
<div class="hero-card">
  <div style="font-size:26px">🤖⚡</div>
  <div class="hero-grad" style="font-size:19px">QA Automation + IA</div>
  <div style="margin-top:11px"><span class="hero-dot"></span>&nbsp;<b>Disponível para vagas</b></div>
  <div style="font-size:13px;color:#444;margin-top:3px">Remote Global · São Luís, MA</div>
  <div style="margin-top:12px">
    <span class="hero-pill" style="background:rgba(37,211,102,.16);color:#1e8f4b">💡 NLP PT</span>
    <span class="hero-pill" style="background:rgba(246,130,29,.16);color:#d97706">🧠 Gemini</span>
    <span class="hero-pill" style="background:rgba(46,124,246,.16);color:#1d63d8">🚀 Streamlit</span>
  </div>
  <div class="hero-marquee"><span>{}</span></div>
  <div style="margin-top:10px;font-weight:700">⚡ Vamos construir?</div>
</div>
""".format(MARQUEE_TEXT), unsafe_allow_html=True)

# --- BOTÕES DE CONTATO (ícones oficiais embutidos) ---
# auto-gerado
_B64 = {
    "whatsapp": "PHN2ZyByb2xlPSJpbWciIHZpZXdCb3g9IjAgMCAyNCAyNCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBmaWxsPSIjZmZmZmZmIiBkPSJNMTcuNDcyIDE0LjM4MmMtLjI5Ny0uMTQ5LTEuNzU4LS44NjctMi4wMy0uOTY3LS4yNzMtLjA5OS0uNDcxLS4xNDgtLjY3LjE1LS4xOTcuMjk3LS43NjcuOTY2LS45NCAxLjE2NC0uMTczLjE5OS0uMzQ3LjIyMy0uNjQ0LjA3NS0uMjk3LS4xNS0xLjI1NS0uNDYzLTIuMzktMS40NzUtLjg4My0uNzg4LTEuNDgtMS43NjEtMS42NTMtMi4wNTktLjE3My0uMjk3LS4wMTgtLjQ1OC4xMy0uNjA2LjEzNC0uMTMzLjI5OC0uMzQ3LjQ0Ni0uNTIuMTQ5LS4xNzQuMTk4LS4yOTguMjk4LS40OTcuMDk5LS4xOTguMDUtLjM3MS0uMDI1LS41Mi0uMDc1LS4xNDktLjY2OS0xLjYxMi0uOTE2LTIuMjA3LS4yNDItLjU3OS0uNDg3LS41LS42NjktLjUxLS4xNzMtLjAwOC0uMzcxLS4wMS0uNTctLjAxLS4xOTggMC0uNTIuMDc0LS43OTIuMzcyLS4yNzIuMjk3LTEuMDQgMS4wMTYtMS4wNCAyLjQ3OSAwIDEuNDYyIDEuMDY1IDIuODc1IDEuMjEzIDMuMDc0LjE0OS4xOTggMi4wOTYgMy4yIDUuMDc3IDQuNDg3LjcwOS4zMDYgMS4yNjIuNDg5IDEuNjk0LjYyNS43MTIuMjI3IDEuMzYuMTk1IDEuODcxLjExOC41NzEtLjA4NSAxLjc1OC0uNzE5IDIuMDA2LTEuNDEzLjI0OC0uNjk0LjI0OC0xLjI4OS4xNzMtMS40MTMtLjA3NC0uMTI0LS4yNzItLjE5OC0uNTctLjM0N20tNS40MjEgNy40MDNoLS4wMDRhOS44NyA5Ljg3IDAgMDEtNS4wMzEtMS4zNzhsLS4zNjEtLjIxNC0zLjc0MS45ODIuOTk4LTMuNjQ4LS4yMzUtLjM3NGE5Ljg2IDkuODYgMCAwMS0xLjUxLTUuMjZjLjAwMS01LjQ1IDQuNDM2LTkuODg0IDkuODg4LTkuODg0IDIuNjQgMCA1LjEyMiAxLjAzIDYuOTg4IDIuODk4YTkuODI1IDkuODI1IDAgMDEyLjg5MyA2Ljk5NGMtLjAwMyA1LjQ1LTQuNDM3IDkuODg0LTkuODg1IDkuODg0bTguNDEzLTE4LjI5N0ExMS44MTUgMTEuODE1IDAgMDAxMi4wNSAwQzUuNDk1IDAgLjE2IDUuMzM1LjE1NyAxMS44OTJjMCAyLjA5Ni41NDcgNC4xNDIgMS41ODggNS45NDVMLjA1NyAyNGw2LjMwNS0xLjY1NGExMS44ODIgMTEuODgyIDAgMDA1LjY4MyAxLjQ0OGguMDA1YzYuNTU0IDAgMTEuODktNS4zMzUgMTEuODkzLTExLjg5M2ExMS44MjEgMTEuODIxIDAgMDAtMy40OC04LjQxM1oiLz48L3N2Zz4=",
    "linkedin": "PHN2ZyByb2xlPSJpbWciIHZpZXdCb3g9IjAgMCAyNCAyNCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBmaWxsPSIjZmZmZmZmIiBkPSJNMjAuNDQ3IDIwLjQ1MmgtMy41NTR2LTUuNTY5YzAtMS4zMjgtLjAyNy0zLjAzNy0xLjg1Mi0zLjAzNy0xLjg1MyAwLTIuMTM2IDEuNDQ1LTIuMTM2IDIuOTM5djUuNjY3SDkuMzUxVjloMy40MTR2MS41NjFoLjA0NmMuNDc3LS45IDEuNjM3LTEuODUgMy4zNy0xLjg1IDMuNjAxIDAgNC4yNjcgMi4zNyA0LjI2NyA1LjQ1NXY2LjI4NnpNNS4zMzcgNy40MzNjLTEuMTQ0IDAtMi4wNjMtLjkyNi0yLjA2My0yLjA2NSAwLTEuMTM4LjkyLTIuMDYzIDIuMDYzLTIuMDYzIDEuMTQgMCAyLjA2NC45MjUgMi4wNjQgMi4wNjMgMCAxLjEzOS0uOTI1IDIuMDY1LTIuMDY0IDIuMDY1em0xLjc4MiAxMy4wMTlIMy41NTVWOWgzLjU2NHYxMS40NTJ6TTIyLjIyNSAwSDEuNzcxQy43OTIgMCAwIC43NzQgMCAxLjcyOXYyMC41NDJDMCAyMy4yMjcuNzkyIDI0IDEuNzcxIDI0aDIwLjQ1MUMyMy4yIDI0IDI0IDIzLjIyNyAyNCAyMi4yNzFWMS43MjlDMjQgLjc3NCAyMy4yIDAgMjIuMjIyIDBoLjAwM3oiLz48L3N2Zz4=",
    "gmail": "PHN2ZyByb2xlPSJpbWciIHZpZXdCb3g9IjAgMCAyNCAyNCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBmaWxsPSIjZmZmZmZmIiBkPSJNMjQgNS40NTd2MTMuOTA5YzAgLjkwNC0uNzMyIDEuNjM2LTEuNjM2IDEuNjM2aC0zLjgxOVYxMS43M0wxMiAxNi42NGwtNi41NDUtNC45MXY5LjI3M0gxLjYzNkExLjYzNiAxLjYzNiAwIDAgMSAwIDE5LjM2NlY1LjQ1N2MwLTIuMDIzIDIuMzA5LTMuMTc4IDMuOTI3LTEuOTY0TDUuNDU1IDQuNjQgMTIgOS41NDhsNi41NDUtNC45MSAxLjUyOC0xLjE0NUMyMS42OSAyLjI4IDI0IDMuNDM0IDI0IDUuNDU3eiIvPjwvc3ZnPg==",
}

CONTATO_URLS = {
    "whatsapp": "https://wa.me/5598985914235?text=Ol%C3%A1%20Iago%2C%20vi%20seu%20portf%C3%B3lio%20de%20IA%20e%20QA%20e%20gostaria%20de%20conversar%20sobre%20uma%20oportunidade!",
    "linkedin": "https://www.linkedin.com/in/iago-nunes-897a5832b/?lipi=urn%3Ali%3Apage%3Ad_flagship3_profile_view_base_contact_details%3B%2F15y3S36T5SI8UZodVDXGw%3D%3D",
    "gmail": "mailto:iagonunes513@gmail.com?subject=Oportunidade%20de%20IA%20/%20QA&body=Ol%C3%A1%20Iago%2C%20vi%20seu%20app%20de%20triagem%20de%20bugs%20e%20gostaria%20de%20conversar%20sobre%20uma%20oportunidade!",
}
CONTATO_BTNS = [
    ("whatsapp", "Falar com Iago no WhatsApp", "#25D366"),
    ("linkedin", "Conectar no LinkedIn", "#0A66C2"),
    ("gmail", "Enviar E-mail", "#EA4335"),
]

CONTATO_CSS = """
<style>
.contact-btn {
  display: flex;
  align-items: center;
  color: #fff;
  border: none;
  padding: 11px 16px;
  border-radius: 8px;
  cursor: pointer;
  width: 100%;
  margin: 4px 0;
  font-weight: 600;
  font-size: 15px;
  transition: transform .15s ease, filter .15s ease;
}
.contact-btn:hover { transform: scale(1.02); filter: brightness(1.06); }
</style>
"""

def _contato_icon(nome: str) -> str:
    href = "data:image/svg+xml;base64," + _B64[nome]
    return f'<img src="{href}" width="17" height="17" style="vertical-align:middle; margin-right:9px"/>'

def render_contato():
    st.markdown(CONTATO_CSS, unsafe_allow_html=True)
    botoes = "\n".join(
        f'<a href="{CONTATO_URLS[nome]}" target="_blank">'
        f'<button class="contact-btn" style="background:{cor}">{_contato_icon(nome)}{texto}</button></a>'
        for nome, texto, cor in CONTATO_BTNS
    )
    st.markdown(f"<div>{botoes}</div>", unsafe_allow_html=True)
