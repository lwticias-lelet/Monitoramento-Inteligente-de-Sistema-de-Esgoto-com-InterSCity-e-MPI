#!/usr/bin/env python3
"""
Conector para integração com AnyLogic
Monitora arquivos CSV gerados pelo AnyLogic e processa novos dados
"""

import json
import time
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class AnyLogicFileHandler(FileSystemEventHandler):
    """Handler para monitorar mudanças nos arquivos do AnyLogic"""
    
    def __init__(self, connector):
        self.connector = connector
        self.logger = logging.getLogger(__name__)
    
    def on_modified(self, event):
        """Chamado quando um arquivo é modificado"""
        if not event.is_directory:
            file_path = Path(event.src_path)
            
            # Verificar se é um arquivo CSV
            if file_path.suffix.lower() == '.csv':
                self.logger.info(f"Arquivo CSV modificado: {file_path}")
                self.connector.process_new_data(file_path)
    
    def on_created(self, event):
        """Chamado quando um arquivo é criado"""
        if not event.is_directory:
            file_path = Path(event.src_path)
            
            # Verificar se é um arquivo CSV
            if file_path.suffix.lower() == '.csv':
                self.logger.info(f"Novo arquivo CSV criado: {file_path}")
                # Aguardar um pouco para garantir que o arquivo foi completamente escrito
                time.sleep(2)
                self.connector.process_new_data(file_path)

