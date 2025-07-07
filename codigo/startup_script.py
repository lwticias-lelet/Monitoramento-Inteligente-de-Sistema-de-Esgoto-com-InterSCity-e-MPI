#!/usr/bin/env python3
"""
Script de inicialização simplificado e corrigido para o Sistema de Monitoramento
"""

import os
import sys
import subprocess
from pathlib import Path

def print_banner():
    """Exibe banner do sistema"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║          Sistema de Monitoramento de Esgotamento Sanitário  ║
║                     Versão Corrigida 1.0                   ║
╚══════════════════════════════════════════════════════════════╝
    """)

def check_python():
    """Verifica versão do Python"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor} não suportado. Requer Python 3.8+")
        return False

def setup_environment():
    """Configura ambiente básico"""
    print("\n🔧 Configurando ambiente...")
    
    # Criar diretórios necessários
    directories = [
        "data/csv",
        "data/processed", 
        "logs",
        "config"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 {directory}")
    
    print("✅ Diretórios criados")

def install_basic_dependencies():
    """Instala dependências básicas"""
    print("\n📦 Instalando dependências básicas...")
    
    basic_packages = [
        "pandas>=2.0.0",
        "numpy>=1.24.0", 
        "plotly>=5.15.0",
        "dash>=2.13.0",
        "dash-bootstrap-components>=1.4.0",
        "requests>=2.28.0"
    ]
    
    for package in basic_packages:
        try:
            print(f"  Instalando {package}...")
            subprocess.run([sys.executable, "-m", "pip", "install", package], 
                         check=True, capture_output=True)
            print(f"  ✅ {package}")
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Erro ao instalar {package}: {e}")
            return False
    
    print("✅ Dependências instaladas")
    return True

def create_sample_csv():
    """Cria arquivo CSV de exemplo"""
    print("\n📄 Criando arquivo CSV de exemplo...")
    
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta
    
    # Gerar dados de exemplo
    n_records = 50
    base_time = datetime.now() - timedelta(hours=1)
    
    data = []
    for i in range(n_records):
        for sensor_id in range(1, 4):  # 3 sensores
            timestamp = base_time + timedelta(minutes=i*2)
            
            record = {
                'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'sensor_id': f'S{sensor_id:03d}',
                'flow_rate': np.random.normal(50, 10),
                'pressure': np.random.normal(2.5, 0.5),
                'temperature': np.random.normal(25, 3),
                'ph_level': np.random.normal(7.2, 0.5),
                'turbidity': np.random.normal(20, 5),
                'location_x': -46.731386 + np.random.normal(0, 0.01),
                'location_y': -23.559616 + np.random.normal(0, 0.01),
                'status': np.random.choice(['NORMAL', 'ALERTA'], p=[0.9, 0.1])
            }
            data.append(record)
    
    df = pd.DataFrame(data)
    sample_file = Path("data/csv/monitoramento_sample.csv")
    df.to_csv(sample_file, index=False)
    
    print(f"✅ Arquivo criado: {sample_file} ({len(df)} registros)")
    return str(sample_file)

def test_system():
    """Testa componentes do sistema"""
    print("\n🧪 Testando componentes...")
    
    try:
        # Testar imports
        sys.path.insert(0, str(Path.cwd()))
        sys.path.insert(0, str(Path.cwd() / "src"))
        
        print("  Testando imports...")
        
        # Teste básico de pandas
        import pandas as pd
        print("  ✅ pandas")
        
        # Teste básico de plotly
        import plotly.graph_objs as go
        print("  ✅ plotly")
        
        # Teste básico de dash
        from dash import Dash, html, dcc
        print("  ✅ dash")
        
        print("✅ Todos os imports funcionando")
        return True
        
    except ImportError as e:
        print(f"❌ Erro de import: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def run_dashboard_only():
    """Executa apenas o dashboard com dados de exemplo"""
    print("\n🚀 Iniciando dashboard...")
    
    try:
        # Executar dashboard diretamente
        exec(open("src/visualization/dashboard.py").read())
        
    except FileNotFoundError:
        print("❌ Arquivo dashboard.py não encontrado")
        print("💡 Executando dashboard inline...")
        
        # Dashboard mínimo inline
        from dash import Dash, html, dcc
        import dash_bootstrap_components as dbc
        
        app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        
        app.layout = dbc.Container([
            html.H1("🚰 Sistema de Monitoramento", className="text-center text-primary mb-4"),
            dbc.Alert("Sistema funcionando! Dashboard básico ativo.", color="success"),
            html.P("Para funcionalidade completa, execute: python scripts/main_simple.py --mode dashboard")
        ])
        
        print("✅ Dashboard básico iniciado em http://localhost:8050")
        app.run(debug=True, port=8050)
        
    except Exception as e:
        print(f"❌ Erro ao executar dashboard: {e}")

def main():
    """Função principal"""
    print_banner()
    
    # Verificar Python
    if not check_python():
        print("\n❌ Sistema não pode continuar. Instale Python 3.8+")
        return False
    
    # Configurar ambiente
    setup_environment()
    
    # Instalar dependências
    if not install_basic_dependencies():
        print("\n❌ Falha na instalação de dependências")
        return False
    
    # Criar dados de exemplo
    sample_file = create_sample_csv()
    
    # Testar sistema
    if not test_system():
        print("\n❌ Falha nos testes do sistema")
        return False
    
    print(f"""
✅ Sistema configurado com sucesso!

📋 Próximos passos:

1. Dashboard apenas:
   python scripts/main_simple.py --mode dashboard

2. Processar dados:
   python scripts/main_simple.py --mode process --file "{sample_file}"

3. Sistema completo:
   python scripts/main_simple.py --mode both --file "{sample_file}"

4. Com InterSCity:
   python scripts/main_simple.py --mode both --enable-interscity

🌐 Dashboard estará em: http://localhost:8050
    """)
    
    # Perguntar se quer iniciar dashboard
    try:
        choice = input("\n🚀 Iniciar dashboard agora? (s/N): ").lower().strip()
        if choice in ['s', 'sim', 'y', 'yes']:
            run_dashboard_only()
    except KeyboardInterrupt:
        print("\n👋 Até logo!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)