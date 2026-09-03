# 01 — Requisitos

Documentação de engenharia de software do **AI Bug Triage System**, seguindo o processo de qualidade. Aqui estão os requisitos **funcionais (RF)** e **não-funcionais (RNF)** que guiam a construção.

## 1. Contexto

O app recebe o **relato de um bug** em linguagem natural e o **classifica automaticamente** quanto à severidade, gerando também uma **documentação técnica em Gherkin**. O público-alvo são times de QA e desenvolvedores que precisam priorizar erros e reproduzi-los com rapidez.

## 2. Requisitos Funcionais (RF)

| ID | Requisito | Prioridade |
|---|---|---|
| RF-01 | Classificar a severidade do bug em **CRÍTICA / MÉDIA / NORMAL** | Alta |
| RF-02 | Identificar o **sentimento** do relato (Frustrado / Negativo / Neutro / Positivo) | Alta |
| RF-03 | Listar os **fatores** que justificaram a triagem (termos + negações) | Alta |
| RF-04 | Gerar **documentação Gherkin** (Dado/Quando/Então) baseada na severidade | Alta |
| RF-05 | **Não** disparar severidade para palavras de vocabulário de teste (`erro`, `bug`, `falha`, `defeito`) — evita falso-positivo | Alta |
| RF-06 | **Conciliar** o resultado do motor local com a análise por IA, pela regra do **maior vence** | Média |
| RF-07 | **Sinalizar divergência** quando os dois motores discordam (recomendação de revisão humana) | Média |
| RF-08 | **Exportar** o relatório em Markdown, abrir Issue no GitHub ou enviar ao Jira | Média |
| RF-09 | Manter **histórico da sessão** em tabela com opção de limpar | Baixa |
| RF-10 | Rodar **100% offline** no motor local (sem API externa) | Alta |

## 3. Requisitos Não-Funcionais (RNF)

| ID | Requisito | Tipo |
|---|---|---|
| RNF-01 | **Determinístico**: mesma entrada produz sempre a mesma triagem | Consistência |
| RNF-02 | **Zero dependência externa** no motor local (apenas stdlib) | Portabilidade |
| RNF-03 | **Baixa latência**: triagem instantânea na interface | Performance |
| RNF-04 | **Fallback automático** para o motor local quando a API de IA falhar | Confiabilidade |
| RNF-05 | Interface **intuitiva e com identidade visual** própria | Usabilidade |
| RNF-06 | Código **testado** por `pytest` (12 casos) e validado por **CI** | Qualidade |
| RNF-07 | **Transparência**: informar qual motor foi usado em cada triagem | Auditoria |

## 4. Limites e decisões de contorno

- Palavras como `erro`, `bug`, `falha` e `defeito` são **vocabulário normal de teste** e **não** escalam severidade sozinhas (decisão de QA para evitar ruído).
- O termo `funciona` fica fora do léxico positivo porque aparece dentro de **negações** ("não funciona") — somaria contra si mesmo.
- A análise por IA **nunca** recebe a chave via repositório; ela vem de Secrets/`.env`.
