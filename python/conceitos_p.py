# CONCEITOS DA LINGUAGEM DE PROGRAMAÇÃO PYTHON---------------******////%%!!!

# o input() pode ser sozinho ou acompanhado de classes

# classes: str(string ou texto ) int(números inteiros ) float(pontos flutuantes com . decimais )

# if,elif, else ,and ,or ,not ,in => controla o fluxo de execução no python! são nossas condições/comparações
# são funções 

# no caso da função def() é para definir bloco de códigos e para executar precisar chamar ()

# input: é a entrada que receber o texto / output é a saida

# variáveis: são criadas para receber valores / podem receber o valor de outras variáveis

# sinais: = receber / == igual / <=/>= maior ou menor igual != diferente/igual

# sintaxe:=> são como regras gramaticais em python

# algoritmo/logica:=> criamos para construção de alguma coisa

# prompt: é o input ou texto mencioando ao usuario fica entre aspas simples ou duplas

# parâmetro: é referente aos caracteres ou valores que são passados para dentro de uma função(1,2,3,'texto' True False  etc )

# bibliotecas: são caixa de ferramentas podemos usar para coisas específicas 

# precisamos importar e dar apelido exemplo pandas as pd    

# os comentários: são para orientar na construção do codigo  

# é interessante sempre escrever os codigos pensando na melhor experiencia do usuario (UX)

# métodos de string: como .append() .remove() .submit() .lower() .strip() Ele executa uma ação no próprio objeto.
# dentro de um input() /string ou variável 
# o return: Encerra a execução de uma função (def) e devolve um valor (ou não) para quem a chamou.

# o break: Encerra imediatamente um loop (for ou while), mas o código continua a ser executado logo após o loop.

# outros métodos: .get() .start() .stop() .config() .pack() .package() .path() .upper() .strip() .format() .join() .split() .replace() .find() .count()


# o raise: Levanta uma exceção (erro) de forma explícita, interrompendo o fluxo normal do programa. Pode ser usado para validação de dados.

# o try/except: Bloco usado para tratar exceções (erros) que podem ocorrer durante a execução do código, permitindo que o programa continue rodando.

# while: Cria um loop que continua executando enquanto uma condição for verdadeira.

# Exemplo prático combinando vários conceitos acima:

# @property serve para criar propriedades em classes, permitindo o acesso controlado a atributos privados.

# @setter permite definir valores para essas propriedades, aplicando validações ou transformações conforme necessário.

# for : Cria um loop que itera sobre uma sequência (como listas, strings, etc.), executando um bloco de código para cada item.

# @dataclass: Um decorador que simplifica a criação de classes que são principalmente usadas para armazenar dados, gerando automaticamente métodos especiais como __init__() e __repr__().

# import: é usado para importar bibliotecas ou módulos externos para o código

# from: é usado para importar partes específicas de uma biblioteca ou módulo

# as: é usado para dar um apelido a uma biblioteca ou módulo importado 

# lambda: Cria funções anônimas (sem nome) de forma concisa, geralmente usadas para operações simples e rápidas.

# Exemplos práticos: lambda x: x * 2  (função que multiplica o valor por 2)

# list comprehension: Uma forma concisa de criar listas a partir de outras listas ou iteráveis, aplicando uma expressão e opcionalmente um filtro.

# Exemplo: [x * 2 for x in range(5) if x % 2 == 0]  (cria uma lista com números pares multiplicados por 2)

# f-strings: Uma forma moderna e eficiente de formatar strings em Python, permitindo a inclusão direta de expressões dentro de literais de string.

# Exemplo: nome = "Iago"; idade = 30; f"Meu nome é {nome} e tenho {idade} anos."    

# zip(): Uma função que combina múltiplas iteráveis (como listas ou tuplas) em um único iterável de tuplas, agrupando elementos correspondentes.

# Exemplo: zip([1, 2, 3], ['a', 'b , 'c']) resulta em [(1, 'a'), (2, 'b'), (3, 'c')]

# enumerate(): Uma função que adiciona um contador automático a um iterável, retornando pares de índice e valor.

# Exemplo: enumerate(['a', 'b', 'c']) resulta em [(0, 'a'), (1, 'b'), (2, 'c')]

# with: Uma declaração que simplifica o gerenciamento de recursos, garantindo que eles sejam corretamente adquiridos e liberados, como arquivos ou conexões de rede.

# Exemplo: with open('arquivo.txt', 'r') as f: lê o arquivo e fecha automaticamente após o bloco.

# yield: Usado em funções geradoras para produzir uma série de valores ao longo do tempo, permitindo a iteração sobre esses valores sem armazená-los todos na memória de uma vez.

# Exemplo: def contador(): for i in range(5): yield i  cria um gerador que produz números de 0 a 4.

