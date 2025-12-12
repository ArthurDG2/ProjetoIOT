#!/usr/bin/env python
"""
Script Interativo para Rodar Machine Learning
Facilita execução de análises e modelos
"""

import os
import sys
import subprocess
import mysql.connector
from datetime import datetime
from dotenv import load_dotenv

# Configuração do banco de dados, pega do .env
# Carrega variáveis do arquivo .env
load_dotenv()

db_config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

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

def verificar_dados():
    """Verifica quantos registros tem no banco"""
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM leituras")
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    except Exception as e:
        print(f"{Colors.RED}[ERRO] Erro ao conectar ao banco: {e}{Colors.RESET}")
        return 0

def menu_principal():
    """Menu principal"""
    print_header("[ML] MACHINE LEARNING - ANALISE AGRICOLA")
    
    # Verificar dados
    count = verificar_dados()
    print(f"[INFO] Registros no banco de dados: {Colors.GREEN}{count}{Colors.RESET}")
    
    if count < 50:
        print(f"{Colors.YELLOW}[AVISO] Recomendado ter pelo menos 100 registros para bons resultados{Colors.RESET}")
        print(f"   Deixe o simulador rodar: cd simulador && python alimentar_dados.py\n")
    
    print("Escolha uma opcao:\n")
    print(f"  {Colors.BLUE}1{Colors.RESET} - [CORRELACAO] Analise de Correlacao (Rapido)")
    print(f"  {Colors.BLUE}2{Colors.RESET} - [ML] Treinar Modelo ML (Recomendado)")
    print(f"  {Colors.BLUE}3{Colors.RESET} - [ALL] Rodar Tudo (Correlacao + ML)")
    print(f"  {Colors.BLUE}4{Colors.RESET} - [VIEW] Ver Resultados Anteriores")
    print(f"  {Colors.BLUE}5{Colors.RESET} - [CLEAN] Limpar Resultados")
    print(f"  {Colors.BLUE}0{Colors.RESET} - [EXIT] Sair")
    print()

def rodar_correlacao():
    """Executa análise de correlação"""
    print_header("[CORRELACAO] EXECUTANDO ANALISE DE CORRELACAO")
    
    try:
        print(f"{Colors.YELLOW}Carregando dados...{Colors.RESET}")
        result = subprocess.run(['python', 'correlacao.py'], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"{Colors.GREEN}[OK] Analise de Correlacao concluida!{Colors.RESET}")
            print(f"\n[FILES] Arquivos gerados:")
            print(f"   - docs/resultados/correlacao_pearson.csv")
            print(f"   - docs/resultados/correlacao_heatmap.png\n")
            return True
        else:
            print(f"{Colors.RED}[ERRO] Erro na analise:{Colors.RESET}")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"{Colors.RED}[ERRO] Erro: {e}{Colors.RESET}")
        return False

def rodar_ml():
    """Executa treinamento de modelo"""
    print_header("[ML] EXECUTANDO MACHINE LEARNING")
    
    try:
        print(f"{Colors.YELLOW}Carregando dados e treinando modelos...{Colors.RESET}")
        print(f"{Colors.YELLOW}Isso pode levar 30-60 segundos...{Colors.RESET}\n")
        
        result = subprocess.run(['python', 'modelo_producao.py'], capture_output=True, text=True)
        os.chdir('..')
        
        if result.returncode == 0:
            print(f"{Colors.GREEN}[OK] Treinamento concluido!{Colors.RESET}")
            print(f"\n[FILES] Arquivos gerados:")
            print(f"   - modelos/modelo_producao.pkl")
            print(f"   - modelos/scaler.pkl")
            print(f"   - docs/resultados/importancia_features.png")
            print(f"   - docs/resultados/relatorio_ml.txt\n")
            
            # Tentar ler o relatório
            try:
                with open('docs/resultados/relatorio_ml.txt', 'r', encoding='utf-8') as f:
                    conteudo = f.read()
                    print(f"{Colors.BLUE}{conteudo}{Colors.RESET}")
            except:
                pass
            
            return True
        else:
            print(f"{Colors.RED}[ERRO] Erro no treinamento:{Colors.RESET}")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"{Colors.RED}[ERRO] Erro: {e}{Colors.RESET}")
        return False

