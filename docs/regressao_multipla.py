# regressao_multipla.py
import mysql.connector
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
import joblib
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

def carregar_dados_regressao():
    """Carrega dados para análise de regressão múltipla"""
    try:
        conn = get_db_connection()
        
        query = """
            SELECT 
                temperatura_solo, umidade_solo, condutividade_solo, ph,
                npk_n, npk_p, npk_k,
                temperatura_ar, umidade_relativa, radiacao_solar,
                velocidade_vento, pluviometria_mm,
                altura_planta, biomassa_estimada, area_foliar_lai,
                producao_kg
            FROM dados_solo
            WHERE producao_kg IS NOT NULL
            AND temperatura_solo IS NOT NULL
            AND umidade_solo IS NOT NULL
            AND ph IS NOT NULL
            AND npk_n IS NOT NULL
            AND altura_planta IS NOT NULL
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        print(f"Dados carregados: {df.shape[0]} registros, {df.shape[1]} variáveis")
        print(f"Variáveis: {list(df.columns)}")
        
        return df
        
    except Exception as e:
        print(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

def preparar_dados(df, target_col='producao_kg'):
    """Prepara dados para modelagem"""
    if df.empty:
        return None, None, None, None, None, None
    
    # Separar features e target
    X = df.drop(columns=[target_col])
    y = df[target_col]
    
    # Verificar valores nulos
    if X.isnull().any().any():
        print("Valores nulos encontrados nas features. Preenchendo com médias...")
        X = X.fillna(X.mean())
    
    # Dividir em treino e teste
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print(f"Treino: {X_train.shape[0]} amostras")
    print(f"Teste: {X_test.shape[0]} amostras")
    
    return X, y, X_train, X_test, y_train, y_test

def regressao_multipla_statsmodels(X, y):
    """Regressão múltipla usando statsmodels para estatísticas detalhadas"""
    print("\n" + "="*80)
    print("REGRESSÃO MÚLTIPLA - STATSMODELS")
    print("="*80)
    
    # Adicionar constante para o intercepto
    X_const = sm.add_constant(X)
    
    # Ajustar o modelo
    model = sm.OLS(y, X_const).fit()
    
    # Exibir resumo completo
    print(model.summary())
    
    # Salvar resumo em arquivo
    with open('resultados_regressao/resumo_modelo.txt', 'w') as f:
        f.write(str(model.summary()))
    
    # Calcular VIF para multicolinearidade
    print("\n" + "="*80)
    print("FATOR DE INFLACÃO DA VARIÂNCIA (VIF)")
    print("="*80)
    
    vif_data = pd.DataFrame()
    vif_data["Variável"] = X_const.columns
    vif_data["VIF"] = [variance_inflation_factor(X_const.values, i) 
                      for i in range(X_const.shape[1])]
    
    print(vif_data.to_string(index=False))
    
    # Interpretação do VIF
    print("\nInterpretação do VIF:")
    print("VIF < 5: Baixa multicolinearidade")
    print("5 ≤ VIF < 10: Multicolinearidade moderada")
    print("VIF ≥ 10: Alta multicolinearidade")
    
    return model, vif_data

def regressao_multipla_scikit(X_train, X_test, y_train, y_test):
    """Regressão múltipla usando scikit-learn com validação cruzada"""
    print("\n" + "="*80)
    print("REGRESSÃO MÚLTIPLA - SCIKIT-LEARN")
    print("="*80)
    
    resultados = {}
    
    # Definir modelos
    modelos = {
        'Linear': LinearRegression(),
        'Ridge': Ridge(alpha=1.0),
        'Lasso': Lasso(alpha=0.1)
    }
    
    for nome, modelo in modelos.items():
        print(f"\n{nome} Regression:")
        
        # Criar pipeline com normalização
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('regressor', modelo)
        ])
        
        # Treinar modelo
        pipeline.fit(X_train, y_train)
        
        # Previsões
        y_pred_train = pipeline.predict(X_train)
        y_pred_test = pipeline.predict(X_test)
        
        # Métricas
        mse_train = mean_squared_error(y_train, y_pred_train)
        mse_test = mean_squared_error(y_test, y_pred_test)
        r2_train = r2_score(y_train, y_pred_train)
        r2_test = r2_score(y_test, y_pred_test)
        mae_test = mean_absolute_error(y_test, y_pred_test)
        
        # Validação cruzada
        cv_scores = cross_val_score(pipeline, X_train, y_train, 
                                   cv=5, scoring='r2')
        
        print(f"  MSE Treino: {mse_train:.2f}")
        print(f"  MSE Teste: {mse_test:.2f}")
        print(f"  R² Treino: {r2_train:.3f}")
        print(f"  R² Teste: {r2_test:.3f}")
        print(f"  MAE Teste: {mae_test:.2f}")
        print(f"  R² Validação Cruzada: {cv_scores.mean():.3f} (±{cv_scores.std():.3f})")
        
        # Coeficientes (apenas para modelos lineares)
        if hasattr(pipeline.named_steps['regressor'], 'coef_'):
            coefs = pipeline.named_steps['regressor'].coef_
            print(f"  Número de coeficientes: {len(coefs)}")
            
            # Mostrar coeficientes mais importantes
            coef_df = pd.DataFrame({
                'Variável': X_train.columns,
                'Coeficiente': coefs,
                'Absoluto': np.abs(coefs)
            }).sort_values('Absoluto', ascending=False)
            
            print("\n  Coeficientes mais importantes:")
            print(coef_df.head(10).to_string(index=False))
        
        resultados[nome] = {
            'modelo': pipeline,
            'r2_treino': r2_train,
            'r2_teste': r2_test,
            'mse_teste': mse_test,
            'mae_teste': mae_test,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std()
        }
    
    return resultados

def regressao_polinomial(X_train, X_test, y_train, y_test, grau=2):
    """Regressão polinomial"""
    print("\n" + "="*80)
    print(f"REGRESSÃO POLINOMIAL (grau {grau})")
    print("="*80)
    
    # Criar pipeline com features polinomiais
    pipeline = Pipeline([
        ('poly', PolynomialFeatures(degree=grau, include_bias=False)),
        ('scaler', StandardScaler()),
        ('regressor', LinearRegression())
    ])
    
    # Treinar modelo
    pipeline.fit(X_train, y_train)
    
    # Previsões
    y_pred_train = pipeline.predict(X_train)
    y_pred_test = pipeline.predict(X_test)
    
    # Métricas
    mse_test = mean_squared_error(y_test, y_pred_test)
    r2_train = r2_score(y_train, y_pred_train)
    r2_test = r2_score(y_test, y_pred_test)
    
    print(f"R² Treino: {r2_train:.3f}")
    print(f"R² Teste: {r2_test:.3f}")
    print(f"MSE Teste: {mse_test:.2f}")
    print(f"Número de features: {pipeline.named_steps['poly'].n_output_features_}")
    
    return pipeline, r2_test

def analise_residuos(modelo, X_test, y_test, nome_modelo):
    """Análise de resíduos do modelo"""
    print(f"\nAnálise de Resíduos - {nome_modelo}")
    
    # Previsões
    y_pred = modelo.predict(X_test)
    residuos = y_test - y_pred
    
    # Estatísticas dos resíduos
    print(f"Média dos resíduos: {residuos.mean():.3f}")
    print(f"Desvio padrão dos resíduos: {residuos.std():.3f}")
    print(f"Resíduos entre ±2σ: {((residuos.abs() <= 2*residuos.std()).sum() / len(residuos) * 100):.1f}%")
    
    return residuos

def plot_resultados(df, modelos_resultados, residuos):
    """Cria visualizações dos resultados"""
    print("\n" + "="*80)
    print("GERANDO VISUALIZAÇÕES")
    print("="*80)
    
    # Criar diretório para resultados
    import os
    if not os.path.exists('resultados_regressao'):
        os.makedirs('resultados_regressao')
    
    # 1. Gráfico de dispersão valores reais vs preditos
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    # Para cada modelo
    modelos_nomes = list(modelos_resultados.keys())
    for i, nome in enumerate(modelos_nomes[:4]):
        ax = axes[i//2, i%2]
        modelo = modelos_resultados[nome]['modelo']
        X = df.drop(columns=['producao_kg'])
        y = df['producao_kg']
        
        y_pred = modelo.predict(X)
        
        ax.scatter(y, y_pred, alpha=0.5, s=20)
        ax.plot([y.min(), y.max()], [y.min(), y.max()], 'r--', lw=2)
        ax.set_xlabel('Valores Reais (kg)')
        ax.set_ylabel('Valores Preditos (kg)')
        ax.set_title(f'{nome} - R²: {modelos_resultados[nome]["r2_teste"]:.3f}')
        ax.grid(True, alpha=0.3)
    
    # 2. Comparação de R² entre modelos
    ax = axes[1, 2]
    r2_values = [modelos_resultados[nome]['r2_teste'] for nome in modelos_nomes]
    bars = ax.bar(range(len(modelos_nomes)), r2_values)
    ax.set_xlabel('Modelo')
    ax.set_ylabel('R² no Teste')
    ax.set_title('Comparação de Performance dos Modelos')
    ax.set_xticks(range(len(modelos_nomes)))
    ax.set_xticklabels(modelos_nomes, rotation=45)
    
    # Adicionar valores nas barras
    for bar, val in zip(bars, r2_values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f'{val:.3f}', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig('resultados_regressao/comparacao_modelos.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # 3. Importância das variáveis (para modelos lineares)
    for nome in modelos_nomes:
        if 'Linear' in nome:
            modelo = modelos_resultados[nome]['modelo']
            if hasattr(modelo.named_steps['regressor'], 'coef_'):
                coefs = modelo.named_steps['regressor'].coef_
                
                # Criar DataFrame com coeficientes
                coef_df = pd.DataFrame({
                    'Variável': X_test.columns,
                    'Coeficiente': coefs,
                    'Importância_Absoluta': np.abs(coefs)
                }).sort_values('Importância_Absoluta', ascending=False)
                
                # Plotar coeficientes
                plt.figure(figsize=(12, 6))
                bars = plt.barh(coef_df['Variável'][:15], coef_df['Coeficiente'][:15])
                plt.xlabel('Coeficiente')
                plt.title(f'Coeficientes mais importantes - {nome}')
                plt.grid(True, alpha=0.3, axis='x')
                
                # Adicionar valores nas barras
                for bar in bars:
                    width = bar.get_width()
                    plt.text(width, bar.get_y() + bar.get_height()/2,
                            f'{width:.3f}', ha='left' if width >= 0 else 'right',
                            va='center')
                
                plt.tight_layout()
                plt.savefig(f'resultados_regressao/coeficientes_{nome}.png', 
                           dpi=300, bbox_inches='tight')
                plt.show()
                
                # Salvar coeficientes em CSV
                coef_df.to_csv(f'resultados_regressao/coeficientes_{nome}.csv', index=False)
    
    # 4. Gráfico de resíduos
    if residuos is not None and len(residuos) > 0:
        plt.figure(figsize=(12, 10))
        
        # Histograma dos resíduos
        plt.subplot(2, 2, 1)
        plt.hist(residuos, bins=30, edgecolor='black', alpha=0.7)
        plt.xlabel('Resíduos')
        plt.ylabel('Frequência')
        plt.title('Distribuição dos Resíduos')
        plt.axvline(x=0, color='r', linestyle='--')
        
        # QQ plot
        plt.subplot(2, 2, 2)
        sm.qqplot(residuos, line='s', ax=plt.gca())
        plt.title('QQ Plot dos Resíduos')
        
        # Resíduos vs Valores Preditos
        plt.subplot(2, 2, 3)
        plt.scatter(y_pred, residuos, alpha=0.5, s=20)
        plt.axhline(y=0, color='r', linestyle='--')
        plt.xlabel('Valores Preditos')
        plt.ylabel('Resíduos')
        plt.title('Resíduos vs Valores Preditos')
        
        # Resíduos vs Ordem
        plt.subplot(2, 2, 4)
        plt.plot(residuos, 'o', alpha=0.5, markersize=4)
        plt.axhline(y=0, color='r', linestyle='--')
        plt.xlabel('Ordem da Observação')
        plt.ylabel('Resíduos')
        plt.title('Resíduos em Função da Ordem')
        
        plt.tight_layout()
        plt.savefig('resultados_regressao/analise_residuos.png', dpi=300, bbox_inches='tight')
        plt.show()

def gerar_relatorio_final(modelos_resultados, vif_data=None):
    """Gera relatório final em JSON"""
    relatorio = {
        'data_analise': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'modelos': {},
        'recomendacoes': []
    }
    
    # Adicionar informações dos modelos
    for nome, info in modelos_resultados.items():
        relatorio['modelos'][nome] = {
            'r2_teste': float(info['r2_teste']),
            'mse_teste': float(info['mse_teste']),
            'mae_teste': float(info['mae_teste']),
            'cv_r2_mean': float(info['cv_mean']),
            'cv_r2_std': float(info['cv_std'])
        }
    
    # Identificar melhor modelo
    melhor_modelo = max(modelos_resultados.items(), 
                       key=lambda x: x[1]['r2_teste'])
    
    relatorio['melhor_modelo'] = {
        'nome': melhor_modelo[0],
        'r2_teste': float(melhor_modelo[1]['r2_teste']),
        'descricao': f"O modelo {melhor_modelo[0]} obteve o melhor R² no conjunto de teste"
    }
    
    # Recomendações
    r2_melhor = melhor_modelo[1]['r2_teste']
    
    if r2_melhor >= 0.8:
        relatorio['recomendacoes'].append(
            "Modelo com excelente poder preditivo (R² ≥ 0.8). Pode ser usado para previsões."
        )
    elif r2_melhor >= 0.6:
        relatorio['recomendacoes'].append(
            "Modelo com bom poder preditivo (0.6 ≤ R² < 0.8). Útil para estimativas, mas com cautela."
        )
    elif r2_melhor >= 0.4:
        relatorio['recomendacoes'].append(
            "Modelo com poder preditivo moderado (0.4 ≤ R² < 0.6). Considere coletar mais dados ou adicionar variáveis."
        )
    else:
        relatorio['recomendacoes'].append(
            "Modelo com baixo poder preditivo (R² < 0.4). As variáveis atuais não explicam bem a produção."
        )
    
    # Adicionar informações de multicolinearidade se disponível
    if vif_data is not None:
        vars_alta_vif = vif_data[vif_data['VIF'] >= 10]
        if not vars_alta_vif.empty:
            relatorio['alertas'] = {
                'multicolinearidade': 'ALTA detectada nas seguintes variáveis:',
                'variaveis': vars_alta_vif['Variável'].tolist()
            }
            relatorio['recomendacoes'].append(
                "Alta multicolinearidade detectada. Considere remover ou combinar variáveis correlacionadas."
            )
    
    # Salvar relatório
    with open('resultados_regressao/relatorio_final.json', 'w', encoding='utf-8') as f:
        json.dump(relatorio, f, indent=2, ensure_ascii=False)
    
    print("\nRelatório final salvo em 'resultados_regressao/relatorio_final.json'")
    
    return relatorio

def main():
    """Função principal"""
    print("="*80)
    print("ANÁLISE DE REGRESSÃO MÚLTIPLA PARA PRODUÇÃO AGRÍCOLA")
    print("="*80)
    
    # 1. Carregar dados
    df = carregar_dados_regressao()
    
    if df.empty:
        print("Nenhum dado disponível para análise.")
        return
    
    # 2. Preparar dados
    X, y, X_train, X_test, y_train, y_test = preparar_dados(df)
    
    if X is None:
        print("Dados insuficientes para análise.")
        return
    
    # 3. Regressão múltipla com statsmodels
    modelo_stats, vif_data = regressao_multipla_statsmodels(X, y)
    
    # 4. Regressão múltipla com scikit-learn
    resultados = regressao_multipla_scikit(X_train, X_test, y_train, y_test)
    
    # 5. Regressão polinomial
    modelo_poly, r2_poly = regressao_polinomial(X_train, X_test, y_train, y_test)
    
    resultados['Polinomial'] = {
        'modelo': modelo_poly,
        'r2_teste': r2_poly,
        'mse_teste': None,
        'mae_teste': None,
        'cv_mean': None,
        'cv_std': None
    }
    
    # 6. Análise de resíduos do melhor modelo
    melhor_nome = max(resultados.items(), key=lambda x: x[1]['r2_teste'])[0]
    residuos = analise_residuos(
        resultados[melhor_nome]['modelo'], 
        X_test, 
        y_test, 
        melhor_nome
    )
    
    # 7. Visualizações
    plot_resultados(df, resultados, residuos)
    
    # 8. Gerar relatório final
    relatorio = gerar_relatorio_final(resultados, vif_data)
    
    # 9. Salvar melhor modelo
    melhor_modelo = resultados[melhor_nome]['modelo']
    joblib.dump(melhor_modelo, 'resultados_regressao/melhor_modelo.pkl')
    print(f"\nMelhor modelo ({melhor_nome}) salvo em 'resultados_regressao/melhor_modelo.pkl'")
    
    # 10. Mostrar conclusões
    print("\n" + "="*80)
    print("CONCLUSÕES")
    print("="*80)
    print(f"1. Melhor modelo: {relatorio['melhor_modelo']['nome']}")
    print(f"2. R² do melhor modelo: {relatorio['melhor_modelo']['r2_teste']:.3f}")
    print(f"3. Total de variáveis analisadas: {X.shape[1]}")
    print(f"4. Tamanho do conjunto de dados: {df.shape[0]} observações")
    
    print("\nRecomendações:")
    for i, rec in enumerate(relatorio['recomendacoes'], 1):
        print(f"{i}. {rec}")

if __name__ == "__main__":
    main()