# Exemplos práticos combinando vários conceitos acima:

# def coletar_dados(): 

#   nome = input("Digite seu nome: ").strip()
#   idade = int(input("Digite sua idade: ").strip())
#   if idade < 18:
#       raise ValueError("Idade deve ser maior ou igual a 18 anos.")
#   return nome, idade
# try:
#   nome, idade = coletar_dados()
#   print(f"Nome: {nome}, Idade: {idade}")
# except ValueError as e:
#   print(f"Erro: {e}")

# OBS: Esses são apenas alguns dos muitos conceitos e funcionalidades do Python. 
# A linguagem é rica e possui diversas outras características que podem ser exploradas conforme o desenvolvimento progride.

# FIM DOS CONCEITOS DA LINGUAGEM DE PROGRAMAÇÃO PYTHON---------------******////%%!!!]]
# Novo conceito em python: Programação Orientada a Objetos (POO) com classes e objetos.
# Uma classe é um molde para criar objetos (instâncias) que agrupam dados e funcionalidades relacionadas.
# Exemplo prático de uma classe em Python:
class Pessoa:
    def __init__(self, nome, idade):
        self.nome = nome  # Atributo de instância
        self.idade = idade  # Atributo de instância

    def apresentar(self):
        return f"Olá, meu nome é {self.nome} e tenho {self.idade} anos."
# Criando um objeto (instância) da classe Pessoa
pessoa1 = Pessoa("Iago", 30)
# Acessando atributos e chamando um método
print(pessoa1.nome)  # Saída: Iago
print(pessoa1.apresentar())  # Saída: Olá, meu nome é Iago e tenho 30 anos.
# Fim do exemplo prático de POO com classes e objetos em Python.

# Outros conceitos importantes em POO:
# Herança: Permite criar uma nova classe baseada em uma classe existente, herdando seus atributos e métodos.
# Polimorfismo: Permite que diferentes classes tenham métodos com o mesmo nome, mas comportamentos diferentes.
# Encapsulamento: Restringe o acesso direto a alguns componentes de um objeto, promovendo a modularidade e a proteção dos dados.
# Abstração: Permite focar nos aspectos essenciais de um objeto, ocultando detalhes complexos.
# Esses conceitos ajudam a organizar e estruturar o código de forma mais eficiente e reutilizável.
# Fim dos conceitos de POO em Python.

# exemplo de estrutura para iniciar qualquer prejeto em python com classes e objetos
class Projeto:
    def __init__(self, nome):
        self.nome = nome

    def iniciar(self):
        print(f"Projeto {self.nome} iniciado!")

    def finalizar(self):
        print(f"Projeto {self.nome} finalizado!")
meu_projeto = Projeto("Meu Primeiro Projeto")
meu_projeto.iniciar()
meu_projeto.finalizar()
# Fim do exemplo de estrutura para iniciar qualquer projeto em python com classes e objetos.
# exemplo de estrutura para resolver qualquer problema em python com classes e objetos
class SolucionadorDeProblemas:
    def __init__(self, problema):
        self.problema = problema

    def analisar(self):
        print(f"Analisando o problema: {self.problema}")

    def resolver(self):
        print(f"Resolvendo o problema: {self.problema}")

    def relatar(self):
        print(f"Relatório do problema: {self.problema} resolvido com sucesso!")
meu_problema = SolucionadorDeProblemas("Erro de Conexão")
meu_problema.analisar()
meu_problema.resolver()
meu_problema.relatar()
# Fim do exemplo de estrutura para resolver qualquer problema em python com classes e objetos.
# exemplo de estrutura com interface gráfica usando classes e objetos em python
import customtkinter as ctk
# Define a aparência padrão (dark, light, system)
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
# Cria a janela principal
janela = (ctk.CTk())
janela.title("Interface Gráfica com POO")
janela.geometry("400x300")
# Define uma classe para a aplicação
class Aplicacao:
    def __init__(self, janela):
        self.janela = janela
        self.janela.title("Interface Gráfica com POO")
        self.janela.geometry("400x300")
        self.label = ctk.CTkLabel(janela, text="Olá, Mundo!", font=("Arial", 24))
        self.label.pack(pady=20)
        self.botao = ctk.CTkButton(janela, text="Clique Aqui", command=self.mudar_texto)
        self.botao.pack(pady=10)
    def mudar_texto(self):
        self.label.configure(text="Você clicou no botão!")
# Cria uma instância da classe Aplicacao
aplicacao = Aplicacao(janela)
# Inicia o loop principal da interface gráfica
janela.mainloop()
# Fim do exemplo de estrutura com interface gráfica usando classes e objetos em python.
# exemplo de estrurura de framework flet com classes e objetos em python
import flet as ft
class MyApp(ft.controls.UserControl):
    def build(self):
        return ft.Column(
            [
                ft.Text("Olá, Mundo!", size=30),
                ft.ElevatedButton("Clique Aqui", on_click=self.on_button_click),
            ]
        )
    def on_button_click(self, e):
        self.page.add(ft.Text("Você clicou no botão!"))
