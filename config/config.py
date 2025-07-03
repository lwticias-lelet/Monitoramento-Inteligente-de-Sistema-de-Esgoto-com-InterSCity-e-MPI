"""
Configurações do Sistema de Monitoramento de Esgoto
"""
import os
from pathlib import Path

# Diretórios base
BASE_DIR = Path(__file__).parent.parent
SRC_DIR = BASE_DIR / "src"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Arquivos de dados
DADOS_ANYLOGIC = Path("C:/temp/dados_sensores.csv")
DADOS_SISTEMA = DATA_DIR / "dados_sistema.csv"
DADOS_PROCESSADOS = DATA_DIR / "dados_processados.json"

# Configurações do sistema
SISTEMA_CONFIG = {
    "mpi_processes": 4,
    "ciclos_monitoramento": 100,
    "intervalo_ciclo": 30,  # segundos
    "max_sensores": 20,
    "timeout_leitura": 10,  # segundos
}

# Configurações de detecção de anomalias
ANOMALIA_CONFIG = {
    "min_historico": 10,
    "max_historico": 50,
    "threshold_desvio": 2.5,
    "threshold_critico": 3.5,
    "prob_anomalia_teste": 0.05,
}

# Configurações do InterSCity
INTERSITY_CONFIG = {
    "host": "localhost",
    "port": 5000,
    "api_base": "/api",
    "timeout": 30,
    "retry_attempts": 3,
}

# Configurações de logging
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "[%(asctime)s] %(levelname)s - RANK %(rank)s: %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S",
    "max_log_size": 10 * 1024 * 1024,  # 10MB
    "backup_count": 5,
}

# Garantir que diretórios existem
def setup_directories():
    """Cria diretórios necessários se não existirem"""
    directories = [DATA_DIR, LOGS_DIR, Path("C:/temp")]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    print(f"✅ Diretórios configurados:")
    print(f"   📁 Projeto: {BASE_DIR}")
    print(f"   📁 Dados: {DATA_DIR}")
    print(f"   📁 Logs: {LOGS_DIR}")

if __name__ == "__main__":
    setup_directories()