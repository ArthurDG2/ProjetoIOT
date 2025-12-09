from flask import Flask, request, jsonify
try:
    import pymysql
    pymysql.install_as_MySQLdb()  # Faz pymysql funcionar como MySQLdb
    import MySQLdb  # Agora funcionará
    print("Usando pymysql como MySQLdb")
except ImportError:
    print("Erro: pymysql não instalado")
    exit(1)


app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '1234'
app.config['MYSQL_DB'] = 'iot_db'

db = MySQLdb.connect(
    host=app.config['MYSQL_HOST'],
    user=app.config['MYSQL_USER'],
    passwd=app.config['MYSQL_PASSWORD'],
    db=app.config['MYSQL_DB']
)

@app.route('/api/solo', methods=['POST'])
def receber_dados():
    data = request.get_json()

    try:
        cursor = db.cursor()

        query = """
            INSERT INTO dados_solo (
                latitude, longitude,
                temperatura_solo, umidade_solo, condutividade_solo, ph,
                npk_n, npk_p, npk_k,
                temperatura_ar, pressao, altitude, umidade_relativa,
                radiacao_solar, indice_uv, velocidade_vento, pluviometria_mm,
                altura_planta, biomassa_estimada, area_foliar_lai,
                cultura, estagio_fenologico, data_plantio
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 
                      %s, %s, %s, %s, %s, %s, %s, %s,
                      %s, %s, %s, %s, %s, %s)
        """

        values = (
            data['latitude'], data['longitude'],
            data['temperatura_solo'], data['umidade_solo'], data['condutividade_solo'], data['ph'],
            data['npk_n'], data['npk_p'], data['npk_k'],
            data['temperatura_ar'], data['pressao'], data['altitude'], data['umidade_relativa'],
            data['radiacao_solar'], data['indice_uv'], data['velocidade_vento'], data['pluviometria_mm'],
            data['altura_planta'], data['biomassa_estimada'], data['area_foliar_lai'],
            data['cultura'], data['estagio_fenologico'], data['data_plantio']
        )

        cursor.execute(query, values)
        db.commit()

        return jsonify({"status": "ok", "mensagem": "Dados inseridos com sucesso."}), 200

    except Exception as e:
        print("Erro API:", e)
        return jsonify({"status": "erro", "mensagem": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')