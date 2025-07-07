#!/usr/bin/env python3
"""
Processador de dados CSV para o sistema de monitoramento
Responsável por carregar, validar e processar dados dos sensores
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

class CSVProcessor:
    """Processador de dados CSV com validação e limpeza"""
    
    def __init__(self, config_path: str = "config/config.json"):
        self.config = self._load_config(config_path)
        self._setup_logging()
        
        # Configurar caminhos
        self.input_path = Path(self.config['data']['csv_input_path'])
        self.output_path = Path(self.config['data']['processed_output_path'])
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Cache para dados processados
        self.data_cache = {}
        self.cache_timeout = 300  # 5 minutos
        
        self.logger.info("CSV Processor inicializado")
    
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
            format='%(asctime)s - CSVProcessor - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def load_csv_file(self, file_path: str) -> pd.DataFrame:
        """Carrega um arquivo CSV com tratamento de erros"""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                self.logger.error(f"Arquivo não encontrado: {file_path}")
                return pd.DataFrame()
            
            # Verificar cache
            cache_key = str(file_path)
            if cache_key in self.data_cache:
                cached_data, cached_time = self.data_cache[cache_key]
                if (datetime.now() - cached_time).seconds < self.cache_timeout:
                    self.logger.debug(f"Dados carregados do cache: {file_path}")
                    return cached_data
            
            # Carregar CSV
            df = pd.read_csv(file_path, encoding='utf-8')
            
            # Atualizar cache
            self.data_cache[cache_key] = (df.copy(), datetime.now())
            
            self.logger.info(f"CSV carregado: {file_path} - {len(df)} registros")
            return df
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar CSV {file_path}: {e}")
            return pd.DataFrame()
    
    def validate_data_structure(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Valida a estrutura dos dados"""
        errors = []
        
        # Verificar se DataFrame está vazio
        if df.empty:
            errors.append("DataFrame está vazio")
            return False, errors
        
        # Verificar colunas obrigatórias
        required_columns = self.config['anylogic']['expected_columns']
        missing_columns = set(required_columns) - set(df.columns)
        
        if missing_columns:
            errors.append(f"Colunas faltando: {missing_columns}")
        
        # Verificar tipos de dados
        numeric_columns = ['flow_rate', 'pressure', 'temperature', 'ph_level', 'turbidity']
        
        for col in numeric_columns:
            if col in df.columns:
                non_numeric = df[col].apply(lambda x: not isinstance(x, (int, float)) and not pd.isna(x))
                if non_numeric.any():
                    errors.append(f"Coluna {col} contém valores não numéricos")
        
        # Verificar duplicatas
        if df.duplicated().any():
            errors.append("Dados contêm registros duplicados")
        
        # Verificar valores nulos em campos críticos
        critical_fields = ['sensor_id', 'timestamp']
        for field in critical_fields:
            if field in df.columns and df[field].isnull().any():
                errors.append(f"Campo crítico {field} contém valores nulos")
        
        return len(errors) == 0, errors
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpa e padroniza os dados"""
        if df.empty:
            return df
        
        try:
            cleaned_df = df.copy()
            
            # Remover duplicatas
            initial_count = len(cleaned_df)
            cleaned_df = cleaned_df.drop_duplicates()
            
            if len(cleaned_df) < initial_count:
                self.logger.info(f"Removidas {initial_count - len(cleaned_df)} duplicatas")
            
            # Converter timestamp
            if 'timestamp' in cleaned_df.columns:
                cleaned_df['timestamp'] = pd.to_datetime(cleaned_df['timestamp'], errors='coerce')
                
                # Remover registros com timestamp inválido
                invalid_timestamps = cleaned_df['timestamp'].isnull()
                if invalid_timestamps.any():
                    self.logger.warning(f"Removidos {invalid_timestamps.sum()} registros com timestamp inválido")
                    cleaned_df = cleaned_df[~invalid_timestamps]
            
            # Limpar dados numéricos
            numeric_columns = ['flow_rate', 'pressure', 'temperature', 'ph_level', 'turbidity']
            
            for col in numeric_columns:
                if col in cleaned_df.columns:
                    # Converter para numérico
                    cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce')
                    
                    # Aplicar filtros específicos por coluna
                    if col == 'flow_rate':
                        cleaned_df = cleaned_df[(cleaned_df[col] >= 0) & (cleaned_df[col] <= 1000)]
                    elif col == 'pressure':
                        cleaned_df = cleaned_df[(cleaned_df[col] >= 0) & (cleaned_df[col] <= 10)]
                    elif col == 'temperature':
                        cleaned_df = cleaned_df[(cleaned_df[col] >= -10) & (cleaned_df[col] <= 60)]
                    elif col == 'ph_level':
                        cleaned_df = cleaned_df[(cleaned_df[col] >= 0) & (cleaned_df[col] <= 14)]
                    elif col == 'turbidity':
                        cleaned_df = cleaned_df[(cleaned_df[col] >= 0) & (cleaned_df[col] <= 1000)]
            
            # Preencher valores nulos com médias ou valores padrão
            for col in numeric_columns:
                if col in cleaned_df.columns:
                    null_count = cleaned_df[col].isnull().sum()
                    if null_count > 0:
                        if null_count / len(cleaned_df) < 0.1:  # Menos de 10% nulos
                            cleaned_df[col].fillna(cleaned_df[col].median(), inplace=True)
                        else:
                            # Muitos nulos, usar valor padrão
                            default_values = {
                                'flow_rate': 0.0,
                                'pressure': 1.0,
                                'temperature': 20.0,
                                'ph_level': 7.0,
                                'turbidity': 0.0
                            }
                            cleaned_df[col].fillna(default_values.get(col, 0.0), inplace=True)
            
            # Padronizar sensor_id
            if 'sensor_id' in cleaned_df.columns:
                cleaned_df['sensor_id'] = cleaned_df['sensor_id'].astype(str).str.strip()
            
            # Adicionar colunas de controle
            cleaned_df['processed_at'] = datetime.now()
            cleaned_df['data_quality_score'] = self._calculate_quality_score(cleaned_df)
            
            self.logger.info(f"Limpeza concluída: {len(df)} -> {len(cleaned_df)} registros")
            
            return cleaned_df
            
        except Exception as e:
            self.logger.error(f"Erro na limpeza dos dados: {e}")
            return df
    
    def _calculate_quality_score(self, df: pd.DataFrame) -> pd.Series:
        """Calcula score de qualidade dos dados"""
        scores = pd.Series(1.0, index=df.index)
        
        # Penalizar valores extremos
        numeric_columns = ['flow_rate', 'pressure', 'temperature', 'ph_level', 'turbidity']
        
        for col in numeric_columns:
            if col in df.columns:
                # Calcular z-score
                z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                
                # Penalizar outliers
                outlier_penalty = np.where(z_scores > 3, 0.3, 0)
                scores -= outlier_penalty
        
        # Garantir que scores estejam entre 0 e 1
        scores = np.clip(scores, 0, 1)
        
        return scores
    
    def aggregate_data(self, df: pd.DataFrame, time_window: str = '1H') -> pd.DataFrame:
        """Agrega dados por janela de tempo"""
        if df.empty or 'timestamp' not in df.columns:
            return df
        
        try:
            # Configurar timestamp como índice
            df_agg = df.set_index('timestamp')
            
            # Agrupar por sensor e janela de tempo
            if 'sensor_id' in df.columns:
                grouped = df_agg.groupby('sensor_id').resample(time_window)
            else:
                grouped = df_agg.resample(time_window)
            
            # Calcular agregações
            numeric_columns = ['flow_rate', 'pressure', 'temperature', 'ph_level', 'turbidity']
            
            agg_dict = {}
            for col in numeric_columns:
                if col in df.columns:
                    agg_dict[f'{col}_mean'] = (col, 'mean')
                    agg_dict[f'{col}_std'] = (col, 'std')
                    agg_dict[f'{col}_min'] = (col, 'min')
                    agg_dict[f'{col}_max'] = (col, 'max')
            
            # Adicionar contagem
            agg_dict['count'] = ('sensor_id', 'count')
            
            # Aplicar agregação
            result = grouped.agg(agg_dict)
            
            # Limpar índices
            result = result.reset_index()
            
            self.logger.info(f"Agregação concluída: {len(df)} -> {len(result)} registros")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro na agregação: {e}")
            return df
    
    def detect_anomalies_statistical(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detecta anomalias usando métodos estatísticos"""
        if df.empty:
            return df
        
        try:
            result_df = df.copy()
            numeric_columns = ['flow_rate', 'pressure', 'temperature', 'ph_level', 'turbidity']
            
            for col in numeric_columns:
                if col in df.columns:
                    # Método IQR para detecção de outliers
                    Q1 = df[col].quantile(0.25)
                    Q3 = df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    
                    # Marcar anomalias
                    result_df[f'{col}_anomaly'] = (
                        (df[col] < lower_bound) | 
                        (df[col] > upper_bound)
                    )
                    
                    # Método Z-score
                    z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                    result_df[f'{col}_zscore'] = z_scores
                    result_df[f'{col}_zscore_anomaly'] = z_scores > 3
            
            # Criar score geral de anomalia
            anomaly_columns = [col for col in result_df.columns if col.endswith('_anomaly')]
            result_df['anomaly_count'] = result_df[anomaly_columns].sum(axis=1)
            result_df['is_anomaly'] = result_df['anomaly_count'] > 0
            
            anomaly_count = result_df['is_anomaly'].sum()
            self.logger.info(f"Detectadas {anomaly_count} anomalias de {len(df)} registros")
            
            return result_df
            
        except Exception as e:
            self.logger.error(f"Erro na detecção de anomalias: {e}")
            return df
    
    def save_processed_data(self, df: pd.DataFrame, suffix: str = "processed") -> str:
        """Salva dados processados"""
        if df.empty:
            return ""
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_path / f"data_{suffix}_{timestamp}.csv"
            
            # Salvar CSV
            df.to_csv(output_file, index=False, encoding='utf-8')
            
            # Salvar metadados
            metadata = {
                'timestamp': datetime.now().isoformat(),
                'records_count': len(df),
                'columns': list(df.columns),
                'file_path': str(output_file),
                'data_summary': {
                    'sensors_count': df['sensor_id'].nunique() if 'sensor_id' in df.columns else 0,
                    'time_range': {
                        'start': df['timestamp'].min().isoformat() if 'timestamp' in df.columns else None,
                        'end': df['timestamp'].max().isoformat() if 'timestamp' in df.columns else None
                    }
                }
            }
            
            # Adicionar estatísticas numéricas
            numeric_columns = ['flow_rate', 'pressure', 'temperature', 'ph_level', 'turbidity']
            stats = {}
            
            for col in numeric_columns:
                if col in df.columns:
                    stats[col] = {
                        'mean': float(df[col].mean()),
                        'std': float(df[col].std()),
                        'min': float(df[col].min()),
                        'max': float(df[col].max()),
                        'median': float(df[col].median())
                    }
            
            metadata['statistics'] = stats
            
            # Salvar metadados
            metadata_file = self.output_path / f"metadata_{suffix}_{timestamp}.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Dados salvos: {output_file}")
            
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar dados: {e}")
            return ""
    
    def process_file(self, file_path: str, save_results: bool = True) -> Optional[pd.DataFrame]:
        """Processa um arquivo CSV completo"""
        try:
            self.logger.info(f"Iniciando processamento: {file_path}")
            
            # Carregar dados
            df = self.load_csv_file(file_path)
            
            if df.empty:
                self.logger.warning(f"Arquivo vazio ou erro no carregamento: {file_path}")
                return None
            
            # Validar estrutura
            is_valid, errors = self.validate_data_structure(df)
            
            if not is_valid:
                self.logger.error(f"Estrutura inválida: {errors}")
                return None
            
            # Limpar dados
            cleaned_df = self.clean_data(df)
            
            # Detectar anomalias
            anomaly_df = self.detect_anomalies_statistical(cleaned_df)
            
            # Salvar resultados se solicitado
            if save_results:
                self.save_processed_data(anomaly_df, "processed")
            
            self.logger.info(f"Processamento concluído: {file_path}")
            
            return anomaly_df
            
        except Exception as e:
            self.logger.error(f"Erro no processamento: {e}")
            return None
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """Retorna resumo do processamento"""
        processed_files = list(self.output_path.glob("data_processed_*.csv"))
        
        summary = {
            'total_files_processed': len(processed_files),
            'last_processing': None,
            'total_records': 0,
            'cache_stats': {
                'cached_files': len(self.data_cache),
                'cache_timeout': self.cache_timeout
            }
        }
        
        if processed_files:
            # Arquivo mais recente
            latest_file = max(processed_files, key=lambda f: f.stat().st_mtime)
            summary['last_processing'] = datetime.fromtimestamp(latest_file.stat().st_mtime).isoformat()
            
            # Contar registros totais
            try:
                for file_path in processed_files[-5:]:  # Últimos 5 arquivos
                    df = pd.read_csv(file_path)
                    summary['total_records'] += len(df)
            except Exception as e:
                self.logger.error(f"Erro ao calcular resumo: {e}")
        
        return summary

if __name__ == "__main__":
    processor = CSVProcessor()
    
    # Exemplo de uso
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        result = processor.process_file(file_path)
        
        if result is not None:
            print(f"Processamento concluído: {len(result)} registros")
            print(processor.get_processing_summary())
        else:
            print("Erro no processamento")
    else:
        print("Uso: python csv_processor.py <caminho_do_arquivo_csv>")