def rodar_tudo():
    """Executa correlação e ML"""
    print_header("[ALL] EXECUTANDO TUDO (CORRELACAO + ML)")
    
    print(f"{Colors.YELLOW}Fase 1: Análise de Correlação...{Colors.RESET}\n")
    if not rodar_correlacao():
        return False
    
    input(f"{Colors.BLUE}Pressione ENTER para continuar com ML...{Colors.RESET}")
    
    print()
    if not rodar_ml():
        return False
    
    print(f"{Colors.GREEN}[OK] Tudo concluido com sucesso!{Colors.RESET}\n")
    print(f"[NEXT] Proximas etapas:")
    print(f"   1. Analise os graficos em docs/resultados/")
    print(f"   2. Leia o relatorio em docs/resultados/relatorio_ml.txt")
    print(f"   3. Use o modelo para fazer predicoes\n")
    
    return True

def ver_resultados():
    """Mostra resultados anteriores"""
    print_header("[VIEW] RESULTADOS ANTERIORES")
    
    caminho = './docs/resultados/'
    
    if not os.path.exists(caminho):
        print(f"{Colors.RED}[ERRO] Pasta de resultados nao encontrada{Colors.RESET}")
        return
    
    arquivos = os.listdir(caminho)
    
    if not arquivos:
        print(f"{Colors.RED}[ERRO] Nenhum resultado gerado ainda{Colors.RESET}")
        return
    
    print(f"Arquivos disponíveis:\n")
    for i, arquivo in enumerate(arquivos, 1):
        caminho_completo = os.path.join(caminho, arquivo)
        tamanho = os.path.getsize(caminho_completo)
        tamanho_kb = tamanho / 1024
        print(f"  {Colors.BLUE}{i}{Colors.RESET}. {arquivo} ({tamanho_kb:.1f} KB)")
    
    # Tentar mostrar relatório
    relatorio = os.path.join(caminho, 'relatorio_ml.txt')
    if os.path.exists(relatorio):
        print(f"\n{Colors.BLUE}{'='*70}")
        print("Conteúdo do relatório:")
        print(f"{'='*70}{Colors.RESET}\n")
        try:
            with open(relatorio, 'r', encoding='utf-8') as f:
                print(f.read())
        except Exception as e:
            print(f"{Colors.RED}[ERRO] Erro ao ler: {e}{Colors.RESET}")

def limpar_resultados():
    """Limpa resultados anteriores"""
    print_header("[CLEAN] LIMPAR RESULTADOS")
    
    resposta = input(f"{Colors.YELLOW}Tem certeza? Isto apagará todos os gráficos e relatórios (s/n): {Colors.RESET}")
    
    if resposta.lower() != 's':
        print(f"{Colors.YELLOW}Cancelado{Colors.RESET}")
        return
    
    try:
        import shutil
        caminho = 'docs/resultados/'
        
        if os.path.exists(caminho):
            shutil.rmtree(caminho)
            os.makedirs(caminho)
            print(f"{Colors.GREEN}[OK] Resultados limpos!{Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}Pasta não existe{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}[ERRO] Erro: {e}{Colors.RESET}")

def main():
    """Loop principal"""
    while True:
        menu_principal()
        
        try:
            opcao = input(f"Digite sua escolha (0-5): {Colors.BLUE}")
            print(Colors.RESET)
            
            if opcao == '0':
                print(f"{Colors.YELLOW}Ate logo!{Colors.RESET}\n")
                break
            elif opcao == '1':
                rodar_correlacao()
            elif opcao == '2':
                count = verificar_dados()
                if count < 50:
                    print(f"{Colors.RED}[ERRO] Pouco dados no banco ({count} registros){Colors.RESET}")
                    print(f"   Execute: cd simulador && python alimentar_dados.py")
                else:
                    rodar_ml()
            elif opcao == '3':
                count = verificar_dados()
                if count < 50:
                    print(f"{Colors.RED}[ERRO] Pouco dados no banco ({count} registros){Colors.RESET}")
                else:
                    rodar_tudo()
            elif opcao == '4':
                ver_resultados()
            elif opcao == '5':
                limpar_resultados()
            else:
                print(f"{Colors.RED}[ERRO] Opcao invalida{Colors.RESET}")
            
            input(f"\n{Colors.YELLOW}Pressione ENTER para continuar...{Colors.RESET}")
        
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Cancelado pelo usuário{Colors.RESET}\n")
            break
        except Exception as e:
            print(f"{Colors.RED}[ERRO] Erro: {e}{Colors.RESET}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Saindo...{Colors.RESET}\n")
        sys.exit(0)