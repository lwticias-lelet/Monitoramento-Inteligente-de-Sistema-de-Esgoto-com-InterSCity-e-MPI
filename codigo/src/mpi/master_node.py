#!/usr/bin/env python3
"""
Master Node para o Sistema de Monitoramento de Esgotamento Sanitário
Responsável por coordenar o processamento distribuído dos dados
"""

import json
import time
import logging
from mpi4py import MPI
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

class MasterNode:
    def __init__(self, config_path: str = "config/config.json"):
        """Inicializa o nó master"""
        self.comm = MPI.COMM_WORLD
        self.rank = self.comm.Get_rank()
        self.size = self.comm.Get_size()
        
        # Carregar configurações
        self.config = self._load_config(config_path)
        
        # Configurar logging
        self._setup_logging()
        
        # Verificar se é o master
        if self.rank != self.config['mpi']['master_rank']:
            raise ValueError(f"Este processo não é o master node. Rank: {self.rank}")
        
        self.logger.info(f"Master node iniciado com {self.size} processos")
        
        # Inicializar estruturas de dados
        self.data_queue = []
        self.results_buffer = []
        self.worker_status = {i: 'idle' for i in range(1, self.size)}
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Carrega configurações do arquivo JSON"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Arquivo de configuração não encontrado: {config_path}")
    
    def _setup_logging(self):
        """Configura o sistema de logging"""
        logging.basicConfig(
            level=logging.INFO if self.config['system']['debug'] else logging.WARNING,
            format='%(asctime)s - Master[%(process)d] - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def load_data_from_anylogic(self) -> pd.DataFrame:
        """Carrega dados exportados do AnyLogic"""
        csv_path = self.config['anylogic']['export_path']
        
        try:
            if not Path(csv_path).exists():
                self.logger.warning(f"Arquivo CSV não encontrado: {csv_path}")
                return pd.DataFrame()
            
            df = pd.read_csv(csv_path)
            self.logger.info(f"Carregados {len(df)} registros do AnyLogic")
            
            # Validar colunas esperadas
            expected_cols = self.config['anylogic']['expected_columns']
            missing_cols = set(expected_cols) - set(df.columns)
            
            if missing_cols:
                self.logger.warning(f"Colunas faltando no CSV: {missing_cols}")
            
            return df
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar dados do AnyLogic: {e}")
            return pd.DataFrame()
    
    def distribute_work(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Distribui o trabalho entre os workers"""
        if data.empty:
            return []
        
        batch_size = self.config['data']['batch_size']
        num_workers = self.size - 1
        
        # Dividir dados em lotes
        batches = []
        for i in range(0, len(data), batch_size):
            batch = data.iloc[i:i+batch_size]
            batches.append(batch.to_dict('records'))
        
        self.logger.info(f"Distribuindo {len(batches)} lotes entre {num_workers} workers")
        
        # Enviar trabalho para workers
        results = []
        batch_idx = 0
        active_workers = set()
        
        # Enviar trabalho inicial
        for worker_rank in range(1, min(self.size, len(batches) + 1)):
            if batch_idx < len(batches):
                work_data = {
                    'batch_id': batch_idx,
                    'data': batches[batch_idx],
                    'config': self.config['monitoring']['alert_thresholds']
                }
                
                self.comm.send(work_data, dest=worker_rank, tag=1)
                active_workers.add(worker_rank)
                self.worker_status[worker_rank] = 'working'
                batch_idx += 1
                
                self.logger.debug(f"Enviado lote {batch_idx-1} para worker {worker_rank}")
        
        # Coletar resultados e enviar mais trabalho
        while active_workers:
            for worker_rank in list(active_workers):
                if self.comm.iprobe(source=worker_rank, tag=2):
                    result = self.comm.recv(source=worker_rank, tag=2)
                    results.append(result)
                    
                    self.logger.debug(f"Recebido resultado do worker {worker_rank}")
                    
                    # Enviar mais trabalho se disponível
                    if batch_idx < len(batches):
                        work_data = {
                            'batch_id': batch_idx,
                            'data': batches[batch_idx],
                            'config': self.config['monitoring']['alert_thresholds']
                        }
                        
                        self.comm.send(work_data, dest=worker_rank, tag=1)
                        batch_idx += 1
                        
                        self.logger.debug(f"Enviado lote {batch_idx-1} para worker {worker_rank}")
                    else:
                        # Sem mais trabalho, finalizar worker
                        self.comm.send(None, dest=worker_rank, tag=1)
                        active_workers.remove(worker_rank)
                        self.worker_status[worker_rank] = 'idle'
            
            time.sleep(0.1)  # Pequena pausa para evitar uso excessivo de CPU
        
        return results
    
    def process_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Processa e consolida os resultados dos workers"""
        if not results:
            return {}
        
        # Consolidar estatísticas
        total_records = sum(r.get('records_processed', 0) for r in results)
        total_alerts = sum(r.get('alerts_count', 0) for r in results)
        
        # Coletar todos os alertas
        all_alerts = []
        for result in results:
            all_alerts.extend(result.get('alerts', []))
        
        # Calcular estatísticas agregadas
        all_data = []
        for result in results:
            all_data.extend(result.get('processed_data', []))
        
        if all_data:
            df_all = pd.DataFrame(all_data)
            
            stats = {
                'total_records': total_records,
                'total_alerts': total_alerts,
                'processing_time': datetime.now().isoformat(),
                'statistics': {
                    'flow_rate': {
                        'mean': df_all['flow_rate'].mean(),
                        'std': df_all['flow_rate'].std(),
                        'min': df_all['flow_rate'].min(),
                        'max': df_all['flow_rate'].max()
                    },
                    'pressure': {
                        'mean': df_all['pressure'].mean(),
                        'std': df_all['pressure'].std(),
                        'min': df_all['pressure'].min(),
                        'max': df_all['pressure'].max()
                    },
                    'temperature': {
                        'mean': df_all['temperature'].mean(),
                        'std': df_all['temperature'].std(),
                        'min': df_all['temperature'].min(),
                        'max': df_all['temperature'].max()
                    }
                },
                'alerts': all_alerts
            }
        else:
            stats = {
                'total_records': 0,
                'total_alerts': 0,
                'processing_time': datetime.now().isoformat(),
                'statistics': {},
                'alerts': []
            }
        
        return stats
    
    def save_results(self, results: Dict[str, Any]):
        """Salva os resultados processados"""
        output_path = Path(self.config['data']['processed_output_path'])
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_path / f"processed_results_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Resultados salvos em: {output_file}")
    
    def run(self):
        """Executa o loop principal do master node"""
        self.logger.info("Iniciando processamento distribuído")
        
        try:
            while True:
                # Carregar dados do AnyLogic
                data = self.load_data_from_anylogic()
                
                if not data.empty:
                    # Distribuir trabalho
                    results = self.distribute_work(data)
                    
                    # Processar resultados
                    final_results = self.process_results(results)
                    
                    # Salvar resultados
                    self.save_results(final_results)
                    
                    # Log estatísticas
                    self.logger.info(f"Processados {final_results['total_records']} registros")
                    self.logger.info(f"Gerados {final_results['total_alerts']} alertas")
                
                # Aguardar próximo ciclo
                time.sleep(self.config['anylogic']['polling_interval'])
                
        except KeyboardInterrupt:
            self.logger.info("Interrompido pelo usuário")
        except Exception as e:
            self.logger.error(f"Erro no processamento: {e}")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Finaliza o master node e todos os workers"""
        self.logger.info("Finalizando workers...")
        
        # Enviar comando de finalização para todos os workers
        for worker_rank in range(1, self.size):
            self.comm.send(None, dest=worker_rank, tag=1)
        
        self.logger.info("Master node finalizado")

if __name__ == "__main__":
    master = MasterNode()
    master.run()