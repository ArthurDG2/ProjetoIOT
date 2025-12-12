#!/usr/bin/env python
"""
Script de Diagnóstico Rápido - IoT Agro API
Verifica se todos os componentes estão funcionando
"""

import requests
import sys
import time
from datetime import datetime

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_header(titulo):
    print(f"\n{Colors.BLUE}{'='*70}")
    print(f"  {titulo}")
    print(f"{'='*70}{Colors.RESET}\n")

def teste_conexao(url, nome, metodo='GET', timeout=3, **kwargs):
    try:
        if metodo == 'GET':
            response = requests.get(url, timeout=timeout, **kwargs)
        elif metodo == 'POST':
            response = requests.post(url, timeout=timeout, **kwargs)
        
        if response.status_code == 200:
            print(f"{Colors.GREEN}✅ {nome}{Colors.RESET}")
            return True, response.json() if response.content else {}
        else:
            print(f"{Colors.RED}❌ {nome} (Status: {response.status_code}){Colors.RESET}")
            try:
                data = response.json()
                if 'mensagem' in data:
                    print(f"   {Colors.RED}Mensagem: {data['mensagem']}{Colors.RESET}")
            except:
                pass
            return False, None
    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED}❌ {nome} - Conexão recusada{Colors.RESET}")
        return False, None
    except requests.exceptions.Timeout:
        print(f"{Colors.RED}❌ {nome} - Timeout{Colors.RESET}")
        return False, None
    except Exception as e:
        print(f"{Colors.RED}❌ {nome} - {str(e)}{Colors.RESET}")
        return False, None

def teste_api_saude(api_url='http://localhost:5000'):
    try:
        response = requests.get(f'{api_url}/api/saude', timeout=3)
        if response.status_code == 200:
            dados = response.json()
            print(f"{Colors.GREEN}✅ API de Saúde{Colors.RESET}")
            print(f"   - Status: {dados.get('status', 'N/A')}")
            print(f"   - Database: {dados.get('database', 'N/A')}")
            print(f"   - Uptime: {dados.get('uptime', 'N/A')}")
            return True, dados
        else:
            print(f"{Colors.RED}❌ API de Saúde falhou (Status: {response.status_code}){Colors.RESET}")
            return False, None
    except Exception as e:
        print(f"{Colors.RED}❌ Erro ao acessar API de Saúde: {str(e)}{Colors.RESET}")
        return False, None

def teste_api_dados(api_url='http://localhost:5000'):
    try:
        response = requests.get(f'{api_url}/api/dados?limit=1', timeout=3)
        if response.status_code == 200:
            dados = response.json()
            if dados.get('status') == 'ok':
                total = dados.get('total', 0)
                print(f"{Colors.GREEN}✅ API retornando dados ({total} registros){Colors.RESET}")
                if total > 0 and dados.get('dados'):
                    ultimo = dados['dados'][0]
                    print(f"   - Último ID: {ultimo.get('id', 'N/A')}")
                    print(f"   - Cultura: {ultimo.get('cultura', 'N/A')}")
                    print(f"   - Data: {ultimo.get('data_observacao', 'N/A')}")
                return True, dados
            else:
                print(f"{Colors.RED}❌ API retornou status de erro{Colors.RESET}")
                return False, None
        else:
            print(f"{Colors.RED}❌ API sem dados (Status: {response.status_code}){Colors.RESET}")
            return False, None
    except Exception as e:
        print(f"{Colors.RED}❌ Erro ao acessar API de dados: {str(e)}{Colors.RESET}")
        return False, None

def teste_api_ultimos(api_url='http://localhost:5000'):
    try:
        response = requests.get(f'{api_url}/api/ultimos', timeout=3)
        if response.status_code == 200:
            dados = response.json()
            print(f"{Colors.GREEN}✅ API de Últimas Leituras{Colors.RESET}")
            
            if dados.get('atual'):
                atual = dados['atual']
                print(f"   - Temperatura Solo: {atual.get('temperatura_solo', 'N/A')}°C")
                print(f"   - Umidade Solo: {atual.get('umidade_solo', 'N/A')}%")
                print(f"   - pH: {atual.get('ph', 'N/A')}")
                print(f"   - Cultura: {atual.get('cultura', 'N/A')}")
            
            if dados.get('ultimas_culturas'):
                print(f"   - Culturas ativas: {len(dados['ultimas_culturas'])}")
                
            return True, dados
        else:
            print(f"{Colors.RED}❌ API de últimas leituras falhou{Colors.RESET}")
            return False, None
    except Exception as e:
        print(f"{Colors.RED}❌ Erro ao acessar últimas leituras: {str(e)}{Colors.RESET}")
        return False, None

