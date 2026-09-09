# Análise por IA (LLM) — Fase 3 do projeto
# Integração com Google Gemini via google-genai, com fallback para
# modelo open-weight via Groq caso o Gemini expire tokens / caia (503/429/chave inválida).
# Desenho:
#  1. Chave: st.secrets (Streamlit Cloud) OU arquivo local .env (gitignored).
#  2. Prompt pede apenas JSON (schema fixo) com temperature baixa.
#  3. Qualquer erro -> retorna (None, mensagem): o motor local segue de pé.
#  4. Ordem: Gemini (todos os modelos) -> Groq (open-weight) -> erro.

import json
import os
import re

import requests

MODELO = "gemini-3.5-flash"

# Ordem de preferência: caso o primário caia com 503 (alta demanda),
# tenta os alternativos antes de desistir.
MODELOS = [
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
]

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
# Modelo open-weight padrão no Groq: sucessor recomendado do Llama 3.3 70B
# (Llama de chat foi aposentado do tier grátis do Groq em 2026). Tem JSON mode,
# multilíngue (inclui PT-BR) e roda grátis. Sobrescrevível via GROQ_MODELO.
GROQ_MODELO_PADRAO = "openai/gpt-oss-120b"

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

PROMPT_RAG = """Você é um assistente sênior de QA. Recebeu um RELATO ATUAL sobre um bug e a
lista de TRIAGENS ANTERIORES (histórico persistido do app). Use as anteriores para dizer
se o problema é RECORRENTE e como foi resolvido antes.

Responda APENAS com JSON válido (sem markdown, sem texto extra), usando exatamente este schema:

{
  "severidade": "critica|alta|media|baixa",
  "categoria": "funcionalidade|performance|seguranca|design|outro",
  "causa_raiz": "causa provável, em uma frase",
  "passos_repro": ["1º passo", "2º passo", "3º passo"],
  "resumo_tecnico": "resumo técnico curto",
  "ja_aconteceu": true,
  "resolucao_anterior": "como foi resolvido da última vez (resumo), ou vazio se nunca ocorreu",
  "registros_similar": ["id1", "id2"]
}

Regras:
- Se nenhuma triagem anterior for útil, responda "ja_aconteceu": false e "resolucao_anterior": "".
- Se a informação for insuficiente, use categoria "outro" e severidade "media".
- Não invente resolução: se o histórico não mostra como resolveu, deixe vazio.

TRIAGENS ANTERIORES (histórico):
{contexto}

RELATO ATUAL:
{relato}
"""


def _ler_do_env(nome):
    """Carrega uma chave do arquivo .env (apenas leitura, nunca commitado)."""
    caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(caminho):
        return None
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            chave, _, valor = linha.partition("=")
            if chave.strip() == nome:
                return valor.strip()
    return None


def _chave(nome):
    # 1) Streamlit Cloud: Settings -> Secrets -> <NOME>
    try:
        import streamlit as st

        return st.secrets.get(nome)
    except Exception:
        pass
    # 2) Local: arquivo .env (gitignored)
    return _ler_do_env(nome)


def _extrair_json(texto):
    """Remove cercas de markdown (```json) caso o modelo desobedeça o prompt."""
    texto = texto.strip()
    cercas = re.findall(r"```(?:json)?\s*(.*?)```", texto, re.DOTALL)
    if cercas:
        texto = cercas[-1].strip()
    return json.loads(texto)


# Último provedor/modelo que respondeu com sucesso (para mostrar na UI).
ULTIMO_PROVEDOR = None
ULTIMO_MODELO = None


def disponivel(modelos_custom=None) -> bool:
    """True se há pelo menos uma chave de LLM configurada (Gemini/Groq) ou um
    modelo próprio adicionado na sessão (traga sua API)."""
    if _chave("GEMINI_API_KEY") or _chave("GROQ_API_KEY"):
        return True
    return bool(modelos_custom)


def _provedor_normalizado(provedor: str | None) -> str | None:
    """Normaliza a escolha de provedor para 'gemini', 'groq' ou None (auto)."""
    if not provedor:
        return None
    p = str(provedor).strip().lower()
    if p.startswith("gem"):
        return "gemini"
    if p.startswith("groq") or p.startswith("llama"):
        return "groq"
    return None


