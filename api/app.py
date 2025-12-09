# api/app.py
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurar log para arquivo
file_handler = RotatingFileHandler('logs/api.log', maxBytes=10000, backupCount=3)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
logger.addHandler(file_handler)

app = Flask(__name__)
CORS(app)  # Habilita CORS para todas as rotas

# Configurar rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

# Configurações do MySQL do .env
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '1234')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'iot_db')
app.config['MYSQL_PORT'] = int(os.getenv('MYSQL_PORT', 3306))

# Chave secreta para autenticação
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'chave-secreta-padrao')

def get_db_connection():
    """Estabelece conexão com o banco de dados"""
    try:
        conn = mysql.connector.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            database=app.config['MYSQL_DB'],
            port=app.config['MYSQL_PORT'],
            connection_timeout=10
        )
        return conn
    except mysql.connector.Error as err:
        logger.error(f"Erro na conexão com MySQL: {err}")
        return None

@app.route('/')
def home():
    """Página inicial da API"""
    return jsonify({
        "api": "IoT Agro API",
        "version": "1.0.0",
        "endpoints": {
            "api/solo": "POST - Receber dados dos sensores",
            "api/dados": "GET - Obter dados históricos",
            "api/estatisticas": "GET - Estatísticas gerais",
            "api/ultimos": "GET - Últimas leituras",
            "api/exportar": "GET - Exportar dados",
            "api/predicao": "POST - Fazer predição de produção",
            "api/saude": "GET - Status da API"
        }
    })

@app.route('/api/saude')
def saude():
    """Endpoint de saúde da API"""
    try:
        conn = get_db_connection()
        if conn and conn.is_connected():
            db_status = "conectado"
            conn.close()
        else:
            db_status = "desconectado"
    except:
        db_status = "erro"
    
    return jsonify({
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "database": db_status,
        "uptime": str(datetime.now() - app_start_time)
    })

@app.route('/api/solo', methods=['POST'])
@limiter.limit("10 per minute")
def receber_dados():
    """Recebe dados dos sensores do ESP32"""
    data = request.get_json()
    
    if not data:
        logger.warning("Requisição POST sem dados JSON")
        return jsonify({
            "status": "erro",
            "mensagem": "Dados JSON inválidos"
        }), 400
    
    # Log dos dados recebidos
    logger.info(f"Dados recebidos: {json.dumps(data)}")
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({
                "status": "erro",
                "mensagem": "Erro na conexão com o banco de dados"
            }), 500
        
        cursor = conn.cursor()

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
            data.get('latitude'), data.get('longitude'),
            data.get('temperatura_solo'), data.get('umidade_solo'), 
            data.get('condutividade_solo'), data.get('ph'),
            data.get('npk_n'), data.get('npk_p'), data.get('npk_k'),
            data.get('temperatura_ar'), data.get('pressao'), 
            data.get('altitude'), data.get('umidade_relativa'),
            data.get('radiacao_solar'), data.get('indice_uv'), 
            data.get('velocidade_vento'), data.get('pluviometria_mm'),
            data.get('altura_planta'), data.get('biomassa_estimada'), 
            data.get('area_foliar_lai'),
            data.get('cultura'), data.get('estagio_fenologico'), 
            data.get('data_plantio')
        )

        cursor.execute(query, values)
        conn.commit()
        inserted_id = cursor.lastrowid

        cursor.close()
        conn.close()

        logger.info(f"Dados inseridos com sucesso. ID: {inserted_id}")
        
        return jsonify({
            "status": "ok", 
            "mensagem": "Dados inseridos com sucesso.",
            "id": inserted_id,
            "timestamp": datetime.now().isoformat()
        }), 200

    except mysql.connector.Error as err:
        logger.error(f"Erro MySQL: {err}")
        return jsonify({
            "status": "erro", 
            "mensagem": f"Erro no banco de dados: {err}"
        }), 500
    except Exception as e:
        logger.error(f"Erro na API: {e}")
        return jsonify({
            "status": "erro", 
            "mensagem": f"Erro interno: {str(e)}"
        }), 500

