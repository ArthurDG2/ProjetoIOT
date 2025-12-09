# anova.py
import mysql.connector
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import scipy.stats as stats
from scipy.stats import f_oneway, kruskal, shapiro, levene
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.libqsturng import psturng
import pingouin as pg
from itertools import combinations
import json
from datetime import datetime

# Configurações do banco de dados
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'password',
    'database': 'iot_db'
}

# Configurações de visualização
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def get_db_connection():
    """Estabelece conexão com o banco de dados"""
    return mysql.connector.connect(**DB_CONFIG)

def carregar_dados_anova():
    """Carrega dados para análise ANOVA"""
    try:
        conn = get_db_connection()
        
        query = """
            SELECT 
                producao_kg,
                estagio_fenologico,
                cultura,
                temperatura_solo,
                umidade_solo,
                ph,
                npk_n,
                altura_planta,
                CASE 
                    WHEN umidade_solo < 20 THEN 'Muito Seco'
                    WHEN umidade_solo BETWEEN 20 AND 35 THEN 'Seco'
                    WHEN umidade_solo BETWEEN 35 AND 50 THEN 'Ideal'
                    WHEN umidade_solo BETWEEN 50 AND 65 THEN 'Úmido'
                    ELSE 'Muito Úmido'
                END as categoria_umidade,
                CASE 
                    WHEN ph < 5.5 THEN 'Muito Ácido'
                    WHEN ph BETWEEN 5.5 AND 6.5 THEN 'Levemente Ácido'
                    WHEN ph BETWEEN 6.5 AND 7.5 THEN 'Neutro'
                    WHEN ph > 7.5 THEN 'Alcalino'
                END as categoria_ph,
                CASE 
                    WHEN temperatura_solo < 18 THEN 'Frio'
                    WHEN temperatura_solo BETWEEN 18 AND 25 THEN 'Ideal'
                    WHEN temperatura_solo BETWEEN 25 AND 30 THEN 'Quente'
                    ELSE 'Muito Quente'
                END as categoria_temperatura
            FROM dados_solo
            WHERE producao_kg IS NOT NULL
            AND estagio_fenologico IS NOT NULL
            AND cultura IS NOT NULL
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        print(f"Dados carregados: {df.shape[0]} registros")
        print(f"Variáveis categóricas disponíveis: {df.select_dtypes(include=['object']).columns.tolist()}")
        
        return df
        
    except Exception as e:
        print(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

def verificar_pressupostos_anova(df, grupo_col, valor_col):
    """Verifica os pressupostos para ANOVA"""
    print("\n" + "="*80)
    print(f"VERIFICAÇÃO DOS PRESSUPOSTOS PARA ANOVA")
    print(f"Grupo: {grupo_col}, Variável: {valor_col}")
    print("="*80)
    
    resultados = {}
    
    # 1. Normalidade (Shapiro-Wilk para cada grupo)
    grupos = df[grupo_col].unique()
    normalidades = []
    
    print(f"\n1. TESTE DE NORMALIDADE (Shapiro-Wilk) - α = 0.05")
    print("-" * 50)
    
    for grupo in grupos:
        dados_grupo = df[df[grupo_col] == grupo][valor_col]
        
        if len(dados_grupo) >= 3:  # Shapiro-Wilk requer mínimo 3 observações
            stat, p_valor = shapiro(dados_grupo)
            normalidades.append(p_valor > 0.05)
            
            print(f"  Grupo '{grupo}':")
            print(f"    n = {len(dados_grupo)}")
            print(f"    W = {stat:.4f}")
            print(f"    p-valor = {p_valor:.4f}")
            print(f"    Normal? {'SIM' if p_valor > 0.05 else 'NÃO'}")
        else:
            print(f"  Grupo '{grupo}': Dados insuficientes (n < 3)")
    
    resultados['normalidade'] = all(normalidades) if normalidades else False
    print(f"\n  Conclusão: Dados {'NORMAL' if resultados['normalidade'] else 'NÃO NORMAL'} distribuídos")
    
    # 2. Homogeneidade de variâncias (Levene)
    print(f"\n2. HOMOGENEIDADE DE VARIÂNCIAS (Levene)")
    print("-" * 50)
    
    grupos_dados = [df[df[grupo_col] == g][valor_col].dropna() for g in grupos]
    
    if len(grupos_dados) >= 2:
        stat, p_valor = levene(*grupos_dados)
        resultados['homocedasticidade'] = p_valor > 0.05
        
        print(f"  Estatística W = {stat:.4f}")
        print(f"  p-valor = {p_valor:.4f}")
        print(f"  Variâncias homogêneas? {'SIM' if p_valor > 0.05 else 'NÃO'}")
    else:
        resultados['homocedasticidade'] = False
        print("  Número insuficiente de grupos para teste de Levene")
    
    # 3. Independência das observações (pressuposto do estudo)
    print(f"\n3. INDEPENDÊNCIA DAS OBSERVAÇÕES")
    print("-" * 50)
    print("  Pressuposto: Observações independentes (estudo transversal)")
    resultados['independencia'] = True
    
    # 4. Tamanho das amostras
    print(f"\n4. TAMANHO DAS AMOSTRAS")
    print("-" * 50)
    
    tamanhos = []
    for grupo in grupos:
        n = len(df[df[grupo_col] == grupo])
        tamanhos.append(n)
        print(f"  Grupo '{grupo}': n = {n}")
    
    resultados['tamanho_amostral'] = all(n >= 5 for n in tamanhos)
    print(f"\n  Todos os grupos têm n ≥ 5? {'SIM' if resultados['tamanho_amostral'] else 'NÃO'}")
    
    return resultados

def anova_um_fator(df, grupo_col, valor_col):
    """ANOVA de um fator"""
    print("\n" + "="*80)
    print(f"ANOVA DE UM FATOR")
    print(f"Fator: {grupo_col}")
    print(f"Variável Dependente: {valor_col}")
    print("="*80)
    
    # Verificar pressupostos
    pressupostos = verificar_pressupostos_anova(df, grupo_col, valor_col)
    
    # Preparar dados
    grupos = df[grupo_col].unique()
    grupos_dados = [df[df[grupo_col] == g][valor_col].dropna() for g in grupos]
    
    # 1. ANOVA paramétrica (One-way ANOVA)
    print("\n" + "="*80)
    print("ANOVA PARAMÉTRICA (One-way ANOVA)")
    print("="*80)
    
    if len(grupos_dados) >= 2:
        # Realizar ANOVA
        f_stat, p_valor = f_oneway(*grupos_dados)
        
        print(f"\nResultados da ANOVA:")
        print(f"  F({len(grupos)-1}, {df[valor_col].count()-len(grupos)}) = {f_stat:.4f}")
        print(f"  p-valor = {p_valor:.4f}")
        print(f"  Diferenças significativas? {'SIM' if p_valor < 0.05 else 'NÃO'}")
        
        # Calcular tamanho do efeito (eta quadrado)
        # SST (Soma total dos quadrados)
        total_mean = df[valor_col].mean()
        sst = ((df[valor_col] - total_mean) ** 2).sum()
        
        # SSB (Soma dos quadrados entre grupos)
        group_means = df.groupby(grupo_col)[valor_col].mean()
        group_counts = df.groupby(grupo_col)[valor_col].count()
        ssb = ((group_means - total_mean) ** 2 * group_counts).sum()
        
        eta_squared = ssb / sst
        
        print(f"\nTamanho do Efeito:")
        print(f"  η² (eta quadrado) = {eta_squared:.4f}")
        print(f"  Interpretação: ")
        if eta_squared < 0.01:
            print(f"    Efeito muito pequeno")
        elif eta_squared < 0.06:
            print(f"    Efeito pequeno")
        elif eta_squared < 0.14:
            print(f"    Efeito médio")
        else:
            print(f"    Efeito grande")
        
        # Post-hoc (Tukey HSD) se ANOVA significativa
        if p_valor < 0.05:
            print("\n" + "="*80)
            print("TESTE POST-HOC (Tukey HSD)")
            print("="*80)
            
            try:
                tukey = pairwise_tukeyhsd(
                    endog=df[valor_col].dropna(),
                    groups=df[grupo_col].dropna(),
                    alpha=0.05
                )
                
                print(tukey.summary())
                
                # Salvar resultados do Tukey
                tukey_df = pd.DataFrame(data=tukey._results_table.data[1:], 
                                      columns=tukey._results_table.data[0])
                tukey_df.to_csv(f'resultados_anova/tukey_{grupo_col}.csv', index=False)
                
            except Exception as e:
                print(f"Erro no teste Tukey: {e}")
                
                # Alternativa: Teste t pareado com correção de Bonferroni
                print("\nTeste t pareado com correção de Bonferroni:")
                pares = list(combinations(grupos, 2))
                
                resultados_t = []
                for grupo1, grupo2 in pares:
                    dados1 = df[df[grupo_col] == grupo1][valor_col]
                    dados2 = df[df[grupo_col] == grupo2][valor_col]
                    
                    t_stat, p_valor_t = stats.ttest_ind(dados1, dados2, equal_var=pressupostos['homocedasticidade'])
                    
                    # Correção de Bonferroni
                    p_ajustado = min(p_valor_t * len(pares), 1.0)
                    
                    resultados_t.append({
                        'Grupo1': grupo1,
                        'Grupo2': grupo2,
                        't': t_stat,
                        'p_original': p_valor_t,
                        'p_ajustado': p_ajustado,
                        'Significativo': p_ajustado < 0.05
                    })
                
                resultados_t_df = pd.DataFrame(resultados_t)
                print(resultados_t_df.to_string(index=False))
        
    else:
        print("Número insuficiente de grupos para ANOVA")
        f_stat, p_valor, eta_squared = None, None, None
    
    # 2. ANOVA não paramétrica (Kruskal-Wallis) se pressupostos violados
    print("\n" + "="*80)
    print("ANOVA NÃO PARAMÉTRICA (Kruskal-Wallis)")
    print("="*80)
    
    if len(grupos_dados) >= 2:
        h_stat, p_valor_kw = kruskal(*grupos_dados)
        
        print(f"\nResultados do Kruskal-Wallis:")
        print(f"  H = {h_stat:.4f}")
        print(f"  p-valor = {p_valor_kw:.4f}")
        print(f"  Diferenças significativas? {'SIM' if p_valor_kw < 0.05 else 'NÃO'}")
        
        # Tamanho do efeito (epsilon quadrado)
        n_total = sum(len(g) for g in grupos_dados)
        epsilon_squared = (h_stat - (len(grupos) - 1)) / (n_total - len(grupos))
        
        print(f"\nTamanho do Efeito:")
        print(f"  ε² (epsilon quadrado) = {epsilon_squared:.4f}")
    