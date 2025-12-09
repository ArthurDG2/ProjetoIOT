import random, datetime, mysql.connector
from math import fabs

DB_HOST='localhost'
DB_USER='root'
DB_PASS='1234'
DB_NAME='iot_db'

def randf(a,b): return round(random.uniform(a,b),3)

def gera_registro(cultura='Soja', plantio_date='2025-01-10'):
    lat = randf(-23.25, -22.90)
    lon = randf(-47.30, -46.80)
    temperatura_solo = randf(15, 35)
    umidade_solo = randf(5, 70)
    condutividade_solo = randf(0.05, 1.5)
    ph = randf(4.5, 8.0)
    npk_n = randf(10,80)
    npk_p = randf(5,50)
    npk_k = randf(10,80)
    temperatura_ar = randf(10,38)
    pressao = randf(980,1030)
    altitude = randf(400,900)
    umidade_relativa = randf(20,98)
    radiacao_solar = randf(0,1200)
    indice_uv = randf(0,12)
    velocidade_vento = randf(0,18)
    pluviometria_mm = randf(0,50)
    altura_planta = randf(0,150)            # cm
    biomassa_estimada = randf(0.01,8.0)     # kg/m2 (exemplo)
    area_foliar_lai = randf(0.1,6.5)
    estag = random.choice(['V0','V1','V2','V3','V4','R1','R2','R3','R4','R5','R6','R7','R8'])
    data_plantio = plantio_date
    data_observacao = (datetime.datetime.now() - datetime.timedelta(days=random.randint(0,120))).strftime('%Y-%m-%d %H:%M:%S')
    producao_kg = None if random.random() < 0.7 else round(randf(200,1500),2)  # 30% têm produção preenchida
    return (
        lat, lon, temperatura_solo, umidade_solo, condutividade_solo, ph, npk_n, npk_p, npk_k,
        temperatura_ar, pressao, altitude, umidade_relativa, radiacao_solar, indice_uv, velocidade_vento, pluviometria_mm,
        altura_planta, biomassa_estimada, area_foliar_lai, 'Soja', estag, data_plantio, data_observacao, producao_kg
    )

def inserir_n(n=1000):
    conn = mysql.connector.connect(host=DB_HOST,user=DB_USER,password=DB_PASS,database=DB_NAME)
    cur = conn.cursor()
    sql = """INSERT INTO dados_solo (
      latitude, longitude, temperatura_solo, umidade_solo, condutividade_solo, ph, npk_n, npk_p, npk_k,
      temperatura_ar, pressao, altitude, umidade_relativa, radiacao_solar, indice_uv, velocidade_vento, pluviometria_mm,
      altura_planta, biomassa_estimada, area_foliar_lai, cultura, estagio_fenologico, data_plantio, data_observacao, producao_kg
    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    for i in range(n):
        cur.execute(sql, gera_registro())
    conn.commit()
    cur.close()
    conn.close()
    print(f"{n} registros inseridos.")

if __name__ == "__main__":
    inserir_n(2000)  # ajuste N conforme desejar