@app.route('/api/dados', methods=['GET'])
@limiter.limit("60 per minute")
def obter_dados():
    """Obtém dados históricos com filtros"""
    try:
        # Parâmetros da query
        limite = request.args.get('limit', 1000, type=int)
        cultura = request.args.get('cultura')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        estagio = request.args.get('estagio')
        
        conn = get_db_connection()
        if not conn:
            return jsonify({
                "status": "erro",
                "mensagem": "Erro na conexão com o banco"
            }), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Construir query dinâmica
        query = "SELECT * FROM dados_solo WHERE 1=1"
        params = []
        
        if cultura:
            query += " AND cultura = %s"
            params.append(cultura)
        
        if estagio:
            query += " AND estagio_fenologico = %s"
            params.append(estagio)
        
        if data_inicio:
            query += " AND data_observacao >= %s"
            params.append(data_inicio)
        
        if data_fim:
            query += " AND data_observacao <= %s"
            params.append(data_fim)
        
        query += " ORDER BY data_observacao DESC LIMIT %s"
        params.append(limite)
        
        cursor.execute(query, params)
        dados = cursor.fetchall()
        
        # Converter datetime para string
        for dado in dados:
            for key, value in dado.items():
                if isinstance(value, datetime):
                    dado[key] = value.isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "status": "ok",
            "total": len(dados),
            "dados": dados
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter dados: {e}")
        return jsonify({
            "status": "erro",
            "mensagem": str(e)
        }), 500

