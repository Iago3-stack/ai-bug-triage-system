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
    "congelando": -1.5, "congela": -1.5, "congelou": -1.5,
    "perda de dados": -2.0, "vazamento": -2.0, "inseguro": -2.0,
    "apagou": -2.0, "corrompeu": -2.0, "perdi": -1.5, "sumiu": -1.5,
    "duplicou": -1.2, "resetou": -1.2, "reinicia sozinho": -1.8,
    "fecha sozinho": -1.8, "fora do ar": -1.8, "indisponível": -1.5,
    "falhou": -1.2, "bugou": -1.5, "bugado": -1.2, "defeituoso": -1.2,
    "pagamento": -1.5, "pagando": -1.5,
    "segurança": -1.5, "senha": -1.0, "login": -1.0, "logado": -1.0,
    "acesso": -0.8, "autenticar": -0.8, "é rejeitado": -1.2,
    "cobrança dupla": -1.8, "cobrou duas": -1.8, "extornar": -1.2,
    # Negados fora dos padrões PADROES_NEGACAO (evitar contagem dupla com eles)
    "não baixa": -1.5, "não loga": -1.5,
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

# Boosters (amplificadores de intensidade): multiplicam o peso do termo que
# precedem. "muito frustrado" vale mais que "frustrado". Determinístico e local:
# só o termo imediatamente precedido pelo booster é amplificado.
BOOSTERS = {
    "muito": 1.6, "bastante": 1.35, "extremamente": 2.0, "altamente": 1.8,
    "totalmente": 1.5, "completamente": 1.6, "super": 1.6, "demais": 1.7,
    "demasiadamente": 1.8, "absurdamente": 2.2, "insuportavelmente": 2.2,
    "incrivelmente": 1.6, "realmente": 1.2, "pra caramba": 1.6,
}

# Diminuidores (atenuadores): espelho dos boosters, multiplicam < 1.0 o termo
# que precedem. "um pouco lenta" vale menos que "lenta". Determinístico e local:
# só o trecho imediatamente antes do termo é considerado.
DIMINUIDORES = {
    "um pouco": 0.6, "um pouquinho": 0.5, "um cadinho": 0.5, "pouco": 0.6,
    "levemente": 0.7, "ligeiramente": 0.7, "sutilmente": 0.8, "quase": 0.7,
    "fracamente": 0.7, "um tico": 0.6, "um nadinha": 0.5,
}

