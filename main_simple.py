#!/usr/bin/env python3
"""
Versão simplificada do sistema sem MPI
"""

import os
import sys
import json
import time
import logging
import argparse
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Adicionar o diretório src ao path
sys.path.append(str(Path(__file__).parent / "src"))

try:
    from data_processing.csv_processor import CSVProcessor
    from visualization.dashboard import MonitoringDashboard
except ImportError as e:
    print(f"Erro ao importar módulos: {e}")
    print("Certifique-se de que está no diretório correto do projeto")
    sys.exit(1)

class SimpleMonitoringSystem:
    """Sistema simplificado sem MPI"""
    
    def __init__(self, config_path: str = "config/config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self._setup_logging()
        
        self.csv_processor = None
        self.dashboard = None
        self.shutdown_flag = False
        
        self.logger.info("Sistema Simplificado inicializado")
    
    def _load_config(self) -> Dict[str, Any]:
        """Carrega configurações do sistema"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "system": {"debug": True},
                "data": {
                    "csv_input_path": "data/csv/",
                    "processed_output_path": "data/processed/",
                    "batch_size": 1000
                },
                "visualization": {"dashboard_port": 8050},
                "anylogic": {
                    "expected_columns": [
                        "timestamp", "sensor_id", "flow_rate", "pressure", 
                        "temperature", "ph_level", "turbidity", "location_x", "location_y"
                    ]
                }
            }
    
    def _setup_logging(self):
        """Configura logging"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / f"simple_system_{datetime.now().strftime('%Y%m%d')}.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def process_csv_file(self, file_path: str):
        """Processa um arquivo CSV específico"""
        try:
            self.csv_processor = CSVProcessor(self.config_path)
            result = self.csv_processor.process_file(file_path)
            
            if result is not None:
                self.logger.info(f"Arquivo processado: {len(result)} registros")
                return True
            else:
                self.logger.error("Erro no processamento")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao processar CSV: {e}")
            return False
    
    def run_dashboard(self):
        """Executa dashboard"""
        try:
            self.dashboard = MonitoringDashboard(self.config_path)
            self.dashboard.run(debug=self.config.get('system', {}).get('debug', True))
        except Exception as e:
            self.logger.error(f"Erro no dashboard: {e}")

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description="Sistema Simplificado de Monitoramento")
    
    parser.add_argument('--mode', choices=['process', 'dashboard', 'both'], default='both')
    parser.add_argument('--file', help='Arquivo CSV específico')
    parser.add_argument('--config', default='config/config.json')
    
    args = parser.parse_args()
    
    try:
        system = SimpleMonitoringSystem(args.config)
        
        if args.mode == 'process':
            if args.file:
                success = system.process_csv_file(args.file)
            else:
                print("Especifique um arquivo com --file")
                sys.exit(1)
            
            if not success:
                sys.exit(1)
        
        elif args.mode == 'dashboard':
            system.run_dashboard()
        
        elif args.mode == 'both':
            if args.file:
                system.process_csv_file(args.file)
            
            print("\n🚀 Iniciando dashboard...")
            print("📊 Acesse: http://localhost:8050")
            print("⏹️  Pressione Ctrl+C para parar")
            
            system.run_dashboard()
            
    except KeyboardInterrupt:
        print("\n⏹️  Sistema interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()