"""Página Legal — Termos de Uso e Política de Privacidade (LGPD).

Página pública (não exige login): deixa transparente que este é um projeto de
pessoa física (sem CNPJ e sem emissão de nota fiscal), o que a ferramenta
coleta e como o titular pode exercer os direitos da LGPD (contato por
WhatsApp/e-mail — sem exclusão automática de dados por aqui).
"""
import os
from urllib.parse import quote

import streamlit as st

_ROTULO_TERMOS = "⚖️ Termos de Uso"
_ROTULO_PRIV = "🛡️ Privacidade · LGPD"


def _aba_da_url() -> str:
    # Preferência: escolha feita no rodapé (button → st.switch_page guarda em
    # session_state). Depois, o link direto `?aba=...`. Por fim, "termos".
    try:
        escolha = st.session_state.get("_aba_legal")
    except Exception:
        escolha = None
    if escolha in ("termos", "privacidade"):
        return escolha
    try:
        aba = st.query_params.get("aba", "termos")
        if isinstance(aba, list):
            aba = aba[0] if aba else "termos"
    except Exception:
        aba = "termos"
    return "privacidade" if str(aba).strip().lower() == "privacidade" else "termos"


def _contato_whatsapp(mensagem: str) -> str:
    num = os.environ.get("WHATSAPP_NUMERO", "").strip().removeprefix("+")
    if not num:
        return ""
    return f"https://wa.me/{num}?text={quote(mensagem)}"


def _contatos() -> str:
    """Bloco de contato para exercer direitos LGPD / tirar dúvidas legais."""
    mensagem = (
        "Olá! Vim pelo AI Bug Triage System. Preciso exercer meus direitos "
        "de dados pessoais (LGPD): "
    )
    wa = _contato_whatsapp(mensagem)
    blocos = []
    if wa:
        blocos.append(
            f'<a href="{wa}" target="_blank" rel="noopener" '
            'style="text-decoration:none">'
            '<span style="display:inline-flex;align-items:center;background:#25D366;'
            'color:#ffffff;padding:9px 16px;border-radius:10px;font-weight:700;'
            'font-size:13px;box-shadow:0 4px 12px rgba(37,211,102,.35)">💬 Falar no WhatsApp</span></a>'
        )
    email = os.environ.get("ADMIN_EMAIL", "").strip()
    if email:
        blocos.append(
            f'<a href="mailto:{email}" style="text-decoration:none">'
            f'<span style="display:inline-flex;align-items:center;background:#2E7CF6;'
            'color:#ffffff;padding:9px 16px;border-radius:10px;font-weight:700;'
            f'font-size:13px;box-shadow:0 4px 12px rgba(46,124,246,.35)">📧 {email}</span></a>'
        )
    se = "\n".join(blocos)
    return f'<div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:6px">{se}</div>' if se else ""


def render():
    import ui_comum  # lazy: ui_comum importa roteador, que importa secoes.legal (ciclo)

    aba = _aba_da_url()

    st.markdown("""
    <div style="height:3px;width:100%;background:linear-gradient(90deg,transparent,#25D366,#2E7CF6,#7c3aed,transparent);border-radius:999px;margin:8px 0"></div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="marca-mastro" style="width:100%;background:linear-gradient(135deg,#0f172a 0%,#16233c 52%,#25D366 175%);border-radius:16px;padding:28px 32px 24px 32px;margin:4px 0 18px;box-shadow:0 8px 22px rgba(15,23,42,.18)">
      <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap">
        <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
          <span style="background:rgba(255,255,255,.12);color:#e2e8f0;border:1px solid rgba(255,255,255,.22);border-radius:999px;padding:4px 14px;font-size:12px;font-weight:800;letter-spacing:.03em">⚖️ LEGAL</span>
          <span style="color:#94a3b8;font-size:12px;font-weight:700;letter-spacing:.05em">TERMOS DE USO · PRIVACIDADE (LGPD)</span>
        </div>
        <span style="color:#64748b;font-size:12px;font-weight:600">{ui_comum.VERSAO}</span>
      </div>
      <div style="color:#ffffff;font-size:24px;font-weight:800;margin-top:14px;letter-spacing:-.01em">Transparência sobre este projeto</div>
      <div style="color:#cbd5e1;font-size:15px;line-height:1.6;margin-top:8px;max-width:94%">
        O <b style="color:#25D366">AI Bug Triage System</b> é um projeto independente, mantido por <b style="color:#ffffff">pessoa física</b> — não há empresa (CNPJ), nem emissão de nota fiscal (NFS-e). Estas páginas explicam em termos simples o que você pode esperar do serviço e como seus dados são tratados.
      </div>
    </div>
    """, unsafe_allow_html=True)

    tab_termos, tab_priv = st.tabs(
        [_ROTULO_TERMOS, _ROTULO_PRIV],
        default=_ROTULO_PRIV if aba == "privacidade" else _ROTULO_TERMOS,
        key=f"legal_abas_{st.session_state.get('_legal_nonce', 0)}",
    )

    with tab_termos:
        _termos()

    with tab_priv:
        _privacidade()


def _card(titulo: str, corpo: str) -> None:
    st.markdown(
        f"<div style='background:#ffffff;color:#0f172a;border:1px solid #e2e8f0;"
        f"border-radius:14px;padding:16px 18px;margin:0 0 14px;box-shadow:0 2px 8px rgba(15,23,42,.06)'>"
        f"<div style='font-weight:800;font-size:15px;color:#0f172a;margin-bottom:6px'>{titulo}</div>"
        f"<div style='font-size:14px;line-height:1.6;color:#334155'>{corpo}</div></div>",
        unsafe_allow_html=True,
    )


