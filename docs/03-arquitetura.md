# 03 — Arquitetura e Fluxo

Visão da arquitetura do **AI Bug Triage System** e do fluxo de processamento de um relato de bug.

## 1. Visão geral

O sistema trabalha com **dois motores de análise** que se **reconciliam** pela regra do **maior vence**:

```
┌─────────────┐     descrição       ┌──────────────────────────────┐
│    Usuário   │ ──────────────────▶ │         home.py (UI)          │
│  (QA/Dev)    │                     │  Streamlit                  │
└─────────────┘                     └──────────────┬───────────────┘
                                                   │
                              ┌────────────────────┴────────────────────┐
                              │                                         │
                    ┌─────────▼─────────┐                      ┌────────▼─────────┐
                    │  triagem.py       │                      │  ia.py (Fase 3)   │
                    │  Motor NLP local  │                      │  Google Gemini     │
                    │  (stdlib, offline)│                      │  JSON estruturado  │
                    └─────────┬─────────┘                      └────────┬─────────┘
                              │                                         │
                              └────────────┬────────────────────────────┘
                                           ▼
                              ┌──────────────────────────────┐
                              │  Reconciliador (maior vence)  │
                              │  + sinal de divergência       │
                              └──────────────┬───────────────┘
                                             ▼
                              ┌──────────────────────────────┐
                              │  Relatório: severidade +      │
                              │  fatores + Gherkin + export   │
                              └──────────────────────────────┘
```

## 2. Componentes

| Módulo | Papel | Dependência |
|---|---|---|
| `home.py` | Interface web (Streamlit): cabeçalho, ferramenta, export, histórico | streamlit |
| `triagem.py` | Motor NLP **offline determinístico**: léxico PT + negações | **stdlib apenas** |
| `ia.py` | Análise por IA (Gemini): causa raiz, categoria, passos — **com fallback** | google-genai |
| `test_triagem.py` | Testes unitários do motor (12 casos) | pytest |
| `.streamlit/config.toml` | Tema e configurações visuais | streamlit |

## 3. Decisões de design

- **Motor local determinístico** (RF-10/RNF-01): garante funcionamento sem internet e resultado reprodutível, servindo de **base de confiança** mesmo se a IA falhar.
- **Fallback automático** (RNF-04): se a API de IA falhar ou não houver chave, a triagem segue com o motor local sem quebrar a experiência.
- **Reconciliação pelo maior vence** (RF-06): nenhum alerta grave é descartado pela concordância com o motor local; divergência é **explicitada** para revisão humana.
- **Transparência** (RNF-07): o relatório informa **qual motor** produziu a análise, permitindo auditoria.

## 4. Fluxo de processamento

1. Usuário informa a descrição do bug.
2. `home.py` chama `triagem.py` → score local (léxico + negação) e sentimento.
3. Se houver chave `GEMINI_API_KEY`, `ia.py` enriquece com causa raiz/categoria; se falhar, **fallback** para o local.
4. O **reconciliador** combina os resultados (maior vence) e marca divergência quando discordam.
5. Gera o relatório com severidade, fatores e **Gherkin**.
6. Usuário pode **exportar** (.md), abrir **Issue** no GitHub ou enviar ao **Jira**; histórico fica na tabela da sessão.
