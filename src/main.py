#!/usr/bin/env python3
"""
Sistema de Monitoramento Inteligente de Esgotamento Sanitário
Arquivo principal para coordenar todos os módulos
"""

import os
import sys
import json
import time
import logging
import argparse
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Adicionar o diretório src ao path
sys.path.append(str(Path(__file__).parent))

from mpi.master_node import MasterNode
from mpi.worker_node import WorkerNode
from anylogic_integration.anylogic_connector import AnyLogicConnector
from data_processing.csv_processor import CSVProcessor
from visualization.dashboard import MonitoringDashboard

class MonitoringSystem:
    """Sistema principal de monitoramento"""
    
    def __init__(self, config_path: str = "config/config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self._setup_logging()
        
        # Componentes do sistema
        self.anylogic_connector = None
        self.csv_processor = None
        self.dashboard = None
        
        # Controle de threads
        self.threads = {}
        self.shutdown_flag = False
        
        self.logger.info("Sistema de Monitoramento inicializado")
    
    def _load_config(self) -> Dict[str, Any]:
        """Carrega configurações do sistema"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Arquivo de configuração não encontrado: {self.config_path}")
    
    def _setup_logging(self):
        """Configura o sistema de logging"""
        # Criar diretório de logs
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Configurar logging
        log_level = logging.INFO if self.config['system']['debug'] else logging.WARNING
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / f"system_{datetime.now().strftime('%Y%m%d')}.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def check_dependencies(self) -> bool:
        """Verifica se todas as dependências estão instaladas"""
        try:
            import mpi4py
            import pandas
            import numpy
            import plotly
            import dash
            
            self.logger.info("Todas as dependências estão instaladas")
            return True
            
        except ImportError as e:
            self.logger.error(f"Dependência faltando: {e}")
            return False
    
    def setup_directories(self):
        """Cria diretórios necessários"""
        directories = [
            self.config['data']['csv_input_path'],
            self.config['data']['processed_output_path'],
            "data/notifications",
            "logs"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
        
        self.logger.info("Diretórios configurados")
    
    def start_anylogic_connector(self):
        """Inicia o conector AnyLogic em thread separada"""
        def run_connector():
            try:
                self.anylogic_connector = AnyLogicConnector(self.config_path)
                self.anylogic_connector.start_monitoring()
            except Exception as e:
                self.logger.error(f"Erro no conector AnyLogic: {e}")
        
        thread = threading.Thread(target=run_connector, name="AnyLogic-Connector")
        thread.daemon = True
        thread.start()
        
        self.threads['anylogic'] = thread
        self.logger.info("Conector AnyLogic iniciado")
    
    def start_dashboard(self):
        """Inicia o dashboard em thread separada"""
        def run_dashboard():
            try:
                self.dashboard = MonitoringDashboard(self.config_path)
                self.dashboard.run(debug=self.config['system']['debug'])
            except Exception as e:
                self.logger.error(f"Erro no dashboard: {e}")
        
        thread = threading.Thread(target=run_dashboard, name="Dashboard")
        thread.daemon = True
        thread.start()
        
        self.threads['dashboard'] = thread
        self.logger.info("Dashboard iniciado")
    
    def run_mpi_system(self):
        """Executa o sistema MPI distribuído"""
        try:
            from mpi4py import MPI
            
            comm = MPI.COMM_WORLD
            rank = comm.Get_rank()
            
            if rank == 0:
                # Master node
                self.logger.info("Iniciando como Master Node")
                master = MasterNode(self.config_path)
                master.run()
            else:
                # Worker node
                self.logger.info(f"Iniciando como Worker Node {rank}")
                worker = WorkerNode()
                worker.run()
                
        except Exception as e:
            self.logger.error(f"Erro no sistema MPI: {e}")
    
    def run_standalone_mode(self):
        """Executa em modo standalone (sem MPI)"""
        self.logger.info("Executando em modo standalone")
        
        # Inicializar processador CSV
        self.csv_processor = CSVProcessor(self.config_path)
        
        try:
            while not self.shutdown_flag:
                # Processar novos arquivos CSV
                csv_files = list(Path(self.config['data']['csv_input_path']).glob("*.csv"))
                
                for csv_file in csv_files:
                    try:
                        self.logger.info(f"Processando arquivo: {csv_file}")
                        result = self.csv_processor.process_file(str(csv_file))
                        
                        if result is not None:
                            self.logger.info(f"Arquivo processado com sucesso: {len(result)} registros")
                        
                    except Exception as e:
                        self.logger.error(f"Erro ao processar {csv_file}: {e}")
                
                # Aguardar próximo ciclo
                time.sleep(self.config['anylogic']['polling_interval'])
                
        except KeyboardInterrupt:
            self.logger.info("Interrompido pelo usuário")
        except Exception as e:
            self.logger.error(f"Erro no modo standalone: {e}")
    
    def run_system(self, mode: str = "mpi"):
        """Executa o sistema completo"""
        self.logger.info(f"Iniciando sistema em modo: {mode}")
        
        # Verificar dependências
        if not self.check_dependencies():
            self.logger.error("Dependências não atendidas")
            return False
        
        # Configurar diretórios
        self.setup_directories()
        
        try:
            if mode == "mpi":
                # Modo distribuído com MPI
                
                # Iniciar componentes auxiliares apenas no master
                from mpi4py import MPI
                if MPI.COMM_WORLD.Get_rank() == 0:
                    self.start_anylogic_connector()
                    self.start_dashboard()
                    
                    # Aguardar um pouco para componentes iniciarem
                    time.sleep(5)
                
                # Executar sistema MPI
                self.run_mpi_system()
                
            elif mode == "standalone":
                # Modo standalone
                self.start_anylogic_connector()
                self.start_dashboard()
                
                # Aguardar componentes iniciarem
                time.sleep(5)
                
                # Executar processamento standalone
                self.run_standalone_mode()
                
            elif mode == "dashboard":
                # Apenas dashboard
                dashboard = MonitoringDashboard(self.config_path)
                dashboard.run(debug=self.config['system']['debug'])
                
            elif mode == "connector":
                # Apenas conector AnyLogic
                connector = AnyLogicConnector(self.config_path)
                connector.start_monitoring()
                
            else:
                self.logger.error(f"Modo desconhecido: {mode}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na execução do sistema: {e}")
            return False
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Finaliza o sistema graciosamente"""
        self.logger.info("Finalizando sistema...")
        
        self.shutdown_flag = True
        
        # Parar conector AnyLogic
        if self.anylogic_connector:
            try:
                self.anylogic_connector.stop_monitoring()
            except:
                pass