def teste_api_estatisticas(api_url='http://localhost:5000'):
    try:
        response = requests.get(f'{api_url}/api/estatisticas', timeout=3)
        if response.status_code == 200:
            dados = response.json()
            print(f"{Colors.GREEN}✅ API de Estatísticas{Colors.RESET}")
            print(f"   - Total registros: {dados.get('total_registros', 0)}")
            print(f"   - Culturas distintas: {dados.get('culturas_distintas', 0)}")
            print(f"   - Dias de coleta: {dados.get('dias_coleta', 0)}")
            if dados.get('media_temp_solo'):
                print(f"   - Temp. solo média: {dados.get('media_temp_solo'):.2f}°C")
            return True, dados
        else:
            print(f"{Colors.RED}❌ API de estatísticas falhou{Colors.RESET}")
            return False, None
    except Exception as e:
        print(f"{Colors.RED}❌ Erro ao acessar estatísticas: {str(e)}{Colors.RESET}")
        return False, None

def teste_api_alertas(api_url='http://localhost:5000'):
    try:
        response = requests.get(f'{api_url}/api/alertas', timeout=3)
        if response.status_code == 200:
            dados = response.json()
            print(f"{Colors.GREEN}✅ API de Alertas{Colors.RESET}")
            alertas = dados.get('alertas', [])
            print(f"   - Total alertas: {len(alertas)}")
            for alerta in alertas[:3]:  # Mostra apenas os 3 primeiros
                print(f"   - {alerta.get('mensagem', 'Alerta')}")
            if len(alertas) > 3:
                print(f"   - ... e mais {len(alertas)-3} alertas")
            return True, dados
        else:
            print(f"{Colors.RED}❌ API de alertas falhou{Colors.RESET}")
            return False, None
    except Exception as e:
        print(f"{Colors.RED}❌ Erro ao acessar alertas: {str(e)}{Colors.RESET}")
        return False, None

def teste_post_dados(api_url='http://localhost:5000'):
    """Testa envio de dados simulados para a API"""
    dados_teste = {
        "latitude": -23.5505,
        "longitude": -46.6333,
        "temperatura_solo": 25.5,
        "umidade_solo": 45.2,
        "condutividade_solo": 1.8,
        "ph": 6.5,
        "npk_n": 45.0,
        "npk_p": 25.0,
        "npk_k": 35.0,
        "temperatura_ar": 28.0,
        "pressao": 1013.25,
        "altitude": 760,
        "umidade_relativa": 65.5,
        "radiacao_solar": 850.0,
        "indice_uv": 6,
        "velocidade_vento": 12.5,
        "pluviometria_mm": 0.0,
        "altura_planta": 1.2,
        "biomassa_estimada": 0.85,
        "area_foliar_lai": 2.8,
        "cultura": "Soja",
        "estagio_fenologico": "Vegetativo",
        "data_plantio": "2024-01-15"
    }
    
    try:
        response = requests.post(
            f'{api_url}/api/solo',
            json=dados_teste,
            timeout=5
        )
        
        if response.status_code == 200:
            resultado = response.json()
            if resultado.get('status') == 'ok':
                print(f"{Colors.GREEN}✅ POST de dados funcionando{Colors.RESET}")
                print(f"   - ID inserido: {resultado.get('id')}")
                print(f"   - Mensagem: {resultado.get('mensagem')}")
                return True, resultado
            else:
                print(f"{Colors.RED}❌ POST retornou status de erro{Colors.RESET}")
                return False, None
        else:
            print(f"{Colors.RED}❌ POST falhou (Status: {response.status_code}){Colors.RESET}")
            try:
                erro = response.json()
                print(f"   {Colors.RED}Erro: {erro.get('mensagem', 'Desconhecido')}{Colors.RESET}")
            except:
                pass
            return False, None
    except Exception as e:
        print(f"{Colors.RED}❌ Erro no POST de dados: {str(e)}{Colors.RESET}")
        return False, None

