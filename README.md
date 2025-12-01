# IAgo - Gerenciador de Atividades 📋

Um gerenciador de tarefas moderno, intuitivo e completo, desenvolvido com **Flet** (Flutter para Python). Perfeito para organizar suas atividades com prioridades, categorias, datas de vencimento e muito mais!

## ✨ Recursos Principais

- ✅ **Persistência de Dados** - Salva automaticamente em JSON
- 🔍 **Busca e Filtro** - Filtre por texto, status, prioridade e categoria
- 📝 **Categorias e Tags** - Organize suas atividades
- ⭐ **Prioridades** - Alta, Média, Baixa
- 📅 **Datas de Vencimento** - Acompanhe prazos
- 🌙 **Tema Escuro/Claro** - Interface adaptável
- 📊 **Exportação CSV** - Exporte seus dados
- 📜 **Histórico de Alterações** - Rastreie mudanças
- 👤 **Login Multiusuário** - Suporte a múltiplos usuários
- 🔐 **Segurança** - Dados persistentes locais

## 🚀 Como Executar

### Pré-requisitos
- Python 3.8+
- pip (gerenciador de pacotes)

### Instalação

1. **Clone o repositório:**
```bash
git clone https://github.com/seu-usuario/IAgo.git
cd IAgo
```

2. **Crie um ambiente virtual (recomendado):**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. **Instale as dependências:**
```bash
pip install flet
```

4. **Execute a aplicação:**
```bash
python python/IAgo_flet_v2.py
```

## 📖 Como Usar

### Login
1. Abra a aplicação
2. Digite um usuário e senha (qualquer valor funciona na versão demo)
3. Clique em "Entrar"

### Adicionar Atividade
1. Digite o texto da atividade no campo "Escreva uma nova atividade aqui..."
2. Clique no ícone "+" ou pressione Enter
3. Atividade aparecerá na lista abaixo

### Editar Atividade
1. Clique em qualquer atividade da lista
2. Painel de edição abrirá
3. Modifique os campos desejados:
   - Texto
   - Prioridade (🔴 Alta, 🟡 Média, 🟢 Baixa)
   - Status (⏳ Pendente, ✅ Feito, ❌ Não Feito)
   - Categoria
   - Tags
   - Data de Vencimento
4. Clique "Salvar" ou "Deletar"

### Buscar e Filtrar
1. Use a barra de busca (🔍) para buscar por texto
2. Use os dropdowns para filtrar por:
   - Status
   - Prioridade
   - Categoria

### Ver Histórico
1. Selecione uma atividade
2. Clique no ícone de histórico (📜)
3. Visualize todas as mudanças realizadas

### Exportar para CSV
1. Selecione uma atividade
2. Clique no ícone de download (📊)
3. Arquivo CSV será gerado com todas as atividades

### Mudar Tema
1. Clique no ícone de lua/sol na barra superior
2. Interface alternará entre modo claro e escuro

## 🎨 Temas

- **Modo Escuro** - Cores neutras e confortáveis para os olhos
- **Modo Claro** - Cores claras com bom contraste

## 📁 Estrutura do Projeto

```
IAgo/
├── python/
│   ├── IAgo_flet_v2.py      # Aplicação principal
│   └── ...
├── atividades.json          # Dados persistentes (auto-gerado)
├── historico.json           # Histórico de alterações (auto-gerado)
├── .gitignore              # Configuração Git
├── README.md               # Este arquivo
└── LICENSE                 # Licença do projeto
```

## 🔧 Tecnologias Utilizadas

- **Flet** - Framework UI (Flutter para Python)
- **Python 3.x** - Linguagem de programação
- **JSON** - Persistência de dados
- **CSV** - Exportação de dados

## 🤝 Contribuindo

Contribuições são bem-vindas! Para contribuir:

1. Faça um Fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

## 📝 Roadmap

- [ ] Integração com Google Calendar
- [ ] Notificações de lembrete
- [ ] Sincronização com nuvem
- [ ] Atalhos de teclado customizáveis
- [ ] Temas adicionais
- [ ] Suporte a anexos
- [ ] API REST para integração

## 🐛 Encontrou um bug?

Abra uma [Issue](https://github.com/seu-usuario/IAgo/issues) descrevendo o problema.

## 📄 Licença

Este projeto está sob a licença [MIT](LICENSE).

## 👨‍💻 Autor

Desenvolvido por **Iago** com ❤️

## 🙏 Agradecimentos

- Obrigado ao time do Flet por este incrível framework
- Agradecimentos especiais ao GitHub Copilot pela assistência no desenvolvimento

---

**Made with ❤️ and Python** 🐍
