# Análise por IA (LLM) — Fase 3 do projeto
# Integração com Google Gemini via google-genai.
# Desenho:
#  1. Chave: st.secrets (Streamlit Cloud) OU arquivo local .env (gitignored).
#  2. Prompt pede apenas JSON (schema fixo) com temperature baixa.
#  3. Qualquer erro -> retorna (None, mensagem): o motor local segue de pé.

import json
import os
import re

MODELO = "gemini-3.5-flash"

# Ordem de preferência: caso o primário caia com 503 (alta demanda),
# tenta os alternativos antes de desistir.
MODELOS = [
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
]

PROMPT = """Você é um assistente sênior de QA. Analise o RELATO DO USUÁRIO sobre um
bug de software e responda APENAS com JSON válido (sem markdown, sem texto extra),
usando exatamente este schema:

{
  "severidade": "critica|alta|media|baixa",
  "categoria": "funcionalidade|performance|seguranca|design|outro",
  "causa_raiz": "causa provável, em uma frase",
  "passos_repro": ["1º passo", "2º passo", "3º passo"],
  "resumo_tecnico": "resumo técnico curto do problema"
}

Se a informação for insuficiente, use categoria "outro" e severidade "media".

RELATO DO USUÁRIO:
{relato}
"""


def _carregar_env():
    """Carrega chave do arquivo .env (apenas leitura, nunca commitado)."""
    caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(caminho):
        return None
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            chave, _, valor = linha.partition("=")
            if chave.strip() == "GEMINI_API_KEY":
                return valor.strip()
    return None


def _chave():
    # 1) Streamlit Cloud: Settings -> Secrets -> GEMINI_API_KEY
    try:
        import streamlit as st

        return st.secrets.get("GEMINI_API_KEY")
    except Exception:
        pass
    # 2) Local: arquivo .env (gitignored)
    return _carregar_env()


def _extrair_json(texto):
    """Remove cercas de markdown (```json) caso o modelo desobedeça o prompt."""
    texto = texto.strip()
    cercas = re.findall(r"```(?:json)?\s*(.*?)```", texto, re.DOTALL)
    if cercas:
        texto = cercas[-1].strip()
    return json.loads(texto)


def analisar_llm(relato):
    """Chama o Gemini e retorna (dict | None, mensagem_erro).

    dict com chaves: severidade, categoria, causa_raiz, passos_repro, resumo_tecnico
    """
    chave = _chave()
    if not chave:
        return None, "Chave GEMINI_API_KEY não configurada."

    try:
        from google import genai
        from google.genai import types

        cliente = genai.Client(api_key=chave)
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
            max_output_tokens=1024,
        )
        conteudo = PROMPT.replace("{relato}", relato[:2000])
        ultimo_erro = None

        # Fallback: tenta vários modelos porque o Gemini costuma falhar
        # com 503 ("alta demanda") de vez em quando.
        import time

        for modelo in MODELOS:
            for tentativa in range(2):
                try:
                    resposta = cliente.models.generate_content(
                        model=modelo, contents=conteudo, config=config
                    )
                    return _extrair_json(resposta.text or "{}"), None
                except Exception as exc:
                    ultimo_erro = f"{modelo}: {type(exc).__name__}: {str(exc)[:90]}"
                    time.sleep(1.5)

        return None, ultimo_erro or "Falha ao chamar a API."
    except Exception as exc:  # qualquer falha de rede/API/JSON
        return None, f"{type(exc).__name__}: {str(exc)[:120]}"


if __name__ == "__main__":
    casos = [
        "O aplicativo dá crash toda vez que tento fazer login.",
        "Estou tentando pagar e o botão não responde, estou muito frustrado!",
        "A cor de fundo podia ser mais escura.",
    ]
    print("=== TESTE DE ANÁLISE POR IA (Gemini) ===\n")
    for caso in casos:
        print(f"Relato: {caso}")
        dados, erro = analisar_llm(caso)
        if erro:
            print(f"  -> erro: {erro}")
        else:
            print(f"  -> severidade: {dados['severidade']}")
            print(f"     categoria : {dados['categoria']}")
            print(f"     causa raiz: {dados['causa_raiz']}")
            print(f"     passos    : {dados['passos_repro']}")
        print()