# Motor de Triagem Inteligente (NLP local, 100% offline e determinístico)
# Substitui a chamada ao Google Translate do TextBlob (bloqueada em datacenter)
# e a lista genérica de palavras-chave antiga.

import re
import unicodedata


# --- 1. LÉXICO: termos mapeados para pesos de severidade ---
# Valores negativos = sinal de problema; positivos = contrabalanço.
LE_XICO = {
    # Técnicos graves (sinal de bug sério / impacto em infra ou negócio)
    "crashando": -2.0, "crash": -2.0,
    "tela azul": -2.0, "erro fatal": -2.0, "erro 500": -2.0, "500": -1.5,
    "trava toda": -2.0, "travando": -1.5, "trava": -1.5, "travado": -1.5,
    "congelando": -1.5, "congela": -1.5,
    "perda de dados": -2.0, "vazamento": -2.0, "inseguro": -2.0,
    "apagou": -2.0, "corrompeu": -2.0,
    "pagamento": -1.5, "pagando": -1.5,
    "segurança": -1.5, "senha": -1.0, "login": -1.0,
    # Emocionais negativos (frustração real do usuário)
    "insuportável": -2.5, "ódio": -2.5, "odeio": -2.5, "lixo": -2.5,
    "frustrado": -2.0, "frustração": -2.0, "frustrante": -2.0,
    "raiva": -2.0, "raivoso": -2.0, "desesperado": -2.0, "desespero": -2.0,
    "péssimo": -2.0, "horrível": -2.0, "terrível": -2.0,
    "inutilizável": -2.0, "revoltado": -2.0, "inaceitável": -2.0,
    "irritado": -1.5, "irritante": -1.5, "decepcionado": -1.5,
    "decepcionante": -1.5, "absurdo": -1.5, "ridículo": -1.5,
    # Negativos gerais (nível médio, sem ser palavra-chave técnica)
    "impossível": -1.5, "grave": -1.5, "urgente": -1.5, "urgência": -1.5,
    "impede": -1.5, "impedindo": -1.5, "impedimento": -1.5,
    "bloqueando": -1.5, "bloqueou": -1.5, "bloqueado": -1.0,
    "quebrou": -1.5, "quebrado": -1.2, "parou": -1.2, "parando": -1.2,
    "ruim": -1.0,
    # Positivos (dão equilíbrio e evitam falso-positivo)
    # "funciona" puro fica de fora: ele aparece dentro de "não funciona",
    # e se somaria contra a própria negação.
    "funcionou": 1.0, "funcionando": 0.6,
    "perfeito": 1.0, "excelente": 1.0, "ótimo": 1.0, "ótima": 1.0, "amei": 1.0,
}

# Padrões de léxico por RAIZ (regex compilados): cobrem flexões/derivações de uma vez.
# \blent(?!es?\b)\w* captura lento/lenta/lentos/lentas/lentamente/lentidão/lentíssimo/lentinho...
# e o lookahead (?!es?\b) exclui apenas "lente"/"lentes" (falsos positivos).
# O peso é somado UMA vez por padrão, mesmo se houver vários matches no texto.
PADROES_LEXICO = [
    (re.compile(r"\blent(?!es?\b)\w*", re.UNICODE), -0.7),
]

# Termos puramente técnicos que NÃO devem escalar severidade sozinhos
# (ex: "erro" e "bug" são palavras do vocabulário de teste, não emoção)
PALAVRAS_TECNICAS_INERTES = {"erro", "bug", "falha", "defeito"}

# Palavras emocionais negativas (para rotular o sentimento com precisão)
EMOCIONAIS_NEGATIVAS = {
    "insuportável", "ódio", "odeio", "lixo", "frustrado", "frustração",
    "frustrante", "raiva", "raivoso", "desesperado", "desespero", "péssimo",
    "horrível", "terrível", "inutilizável", "revoltado", "inaceitável",
    "irritado", "irritante", "decepcionado", "decepcionante", "absurdo",
    "ridículo",
}