# Padrões de léxico por RAIZ (regex compilados): cobrem flexões/derivações de uma vez.
# \blent(?!es?\b)\w* captura lento/lenta/lentos/lentas/lentamente/lentidão/lentíssimo/lentinho...
# e o lookahead (?!es?\b) exclui apenas "lente"/"lentes" (falsos positivos).
# O peso é somado UMA vez por padrão, mesmo se houver vários matches no texto.
PADROES_LEXICO = [
    (re.compile(r"\blent(?!es?\b)\w*", re.UNICODE), -0.7),
    # Erros de serviço explícitos (Postman/newman/curl): peso forte e próprio,
    # sem depender da palavra do domínio ("pagamento" vs "cobrança").
    (re.compile(r"\b(?:internal server error|gateway timeout|service unavailable)\b", re.UNICODE), -1.5),
    (re.compile(r"\bdatabase timeout\b", re.UNICODE), -1.5),
    (re.compile(r"\bconnection refused\b", re.UNICODE), -1.2),
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

# Negadores gerais (regra 2: negação local sobre QUALQUER termo do léxico —
# cobre flexões e verbos que a lista fixa PADROES_NEGACAO não enumera,
# ex.: "não funcionou", "não estava funcionando", "não trava").
NEGADORES = ("não", "nao", "nunca", "jamais", "tampouco")
AUXILIARES_NEGADOS = ("está", "esta", "tá", "ta", "estava", "ficou", "fica",
                      "estando", "ficava", "vem", "estão", "estao")

# Meta-severidade: o próprio usuário julgando o impacto ("nada crítico",
# "baixa prioridade"). É um "voto" explícito que limita o teto, NÃO soma ao
# léxico (sinais de natureza diferente). Determinístico: regex + teto fixo.
META_BAIXA_PRIORIDADE = [
    re.compile(r"\bn[ãa]o\s*[ée]\s*cr[ií]tic", re.UNICODE),
    re.compile(r"\bn[ãa]o\s*[ée]\s*urgente", re.UNICODE),
    re.compile(r"\bn[ãa]o\s*[ée]\s*grave", re.UNICODE),
    re.compile(r"\bnada\s+cr[ií]tic", re.UNICODE),
    re.compile(r"\bb[aa]ixa\s+prioridade", re.UNICODE),
    re.compile(r"\bbeima\s+de\s+urgente", re.UNICODE),
    re.compile(r"\ba g[ée]nt[eê]e\s+segura", re.UNICODE),  # sem perda/dano grave
]
TETO_BAIXA_PRIORIDADE = -0.5  # mesmo que diga "nada crítico", nunca sobe p/ CRÍTICA

# Contexto de teste automatizado (Playwright, Postman/newman, executável de QA):
# relato de uma execução de teste que falhou é ruído de pipeline, NÃO incidente.
# Só capa o teto se NÃO houver sinal forte de incidente real (HTTP 4xx/5xx em
# serviço, produção, perda de dados etc.) — esses mantêm a severidade real.
META_CONTEXTO_TESTE = [
    re.compile(r"\.spec\.(js|ts|py)\b", re.UNICODE),
    re.compile(r"\bexpect\(|toHaveText|locator\(|assertionerror", re.UNICODE),
    re.compile(r"\bplaywright\b|\bnewman\b|\bpostman\b|\bteste automatizado\b", re.UNICODE),
    re.compile(r"\bteste de login\b|\btest case\b|\btc(?:-|_)?\d+", re.UNICODE),
    re.compile(r"\bfailed\b.*\bpassed\b|\bpassed\b.*\bfailed\b", re.UNICODE),
]
META_SINAL_INCIDENTE = [
    re.compile(r"http[s]?://\S+\s+\[?(?:40\d|50\d)", re.UNICODE),
    re.compile(r"\b(?:internal server error|database timeout|connection refused)\b", re.UNICODE),
    re.compile(r"\b(?:produ[çc][ãa]o|em produ[çc][ãa]o|prod)\b", re.UNICODE),
    re.compile(r"\b(?:perda de dados|vazamento|fora do ar|corrompeu)\b", re.UNICODE),
]
TETO_CONTEXTO_TESTE = -0.5  # teste que falhou sem incidente = no máximo MÉDIA

MOTOR = "Léxico PT local (determinístico, offline)"


def _fator_booster(texto, posicao):
    """Fator de intensificação se houver um booster nas 3 palavras antes de `pos`.

    Janela pontual (determinística): olha só o trecho que precede o termo,
    então "muito frustrado" amplifica, mas "frustrado, e muito obrigado" não.
    """
    janela = texto[max(0, posicao - 40):posicao]
    palavras = re.findall(r"[\wà-ú]+", janela)
    if len(palavras) > 3:
        palavras = palavras[-3:]
    melhor = 1.0
    for booster, fator in BOOSTERS.items():
        if booster in palavras:
            melhor = max(melhor, fator)
    return melhor


def _fator_diminuidor(texto, posicao):
    """Fator de atenuação se houver um diminuidor nas 3 palavras antes de `pos`.

    Espelho dos boosters: "um pouco lenta" reduz o peso de "lenta". Igual à
    lógica dos boosters para manter consistência e determinismo.
    """
    janela = texto[max(0, posicao - 40):posicao]
    palavras = re.findall(r"[\wà-ú]+", janela)
    if len(palavras) > 3:
        palavras = palavras[-3:]
    melhor = 1.0
    for diminuidor, fator in sorted(DIMINUIDORES.items(), key=lambda k: len(k[0]), reverse=True):
        if diminuidor in palavras:
            melhor = min(melhor, fator)
    return melhor


def _esta_negado(texto, posicao):
    """True se o termo que começa em `posicao` for precedido por um negador.

    Regra geral e local: olha 1-2 palavras antes (ex.: "não", "não estava").
    Só vale para termos que já tem peso no léxico — evita a caça de exceções.
    """
    janela = re.findall(r"[\wà-ú]+", texto[max(0, posicao - 40):posicao])
    if not janela:
        return False
    if janela[-1] in NEGADORES:
        return True
    if len(janela) >= 2 and janela[-2] in NEGADORES and janela[-1] in AUXILIARES_NEGADOS:
        return True
    return False


def _aplicar_peso(termo, peso, texto):
    """Aplica booster, diminuidor e negação granular ao termo de posição inicial."""
    posicao = texto.index(termo)
    base = peso * _fator_booster(texto, posicao) * _fator_diminuidor(texto, posicao)
    if _esta_negado(texto, posicao):
        # negação de BÊNÇÃO vira maldição; negação de MALDIÇÃO cancela/acalma
        base = -peso * 0.8 if peso > 0 else peso * 0.15
    return base


def _aplicar_lexico(texto):
    """Soma pesos dos termos do léxico sem contar sobreposições duas vezes."""
    acertos = []
    score = 0.0
    for termo in sorted(LE_XICO, key=len, reverse=True):
        if any(termo in ja_visto for ja_visto in acertos):
            continue
        if termo in texto:
            score += _aplicar_peso(termo, LE_XICO[termo], texto)
            acertos.append(termo)
    for padrao, peso in PADROES_LEXICO:
        matches = [m for m in padrao.finditer(texto)]
        if matches:
            score += _aplicar_peso(matches[0].group(), peso, texto)
            acertos.append(matches[0].group())
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


def _fator_enfase(descricao, score):
    """Amplifica a magnitude do score quando há sinais de ênfase no relato:
    palavras em CAIXA ALTA e/ou pontuação repetida ('!!!', '???').

    Conservador: só amplifica se o relato já tem sinal (score != 0) — um texto
    todo em caps neutro não cria severidade do nada.
    """
    if score == 0:
        return 1.0
    fator = 1.0
    caps = re.findall(r"\b[A-ZÀ-Ú][A-ZÀ-Ú]{2,}\b", descricao)
    if caps:
        fator *= 1.3
    if re.search(r"[!?]{2,}", descricao):
        fator = min(fator * 1.2, 1.6)
    return fator


def _aplicar_meta_severidade(descricao, score):
    """Veto do usuário/contexto ao teto de severidade.

    Não soma ao léxico — apenas impõe um teto (score >= TETO) quando:
    1. o relato deixa claro que o impacto é baixo ("nada crítico"), ou
    2. é saída de teste automatizado que falhou SEM sinal de incidente real
       (ruído de pipeline não é acidente de produção).
    Determinístico.
    """
    texto = unicodedata.normalize("NFC", descricao.lower())
    if any(p.search(texto) for p in META_BAIXA_PRIORIDADE):
        return max(score, TETO_BAIXA_PRIORIDADE)
    eh_teste = any(p.search(texto) for p in META_CONTEXTO_TESTE)
    if eh_teste and not any(p.search(texto) for p in META_SINAL_INCIDENTE):
        return max(score, TETO_CONTEXTO_TESTE)
    return score


def triar(descricao):
    """Classifica a severidade de um relato de bug usando NLP local.

    Retorna um dicionário com score, gravidade, sentimento, fatores e motor.
    """
    texto = unicodedata.normalize("NFC", descricao.lower())

    score_lexico, acertos_lexico = _aplicar_lexico(texto)
    score_negacao, acertos_negacao = _aplicar_negacoes(texto)
    score = (score_lexico + score_negacao) * _fator_enfase(descricao, score_lexico + score_negacao)
    score = _aplicar_meta_severidade(descricao, score)

    termos = []
    for t in acertos_lexico:
        if t in PALAVRAS_TECNICAS_INERTES:
            continue
        if _esta_negado(texto, texto.index(t)):
            termos.append(f"{t} (negado)")
        else:
            termos.append(t)
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