@app.route('/api/ultimos', methods=['GET'])
def obter_ultimos():
    """Obtém as últimas leituras para cada sensor"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Última leitura de cada cultura
        cursor.execute("""
            SELECT cultura, MAX(data_observacao) as ultima_leitura
            FROM dados_solo 
            GROUP BY cultura
        """)
        ultimas_culturas = cursor.fetchall()
        
        # Últimas 24 horas agregadas
        cursor.execute("""
            SELECT 
                HOUR(data_observacao) as hora,
                AVG(temperatura_solo) as temp_solo_media,
                AVG(umidade_solo) as umidade_solo_media,
                AVG(temperatura_ar) as temp_ar_media,
                AVG(radiacao_solar) as radiacao_media
            FROM dados_solo 
            WHERE data_observacao >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            GROUP BY HOUR(data_observacao)
            ORDER BY hora
        """)
        ultimas_24h = cursor.fetchall()
        
        # Valores atuais (última leitura)
        cursor.execute("""
            SELECT 
                temperatura_solo, umidade_solo, ph,
                temperatura_ar, umidade_relativa, radiacao_solar,
                altura_planta, cultura, estagio_fenologico,
                data_observacao
            FROM dados_solo 
            ORDER BY data_observacao DESC 
            LIMIT 1
        """)
        atual = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "ultimas_culturas": ultimas_culturas,
            "ultimas_24h": ultimas_24h,
            "atual": atual
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter últimas leituras: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

@app.route('/api/estatisticas', methods=['GET'])
def obter_estatisticas():
    """Retorna estatísticas detalhadas dos dados"""
    try:
        cultura = request.args.get('cultura')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Construir query com filtro de cultura
        query_where = "WHERE 1=1"
        params = []
        
        if cultura:
            query_where += " AND cultura = %s"
            params.append(cultura)
        
        # Estatísticas gerais
        cursor.execute(f"""
            SELECT 
                COUNT(*) as total_registros,
                COUNT(DISTINCT cultura) as culturas_distintas,
                COUNT(DISTINCT DATE(data_observacao)) as dias_coleta,
                MIN(data_observacao) as primeira_leitura,
                MAX(data_observacao) as ultima_leitura,
                COUNT(producao_kg) as registros_com_producao
            FROM dados_solo
            {query_where}
        """, params)
        
        estatisticas = cursor.fetchone()
        
        # Médias gerais
        cursor.execute(f"""
            SELECT 
                AVG(temperatura_solo) as media_temp_solo,
                STDDEV(temperatura_solo) as desvio_temp_solo,
                AVG(umidade_solo) as media_umidade_solo,
                STDDEV(umidade_solo) as desvio_umidade_solo,
                AVG(ph) as media_ph,
                STDDEV(ph) as desvio_ph,
                AVG(altura_planta) as media_altura,
                STDDEV(altura_planta) as desvio_altura,
                AVG(producao_kg) as media_producao,
                STDDEV(producao_kg) as desvio_producao
            FROM dados_solo
            {query_where}
        """, params)
        
        medias = cursor.fetchone()
        
        # Distribuição por cultura
        cursor.execute("""
            SELECT 
                cultura,
                COUNT(*) as total,
                AVG(producao_kg) as media_producao,
                AVG(altura_planta) as media_altura
            FROM dados_solo
            WHERE cultura IS NOT NULL
            GROUP BY cultura
            ORDER BY total DESC
        """)
        
        culturas = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Combinar resultados
        resultado = {**estatisticas, **medias}
        resultado['culturas'] = culturas
        
        # Converter datetime para string
        for key in ['primeira_leitura', 'ultima_leitura']:
            if resultado[key]:
                resultado[key] = resultado[key].isoformat()
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

@app.route('/api/exportar', methods=['GET'])
def exportar_dados():
    """Exporta dados em formato CSV"""
    try:
        formato = request.args.get('formato', 'json')
        limite = request.args.get('limite', 10000, type=int)
        
        conn = get_db_connection()
        
        query = "SELECT * FROM dados_solo ORDER BY data_observacao DESC LIMIT %s"
        df = pd.read_sql(query, conn, params=(limite,))
        
        conn.close()
        
        if formato == 'csv':
            csv_data = df.to_csv(index=False)
            return csv_data, 200, {
                'Content-Type': 'text/csv',
                'Content-Disposition': f'attachment; filename=dados_solo_{datetime.now().strftime("%Y%m%d")}.csv'
            }
        else:
            return jsonify(df.to_dict(orient='records'))
            
    except Exception as e:
        logger.error(f"Erro ao exportar dados: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

@app.route('/api/predicao', methods=['POST'])
def predicao_producao():
    """Endpoint para predição de produção usando modelo ML"""
    try:
        data = request.get_json()
        
        # Verificar campos obrigatórios
        campos_obrigatorios = [
            'temperatura_solo', 'umidade_solo', 'ph',
            'npk_n', 'npk_p', 'npk_k', 'altura_planta'
        ]
        
        for campo in campos_obrigatorios:
            if campo not in data:
                return jsonify({
                    "status": "erro",
                    "mensagem": f"Campo obrigatório faltando: {campo}"
                }), 400
        
        # Aqui você carregaria o modelo treinado
        # Exemplo: modelo = joblib.load('modelos/producao_model.pkl')
        # predicao = modelo.predict([[...]])
        
        # Por enquanto, vamos simular uma predição
        # Esta é uma fórmula simplificada para exemplo
        predicao = (
            data['umidade_solo'] * 0.3 +
            data['npk_n'] * 0.2 +
            data['npk_p'] * 0.15 +
            data['npk_k'] * 0.15 +
            data['altura_planta'] * 0.2
        ) * 10  # Escalar para kg
        
        return jsonify({
            "status": "ok",
            "predicao_kg": round(predicao, 2),
            "timestamp": datetime.now().isoformat(),
            "observacao": "Predição baseada em modelo simplificado"
        })
        
    except Exception as e:
        logger.error(f"Erro na predição: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

@app.route('/api/alertas', methods=['GET'])
def obter_alertas():
    """Retorna alertas baseados em limites predefinidos"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Obter última leitura
        cursor.execute("""
            SELECT * FROM dados_solo 
            ORDER BY data_observacao DESC 
            LIMIT 1
        """)
        ultima = cursor.fetchone()
        
        if not ultima:
            return jsonify({"alertas": []})
        
        alertas = []
        
        # Verificar limites
        limites = {
            'temperatura_solo': {'min': 15, 'max': 30},
            'umidade_solo': {'min': 20, 'max': 60},
            'ph': {'min': 5.5, 'max': 7.5},
            'npk_n': {'min': 30, 'max': 70},
            'npk_p': {'min': 15, 'max': 40},
            'npk_k': {'min': 30, 'max': 60}
        }
        
        for parametro, limites_param in limites.items():
            valor = ultima.get(parametro)
            if valor is not None:
                if valor < limites_param['min']:
                    alertas.append({
                        'parametro': parametro,
                        'valor': valor,
                        'limite': limites_param['min'],
                        'tipo': 'abaixo_minimo',
                        'mensagem': f'{parametro} abaixo do ideal'
                    })
                elif valor > limites_param['max']:
                    alertas.append({
                        'parametro': parametro,
                        'valor': valor,
                        'limite': limites_param['max'],
                        'tipo': 'acima_maximo',
                        'mensagem': f'{parametro} acima do ideal'
                    })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "ultima_leitura": ultima['data_observacao'].isoformat() if ultima['data_observacao'] else None,
            "alertas": alertas
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter alertas: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "status": "erro",
        "mensagem": "Endpoint não encontrado"
    }), 404

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({
        "status": "erro",
        "mensagem": "Limite de requisições excedido"
    }), 429

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Erro interno: {error}")
    return jsonify({
        "status": "erro",
        "mensagem": "Erro interno do servidor"
    }), 500

if __name__ == '__main__':
    # Criar diretório de logs se não existir
    os.makedirs('logs', exist_ok=True)
    
    app_start_time = datetime.now()
    
    logger.info("Iniciando API IoT Agro...")
    app.run(
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000))
    )