def _chamar_gemini(conteudo, temperatura=0.2, max_output_tokens=1024, modelos=None, chave=None):
    """Chama o Gemini com fallback entre modelos. Retorna (dict | None, erro).

    modelos: lista de nomes a tentar (padrão: MODELOS). chave: API key;
    se vazia, usa a chave configurada (secrets/.env) — permite testar qualquer
    modelo Gemini que a chave do usuário acesse (ex.: tier pago).
    """
    chave = chave or _chave("GEMINI_API_KEY")
    if not chave:
        return None, "Chave GEMINI_API_KEY não configurada."
    try:
        from google import genai
        from google.genai import types

        cliente = genai.Client(api_key=chave)
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=temperatura,
            max_output_tokens=max_output_tokens,
        )
        ultimo_erro = None
        import time

        # Fallback: tenta vários modelos porque o Gemini costuma falhar
        # com 503 ("alta demanda") de vez em quando.
        for modelo in modelos or MODELOS:
            for _tentativa in range(2):
                try:
                    resposta = cliente.models.generate_content(
                        model=modelo, contents=conteudo, config=config
                    )
                    global ULTIMO_PROVEDOR, ULTIMO_MODELO
                    ULTIMO_PROVEDOR = "Gemini"
                    ULTIMO_MODELO = modelo
                    return _extrair_json(resposta.text or "{}"), None
                except Exception as exc:
                    ultimo_erro = f"{modelo}: {type(exc).__name__}: {str(exc)[:90]}"
                    time.sleep(1.5)

        return None, ultimo_erro or "Falha ao chamar a API."
    except Exception as exc:  # qualquer falha de rede/API/JSON
        return None, f"{type(exc).__name__}: {str(exc)[:120]}"


def _chamar_openai_compat(conteudo, config, temperatura=0.2, max_output_tokens=1024):
    """Chama qualquer endpoint OpenAI-compatível (/v1/chat/completions).

    config: {"base_url", "chave", "modelo", "rotulo", "tipo": "openai"}.
    Cobre OpenAI, DeepSeek, Ollama/LM Studio local e espelhos do OpenAI.
    Tenta primeiro com JSON mode; se o endpoint não suportar, refaz sem o campo.
    Retorna (dict | None, erro).
    """
    base = (config.get("base_url") or "").strip().rstrip("/")
    chave = (config.get("chave") or "").strip()
    modelo = (config.get("modelo") or "").strip()
    if not base or not chave or not modelo:
        return None, "Configuração do modelo personalizado incompleta (base_url/chave/modelo)."
    url = base if base.endswith("/chat/completions") else f"{base}/chat/completions"
    cabecalho = {"Authorization": f"Bearer {chave}", "Content-Type": "application/json"}
    ultimo_erro = "sem resposta"
    for com_json in (True, False):
        corpo = {
            "model": modelo,
            "messages": [
                {"role": "system",
                 "content": "Você responde apenas com JSON válido, sem markdown."},
                {"role": "user", "content": conteudo},
            ],
            "temperature": temperatura,
            "max_tokens": max_output_tokens,
        }
        if com_json:
            corpo["response_format"] = {"type": "json_object"}
        try:
            resposta = requests.post(url, headers=cabecalho, json=corpo, timeout=60)
            if resposta.status_code != 200:
                ultimo_erro = f"HTTP {resposta.status_code}: {str(resposta.text)[:90]}"
                continue
            payload = resposta.json()
            texto = payload["choices"][0]["message"]["content"]
            global ULTIMO_PROVEDOR, ULTIMO_MODELO
            ULTIMO_PROVEDOR = config.get("rotulo") or "Custom"
            ULTIMO_MODELO = modelo
            return _extrair_json(texto), None
        except Exception as exc:
            ultimo_erro = f"{type(exc).__name__}: {str(exc)[:120]}"
            continue
    return None, f"Custom ({modelo}): {ultimo_erro}"


