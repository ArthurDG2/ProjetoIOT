from flask import Flask, render_template, jsonify
import mysql.connector
import pandas as pd

app = Flask(__name__)
DB = dict(host='localhost', user='root', password='1234', database='iot_db')

def get_latest(n=100):
    conn = mysql.connector.connect(**DB)
    df = pd.read_sql("SELECT * FROM dados_solo ORDER BY data_observacao DESC LIMIT %s", conn, params=(n,))
    conn.close()
    return df

@app.route('/')
def index():
    df = get_latest(200)
    return render_template('index.html', data=df.to_dict(orient='records'))

@app.route('/api/series')
def api_series():
    df = get_latest(500)
    df['data_observacao'] = pd.to_datetime(df['data_observacao']).astype(str)
    return jsonify(df.to_dict(orient='records'))

if __name__ == '__main__':
    app.run(debug=True)