def teste_rate_limiting(api_url='http://localhost:5000'):
    """Testa se o rate limiting está funcionando"""
    print(f"{Colors.YELLOW}⚠️  Testando rate limiting (10 requisições rápidas)...{Colors.RESET}")
    
    sucessos = 0
    falhas = 0
    bloqueios = 0
    
    for i in range(12):
        try:
            response = requests.get(f'{api_url}/api/saude', timeout=2)
            if response.status_code == 200:
                sucessos += 1
            elif response.status_code == 429:
                bloqueios += 1
                if i == 11:  # Última tentativa
                    print(f"{Colors.GREEN}✅ Rate limiting funcionando!{Colors.RESET}")
                    print(f"   - Bloqueou após {sucessos} requisições")
                    return True
            else:
                falhas += 1
        except:
            falhas += 1
        
        time.sleep(0.1)  # Pequena pausa
    
    print(f"{Colors.RED}❌ Rate limiting não funcionou como esperado{Colors.RESET}")
    print(f"   - Sucessos: {sucessos}, Falhas: {falhas}, Bloqueios: {bloqueios}")
    return False

def verificar_endpoints_disponiveis(api_url='http://localhost:5000'):
    """Verifica todos os endpoints da API"""
    endpoints = [
        ('/', 'Home da API'),
        ('/api/saude', 'Saúde da API'),
        ('/api/dados', 'Dados históricos'),
        ('/api/ultimos', 'Últimas leituras'),
        ('/api/estatisticas', 'Estatísticas'),
        ('/api/alertas', 'Alertas'),
        ('/api/exportar?formato=json&limite=1', 'Exportar dados'),
    ]
    
    print(f"\n{Colors.YELLOW}🔍 Verificando todos os endpoints:{Colors.RESET}")
    
    disponiveis = []
    indisponiveis = []
    
    for endpoint, descricao in endpoints:
        status, _ = teste_conexao(f'{api_url}{endpoint}', f'{endpoint} - {descricao}')
        if status:
            disponiveis.append(endpoint)
        else:
            indisponiveis.append(endpoint)
        time.sleep(0.2)  # Evitar sobrecarga
    
    print(f"\n{Colors.GREEN}✅ Endpoints disponíveis: {len(disponiveis)}/{len(endpoints)}{Colors.RESET}")
    if indisponiveis:
        print(f"{Colors.RED}❌ Endpoints indisponíveis:{Colors.RESET}")
        for endpoint in indisponiveis:
            print(f"   - {endpoint}")
    
    return len(disponiveis) == len(endpoints)

