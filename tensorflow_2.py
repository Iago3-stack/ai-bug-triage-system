import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler

def criar_e_treinar_modelo():
    """
    Cria um modelo de recomendação simplificado usando dados fictícios.
    """
    
    print("--- 1. Carregando Dados de Exemplo ---")
    # Dados fictícios: Usuários (linhas) vs Filmes (colunas), valores são avaliações (1 a 5)
    # NaN significa que o usuário não avaliou o filme.
    data = {
        'User': ['Alice', 'Bob', 'Charlie', 'David', 'Eva'],
        'Filme A': [5, 4, np.nan, 4, np.nan],
        'Filme B': [3, np.nan, 5, 3, 4],
        'Filme C': [4, 5, 4, np.nan, 5],
        'Filme D': [np.nan, 3, np.nan, 5, 3],
        'Filme E': [4, 4, 5, 4, 5],
    }
    df = pd.DataFrame(data).set_index('User')
    print("Dados de Avaliações:")
    print(df)
    
    # Preencher valores NaN com a média das avaliações do filme para o cálculo de similaridade
    df_filled = df.fillna(df.mean(axis=0))

    print("\n--- 2. Calculando Similaridade entre Usuários ---")
    # Calculamos a similaridade de cosseno para ver quem tem gostos parecidos
    user_similarity = cosine_similarity(df_filled)
    user_similarity_df = pd.DataFrame(user_similarity, index=df.index, columns=df.index)
    print("Matriz de Similaridade de Usuários:")
    print(user_similarity_df)

    # Escalando os dados (prática comum em ML para normalizar as notas)
    scaler = StandardScaler()
    df_scaled = pd.DataFrame(scaler.fit_transform(df_filled), index=df.index, columns=df.columns)
    
    return df, user_similarity_df, df_scaled

def recomendar_para_usuario(usuario_alvo, df_original, user_similarity_df, df_scaled):
    """
    Gera recomendações para um usuário específico.
    """
    print(f"\n--- 3. Gerando Recomendações para '{usuario_alvo}' ---")

    # Encontrar os 2 usuários mais similares ao usuário alvo (excluindo ele mesmo)
    # Ordena a similaridade de forma descendente e pega os top_n (2)
    similar_users = user_similarity_df[usuario_alvo].sort_values(ascending=False)
    similar_users = similar_users[similar_users.index != usuario_alvo]
    top_n_similar_users = similar_users.head(2)
    
    print(f"Usuários mais similares a {usuario_alvo}:")
    print(top_n_similar_users)

    # Identificar filmes que o usuário alvo AINDA NÃO viu
    filmes_nao_vistos = df_original.loc[usuario_alvo][df_original.loc[usuario_alvo].isna()].index.tolist()
    print(f"\nFilmes que {usuario_alvo} ainda não viu: {filmes_nao_vistos}")

    # Calcular uma pontuação preditiva para os filmes não vistos
    # Multiplica a avaliação dos usuários similares pela similaridade deles
    recommendations = {}
    for filme in filmes_nao_vistos:
        score = 0
        total_similarity = 0
        for similar_user, similarity_score in top_n_similar_users.items():
            # Pega a nota escalada do usuário similar para o filme não visto
            rating = df_scaled.loc[similar_user, filme]
            score += rating * similarity_score
            total_similarity += similarity_score
        
        if total_similarity > 0:
            # Calcula a média ponderada
            recommendations[filme] = score / total_similarity
        else:
            recommendations[filme] = 0

    # Ordenar recomendações pela pontuação preditiva (maior primeiro)
    sorted_recommendations = sorted(recommendations.items(), key=lambda item: item[1], reverse=True)
    
    print(f"\nRecomendações finais para {usuario_alvo}:")
    for filme, pontuacao in sorted_recommendations:
        print(f" - {filme}: Pontuação Preditiva: {pontuacao:.2f}")

# --- Execução Principal ---
if __name__ == "__main__":
    df_original, user_similarity_df, df_scaled = criar_e_treinar_modelo()
    
    # Teste o modelo para a Alice, que não viu o Filme C nem o Filme D
    recomendar_para_usuario('Alice', df_original, user_similarity_df, df_scaled)
