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
| RF-11 | **Análise por IA** opcional (Gemini com fallback Groq) — severidade sugerida, causa raiz, categoria e passos; **seletor de provedor** (Automático / só Gemini / só Groq / **modelo próprio**) com o modelo real no relatório | Média |
| RF-12 | **RAG** no histórico persistido: responder se o bug **já aconteceu** e **como foi resolvido** (retrieval **híbrido BM25 + vetores** com sinônimos e recência + geração), aprendendo com a **resolução registrada** pelo usuário | Média |
| RF-13 | **Dashboard de QA completo**: saúde da suíte (0–10), gauge de % de críticas/altas, filtro por funcionalidade, evolução do score médio/dia, top causas raiz (IA) e taxa + lista de divergências IA vs. motor | Média |
| RF-14 | **Rodapé de doação Pix**: símbolo oficial do Banco Central, botão "Pagar com Pix via link" e QR Code com a chave com `+55`, com botão que **copia a chave sem o DDI** | Baixa |
| RF-15 | **App multi-página** (`Início` / `Triagem de Bugs` / `Dashboard QA`) via `st.navigation`, com URLs próprias e menu nativo na sidebar | Alta |
| RF-16 | **Login multi-tenant (Supabase Auth)**: cadastro com confirmação de e-mail e login (e-mail + senha); **Início público**, Ferramenta e Dashboard exigem login quando o Supabase está configurado; side (👤 + "Sair") | Alta |
| RF-17 | **Sessão persiste no F5**: recarregar a página mantém o usuário logado (cookie + ponte de escrita persistente), com fallback para tela de login com mensagem honesta | Alta |
| RF-18 | **Alerta CRÍTICA/ALTA**: e-mail (SMTP/Gmail) e/ou Discord, configuráveis por usuário/sessão no modal ⚙️ (nada em disco) | Média |
| RF-19 | **Planos Basic/Premium + isolamento por tenant**: `PLANO=free|pago` liga/desliga recursos e todo registro persistido carrega `tenant_id` (filtro por conta) | Média |

## 3. Requisitos Não-Funcionais (RNF)

| ID | Requisito | Tipo |
|---|---|---|
| RNF-01 | **Determinístico**: mesma entrada produz sempre a mesma triagem | Consistência |
| RNF-02 | **Zero dependência externa** no motor local (apenas stdlib) | Portabilidade |
| RNF-03 | **Baixa latência**: triagem instantânea na interface | Performance |
| RNF-04 | **Fallback automático** para o motor local quando a API de IA falhar | Confiabilidade |
| RNF-05 | Interface **intuitiva e com identidade visual** própria | Usabilidade |
| RNF-06 | Código **testado** por `pytest` (**225 casos**) e validado por **CI** | Qualidade |
| RNF-07 | **Transparência**: informar qual motor foi usado em cada triagem | Auditoria |
| RNF-08 | **Privacidade**: chaves/credenciais do visitante ficam só na sessão (nunca em disco/histórico); campos do modal nascem vazios (não expõem secrets do dono) | Segurança |
| RNF-09 | **Isolamento multi-tenant**: cada conta lê/grava apenas os registros do seu `tenant_id` | Segurança |

## 4. Limites e decisões de contorno

- Palavras como `erro`, `bug`, `falha` e `defeito` são **vocabulário normal de teste** e **não** escalam severidade sozinhas (decisão de QA para evitar ruído).
- O termo `funciona` fica fora do léxico positivo porque aparece dentro de **negações** ("não funciona") — somaria contra si mesmo.
- A análise por IA **nunca** recebe a chave via repositório; ela vem de Secrets/`.env`.
