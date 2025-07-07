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

# Adicionar diretório raiz ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from src.data_processing.csv_processor import CSVProcessor, CSVProcessorWithInterSCity
    from src.visualization.dashboard import MonitoringDashboard
except ImportError as e:
    print(f"Erro ao importar módulos: {e}")
    print("Certifique-se de que está no diretório correto do projeto")
    sys.exit(1)

class SimpleMonitoringSystem:
    """Sistema simplificado sem MPI"""
    
    def __init__(self, config_path: str = "config/config.json", interscity_url: str = None):
        self.config_path = config_path
        self.config = self._load_config()
        self._setup_logging()
        
        # Configurar integração InterSCity
        self.interscity_url = interscity_url
        self.interscity_enabled = interscity_url is not None
        
        # Componentes do sistema
        self.csv_processor = None
        self.dashboard = None
        
        # Controle de threads
        self.threads = {}
        self.shutdown_flag = False
        
        if self.interscity_enabled:
            self.logger.info(f"Sistema inicializado com InterSCity: {interscity_url}")
        else:
            self.logger.info("Sistema inicializado")
    
    def process_csv_file(self, file_path: str):
        """Processa um arquivo CSV específico"""
        try:
            if self.interscity_enabled:
                self.csv_processor = CSVProcessorWithInterSCity(self.config_path, self.interscity_url)
                self.logger.info("Usando processador com integração InterSCity")
            else:
                self.csv_processor = CSVProcessor(self.config_path)
                self.logger.info("Usando processador padrão")
            
            result = self.csv_processor.process_file(file_path)
            
            if result is not None:
                self.logger.info(f"Arquivo processado: {len(result)} registros")
                if self.interscity_enabled:
                    self.logger.info("Dados sincronizados com InterSCity")
                return True
            else:
                self.logger.error("Erro no processamento")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao processar CSV: {e}")
            return False
    
    def test_interscity_connection(self):
        """Testa conexão com InterSCity"""
        if not self.interscity_enabled:
            self.logger.info("InterSCity não está habilitado")
            return False
        
        try:
            from interscity_integration.interscity_connector import InterSCityConnector
            interscity = InterSCityConnector(self.interscity_url)
            
            # Testar listagem de capabilities
            capabilities = interscity.list_capabilities()
            if capabilities:
                self.logger.info(f"✓ Conexão com InterSCity funcionando! {len(capabilities)} capabilities encontradas")
                return True
            else:
                self.logger.error("✗ Falha na conexão com InterSCity")
                return False
                
        except Exception as e:
            self.logger.error(f"✗ Erro ao testar InterSCity: {e}")
            return False

# MODIFICAR a função main para adicionar argumentos InterSCity:
def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description="Sistema Simplificado de Monitoramento")
    
    parser.add_argument('--mode', choices=['process', 'dashboard', 'both', 'test-interscity'], default='both')
    parser.add_argument('--file', help='Arquivo CSV específico')
    parser.add_argument('--config', default='config/config.json')
    parser.add_argument('--interscity-url', default='http://api.playground.interscity.org', help='URL do InterSCity')
    parser.add_argument('--enable-interscity', action='store_true', help='Habilitar integração InterSCity')
    
    args = parser.parse_args()
    
    # Configurar InterSCity
    interscity_url = args.interscity_url if args.enable_interscity else None
    
    try:
        system = SimpleMonitoringSystem(args.config, interscity_url)
        
        if args.mode == 'test-interscity':
            if system.test_interscity_connection():
                print("✓ InterSCity funcionando corretamente!")
            else:
                print("✗ Problema com InterSCity")
                sys.exit(1)
        
        elif args.mode == 'process':
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
            
            print("\n Iniciando dashboard...")
            if system.interscity_enabled:
                print(" Dashboard: http://localhost:8050")
                print(" InterSCity: http://api.playground.interscity.org")
            else:
                print(" Dashboard: http://localhost:8050")
            print(" Pressione Ctrl+C para parar")
            
            system.run_dashboard()
            
    except KeyboardInterrupt:
        print("\n  Sistema interrompido pelo usuário")
    except Exception as e:
        print(f" Erro crítico: {e}")
        sys.exit(1)
if __name__ == "__main__":
    main()