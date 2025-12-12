# correlacao.py
import mysql.connector
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, spearmanr
from datetime import datetime
import json

# Configurações do banco de dados
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'password',
    'database': 'iot_db'
}

def get_db_connection():
    """Estabelece conexão com o banco de dados"""
    return mysql.connector.connect(**DB_CONFIG)

def carregar_dados(limite=1000):
    """Carrega dados do banco de dados"""
    try:
        conn = get_db_connection()
        
        query = """
            SELECT 
                temperatura_solo, umidade_solo, condutividade_solo, ph,
                npk_n, npk_p, npk_k,
                temperatura_ar, pressao, altitude, umidade_relativa,
                radiacao_solar, indice_uv, velocidade_vento, pluviometria_mm,
                altura_planta, biomassa_estimada, area_foliar_lai,
                producao_kg, cultura, estagio_fenologico
            FROM dados_solo
            WHERE producao_kg IS NOT NULL
            LIMIT %s
        """
        
        df = pd.read_sql(query, conn, params=(limite,))
        conn.close()
        
        print(f"Dados carregados: {df.shape[0]} registros")
        return df
        
    except Exception as e:
        print(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

def calcular_correlacoes(df, metodo='pearson'):
    """Calcula correlações entre todas as variáveis"""
    # Selecionar apenas colunas numéricas
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if 'producao_kg' not in numeric_cols:
        print("A variável 'producao_kg' não está presente ou não é numérica")
        return pd.DataFrame()
    
    # Remover colunas com muitos valores faltantes
    df_numeric = df[numeric_cols].dropna()
    
    if df_numeric.empty:
        print("Dados insuficientes após remoção de valores nulos")
        return pd.DataFrame()
    
    # Calcular matriz de correlação
    if metodo == 'pearson':
        corr_matrix = df_numeric.corr(method='pearson')
    elif metodo == 'spearman':
        corr_matrix = df_numeric.corr(method='spearman')
    else:
        print(f"Método {metodo} não suportado. Usando Pearson.")
        corr_matrix = df_numeric.corr(method='pearson')
    
    return corr_matrix

def analisar_correlacoes_producao(df):
    """Análise detalhada das correlações com produção"""
    if 'producao_kg' not in df.columns:
        print("Variável produção não encontrada")
        return pd.DataFrame()
    
    resultados = []
    
    # Lista de variáveis para análise
    variaveis = [
        'temperatura_solo', 'umidade_solo', 'condutividade_solo', 'ph',
        'npk_n', 'npk_p', 'npk_k',
        'temperatura_ar', 'umidade_relativa', 'radiacao_solar',
        'altura' 
        ]