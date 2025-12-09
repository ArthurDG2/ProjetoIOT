# dashboard.py
from flask import Flask, render_template, jsonify, request
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta

app = Flask(__name__, template_folder='templates')

# Configurações do banco de dados
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',
    'database': 'iot_db'
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

@app.route('/')
def index():
    """Página principal do dashboard"""
    return render_template('dashboard.html')

@app.route('/api/ultimos_dados')
def api_ultimos_dados():
    """Retorna os últimos dados para o dashboard"""
    try:
        limite = request.args.get('limit', 50)
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT 
                id, data_observacao,
                temperatura_solo, umidade_solo, ph,
                temperatura_ar, umidade_relativa, radiacao_solar,
                altura_planta, biomassa_estimada, producao_kg,
                cultura, estagio_fenologico
            FROM dados_solo 
            ORDER BY data_observacao DESC 
            LIMIT %s
        """
        
        cursor.execute(query, (int(limite),))
        dados = cursor.fetchall()
        
        # Converter datetime para string
        for dado in dados:
            if 'data_observacao' in dado and dado['data_observacao']:
                dado['data_observacao'] = dado['data_observacao'].strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.close()
        conn.close()
        
        return jsonify(dados)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/series_temporais')
def api_series_temporais():
    """Retorna séries temporais para gráficos"""
    try:
        dias = request.args.get('dias', 7)
        variavel = request.args.get('variavel', 'temperatura_solo')
        
        # Lista de variáveis válidas
        variaveis_validas = [
            'temperatura_solo', 'umidade_solo', 'ph', 'condutividade_solo',
            'temperatura_ar', 'umidade_relativa', 'radiacao_solar',
            'altura_planta', 'biomassa_estimada', 'producao_kg'
        ]
        
        if variavel not in variaveis_validas:
            variavel = 'temperatura_solo'
        
        data_inicio = (datetime.now() - timedelta(days=int(dias))).strftime('%Y-%m-%d')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = f"""
            SELECT 
                DATE(data_observacao) as data,
                HOUR(data_observacao) as hora,
                AVG({variavel}) as valor
            FROM dados_solo 
            WHERE data_observacao >= %s
            GROUP BY DATE(data_observacao), HOUR(data_observacao)
            ORDER BY data, hora
        """
        
        cursor.execute(query, (data_inicio,))
        dados = cursor.fetchall()
        
        # Processar dados para o gráfico
        labels = []
        valores = []
        
        for dado in dados:
            label = f"{dado['data']} {dado['hora']:02d}:00"
            labels.append(label)
            valores.append(float(dado['valor']) if dado['valor'] else 0)
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "labels": labels,
            "valores": valores,
            "variavel": variavel,
            "unidade": get_unidade(variavel)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_unidade(variavel):
    """Retorna a unidade de medida para cada variável"""
    unidades = {
        'temperatura_solo': '°C',
        'umidade_solo': '%',
        'ph': '',
        'condutividade_solo': 'dS/m',
        'temperatura_ar': '°C',
        'umidade_relativa': '%',
        'radiacao_solar': 'W/m²',
        'altura_planta': 'cm',
        'biomassa_estimada': 'kg/m²',
        'producao_kg': 'kg'
    }
    return unidades.get(variavel, '')

@app.route('/api/estatisticas_resumo')
def api_estatisticas_resumo():
    """Retorna estatísticas resumidas para o dashboard"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Estatísticas gerais
        cursor.execute("""
            SELECT 
                COUNT(*) as total_leituras,
                COUNT(DISTINCT DATE(data_observacao)) as dias_coleta,
                MIN(data_observacao) as primeira_leitura,
                MAX(data_observacao) as ultima_leitura
            FROM dados_solo
        """)
        estatisticas = cursor.fetchone()
        
        # Médias atuais
        cursor.execute("""
            SELECT 
                AVG(temperatura_solo) as temp_solo_media,
                AVG(umidade_solo) as umidade_solo_media,
                AVG(ph) as ph_medio,
                AVG(temperatura_ar) as temp_ar_media
            FROM dados_solo 
            WHERE data_observacao >= DATE_SUB(NOW(), INTERVAL 1 DAY)
        """)
        medias = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        # Combinar resultados
        resultado = {**estatisticas, **medias}
        
        # Converter datetime para string
        for key in ['primeira_leitura', 'ultima_leitura']:
            if resultado[key]:
                resultado[key] = resultado[key].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/correlacoes')
def api_correlacoes():
    """Retorna correlações para visualização"""
    try:
        conn = get_db_connection()
        
        # Carregar dados em DataFrame
        query = """
            SELECT 
                temperatura_solo, umidade_solo, ph, condutividade_solo,
                npk_n, npk_p, npk_k, temperatura_ar, umidade_relativa,
                radiacao_solar, altura_planta, biomassa_estimada, producao_kg
            FROM dados_solo 
            WHERE producao_kg IS NOT NULL
            LIMIT 1000
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        if df.empty:
            return jsonify({"message": "Dados insuficientes para análise de correlação"})
        
        # Calcular correlações
        correlacoes = df.corr()['producao_kg'].dropna().to_dict()
        
        # Ordenar por valor absoluto
        correlacoes_ordenadas = dict(sorted(
            correlacoes.items(), 
            key=lambda x: abs(x[1]), 
            reverse=True
        ))
        
        return jsonify(correlacoes_ordenadas)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)