def main(page: ft.Page):
    app = MyApp()
    page.add(app)
    page.update()
ft.app(target=main)
# Fim do exemplo de estrutura de framework flet com classes e objetos em python.
# exemplo prático combinando vários conceitos acima em python com classes e objetos
import flet as ft
class MyApp(ft.UserControl):
    def __init__(self, page):
        super().__init__()
        self.page = page
    def build(self):
        return ft.Column(
            [
                ft.Text("Olá, Mundo!", size=30),
                ft.ElevatedButton("Clique Aqui", on_click=self.on_button_click),
            ]
        )
    def on_button_click(self, e):
        self.page.add(ft.Text("Você clicou no botão!")) 
def main(page: ft.Page):
    app = MyApp()
    page.add(app)
    page.update()
ft.app(target=main)
# Fim do exemplo prático combinando vários conceitos acima em python com classes e objetos.
# dominar lista ,dicionario e tuplas em python
# listas: são coleções mutáveis que armazenam múltiplos itens em uma única variável
minha_lista = [1, 2, 3, "quatro", "cinco"]
minha_lista.append(6)  # Adiciona um item ao final da lista
print(minha_lista)  # Saída: [1, 2, 3, 'quatro', 'cinco', 6]
# dicionários: são coleções mutáveis que armazenam pares de chave-valor
meu_dicionario = {"nome": "Iago", "idade": 30, "cidade": "São Paulo"}
meu_dicionario["profissão"] = "Desenvolvedor"  # Adiciona um novo par chave-valor
print(meu_dicionario)  # Saída: {'nome': 'Iago', 'idade': 30, 'cidade': 'São Paulo', 'profissão': 'Desenvolvedor'}
# tuplas: são coleções imutáveis que armazenam múltiplos itens em uma única variável
minha_tupla = (1, 2, 3, "quatro", "cinco")
print(minha_tupla)  # Saída: (1, 2, 3, 'quatro', 'cinco')
# Fim do exemplo prático de listas, dicionários e tuplas em python.
minha_lista = [] 
meu_dicionario = {}
minha_tupla = ()
lista_de_listas = [[1, 2], [3, 4], [5, 6]]
dicionario_de_dicionarios = {"pessoa1": {"nome": "Iago", "idade": 30}, "pessoa2": {"nome": "Ana", "idade": 25}}
tupla_de_tuplas = ((1, 2), (3, 4), (5, 6))
# como selecionar o indinci de de uma lista ,dicionario e tuplas em python
print(minha_lista[0])  # Acessa o primeiro item da lista
print(meu_dicionario["nome"])  # Acessa o valor associado à chave "nome"
print(minha_tupla[0])  # Acessa o primeiro item da tupla
# Fim do exemplo prático de como selecionar o índice de listas, dicionários e tuplas em python.
# como modificar e excluir o indinci de de uma lista ,dicionario e tuplas em python
minha_lista[0] = "novo valor"  # Modifica o primeiro item da lista
del meu_dicionario["idade"]  # Exclui o par chave-valor associado à chave "idade"
# Tuplas são imutáveis, então não podem ser modificadas diretamente
# usando o o loop for em listas ,dicionario e tuplas em python
for item in minha_lista:
    print(item)  # Itera sobre cada item na lista
for chave, valor in meu_dicionario.items():
    print(f"{chave}: {valor}")  # Itera sobre cada par chave-valor no dicionário
for item in minha_tupla:
    print(item)  # Itera sobre cada item na tupla
# tipos de parametros para for em listas ,dicionario e tuplas em python
for i in range(len(minha_lista)):
    print(minha_lista[i])  # Acessa cada item da lista usando o índice
for chave in meu_dicionario:
    print(f"{chave}: {meu_dicionario[chave]}")  # Acessa cada valor do dicionário usando a chave
for i in range(len(minha_tupla)):
    print(minha_tupla[i])  # Acessa cada item da tupla usando o índice
# outros parametros como enumerate e zip em listas ,dicionario e tuplas em python
for indice, item in enumerate(minha_lista):
    print(f"Índice {indice}: {item}")  # Acessa cada item da lista com seu índice
for chave, valor in meu_dicionario.items():
    print(f"{chave}: {valor}")  # Acessa cada par chave-valor no dicionário
for item1, item2 in zip(minha_tupla, minha_lista):
    print(f"Tupla: {item1}, Lista: {item2}")  # Acessa itens correspondentes da tupla e da lista
