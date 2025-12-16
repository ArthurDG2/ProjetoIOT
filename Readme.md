IoT Agro API
API Flask para coleta e análise de dados de sensores agrícolas IoT.

🚀 Instalação Rápida
bash
git clone <repositorio>
cd iot-agro-api
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate (Windows)
pip install -r requirements.txt
cp .env.example .env
# Configure o .env com suas credenciais MySQL

📋 Configuração Mínima (.env)
env
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=sua_senha
MYSQL_DB=iot_db
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

🗄️ Estrutura da Tabela
sql
CREATE TABLE dados_solo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    data_observacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    temperatura_solo DECIMAL(5, 2),
    umidade_solo DECIMAL(5, 2),
    ph DECIMAL(4, 2),
    npk_n DECIMAL(6, 2),
    npk_p DECIMAL(6, 2),
    npk_k DECIMAL(6, 2),
    temperatura_ar DECIMAL(5, 2),
    cultura VARCHAR(50),
    estagio_fenologico VARCHAR(50)
);

📡 Endpoints Principais
POST /api/solo - Enviar dados
json
{
    "temperatura_solo": 22.5,
    "umidade_solo": 45.3,
    "ph": 6.8,
    "cultura": "soja"
}

GET /api/dados - Consultar dados
Parâmetros: limit, cultura, data_inicio, data_fim

GET /api/estatisticas - Estatísticas

GET /api/exportar - Exportar CSV/JSON

🏃‍♂️ Executar
bash
python api/app.py
# Acesse: http://localhost:5000

🛡️ Segurança
Rate limiting: 200 requisições/dia, 50/hora

CORS habilitado

Logs em logs/api.log