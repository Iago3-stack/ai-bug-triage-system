# Contribuindo com o AI Bug Triage System

Obrigado por querer contribuir! 🤝 Este é um projeto de **engenharia de QA** que une NLP offline + análise por IA (Gemini) para triagem automática de bugs.

## Como contribuir

### 🐛 Reportar um bug
Abra uma [issue](https://github.com/Iago3-stack/ai-bug-triage-system/issues) com **reprodução passo a passo**, o esperado vs. o que aconteceu e (se possível) o relatório Gherkin gerado.

### 💡 Sugerir uma melhoria
Abra uma issue com a ideia. As prioridades atuais estão no **Roadmap** do [README](README.md).

### 🛠️ Enviar código (Pull Request)
1. **Faça um fork** e crie uma branch (`feature/...` ou `fix/...`).
2. Mantenha a estrutura existente: motor em módulos separados (`triagem.py`, `ia.py`) e a interface em `home.py`.
3. **Não quebre a compatibilidade offline**: o motor determinístico `triagem.py` deve continuar funcionando **sem internet e sem APIs** (só stdlib).
4. Ao mexer no motor, confira que a **regressão não introduz falsos positivos técnicos** (palavras como *erro*/*bug* não devem disparar severidade sozinhas).
5. Envie o **Pull Request** descrevendo o que mudou e como testar.

## Guias de estilo
- **Python idiomatico** e comentários concisos.
- Texto da interface em **PT-BR**.
- Antes de nova dependência, verifique se dá pra fazer com **stdlib** (o projeto valoriza rodar sem custo/offline).

## Principais
- Preserve o **fallback automático** entre o motor local e a IA.
- Mantenha o relatório **Gherkin** e a **exportação** (MD/GitHub/Jira) funcionando.

Obrigado por ajudar a melhorar a triagem de bugs da comunidade QA! 🐞
