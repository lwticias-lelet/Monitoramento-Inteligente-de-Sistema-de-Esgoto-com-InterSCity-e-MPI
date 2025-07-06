#!/usr/bin/env python3
"""
Worker Node para o Sistema de Monitoramento de Esgotamento Sanitário
Responsável por processar lotes de dados distribuídos pelo master
"""

import json
import time
import logging
from mpi4py import MPI
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional

class WorkerNode:
    def __init__(self):
        """Inicializa o nó worker"""
        self.comm = MPI.COMM_WORLD
        self.rank = self.comm.Get_rank()
        self.size = self.comm.Get_size()
        
        # Configurar logging
        self._setup_logging()
        
        # Verificar se não é o master
        if self.rank == 0:
            raise ValueError(f"Este processo é o master node. Rank: {self.rank}")
        
        self.logger.info(f"Worker node {self.rank} iniciado")
        
    def _setup_logging(self):
        """Configura o sistema de logging"""
        logging.basicConfig(
            level=logging.INFO,
            format=f'%(asctime)s - Worker[{self.rank}] - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def validate_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Valida e limpa os dados recebidos"""
        validated_data = []
        
        for record in data:
            try:
                # Verificar se campos obrigatórios estão presentes
                required_fields = ['sensor_id', 'flow_rate', 'pressure', 'temperature', 'ph_level']
                
                if not all(field in record for field in required_fields):
                    self.logger.warning(f"Registro inválido - campos faltando: {record}")
                    continue
                
                # Converter e validar tipos de dados
                validated_record = {
                    'sensor_id': str(record['sensor_id']),
                    'timestamp': record.get('timestamp', datetime.now().isoformat()),
                    'flow_rate': float(record['flow_rate']),
                    'pressure': float(record['pressure']),
                    'temperature': float(record['temperature']),
                    'ph_level': float(record['ph_level']),
                    'turbidity': float(record.get('turbidity', 0.0)),
                    'location_x': float(record.get('location_x', 0.0)),
                    'location_y': float(record.get('location_y', 0.0))
                }
                
                # Verificar valores válidos
                if (validated_record['flow_rate'] < 0 or 
                    validated_record['pressure'] < 0 or
                    validated_record['temperature'] < -50 or validated_record['temperature'] > 100 or
                    validated_record['ph_level'] < 0 or validated_record['ph_level'] > 14):
                    
                    self.logger.warning(f"Registro com valores inválidos: {validated_record}")
                    continue
                
                validated_data.append(validated_record)
                
            except (ValueError, TypeError) as e:
                self.logger.error(f"Erro ao validar registro {record}: {e}")
                continue
        
        return validated_data
    
    def detect_anomalies(self, data: List[Dict[str, Any]], thresholds: Dict[str, float]) -> List[Dict[str, Any]]:
        """Detecta anomalias nos dados baseado nos thresholds"""
        alerts = []
        
        for record in data:
            record_alerts = []
            
            # Verificar flow_rate
            if record['flow_rate'] > thresholds.get('flow_rate_max', 100.0):
                record_alerts.append({
                    'type': 'flow_rate_high',
                    'value': record['flow_rate'],
                    'threshold': thresholds.get('flow_rate_max', 100.0),
                    'severity': 'high'
                })
            
            # Verificar pressure
            if record['pressure'] > thresholds.get('pressure_max', 5.0):
                record_alerts.append({
                    'type': 'pressure_high',
                    'value': record['pressure'],
                    'threshold': thresholds.get('pressure_max', 5.0),
                    'severity': 'high'
                })
            
            # Verificar temperature
            if record['temperature'] > thresholds.get('temperature_max', 35.0):
                record_alerts.append({
                    'type': 'temperature_high',
                    'value': record['temperature'],
                    'threshold': thresholds.get('temperature_max', 35.0),
                    'severity': 'medium'
                })
            
            # Verificar pH
            ph_min = thresholds.get('ph_min', 6.0)
            ph_max = thresholds.get('ph_max', 8.5)
            
            if record['ph_level'] < ph_min:
                record_alerts.append({
                    'type': 'ph_low',
                    'value': record['ph_level'],
                    'threshold': ph_min,
                    'severity': 'high'
                })
            elif record['ph_level'] > ph_max:
                record_alerts.append({
                    'type': 'ph_high',
                    'value': record['ph_level'],
                    'threshold': ph_max,
                    'severity': 'high'
                })
            
            # Verificar turbidity
            if record['turbidity'] > thresholds.get('turbidity_max', 50.0):
                record_alerts.append({
                    'type': 'turbidity_high',
                    'value': record['turbidity'],
                    'threshold': thresholds.get('turbidity_max', 50.0),
                    'severity': 'medium'
                })
            
            # Adicionar alertas com informações do sensor
            for alert in record_alerts:
                alert.update({
                    'sensor_id': record['sensor_id'],
                    'timestamp': record['timestamp'],
                    'location_x': record['location_x'],
                    'location_y': record['location_y']
                })
                alerts.append(alert)
        
        return alerts
    
    def calculate_statistics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcula estatísticas básicas dos dados"""
        if not data:
            return {}
        
        df = pd.DataFrame(data)
        
        stats = {
            'count': len(data),
            'flow_rate_stats': {
                'mean': df['flow_rate'].mean(),
                'std': df['flow_rate'].std(),
                'min': df['flow_rate'].min(),
                'max': df['flow_rate'].max()
            },
            'pressure_stats': {
                'mean': df['pressure'].mean(),
                'std': df['pressure'].std(),
                'min': df['pressure'].min(),
                'max': df['pressure'].max()
            },
            'temperature_stats': {
                'mean': df['temperature'].mean(),
                'std': df['temperature'].std(),
                'min': df['temperature'].min(),
                'max': df['temperature'].max()
            },
            'ph_stats': {
                'mean': df['ph_level'].mean(),
                'std': df['ph_level'].std(),
                'min': df['ph_level'].min(),
                'max': df['ph_level'].max()
            }
        }
        
        return stats
    
    def process_batch(self, batch_data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa um lote de dados"""
        batch_id = batch_data['batch_id']
        data = batch_data['data']
        thresholds = batch_data['config']
        
        self.logger.info(f"Processando lote {batch_id} com {len(data)} registros")
        
        start_time = time.time()
        
        # Validar dados
        validated_data = self.validate_data(data)
        
        # Detectar anomalias
        alerts = self.detect_anomalies(validated_data, thresholds)
        
        # Calcular estatísticas
        stats = self.calculate_statistics(validated_data)
        
        processing_time = time.time() - start_time
        
        result = {
            'batch_id': batch_id,
            'worker_rank': self.rank,
            'records_processed': len(validated_data),
            'records_invalid': len(data) - len(validated_data),
            'alerts_count': len(alerts),
            'alerts': alerts,
            'statistics': stats,
            'processed_data': validated_data,
            'processing_time': processing_time
        }
        
        self.logger.info(f"Lote {batch_id} processado: {len(validated_data)} registros, "
                        f"{len(alerts)} alertas, {processing_time:.2f}s")
        
        return result
    
    def run(self):
        """Executa o loop principal do worker node"""
        self.logger.info("Worker aguardando trabalho...")
        
        try:
            while True:
                # Aguardar trabalho do master
                work_data = self.comm.recv(source=0, tag=1)
                
                # Verificar se é comando de finalização
                if work_data is None:
                    self.logger.info("Comando de finalização recebido")
                    break
                
                # Processar lote
                result = self.process_batch(work_data)
                
                # Enviar resultado de volta
                self.comm.send(result, dest=0, tag=2)
                
        except Exception as e:
            self.logger.error(f"Erro no worker: {e}")
        finally:
            self.logger.info("Worker finalizado")

if __name__ == "__main__":
    worker = WorkerNode()
    worker.run()