def _chamar_llm(conteudo, temperatura=0.2, max_output_tokens=1024, provedor=None):
    """Dispatcher: Gemini, Groq, modelo próprio (dict) ou ambos (auto/fallback).

    provedor:
      None/"auto" -> tenta Gemini; se falhar, tenta Groq.
      "gemini"    -> só Gemini (sem fallback).
      "groq"      -> só Groq.
      dict        -> modelo próprio adicionado na UI (tipo gemini|openai).
    Retorna (dict | None, erro). Se apenas um provedor foi requisitado e não há
    chave dele, retorna erro imediatamente.
    """
    if isinstance(provedor, dict):
        cfg = provedor
        if cfg.get("tipo") == "gemini":
            chave = cfg.get("chave") or _chave("GEMINI_API_KEY")
            dados, erro = _chamar_gemini(
                conteudo, temperatura, max_output_tokens,
                modelos=[(cfg.get("modelo") or "").strip() or MODELO],
                chave=chave,
            )
            if dados is not None:
                global ULTIMO_PROVEDOR
                ULTIMO_PROVEDOR = cfg.get("rotulo") or "Gemini"
            return dados, erro
        if cfg.get("tipo") == "openai":
            return _chamar_openai_compat(conteudo, cfg, temperatura, max_output_tokens)
        return None, "Configuração de modelo próprio desconhecida."
    escolha = _provedor_normalizado(provedor)
    if escolha == "groq":
        return _chamar_groq(conteudo, temperatura, max_output_tokens)
    if escolha == "gemini":
        return _chamar_gemini(conteudo, temperatura, max_output_tokens)
    # auto: Gemini primeiro, Groq como fallback.
    dados, erro = _chamar_gemini(conteudo, temperatura, max_output_tokens)
    if dados is not None:
        return dados, None
    dados2, erro2 = _chamar_groq(conteudo, temperatura, max_output_tokens)
    if dados2 is not None:
        return dados2, None
    return None, f"{erro} | {erro2}"


def analisar_llm(relato, provedor=None):
    """Chama o LLM (Gemini → Groq ou escolha explícita) e retorna (dict | None, erro).

    dict com chaves: severidade, categoria, causa_raiz, passos_repro, resumo_tecnico
    """
    return _chamar_llm(PROMPT.replace("{relato}", relato[:2000]), provedor=provedor)


def analisar_llm_rag(relato, contexto, provedor=None):
    """Chama o LLM com o histórico recuperado (RAG).

    dict com o schema padrão + ja_aconteceu, resolucao_anterior, registros_similar.
    """
    prompt = (
        PROMPT_RAG
        .replace("{relato}", relato[:2000])
        .replace("{contexto}", (contexto or "")[:6000])
    )
    return _chamar_llm(prompt, provedor=provedor)


def _chamar_groq(conteudo, temperatura=0.2, max_output_tokens=1024):
    """Chama o modelo open-weight (Groq) com resposta em JSON. Retorna (dict | None, erro)."""
    chave = _chave("GROQ_API_KEY")
    if not chave:
        return None, "Chave GROQ_API_KEY não configurada."
    modelo = os.environ.get("GROQ_MODELO", "").strip() or GROQ_MODELO_PADRAO
    try:
        resposta = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {chave}",
                     "Content-Type": "application/json"},
            json={
                "model": modelo,
                "messages": [
                    {"role": "system",
                     "content": "Você responde apenas com JSON válido, sem markdown."},
                    {"role": "user", "content": conteudo},
                ],
                "temperature": temperatura,
                "max_tokens": max_output_tokens,
                "response_format": {"type": "json_object"},
            },
            timeout=60,
        )
        if resposta.status_code != 200:
            return None, f"Groq HTTP {resposta.status_code}: {str(resposta.text)[:90]}"
        payload = resposta.json()
        texto = payload["choices"][0]["message"]["content"]
        global ULTIMO_PROVEDOR, ULTIMO_MODELO
        ULTIMO_PROVEDOR = "Groq"
        ULTIMO_MODELO = modelo
        return _extrair_json(texto), None
    except Exception as exc:
        return None, f"Groq: {type(exc).__name__}: {str(exc)[:120]}"


if __name__ == "__main__":
    casos = [
        "O aplicativo dá crash toda vez que tento fazer login.",
        "Estou tentando pagar e o botão não responde, estou muito frustrado!",
        "A cor de fundo podia ser mais escura.",
    ]
    print("=== TESTE DE ANÁLISE POR IA (Gemini → Groq) ===\n")
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