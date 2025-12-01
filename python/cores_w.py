# Importa a biblioteca necessária para codificar os dados
from sklearn.preprocessing import LabelEncoder

# Lista original de cores (dados categóricos)
cor = ['branco', 'preto', 'amarelo', 'amarelo', 'vermelho', 'branco', 'preto', 'preto']

# Cria uma instância (objeto) do LabelEncoder
label_encoder = LabelEncoder()

# --- Etapa 1: Codificar os dados ---
# O método fit_transform aprende as categorias da lista 'cor' e transforma em valores numéricos.
# 'branco' -> 0
# 'preto' -> 1
# 'amarelo' -> 2
# 'vermelho' -> 3
valores_numericos = label_encoder.fit_transform(cor)

print("Valores numéricos codificados:")
print(valores_numericos)
print("Valores únicos: ", set(valores_numericos))

# --- Etapa 2: Decodificar um valor ---
# O método inverse_transform() transforma um valor numérico de volta para a categoria original.
# Se passarmos o número 2, ele irá retornar 'amarelo', pois foi o valor que a biblioteca atribuiu a essa cor.
valor_real = label_encoder.inverse_transform([2])

print("\nValor decodificado para o número 2:")
print(valor_real)