# --- 2. DETECÇÃO DE NEGAÇÃO: padrões de fala real (ex: "não funciona") ---
PADROES_NEGACAO = [
    (r"\bn[ãa]o\s+(funciona|funcionar|funcionando)", -1.5),
    (r"\bn[ãa]o\s+(responde|respondendo|responder|responderam)", -1.5),
    (r"\bn[ãa]o\s+(abre|abrir|abriu)", -1.5),
    (r"\bn[ãa]o\s+(carrega|carregar|carregando)", -1.5),
    (r"\bn[ãa]o\s+(salva|salvar|salvou)", -1.5),
    (r"\bn[ãa]o\s+(envia|enviar|enviou|envio)", -1.5),
    (r"\bn[ãa]o\s+(consigo|consegue|consegui|conseguir)", -1.5),
    (r"\bn[ãa]o\s+(entra|entrar)", -1.2),
    (r"\bn[ãa]o\s+(aparece|aparecer|apareceu)", -1.0),
    (r"\bn[ãa]o\s+(deixa|deixar)", -1.0),
    (r"\bn[ãa]o\s+(mostra|mostrar)", -1.0),
    (r"\bnunca\s+(funciona|funcionou|carregou|abriu)", -1.5),
    (r"\bparou\s+de\s+(funcionar|responder)", -1.8),
]

MOTOR = "Léxico PT local (determinístico, offline)"


def _aplicar_lexico(texto):
    """Soma pesos dos termos do léxico sem contar sobreposições duas vezes."""
    acertos = []
    score = 0.0
    for termo in sorted(LE_XICO, key=len, reverse=True):
        if any(termo in ja_visto for ja_visto in acertos):
            continue
        if termo in texto:
            score += LE_XICO[termo]
            acertos.append(termo)
    for padrao, peso in PADROES_LEXICO:
        matches = [m.group() for m in padrao.finditer(texto)]
        if matches:
            score += peso
            acertos.append(matches[0])
    return score, acertos


def _aplicar_negacoes(texto):
    """Soma pesos dos padrões de negação encontrados (cada padrão só uma vez)."""
    score = 0.0
    acertos = []
    for padrao, peso in PADROES_NEGACAO:
        if re.search(padrao, texto):
            score += peso
            acertos.append(peso)
    return score, acertos


def triar(descricao):
    """Classifica a severidade de um relato de bug usando NLP local.

    Retorna um dicionário com score, gravidade, sentimento, fatores e motor.
    """
    texto = unicodedata.normalize("NFC", descricao.lower())

    score_lexico, acertos_lexico = _aplicar_lexico(texto)
    score_negacao, acertos_negacao = _aplicar_negacoes(texto)
    score = score_lexico + score_negacao

    termos = [t for t in acertos_lexico if t not in PALAVRAS_TECNICAS_INERTES]
    n_negacoes = len(acertos_negacao)
    neg_fatores = []
    if n_negacoes:
        neg_fatores.append(f"negação ({n_negacoes} padrão negado)" if n_negacoes == 1
                           else f"negação ({n_negacoes} padrões)")
    fatores = list(termos) + neg_fatores
    tem_emocional = any(t in EMOCIONAIS_NEGATIVAS for t in acertos_lexico)

    if score <= -2.0:
        gravidade = "CRÍTICA 🚨"
        sentimento = "Frustrado/Urgente" if tem_emocional else "Urgente/Crítico"
    elif score <= -0.5:
        gravidade = "MÉDIA ⚠️"
        sentimento = "Negativo/Insatisfeito"
    elif score >= 0.5:
        gravidade = "NORMAL ✅"
        sentimento = "Positivo/Satisfeito"
    else:
        gravidade = "NORMAL ✅"
        sentimento = "Neutro/Calmo"

    return {
        "score": score,
        "gravidade": gravidade,
        "sentimento": sentimento,
        "fatores": fatores,
        "motor": MOTOR,
    }


if __name__ == "__main__":
    casos = [
        "O aplicativo está dando crash toda vez que tento fazer login",
        "Estou tentando pagar e o botão não responde, estou muito frustrado!",
        "A cor do fundo podia ser mais escura.",
        "Achei um erro de digitação no rodapé da página.",
        "Não consegui salvar meu relatório, o botão não funciona.",
    ]
    print("=== TESTE DO MOTOR DE TRIAGEM ===\n")
    for caso in casos:
        r = triar(caso)
        print(f"Relato: {caso}")
        print(f"  → {r['gravidade']} | Sentimento: {r['sentimento']} | Score: {r['score']:.2f}")
        print(f"    Fatores: {', '.join(r['fatores']) or 'nenhum'}\n")