class AnyLogicConnector:
    """Conector principal para integração com AnyLogic"""
    
    def __init__(self, config_path: str = "config/config.json"):
        self.config = self._load_config(config_path)
        self._setup_logging()
        
        # Configurar caminhos
        self.watch_path = Path(self.config['data']['csv_input_path'])
        self.watch_path.mkdir(parents=True, exist_ok=True)
        
        # Configurar observer para monitoramento de arquivos
        self.observer = Observer()
        self.file_handler = AnyLogicFileHandler(self)
        
        # Controle de processamento
        self.last_processed_time = {}
        self.processing_lock = False
        
        self.logger.info("AnyLogic Connector inicializado")
    
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
            format='%(asctime)s - AnyLogic - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def validate_csv_structure(self, df: pd.DataFrame) -> bool:
        """Valida se o CSV tem a estrutura esperada"""
        expected_columns = self.config['anylogic']['expected_columns']
        
        # Verificar se todas as colunas esperadas estão presentes
        missing_columns = set(expected_columns) - set(df.columns)
        
        if missing_columns:
            self.logger.error(f"Colunas faltando no CSV: {missing_columns}")
            return False
        
        # Verificar se há dados
        if df.empty:
            self.logger.warning("CSV está vazio")
            return False
        
        return True
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpa e padroniza os dados do CSV"""
        try:
            # Fazer cópia para não modificar o original
            cleaned_df = df.copy()
            
            # Remover linhas com valores nulos em campos críticos
            critical_fields = ['sensor_id', 'flow_rate', 'pressure', 'temperature']
            cleaned_df = cleaned_df.dropna(subset=critical_fields)
            
            # Converter timestamp para datetime se necessário
            if 'timestamp' in cleaned_df.columns:
                cleaned_df['timestamp'] = pd.to_datetime(cleaned_df['timestamp'], errors='coerce')
            
            # Remover outliers extremos
            numeric_columns = ['flow_rate', 'pressure', 'temperature', 'ph_level', 'turbidity']
            
            for col in numeric_columns:
                if col in cleaned_df.columns:
                    # Aplicar limite baseado em percentis
                    Q1 = cleaned_df[col].quantile(0.01)
                    Q3 = cleaned_df[col].quantile(0.99)
                    IQR = Q3 - Q1
                    
                    lower_bound = Q1 - 3 * IQR
                    upper_bound = Q3 + 3 * IQR
                    
                    cleaned_df = cleaned_df[
                        (cleaned_df[col] >= lower_bound) & 
                        (cleaned_df[col] <= upper_bound)
                    ]
            
            # Adicionar metadados
            cleaned_df['processed_timestamp'] = datetime.now()
            cleaned_df['data_source'] = 'anylogic'
            
            self.logger.info(f"Dados limpos: {len(df)} -> {len(cleaned_df)} registros")
            
            return cleaned_df
            
        except Exception as e:
            self.logger.error(f"Erro ao limpar dados: {e}")
            return df
    
    def process_new_data(self, file_path: Path):
        """Processa novo arquivo de dados"""
        if self.processing_lock:
            self.logger.info("Processamento já em andamento, ignorando...")
            return
        
        try:
            self.processing_lock = True
            
            # Verificar se o arquivo foi modificado recentemente
            file_mtime = file_path.stat().st_mtime
            last_processed = self.last_processed_time.get(str(file_path), 0)
            
            if file_mtime <= last_processed:
                self.logger.debug(f"Arquivo {file_path} já foi processado")
                return
            
            # Carregar dados
            self.logger.info(f"Processando arquivo: {file_path}")
            df = pd.read_csv(file_path)
            
            # Validar estrutura
            if not self.validate_csv_structure(df):
                self.logger.error(f"Estrutura inválida no arquivo: {file_path}")
                return
            
            # Limpar dados
            cleaned_df = self.clean_data(df)
            
            # Salvar dados processados
            self.save_processed_data(cleaned_df, file_path)
            
            # Atualizar timestamp de processamento
            self.last_processed_time[str(file_path)] = file_mtime
            
            # Notificar sistema de monitoramento
            self.notify_new_data(cleaned_df)
            
        except Exception as e:
            self.logger.error(f"Erro ao processar arquivo {file_path}: {e}")
        finally:
            self.processing_lock = False
    
    def save_processed_data(self, df: pd.DataFrame, source_file: Path):
        """Salva dados processados"""
        output_path = Path(self.config['data']['processed_output_path'])
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Gerar nome do arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        source_name = source_file.stem
        output_file = output_path / f"{source_name}_processed_{timestamp}.csv"
        
        # Salvar CSV
        df.to_csv(output_file, index=False)
        
        # Salvar metadados
        metadata = {
            'source_file': str(source_file),
            'processed_timestamp': datetime.now().isoformat(),
            'records_count': len(df),
            'columns': list(df.columns),
            'processing_info': {
                'data_range': {
                    'start': df['timestamp'].min().isoformat() if 'timestamp' in df.columns else None,
                    'end': df['timestamp'].max().isoformat() if 'timestamp' in df.columns else None
                },
                'sensors_count': df['sensor_id'].nunique() if 'sensor_id' in df.columns else 0
            }
        }
        
        metadata_file = output_path / f"{source_name}_metadata_{timestamp}.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Dados processados salvos: {output_file}")
    
    def notify_new_data(self, df: pd.DataFrame):
        """Notifica o sistema sobre novos dados disponíveis"""
        # Criar arquivo de notificação para o sistema MPI
        notification = {
            'timestamp': datetime.now().isoformat(),
            'records_count': len(df),
            'sensors': df['sensor_id'].unique().tolist() if 'sensor_id' in df.columns else [],
            'data_summary': {
                'flow_rate_range': [df['flow_rate'].min(), df['flow_rate'].max()] if 'flow_rate' in df.columns else [],
                'pressure_range': [df['pressure'].min(), df['pressure'].max()] if 'pressure' in df.columns else [],
                'temperature_range': [df['temperature'].min(), df['temperature'].max()] if 'temperature' in df.columns else []
            }
        }
        
        # Salvar notificação
        notification_file = Path("data/notifications/new_data.json")
        notification_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(notification_file, 'w', encoding='utf-8') as f:
            json.dump(notification, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Notificação enviada: {len(df)} novos registros")
    
    def start_monitoring(self):
        """Inicia o monitoramento de arquivos"""
        self.logger.info(f"Iniciando monitoramento em: {self.watch_path}")
        
        # Configurar observer
        self.observer.schedule(
            self.file_handler,
            str(self.watch_path),
            recursive=True
        )
        
        # Iniciar monitoramento
        self.observer.start()
        
        try:
            while True:
                time.sleep(self.config['anylogic']['polling_interval'])
                
                # Processar arquivos existentes periodicamente
                self.process_existing_files()
                
        except KeyboardInterrupt:
            self.logger.info("Interrompido pelo usuário")
        finally:
            self.stop_monitoring()
    
    def process_existing_files(self):
        """Processa arquivos existentes no diretório"""
        csv_files = list(self.watch_path.glob("*.csv"))
        
        for csv_file in csv_files:
            try:
                # Verificar se o arquivo foi modificado
                file_mtime = csv_file.stat().st_mtime
                last_processed = self.last_processed_time.get(str(csv_file), 0)
                
                if file_mtime > last_processed:
                    self.process_new_data(csv_file)
                    
            except Exception as e:
                self.logger.error(f"Erro ao processar arquivo existente {csv_file}: {e}")
    
    def stop_monitoring(self):
        """Para o monitoramento de arquivos"""
        self.logger.info("Parando monitoramento...")
        self.observer.stop()
        self.observer.join()
        self.logger.info("Monitoramento parado")
    
    def get_latest_data(self) -> Optional[pd.DataFrame]:
        """Retorna os dados mais recentes processados"""
        processed_path = Path(self.config['data']['processed_output_path'])
        
        if not processed_path.exists():
            return None
        
        # Buscar o arquivo mais recente
        csv_files = list(processed_path.glob("*_processed_*.csv"))
        
        if not csv_files:
            return None
        
        # Ordenar por tempo de modificação
        latest_file = max(csv_files, key=lambda f: f.stat().st_mtime)
        
        try:
            return pd.read_csv(latest_file)
        except Exception as e:
            self.logger.error(f"Erro ao carregar dados mais recentes: {e}")
            return None

if __name__ == "__main__":
    connector = AnyLogicConnector()
    connector.start_monitoring()