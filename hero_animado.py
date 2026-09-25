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
.hero-wrap {
  display: flex;
  justify-content: center;
}
.hero-card {
  max-width: 100%;
  width: 100%;
  border: 1px solid rgba(46,124,246,.4);
  border-radius: 18px;
  padding: 24px 18px 16px;
  background: linear-gradient(135deg, rgba(46,124,246,.09), rgba(139,92,246,.12));
  text-align: center;
  animation: float_item 4s ease-in-out infinite;
  box-shadow: 0 8px 30px rgba(46,124,246,.2);
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

MARQUEE_TEXT = "QA • IA • NLP • RAG • Streamlit • Python • Linux • "

def _css():
    st.markdown(CSS, unsafe_allow_html=True)

def linha():
    _css()
    st.markdown('<div class="hero-line"></div>', unsafe_allow_html=True)

def render():
    _css()
    pill_rag = (
        '<span class="hero-pill" style="background:rgba(139,92,246,.16);color:#7c3aed">'
        '📚 RAG</span>'
    )
    st.markdown("""
<div class="hero-wrap">
<div class="hero-card">
  <div style="font-size:34px">🤖⚡</div>
  <div class="hero-grad" style="font-size:23px">QA Automation + IA</div>
  <div style="margin-top:13px"><span class="hero-dot"></span>&nbsp;<b>Disponível para vagas</b></div>
  <div class="hero-sub" style="font-size:14px;color:#444;margin-top:4px">Remote Global · São Luís, MA</div>
  <div style="margin-top:14px">
    <span class="hero-pill" style="background:rgba(37,211,102,.16);color:#1e8f4b">💡 NLP PT</span>
    {pill_rag}
    <span class="hero-pill" style="background:rgba(46,124,246,.16);color:#1d63d8">👑 Streamlit</span>
  </div>
  <div class="hero-marquee"><span>{MARQUEE_TEXT}</span></div>
  <div style="margin-top:12px;font-weight:700">⚡ Vamos construir?</div>
</div>
</div>
""".format(MARQUEE_TEXT=MARQUEE_TEXT, pill_rag=pill_rag), unsafe_allow_html=True)

# --- BOTÕES DE CONTATO (ícones oficiais embutidos) ---
# auto-gerado
_B64 = {
    "whatsapp": "PHN2ZyByb2xlPSJpbWciIHZpZXdCb3g9IjAgMCAyNCAyNCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBmaWxsPSIjZmZmZmZmIiBkPSJNMTcuNDcyIDE0LjM4MmMtLjI5Ny0uMTQ5LTEuNzU4LS44NjctMi4wMy0uOTY3LS4yNzMtLjA5OS0uNDcxLS4xNDgtLjY3LjE1LS4xOTcuMjk3LS43NjcuOTY2LS45NCAxLjE2NC0uMTczLjE5OS0uMzQ3LjIyMy0uNjQ0LjA3NS0uMjk3LS4xNS0xLjI1NS0uNDYzLTIuMzktMS40NzUtLjg4My0uNzg4LTEuNDgtMS43NjEtMS42NTMtMi4wNTktLjE3My0uMjk3LS4wMTgtLjQ1OC4xMy0uNjA2LjEzNC0uMTMzLjI5OC0uMzQ3LjQ0Ni0uNTIuMTQ5LS4xNzQuMTk4LS4yOTguMjk4LS40OTcuMDk5LS4xOTguMDUtLjM3MS0uMDI1LS41Mi0uMDc1LS4xNDktLjY2OS0xLjYxMi0uOTE2LTIuMjA3LS4yNDItLjU3OS0uNDg3LS41LS42NjktLjUxLS4xNzMtLjAwOC0uMzcxLS4wMS0uNTctLjAxLS4xOTggMC0uNTIuMDc0LS43OTIuMzcyLS4yNzIuMjk3LTEuMDQgMS4wMTYtMS4wNCAyLjQ3OSAwIDEuNDYyIDEuMDY1IDIuODc1IDEuMjEzIDMuMDc0LjE0OS4xOTggMi4wOTYgMy4yIDUuMDc3IDQuNDg3LjcwOS4zMDYgMS4yNjIuNDg5IDEuNjk0LjYyNS43MTIuMjI3IDEuMzYuMTk1IDEuODcxLjExOC41NzEtLjA4NSAxLjc1OC0uNzE5IDIuMDA2LTEuNDEzLjI0OC0uNjk0LjI0OC0xLjI4OS4xNzMtMS40MTMtLjA3NC0uMTI0LS4yNzItLjE5OC0uNTctLjM0N20tNS40MjEgNy40MDNoLS4wMDRhOS44NyA5Ljg3IDAgMDEtNS4wMzEtMS4zNzhsLS4zNjEtLjIxNC0zLjc0MS45ODIuOTk4LTMuNjQ4LS4yMzUtLjM3NGE5Ljg2IDkuODYgMCAwMS0xLjUxLTUuMjZjLjAwMS01LjQ1IDQuNDM2LTkuODg0IDkuODg4LTkuODg0IDIuNjQgMCA1LjEyMiAxLjAzIDYuOTg4IDIuODk4YTkuODI1IDkuODI1IDAgMDEyLjg5MyA2Ljk5NGMtLjAwMyA1LjQ1LTQuNDM3IDkuODg0LTkuODg1IDkuODg0bTguNDEzLTE4LjI5N0ExMS44MTUgMTEuODE1IDAgMDAxMi4wNSAwQzUuNDk1IDAgLjE2IDUuMzM1LjE1NyAxMS44OTJjMCAyLjA5Ni41NDcgNC4xNDIgMS41ODggNS45NDVMLjA1NyAyNGw2LjMwNS0xLjY1NGExMS44ODIgMTEuODgyIDAgMDA1LjY4MyAxLjQ0OGguMDA1YzYuNTU0IDAgMTEuODktNS4zMzUgMTEuODkzLTExLjg5M2ExMS44MjEgMTEuODIxIDAgMDAtMy40OC04LjQxM1oiLz48L3N2Zz4=",
    "linkedin": "PHN2ZyByb2xlPSJpbWciIHZpZXdCb3g9IjAgMCAyNCAyNCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBmaWxsPSIjZmZmZmZmIiBkPSJNMjAuNDQ3IDIwLjQ1MmgtMy41NTR2LTUuNTY5YzAtMS4zMjgtLjAyNy0zLjAzNy0xLjg1Mi0zLjAzNy0xLjg1MyAwLTIuMTM2IDEuNDQ1LTIuMTM2IDIuOTM5djUuNjY3SDkuMzUxVjloMy40MTR2MS41NjFoLjA0NmMuNDc3LS45IDEuNjM3LTEuODUgMy4zNy0xLjg1IDMuNjAxIDAgNC4yNjcgMi4zNyA0LjI2NyA1LjQ1NXY2LjI4NnpNNS4zMzcgNy40MzNjLTEuMTQ0IDAtMi4wNjMtLjkyNi0yLjA2My0yLjA2NSAwLTEuMTM4LjkyLTIuMDYzIDIuMDYzLTIuMDYzIDEuMTQgMCAyLjA2NC45MjUgMi4wNjQgMi4wNjMgMCAxLjEzOS0uOTI1IDIuMDY1LTIuMDY0IDIuMDY1em0xLjc4MiAxMy4wMTlIMy41NTVWOWgzLjU2NHYxMS40NTJ6TTIyLjIyNSAwSDEuNzcxQy43OTIgMCAwIC43NzQgMCAxLjcyOXYyMC41NDJDMCAyMy4yMjcuNzkyIDI0IDEuNzcxIDI0aDIwLjQ1MUMyMy4yIDI0IDI0IDIzLjIyNyAyNCAyMi4yNzFWMS43MjlDMjQgLjc3NCAyMy4yIDAgMjIuMjIyIDBoLjAwM3oiLz48L3N2Zz4=",
    "gmail": "PHN2ZyByb2xlPSJpbWciIHZpZXdCb3g9IjAgMCAyNCAyNCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBmaWxsPSIjZmZmZmZmIiBkPSJNMjQgNS40NTd2MTMuOTA5YzAgLjkwNC0uNzMyIDEuNjM2LTEuNjM2IDEuNjM2aC0zLjgxOVYxMS43M0wxMiAxNi42NGwtNi41NDUtNC45MXY5LjI3M0gxLjYzNkExLjYzNiAxLjYzNiAwIDAgMSAwIDE5LjM2NlY1LjQ1N2MwLTIuMDIzIDIuMzA5LTMuMTc4IDMuOTI3LTEuOTY0TDUuNDU1IDQuNjQgMTIgOS41NDhsNi41NDUtNC45MSAxLjUyOC0xLjE0NUMyMS42OSAyLjI4IDI0IDMuNDM0IDI0IDUuNDU3eiIvPjwvc3ZnPg==",
    "postman": "PHN2ZyByb2xlPSJpbWciIHZpZXdCb3g9IjAgMCAyNCAyNCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBmaWxsPSIjRkY2QzM3IiBkPSJNMTMuNTI3LjA5OUM2Ljk1NS0uNzQ0Ljk0MiAzLjkuMDk5IDEwLjQ3M2MtLjg0MyA2LjU3MiAzLjggMTIuNTg0IDEwLjM3MyAxMy40MjggNi41NzMuODQzIDEyLjU4Ny0zLjgwMSAxMy40MjgtMTAuMzc0QzI0Ljc0NCA2Ljk1NSAyMC4xMDEuOTQzIDEzLjUyNy4wOTl6bTIuNDcxIDcuNDg1YS44NTUuODU1IDAgMCAwLS41OTMuMjVsLTQuNDUzIDQuNDUzLS4zMDctLjMwNy0uNjQzLS42NDNjNC4zODktNC4zNzYgNS4xOC00LjQxOCA1Ljk5Ni0zLjc1M3ptLTQuODYzIDQuODYxbDQuNDQtNC40NGEuNjIuNjIgMCAxIDEgLjg0Ny45MDNsLTQuNjk5IDQuMTI1LS41ODgtLjU4OHptLjMzLjY5NGwtMS4xLjIzOGEuMDYuMDYgMCAwIDEtLjA2Ny0uMDMyLjA2LjA2IDAgMCAxIC4wMS0uMDczbC42NDUtLjY0NS41MTIuNTEyem0tMi44MDMtLjQ1OWwxLjE3Mi0xLjE3Mi44NzkuODc4LTEuOTc5LjQyNmEuMDc0LjA3NCAwIDAgMS0uMDg1LS4wMzkuMDcyLjA3MiAwIDAgMSAuMDEzLS4wOTN6bS0zLjY0NiA2LjA1OGEuMDc2LjA3NiAwIDAgMS0uMDY5LS4wODMuMDc3LjA3NyAwIDAgMSAuMDIyLS4wNDZoLjAwMmwuOTQ2LS45NDYgMS4yMjIgMS4yMjItMi4xMjMtLjE0N3ptMi40MjUtMS4yNTZhLjIyOC4yMjggMCAwIDAtLjExNy4yNTZsLjIwMy44NjVhLjEyNS4xMjUgMCAwIDEtLjIxMS4xMTdoLS4wMDNsLS45MzQtLjkzNC0uMjk0LS4yOTUgMy43NjItMy43NTggMS44Mi0uMzkzLjg3NC44NzRjLTEuMjU1IDEuMTAyLTIuOTcxIDIuMjAxLTUuMSAzLjI2OHptNS4yNzktMy40MjhoLS4wMDJsLS44MzktLjgzOSA0LjY5OS00LjEyNWEuOTUyLjk1MiAwIDAgMCAuMTE5LS4xMjdjLS4xNDggMS4zNDUtMi4wMjkgMy4yNDUtMy45NzcgNS4wOTF6bTMuNjU3LTYuNDZsLS4wMDMtLjAwMmExLjgyMiAxLjgyMiAwIDAgMSAyLjQ1OS0yLjY4NGwtMS42MSAxLjYxM2EuMTE5LjExOSAwIDAgMCAwIC4xNjlsMS4yNDcgMS4yNDdhMS44MTcgMS44MTcgMCAwIDEtMi4wOTMtLjM0M3ptMi41NzggMGExLjcxNCAxLjcxNCAwIDAgMS0uMjcxLjIxOGgtLjAwMWwtMS4yMDctMS4yMDcgMS41MzMtMS41MzNjLjY2MS43Mi42MzcgMS44MzItLjA1NCAyLjUyMnpNMTguODU1IDYuMDVhLjE0My4xNDMgMCAwIDAtLjA1My4xNTcuNDE2LjQxNiAwIDAgMS0uMDUzLjQ1LjE0LjE0IDAgMCAwIC4wMjMuMTk3LjE0MS4xNDEgMCAwIDAgLjA4NC4wMy4xNC4xNCAwIDAgMCAuMTA2LS4wNS42OTEuNjkxIDAgMCAwIC4wODctLjc1MS4xMzguMTM4IDAgMCAwLS4xOTQtLjAzM3oiLz48L3N2Zz4=",
}

# --- SÍMBOLOS OFICIAIS DAS MARCAS DE IA (PD-textlogo via Wikimedia Commons) ---
# Logotipo "groq" (wordmark oficial) — viewBox real 152x55.5.
_GROQ_WORDMARK_PATHS = (
    '<path d="M84.848,34.137c-9.798,0-17.769,7.971-17.769,17.77s7.971,17.769,17.769,17.769'
    's17.77-7.971,17.77-17.769S94.645,34.137,84.848,34.137z M84.848,63.013c-6.124,0-11.106-4.983'
    '-11.106-11.106s4.982-11.106,11.106-11.106c6.124,0,11.106,4.982,11.106,11.106'
    'S90.973,63.013,84.848,63.013z"/>',
    '<path d="M60.315,34.206c-0.607-0.068-1.217-0.104-1.827-0.108c-0.304,0-0.595,0.009-0.893,0.014'
    's-0.594,0.033-0.891,0.051c-1.197,0.094-2.382,0.299-3.541,0.611c-2.329,0.629-4.574,1.723-6.515,3.277'
    'c-1.97,1.57-3.548,3.575-4.611,5.859c-0.53,1.138-0.921,2.336-1.165,3.567c-0.121,0.608-0.21,1.222'
    '-0.266,1.84c-0.02,0.307-0.055,0.615-0.059,0.921l-0.011,0.459l-0.005,0.23v0.19l0.015,5.951l0.015,5.951'
    'l0.041,5.95h6.664l0.042-5.95l0.015-5.952l0.015-5.951v-0.182l0.005-0.142l0.008-0.285c0-0.191,0.028-0.375,'
    '0.039-0.564c0.036-0.37,0.091-0.738,0.165-1.102c0.146-0.716,0.374-1.413,0.678-2.077c0.613-1.332,'
    '1.528-2.502,2.673-3.419c1.156-0.932,2.541-1.628,4.038-2.042c0.757-0.207,1.532-0.344,2.314-0.408'
    'c0.198-0.011,0.395-0.03,0.594-0.037c0.199-0.007,0.402-0.013,0.595-0.012c0.383,0,0.76,0.025,1.142,0.06'
    'c1.518,0.153,2.989,0.619,4.318,1.368l3.326-5.776C65.108,35.263,62.753,34.484,60.315,34.206z"/>',
    '<path d="M17.77,34.048C7.971,34.048,0,42.019,0,51.817s7.971,17.77,17.77,17.77h5.844v-6.664H17.77'
    'c-6.124,0-11.106-4.982-11.106-11.106s4.982-11.106,11.106-11.106s11.132,4.982,11.132,11.106l0,0v16.365l0,0'
    'c0,6.084-4.954,11.039-11.023,11.103c-2.904-0.024-5.681-1.191-7.729-3.25l-4.712,4.712c3.266,3.283,7.691,5.151,'
    '12.321,5.201v0.003c0.04,0,0.08,0,0.119,0h0.125v-0.003c9.659-0.131,17.48-8.005,17.525-17.686l0.006-16.881'
    'C35.302,41.785,27.422,34.048,17.77,34.048z"/>',
    '<path d="M124.083,34.137c-9.798,0-17.769,7.971-17.769,17.77s7.971,17.769,17.769,17.769h6.08v-6.663h-6.08'
    'c-6.124,0-11.106-4.983-11.106-11.106s4.982-11.106,11.106-11.106c5.799,0,10.572,4.468,11.062,10.143h-0.01'
    'v34.12h6.664V51.907l0,0C141.797,42.108,133.881,34.137,124.083,34.137z"/>',
    '<polygon points="151.983,35.04 151.033,35.04 149.737,37.053 148.399,35.04 147.44,35.04 147.44,38.624 '
    '148.511,38.624 148.511,36.88 149.461,38.288 149.979,38.288 150.912,36.836 150.929,38.624 152,38.624"/>',
    '<polygon points="143.519,35.896 144.685,35.896 144.685,38.624 145.86,38.624 145.86,35.896 147.034,35.896 '
    '147.034,35.04 143.519,35.04"/>',
)


def _svg_groq(tamanho: int = 18, cor: str = "#0f172a") -> str:
    largura = max(20, round(tamanho * 152 / 55.5))
    return (
        f'<svg width="{largura}" height="{tamanho}" viewBox="0 32.25 152 55.5" '
        f'role="img" aria-label="Groq" style="display:inline-block;vertical-align:-0.18em">'
        f'<g fill="{cor}">{"".join(_GROQ_WORDMARK_PATHS)}</g></svg>'
    )


def _svg_gmail(tamanho: int = 17) -> str:
    """'M' colorido oficial do Gmail (2020) em SVG inline (mesmo método do 'G' do Google)."""
    largura = round(tamanho * 88 / 66)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="52 42 88 66" '
        f'width="{largura}" height="{tamanho}" role="img" aria-label="Gmail" '
        f'style="display:inline-block;vertical-align:middle">'
        '<path fill="#4285f4" d="M58 108h14V74L52 59v43c0 3.32 2.69 6 6 6"/>'
        '<path fill="#34a853" d="M120 108h14c3.32 0 6-2.69 6-6V59l-20 15"/>'
        '<path fill="#fbbc04" d="M120 48v26l20-15v-8c0-7.42-8.47-11.65-14.4-7.2"/>'
        '<path fill="#ea4335" d="M72 74V48l24 18 24-18v26L96 92"/>'
        '<path fill="#c5221f" d="M52 51v8l20 15V48l-5.6-4.2c-5.94-4.45-14.4-.22-14.4 7.2"/>'
        '</svg>'
    )


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

def _img_postman(tamanho: int = 17) -> str:
    """Logo oficial do Postman (herói voador) via <img> base64 — o mesmo método
    dos ícones de contato (WhatsApp/LinkedIn), que sempre renderiza."""
    return (
        f'<img src="data:image/svg+xml;base64,{_B64["postman"]}" '
        f'width="{tamanho}" height="{tamanho}" alt="Postman" '
        f'style="vertical-align:middle;display:inline-block"/>'
    )


def _contato_icon(nome: str) -> str:
    if nome == "gmail":
        return (
            '<span style="display:inline-block;background:#ffffff;border-radius:4px;'
            'padding:1px 2px;vertical-align:middle;margin-right:9px;line-height:0">'
            + _svg_gmail()
            + "</span>"
        )
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