# assim como o break , continue ,pass , return em listas ,dicionario e tuplas em python
for item in minha_lista:
    if item == "pular":
        continue  # Pula para a próxima iteração
    if item == "parar":
        break  # Encerra o loop
    print(item)
def exemplo_pass():
    pass  # Placeholder para código futuro
def exemplo_return():
    return "Valor retornado"
print(exemplo_return())  # Chama a função e imprime o valor retornado
# isso tanto para o while em listas ,dicionario e tuplas em python
contador = 0
while contador < 5:
    print(contador)
    contador += 1
    if contador == 3:
        break  # Encerra o loop quando o contador for 3
    elif contador == 2:
        continue  # Pula para a próxima iteração
def exemplo_pass_while():
    pass  # Placeholder para código futuro
def exemplo_return_while():
    return "Valor retornado do while"
print(exemplo_return_while())  # Chama a função e imprime o valor retornado
#vamos ver exemplos do iterables em python com listas ,dicionario e tuplas em python

# listas minha_lista = [1, 2, 3, 4, 5]
iterador_lista = iter(minha_lista)
print(next(iterador_lista))  # Saída: 1
print(next(iterador_lista))  # Saída: 2

# dicionários meu_dicionario = {"a": 1, "b": 2, "c": 3}
iterador_dicionario = iter(meu_dicionario)  # Isso itera pelas chaves
print(next(iterador_dicionario))  # Saída: "a"
print(next(iterador_dicionario))  # Saída: "b"

# tuplas minha_tupla = (1, 2, 3, 4, 5)
iterador_tupla = iter(minha_tupla)
print(next(iterador_tupla))  # Saída: 1
print(next(iterador_tupla))  # Saída: 2
# Fim dos exemplos do iterables em python com listas ,dicionario e tuplas em python.

#exemplos para dominar dados em python com listas ,dicionario e tuplas em python usando o pandas
import pandas as pd
# Criando uma lista
minha_lista = [1, 2, 3, 4, 5]
serie_lista = pd.Series(minha_lista)
print(serie_lista)  # Converte a lista em uma Series do pandas
# Criando um dicionário 
meu_dicionario = {"nome": ["Iago", "Ana"], "idade": [30, 25]}
dataframe_dicionario = pd.DataFrame(meu_dicionario)
print(dataframe_dicionario)  # Converte o dicionário em um DataFrame do pandas
# Criando uma tupla
minha_tupla = (1, 2, 3, 4, 5)
serie_tupla = pd.Series(minha_tupla)
print(serie_tupla)  # Converte a tupla em uma Series do pandas
# analisando dados com pandas em python buscando dados de uma planilha excel
# Carregando dados de um arquivo Excel
dataframe_excel = pd.read_excel("dados.xlsx")
print(dataframe_excel.head())  # Exibe as primeiras linhas do DataFrame
# Filtrando dados
dados_filtrados = dataframe_excel[dataframe_excel["idade"] > 25]
print(dados_filtrados)  # Exibe os dados filtrados
# Estatísticas descritivas
estatisticas = dataframe_excel.describe()
print(estatisticas)  # Exibe estatísticas descritivas dos dados

#--------------------------------------------------------@##-----------------------------------------
# exemplo de como criar modelos de IA avançados em python com listas ,dicionario e tuplas em python usando o pandas e sklearn
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
# Suponha que temos um DataFrame com dados
data = {"idade": [25, 30, 35, 40, 45], "salario": [3000, 4000, 5000, 6000, 7000]}
df = pd.DataFrame(data) 
X = df[["idade"]]  # Variável independente
y = df["salario"]  # Variável dependente
# Dividindo os dados em conjunto de treino e teste
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
# Criando o modelo de regressão linear
modelo = LinearRegression()
modelo.fit(X_train, y_train)  # Treinando o modelo
# Fazendo previsões
previsoes = modelo.predict(X_test)
print(previsoes)  # Exibe as previsões

# aumentando a criação do modelo de IA usando um Support Vector Machine (SVM)
from sklearn.svm import SVR
# Criando o modelo SVM
modelo_svm = SVR(kernel='linear')
modelo_svm.fit(X_train, y_train)  # Treinando o modelo SVM
# Fazendo previsões com o modelo SVM
previsoes_svm = modelo_svm.predict(X_test)
print(previsoes_svm)  # Exibe as previsões do modelo SVM 

# criando um modelo de IA usando um SGDB especifico que foca em grandes volumes de dados
from sklearn.linear_model import SGDRegressor
# Criando o modelo SGDR
modelo_sgdr = SGDRegressor(max_iter=1000, tol=1e-3)
modelo_sgdr.fit(X_train, y_train)  # Treinando o modelo SGDR
# Fazendo previsões com o modelo SGDR
previsoes_sgdr = modelo_sgdr.predict(X_test)
print(previsoes_sgdr)  # Exibe as previsões do modelo SGDR


