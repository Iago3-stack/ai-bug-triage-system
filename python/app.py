# app.py

from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_bootstrap import Bootstrap5

app = Flask(__name__)
app.config['SECRET_KEY'] = 'uma_chave_secreta_muito_forte_e_longa'
Bootstrap5(app) # Inicializa o Bootstrap para o Flask

# Dados de exemplo (imagine que isso veio de um banco de dados)
ITENS_CADASTRO = [
    {'id': 1, 'nome': 'Notebook Dell XPS', 'valor': 8500.00, 'descricao': 'Notebook de alta performance para desenvolvimento.'},
    {'id': 2, 'nome': 'Monitor UltraWide LG', 'valor': 2100.00, 'descricao': 'Monitor 34 polegadas, ideal para multitarefas.'},
    {'id': 3, 'nome': 'Teclado Mecânico', 'valor': 450.00, 'descricao': 'RGB, switches brown, excelente para programar.'}
]

# Rota principal (página inicial)
@app.route('/')
def index():
    # Verifica se o usuário está logado e passa a informação para o template
    logado = 'username' in session
    return render_template('index.html', titulo='Página Inicial', logado=logado)

# Rota de Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Validação simples (usuário 'admin', senha '1234')
        if username == 'admin' and password == '1234':
            session['username'] = username # Armazena o usuário na sessão
            flash(f'Olá, {username}! Você está logado.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login inválido. Tente novamente.', 'danger')
            return redirect(url_for('login'))
            
    return render_template('login.html', titulo='Login')

# Rota de Logout
@app.route('/logout')
def logout():
    session.pop('username', None) # Remove o usuário da sessão
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('index'))

# Rota para a página de Itens
@app.route('/itens')
def itens():
    # Passamos a lista de itens para o template HTML
    return render_template('itens.html', titulo='Itens Cadastrados', itens=ITENS_CADASTRO)

# Rota para a página "Contato"
@app.route('/contato', methods=['GET', 'POST'])
def contato():
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        mensagem = request.form.get('mensagem')
        print(f"Nova mensagem recebida de {nome} ({email}): {mensagem}")
        flash('Obrigado! Sua mensagem foi enviada com sucesso.', 'success')
        return redirect(url_for('index'))
        
    return render_template('contato.html', titulo="Contato")

if __name__ == '__main__':
    app.run(debug=True)
