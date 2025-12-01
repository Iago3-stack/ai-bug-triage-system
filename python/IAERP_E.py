import pandas as pd
from sklearn.preprocessing import LabelEncoder
# Importamos a ferramenta de Machine Learning: Regressão Logística
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

# ------------------------------------------------
# SIMULAÇÃO DE DADOS DE UM E-COMMERCE (INPUT)
# ------------------------------------------------

dados = {
    'cliente_id': [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
    'regiao': ['Sul', 'Sudeste', 'Nordeste', 'Sul', 'Sudeste', 'Nordeste', 'Sul', 'Sudeste', 'Nordeste', 'Sudeste'],
    'plano': ['Premium', 'Básico', 'Premium', 'Premium', 'Básico', 'Premium', 'Básico', 'Premium', 'Básico', 'Básico'],
    # A Variável Alvo (Y): 1 se o cliente cancelou, 0 se não cancelou
    'churn': [0, 1, 0, 1, 0, 0, 1, 0, 1, 0] 
}

# Cria o DataFrame (a tabela)
df = pd.DataFrame(dados)
print("--- Módulo de Gestão de Clientes - V1.0 ---")
print("1. Tabela Original (Dados Categóricos):\n", df)

# ------------------------------------------------
# PRÉ-PROCESSAMENTO (ETAPA ESSENCIAL DO SEU ERP)
# ------------------------------------------------

label_encoder = LabelEncoder()

# Codificação das variáveis categóricas para NÚMEROS (ML só entende números)
df['regiao_codificada'] = label_encoder.fit_transform(df['regiao'])
df['plano_codificado'] = label_encoder.fit_transform(df['plano'])

# ------------------------------------------------
# TREINAMENTO DO MODELO (O "AI" DO SEU ERP)
# ------------------------------------------------

# Definimos as Variáveis Preditivas (X) e a Variável Alvo (Y)
# X (Características): 'regiao' e 'plano' codificados.
X = df[['regiao_codificada', 'plano_codificado']]
# Y (O que queremos prever): 'churn' (cancelamento)
Y = df['churn']

# Normalmente separamos em treino e teste, mas aqui vamos usar todos os dados para simplificar.

# 1. Cria a instância do Algoritmo de Regressão Logística
modelo = LogisticRegression()

# 2. TREINA o modelo com os dados (Aprende os padrões)
# O modelo aprende: se 'regiao_codificada' for X e 'plano_codificado' for Y, a chance de 'churn' é Z.
modelo.fit(X, Y)

print("\n2. Modelo de Previsão de CHURN TREINADO com Sucesso.")

# ------------------------------------------------
# PREVISÃO (TOMADA DE DECISÃO DO ERP)
# ------------------------------------------------

# SIMULAÇÃO: Criamos um NOVO CLIENTE que o modelo nunca viu.
# Novo Cliente: Região Sudeste (codificada como 1) e Plano Básico (codificado como 0)

novo_cliente = pd.DataFrame({
    'regiao_codificada': [1],  
    'plano_codificado': [0]
})

# O modelo faz a PREVISÃO
previsao = modelo.predict(novo_cliente)

print("\n3. Previsão de Churn para NOVO CLIENTE:")

if previsao[0] == 1:
    print("   PREVISÃO DO MODELO: ALTO RISCO DE CANCELAMENTO (CHURN = 1)")
    print("   Ação Sugerida pelo ERP: Enviar uma oferta especial.")
else:
    print("   PREVISÃO DO MODELO: BAIXO RISCO DE CANCELAMENTO (CHURN = 0)")
    print("   Ação Sugerida pelo ERP: Monitoramento normal.")

# ------------------------------------------------
# RESULTADO FINAL PRONTO PARA O MODELO (OUTPUT)
# ------------------------------------------------

# A tabela final, que foi usada para o treinamento, é a seguinte:
print("\n4. Tabela Final Usada no Treinamento:")
print(df[['cliente_id', 'regiao_codificada', 'plano_codificado', 'churn']])
