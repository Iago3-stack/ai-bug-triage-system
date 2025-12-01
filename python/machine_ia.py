import pandas as pd
from sklearn.preprocessing import LabelEncoder

# ------------------------------------------------
# SIMULAÇÃO DE DADOS DE UM E-COMMERCE (INPUT)
# ------------------------------------------------

dados = {
    'cliente_id': [101, 102, 103, 104, 105, 106],
    'regiao': ['Sul', 'Sudeste', 'Nordeste', 'Sul', 'Sudeste', 'Nordeste'],
    'plano': ['Premium', 'Básico', 'Premium', 'Premium', 'Básico', 'Premium'],
    # 'Churn' é a variável alvo: 1 se o cliente cancelou, 0 se não cancelou
    'churn': [0, 1, 0, 1, 0, 0] 
}

# Cria o DataFrame (a tabela)
df = pd.DataFrame(dados)
print("--- 1. Tabela Original (Dados Categóricos) ---")
print(df)
print("\n")


# ------------------------------------------------
# PRÉ-PROCESSAMENTO PARA MACHINE LEARNING (ALGORITMO)
# ------------------------------------------------

# Modelos de Machine Learning só trabalham com NÚMEROS.
# Precisamos transformar as colunas 'regiao' e 'plano' em números.

label_encoder = LabelEncoder()

# 1. Aplicando Label Encoding na coluna 'regiao'
# Exemplo: 'Sul' -> 2, 'Sudeste' -> 1, 'Nordeste' -> 0
df['regiao_codificada'] = label_encoder.fit_transform(df['regiao'])

# 2. Aplicando Label Encoding na coluna 'plano'
# Exemplo: 'Premium' -> 1, 'Básico' -> 0
df['plano_codificado'] = label_encoder.fit_transform(df['plano'])


# ------------------------------------------------
# RESULTADO PRONTO PARA O MODELO (OUTPUT)
# ------------------------------------------------

# Mantemos apenas as colunas numéricas necessárias para treinar o modelo
df_final = df[['cliente_id', 'regiao_codificada', 'plano_codificado', 'churn']]

print("--- 2. Tabela Codificada (Pronta para o ML) ---")
print(df_final)

# Agora, o modelo de ML pode usar as colunas 'regiao_codificada' e 'plano_codificado'
# para tentar prever o 'churn' (cancelamento).
