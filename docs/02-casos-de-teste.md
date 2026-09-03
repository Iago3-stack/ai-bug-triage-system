# 02 — Casos de Teste

Casos de teste documentados em **Gherkin** (padrão BDD) para validar o motor de triagem. Estes casos espelham os **12 testes automatizados** de `test_triagem.py`, que rodam no **CI** (GitHub Actions) a cada push.

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

Resultado esperado: **12 passed** (também validado automaticamente pelo CI).
