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