def _termos() -> None:
    st.markdown("### 📜 Termos de Uso")
    _card("1. O serviço", "O <b>AI Bug Triage System</b> é uma ferramenta de triagem de bugs: você cola um relato (ou a saída de um teste Playwright/Postman) e ele classifica a severidade, prioriza e monta um relatório. Os resultados com IA (Gemini/Groq) são gerados por modelos de linguagem e <b>podem conter erros</b> — não substituem a análise final de um profissional de QA.")
    _card("2. Contas e login", "Você cria uma conta com <b>e-mail e senha</b> (Supabase Auth). É de sua responsabilidade manter suas credenciais seguras. Cada conta tem o seu próprio plano e histórico.")
    _card("3. Planos (Basic e Premium)", "O plano <b>Basic</b> é gratuito. O <b>Premium</b> custa <b>R$ 19,99/mês</b>, pago via Pix (PagBank). <b>Este projeto é de pessoa física: não há CNPJ e não é emitida nota fiscal (NFS-e).</b> Pedidos de estorno são analisados caso a caso pelo responsável.")
    _card("4. Uso aceitável", "Você não deve usar a ferramenta para qualquer fim ilegal ou para enviar dados que você não tenha autorização para processar. A ferramenta <b>mascara automaticamente</b> credenciais e dados pessoais (e-mail, CPF, token, senha) antes de qualquer envio a IA/Jira/GitHub/histórico.")
    _card("5. Limitação de responsabilidade", "O serviço é fornecido <b>no estado em que se encontra</b> ('as is'). O responsável não se responsabiliza por decisões tomadas com base nos relatórios gerados, indisponibilidades temporárias ou perdas indiretas.")
    _card("6. Alterações", "Estes termos podem ser atualizados a qualquer momento. O uso continuado do serviço após uma alteração significa aceitação dos novos termos.")
    _card("7. Contato e lei aplicável", "Dúvidas sobre o serviço podem ser tiradas no WhatsApp/suporte. Este produto é operado a partir do Brasil e submete-se à legislação brasileira.")


def _privacidade() -> None:
    st.markdown("### 🛡️ Política de Privacidade (LGPD — Lei 13.709/2018)")
    _card("Quem é o responsável (controlador)", "Este projeto é mantido por <b>Iago Nunes de Araújo</b>, <b>pessoa física</b>, <b>sem CNPJ</b>. Não há emissão de nota fiscal e não há quadro societário: o tratamento de dados aqui descrito é conduzido diretamente pelo responsável.")
    _card("Quais dados coletamos", "<b>· E-mail</b> — criação da conta e login.<br/><b>· CPF e nome</b> — <b>apenas</b> quando você assina o Premium, para gerar o Pix de cobrança no PagBank.<br/><b>· Conteúdo que você cola para triar</b> — o relato do bug, que <b>pode conter dados pessoais</b>, e fica guardado no seu histórico para o funcionamento (RAG e alertas).<br/><b>· Uso do site</b> — dados básicos de acesso tratados pela plataforma de hospedagem.")
    _card("Para que usamos", "Criar e manter sua conta, processar sua assinatura (Pix), executar a triagem (inclusive com IA) e gerar os alertas/histórico que você pediu. <b>Não vendemos seus dados e não usamos seus relatos para treinar modelos.</b>")
    _card("O que já fazemos para proteger", "Os <b>guardrails do sistema mascaram automaticamente</b> e-mail, CPF, token, senha e outros dados sensíveis <b>antes</b> de qualquer envio para IA, Jira, GitHub ou histórico — evitando vazamento acidental de credenciais e PII.")
    _card("Com quem compartilhamos", "Apenas com a <b>infraestrutura necessária para operar</b>: Streamlit Cloud (hospedagem do app), Supabase (autenticação e dados), Render (webhook de confirmação de pagamento) e PagBank (cobrança do Pix). Nenhum desses serviços usa seus dados para publicidade.")
    _card("Por quanto tempo guardamos", "Mantemos seus dados <b>enquanto sua conta estiver ativa</b> (necessário para login, histórico e assinatura). Ao pedir a exclusão, apagamos o que for possível tecnicamente e em tempo razoável.")
    _card("Seus direitos (art. 18 da LGPD)", "Você pode, a qualquer momento, pedir <b>acesso, correção, portabilidade e eliminação</b> dos seus dados pessoais. Para isso, basta entrar em contato pelo canal abaixo informando o que deseja.")
    _contatos_html = _contatos()
    if _contatos_html:
        st.markdown(
            f'<div style="background:#ffffff;color:#0f172a;border:1px solid #e2e8f0;'
            f'border-radius:14px;padding:16px 18px;margin:0 0 14px;box-shadow:0 2px 8px rgba(15,23,42,.06)">'
            f'<div style="font-weight:800;font-size:15px;margin-bottom:6px">✉️ Para exercer seus direitos</div>'
            f'<div style="font-size:14px;line-height:1.6;color:#334155">Envie uma mensagem dizendo que deseja '
            f'exercer seus direitos LGPD (ex.: “quero apagar meus dados”). O atendimento é feito por '
            f'uma pessoa, então respondemos normalmente em até 2 dias úteis.</div>{_contatos_html}</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        "Referência legal: [ANPD — Autoridade Nacional de Proteção de Dados](https://www.gov.br/anpd/pt-br) "
        "(abre em nova guia)."
    )