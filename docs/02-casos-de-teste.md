# 02 — Casos de Teste

Casos de teste documentados em **Gherkin** (padrão BDD) para validar o motor de triagem. Estes casos espelham os testes automatizados de `test_triagem.py` (motor: **18 testes**), que rodam no **CI** (GitHub Actions) a cada push junto com os demais (Jira, persistência, guardrails, dashboard e RAG — **71 no total**).

## Matriz de casos de teste

| ID | Cenário | Entrada (relato) | Esperado | Automatizado |
|---|---|---|---|---|
| CT-01 | Bug crítico de crash/login | "o aplicativo está dando crash toda vez que tento fazer login" | CRÍTICA 🚨 | ✅ |
| CT-02 | Perda de dados / segurança | "perdi todos os meus dados depois do vazamento de segurança" | CRÍTICA 🚨 | ✅ |
| CT-03 | Frustração + pagamento | "não consigo pagar e estou muito frustrado" | MÉDIA ⚠️ ou CRÍTICA | ✅ |
| CT-04 | Botão sem resposta | "o botão não responde quando tento salvar" | MÉDIA ⚠️ ou CRÍTICA | ✅ |
| CT-05 | *Erro de digitação* (vocab de teste) | "achei um erro de digitação no rodapé da página" | NORMAL ✅ | ✅ |
| CT-06 | *Bug* (vocab de teste) | "encontrei um bug no rodapé da página inicial" | NORMAL ✅ | ✅ |
| CT-07 | Frustração emocional | "estou desesperado, isso é inaceitável" | Sentimento Frustrado/Negativo | ✅ |
| CT-08 | Sucesso | "a funcionalidade está funcionando perfeitamente, ótimo" | NORMAL ✅ + Positivo | ✅ |
| CT-09 | Determinismo | mesmo relato rodado 2× | resultado idêntico | ✅ |
| CT-10 | Fatores presentes | "não consigo salvar e o botão não responde" | `fatores` não-vazio | ✅ |
| CT-11 | Léxico negativo | "isso está crashando todo dia" | score < 0, termo detectado | ✅ |
| CT-12 | Padrão de negação | "o botão não funciona" | score < 0, negação detectada | ✅ |

## Exemplo de caso de teste em Gherkin

```gherkin
Cenário: Bug crítico com indício de login
  Dado que o analista deseja triar um relato
  Quando informo "o aplicativo está dando crash toda vez que tento fazer login"
  Então o grau de severidade deve ser CRÍTICA
  E o relatório deve trazer os fatores "crash" e "login"
```

```gherkin
Cenário: Vocabulário de teste não deve escalar severidade
  Dado que o analista deseja triar um relato
  Quando informo "encontrei um bug no rodapé da página inicial"
  Então o grau de severidade deve ser NORMAL
  E não deve haver alerta de severidade elevada
```

## Como rodar

```bash
pip install -r requirements-dev.txt
pytest -v
```

Resultado esperado: **71 passed** (18 do motor + 15 do Jira + 8 da persistência + 14 dos guardrails + 6 do dashboard + 10 do RAG — também validado automaticamente pelo CI).

## Guardrails (casos de teste da camada de segurança)

A camada `guardrails.py` detecta e mascara credenciais/PII antes do envio a IA/Jira/GitHub/histórico (**14 testes**):

| ID | Cenário | Entrada (relato) | Esperado |
|---|---|---|---|
| GR-01 | Token Atlassian | `ATATT3xFfG...` | detectado + mascarado |
| GR-02 | Chave Gemini/Google | `AQ.Ab...` / `AIza...` | detectado + mascarado |
| GR-03 | Chave OpenAI / GitHub | `sk-...` / `ghp_...` / `github_pat_...` | detectado + mascarado |
| GR-04 | E-mail | `teste.qa@exemplo.com` | detectado + mascarado |
| GR-05 | **Senha numérica** | `senha 4323454321` | detectado + mascarado |
| GR-06 | **Telefone** | `(11) 98888-7777` | detectado + mascarado |
| GR-07 | **CPF** | `123.456.789-00` | detectado + mascarado |
| GR-08 | Texto comum | "o app travou no pagamento" | **nada** detectado (falso-positivo zero) |
| GR-09 | Número comum | "versão 2026 do sistema" | **não** mascarar |

> Aviso exibido ao usuário: "🔒 Credencial/PII detectada no relato (e-mail, senha (com números), telefone, CPF). A informação sensível foi mascarada e não será enviada à IA, ao Jira, ao GitHub ou ao histórico."
