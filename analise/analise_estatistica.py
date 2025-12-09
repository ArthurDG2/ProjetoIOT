import mysql.connector
import pandas as pd
import numpy as np
from scipy.stats import pearsonr
import statsmodels.api as sm
from statsmodels.formula.api import ols
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, r2_score


# Config DB
DB = dict(host='localhost', user='root', password='1234', database='iot_db')

def carrega_dados():
    conn = mysql.connector.connect(**DB)
    query = "SELECT * FROM dados_solo"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def correlacoes(df, target='producao_kg'):
    vars = ['temperatura_solo','umidade_solo','condutividade_solo','ph','npk_n','npk_p','npk_k',
            'temperatura_ar','pressao','umidade_relativa','radiacao_solar','indice_uv','velocidade_vento','pluviometria_mm',
            'altura_planta','biomassa_estimada','area_foliar_lai']
    results = {}
    df2 = df.dropna(subset=[target])
    for v in vars:
        if v in df2.columns and df2[v].notnull().sum() > 2:
            try:
                corr, p = pearsonr(df2[v], df2[target])
                results[v] = (corr, p)
            except Exception as e:
                results[v] = (np.nan, np.nan)
    return results

def regressao_linear_simples(df, xvar, target='producao_kg'):
    df2 = df.dropna(subset=[xvar, target])
    X = df2[[xvar]].values
    y = df2[target].values
    model = LinearRegression().fit(X,y)
    ypred = model.predict(X)
    return {'coef': model.coef_[0], 'intercept': model.intercept_, 'r2': model.score(X,y)}

def regressao_multipla(df, features, target='producao_kg'):
    df2 = df.dropna(subset=features+[target])
    X = df2[features]
    y = df2[target]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    pipeline = Pipeline([('scaler', StandardScaler()), ('reg', RandomForestRegressor(n_estimators=100, random_state=42))])
    pipeline.fit(X_train, y_train)
    ypred = pipeline.predict(X_test)
    return {
        'rmse': mean_squared_error(y_test, ypred, squared=False),
        'r2': r2_score(y_test, ypred),
        'feature_importances': pipeline.named_steps['reg'].feature_importances_
    }

def anova_example(df, target='producao_kg'):
    # ANOVA: efeito do estágio fenológico sobre a produção (exemplo)
    df2 = df.dropna(subset=[target, 'estagio_fenologico'])
    model = ols(f'{target} ~ C(estagio_fenologico)', data=df2).fit()
    aov_table = sm.stats.anova_lm(model, typ=2)
    return aov_table

if __name__ == "__main__":
    df = carrega_dados()
    print("Tamanho do dataset:", df.shape)

    # Correlações
    corr = correlacoes(df)
    print("Correlação (pearson) com produção (apenas variáveis com p calculado):")
    for k,(c,p) in corr.items():
        print(f" {k}: corr={c:.3f} p={p:.4f}")

    # Regressão linear simples (exemplo com umidade do solo)
    rl = regressao_linear_simples(df,'umidade_solo')
    print("Regressão linear simples (umidade_solo):", rl)

    # Regressão múltipla
    features = ['umidade_solo','temperatura_solo','ph','npk_n','pluviometria_mm','area_foliar_lai']
    rm = regressao_multipla(df, features)
    print("Regressão múltipla (RandomForest) - RMSE, R2:", rm['rmse'], rm['r2'])
    print("Importâncias:", dict(zip(features, rm['feature_importances'])))

    # ANOVA
    try:
        aov = anova_example(df)
        print("ANOVA por estagio_fenologico:\n", aov)
    except Exception as e:
        print("ANOVA falhou:", e)