def main():
    print(f"\n{Colors.BLUE}")
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║  🔧 DIAGNÓSTICO DE COMPONENTES - IoT Agro API                    ║")
    print("║  Versão: Compatível com API Flask                                ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print(Colors.RESET)
    
    # Configuração
    api_url = input(f"{Colors.YELLOW}Informe a URL da API (padrão: http://localhost:5000): {Colors.RESET}") or "http://localhost:5000"
    
    resultados = {}
    
    # Teste 1: Saúde básica
    print_header("1️⃣  SAÚDE BÁSICA DA API")
    resultados['api_saude'], dados_saude = teste_api_saude(api_url)
    
    # Teste 2: Endpoints principais
    print_header("2️⃣  ENDPOINTS PRINCIPAIS")
    resultados['api_dados'], _ = teste_api_dados(api_url)
    resultados['api_ultimos'], _ = teste_api_ultimos(api_url)
    resultados['api_estatisticas'], _ = teste_api_estatisticas(api_url)
    resultados['api_alertas'], _ = teste_api_alertas(api_url)
    
    # Teste 3: Envio de dados
    print_header("3️⃣  ENVIO DE DADOS (POST)")
    resultados['api_post'], _ = teste_post_dados(api_url)
    
    # Teste 4: Rate limiting
    print_header("4️⃣  SEGURANÇA E LIMITES")
    resultados['rate_limiting'] = teste_rate_limiting(api_url)
    
    # Teste 5: Todos endpoints
    print_header("5️⃣  VERIFICAÇÃO COMPLETA")
    resultados['todos_endpoints'] = verificar_endpoints_disponiveis(api_url)
    
    # Resumo
    print_header("📊 RESUMO DOS TESTES")
    
    total = len(resultados)
    passou = sum(1 for v in resultados.values() if v)
    
    if passou == total:
        print(f"{Colors.GREEN}🎉 PERFEITO! {passou}/{total} testes passaram!{Colors.RESET}")
    elif passou >= total * 0.7:
        print(f"{Colors.YELLOW}⚠️  BOM! {passou}/{total} testes passaram{Colors.RESET}")
    else:
        print(f"{Colors.RED}❌ PROBLEMAS! Apenas {passou}/{total} testes passaram{Colors.RESET}")
    
    print(f"\n{Colors.BLUE}Detalhes:{Colors.RESET}")
    for nome, status in resultados.items():
        status_str = f"{Colors.GREEN}✅" if status else f"{Colors.RED}❌"
        print(f"   {status_str} {nome.replace('_', ' ').title()}{Colors.RESET}")
    
    # Recomendações
    print_header("📋 RECOMENDAÇÕES E SOLUÇÕES")
    
    if not resultados.get('api_saude'):
        print(f"{Colors.RED}❌ API não está respondendo!{Colors.RESET}")
        print(f"   {Colors.YELLOW}Solução:{Colors.RESET} Execute: python app.py na pasta api")
        print(f"   {Colors.YELLOW}Verifique:{Colors.RESET} Porta 5000 está livre?")
    
    if not resultados.get('api_dados'):
        print(f"{Colors.YELLOW}⚠️  API está rodando mas sem dados{Colors.RESET}")
        print(f"   {Colors.YELLOW}Solução:{Colors.RESET}")
        print(f"   1. Use o simulador: python simulador.py")
        print(f"   2. Ou envie dados manualmente via POST para /api/solo")
    
    if not resultados.get('api_post'):
        print(f"{Colors.RED}❌ Não consegue enviar dados para API{Colors.RESET}")
        print(f"   {Colors.YELLOW}Solução:{Colors.RESET}")
        print(f"   - Verifique se o MySQL está rodando")
        print(f"   - Confira as credenciais no arquivo .env")
    
    if resultados.get('api_saude') and dados_saude:
        db_status = dados_saude.get('database', 'desconhecido')
        if db_status != 'conectado':
            print(f"{Colors.RED}❌ Banco de dados: {db_status}{Colors.RESET}")
            print(f"   {Colors.YELLOW}Solução:{Colors.RESET}")
            print(f"   - Inicie o MySQL: sudo service mysql start")
            print(f"   - Verifique conexão: mysql -u root -p")
            print(f"   - Confira variáveis no .env")
    
    if passou == total:
        print(f"\n{Colors.GREEN}🎉 TUDO FUNCIONANDO PERFEITAMENTE!{Colors.RESET}")
        print(f"   {Colors.YELLOW}Próximos passos:{Colors.RESET}")
        print(f"   1. Acesse a documentação: {api_url}/")
        print(f"   2. Teste endpoints específicos")
        print(f"   3. Configure o frontend/dashboard")
        print(f"   4. Monitore os logs em logs/api.log")
    
    print_header("🚀 COMANDOS ÚTEIS")
    print(f"{Colors.YELLOW}Iniciar API:{Colors.RESET} python app.py")
    print(f"{Colors.YELLOW}Ver logs:{Colors.RESET} tail -f logs/api.log")
    print(f"{Colors.YELLOW}Testar endpoint:{Colors.RESET} curl {api_url}/api/saude")
    print(f"{Colors.YELLOW}Enviar dados teste:{Colors.RESET} curl -X POST {api_url}/api/solo -H 'Content-Type: application/json' -d @dados_teste.json")
    
    return 0 if passou == total else 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}Diagnóstico interrompido pelo usuário{Colors.RESET}\n")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}Erro durante diagnóstico: {e}{Colors.RESET}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)