import mysql.connector
import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
import joblib

DB = dict(host='localhost', user='seu_usuario', password='sua_senha', database='iot_db')

def load_data():
    conn = mysql.connector.connect(**DB)
    df = pd.read_sql("SELECT * FROM dados_solo WHERE producao_kg IS NOT NULL", conn)
    conn.close()
    return df

if __name__ == "__main__":
    df = load_data()
    # features possíveis
    features = ['umidade_solo','temperatura_solo','ph','npk_n','npk_p','npk_k','pluviometria_mm','radiacao_solar','area_foliar_lai','altura_planta']
    df = df.dropna(subset=features+['producao_kg'])
    X = df[features]
    y = df['producao_kg']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('model', RandomForestRegressor(random_state=42, n_estimators=200))
    ])

    pipeline.fit(X_train, y_train)
    ypred = pipeline.predict(X_test)
    print("RMSE:", mean_squared_error(y_test, ypred, squared=False))
    print("R2:", r2_score(y_test, ypred))

    # importância de features (RandomForest)
    importances = pipeline.named_steps['model'].feature_importances_
    print(dict(zip(features, importances)))

    # salvar modelo
    joblib.dump(pipeline, 'modelo_producao_rf.pkl')
    print("Modelo salvo em modelo_producao_rf.pkl")