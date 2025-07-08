#!/usr/bin/env python3
"""
API REST para integração com Node-RED
Adicione este arquivo como: codigo/src/api/nodered_api.py
"""

from flask import Flask, jsonify, request
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging
import sys
import os

# Adicionar diretório src ao path
sys.path.append(str(Path(__file__).parent.parent))

from data_processing.csv_processor import CSVProcessor
from visualization.dashboard import MonitoringDashboard

class NodeREDAPI:
    """API REST para integração com Node-RED"""
    
    def __init__(self, config_path: str = "config/config.json"):
        self.app = Flask(__name__)
        self.config_path = config_path
        
        # Inicializar processador
        self.csv_processor = CSVProcessor(config_path)
        
        # Configurar rotas
        self.setup_routes()
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def setup_routes(self):
        """Configura as rotas da API"""
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Verificar se o sistema está funcionando"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'service': 'Monitoramento Esgotamento Sanitário'
            })
        
        @self.app.route('/api/sensors', methods=['GET'])
        def get_sensors():
            """Listar todos os sensores ativos"""
            try:
                df = self.load_latest_data()
                if df is None or df.empty:
                    return jsonify({'sensors': []})
                
                sensors = df['sensor_id'].unique().tolist() if 'sensor_id' in df.columns else []
                
                return jsonify({
                    'sensors': sensors,
                    'count': len(sensors),
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/sensor/<sensor_id>/latest', methods=['GET'])
        def get_sensor_latest(sensor_id):
            """Obter dados mais recentes de um sensor específico"""
            try:
                df = self.load_latest_data()
                if df is None or df.empty:
                    return jsonify({'error': 'No data available'}), 404
                
                sensor_data = df[df['sensor_id'] == sensor_id]
                if sensor_data.empty:
                    return jsonify({'error': f'Sensor {sensor_id} not found'}), 404
                
                # Pegar registro mais recente
                latest = sensor_data.iloc[-1].to_dict()
                
                # Converter timestamp para string se existir
                if 'timestamp' in latest:
                    latest['timestamp'] = pd.to_datetime(latest['timestamp']).isoformat()
                
                return jsonify({
                    'sensor_id': sensor_id,
                    'data': latest,
                    'retrieved_at': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/alerts', methods=['GET'])
        def get_alerts():
            """Obter alertas ativos"""
            try:
                df = self.load_latest_data()
                if df is None or df.empty or 'is_anomaly' not in df.columns:
                    return jsonify({'alerts': []})
                
                # Filtrar apenas anomalias
                alerts_df = df[df['is_anomaly'] == True]
                
                alerts = []
                for _, row in alerts_df.iterrows():
                    alert = {
                        'sensor_id': row['sensor_id'],
                        'timestamp': pd.to_datetime(row['timestamp']).isoformat() if 'timestamp' in row else None,
                        'alert_type': 'anomaly',
                        'severity': 'high' if row.get('anomaly_count', 0) > 2 else 'medium',
                        'parameters': {}
                    }
                    
                    # Adicionar parâmetros específicos
                    if row.get('flow_rate_anomaly', False):
                        alert['parameters']['flow_rate'] = row.get('flow_rate')
                    if row.get('pressure_anomaly', False):
                        alert['parameters']['pressure'] = row.get('pressure')
                    if row.get('temperature_anomaly', False):
                        alert['parameters']['temperature'] = row.get('temperature')
                    
                    alerts.append(alert)
                
                return jsonify({
                    'alerts': alerts,
                    'count': len(alerts),
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/data/process', methods=['POST'])
        def process_data():
            """Processar novos dados enviados pelo Node-RED"""
            try:
                data = request.get_json()
                
                if not data:
                    return jsonify({'error': 'No data provided'}), 400
                
                # Validar formato dos dados
                required_fields = ['sensor_id', 'flow_rate', 'pressure', 'temperature']
                for field in required_fields:
                    if field not in data:
                        return jsonify({'error': f'Missing field: {field}'}), 400
                
                # Criar DataFrame temporário
                df = pd.DataFrame([data])
                
                # Processar dados
                result = self.csv_processor.clean_data(df)
                
                if not result.empty:
                    # Salvar dados processados
                    output_file = self.csv_processor.save_processed_data(result, "nodered")
                    
                    return jsonify({
                        'status': 'processed',
                        'records': len(result),
                        'output_file': output_file,
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    return jsonify({'error': 'Data processing failed'}), 500
                    
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/statistics', methods=['GET'])
        def get_statistics():
            """Obter estatísticas gerais do sistema"""
            try:
                df = self.load_latest_data()
                if df is None or df.empty:
                    return jsonify({'error': 'No data available'}), 404
                
                stats = {
                    'total_records': len(df),
                    'total_sensors': df['sensor_id'].nunique() if 'sensor_id' in df.columns else 0,
                    'total_alerts': df['is_anomaly'].sum() if 'is_anomaly' in df.columns else 0,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Adicionar estatísticas por parâmetro
                numeric_columns = ['flow_rate', 'pressure', 'temperature', 'ph_level', 'turbidity']
                
                for col in numeric_columns:
                    if col in df.columns:
                        stats[f'{col}_stats'] = {
                            'mean': float(df[col].mean()),
                            'min': float(df[col].min()),
                            'max': float(df[col].max()),
                            'std': float(df[col].std())
                        }
                
                return jsonify(stats)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/sensor/<sensor_id>/history', methods=['GET'])
        def get_sensor_history(sensor_id):
            """Obter histórico de um sensor"""
            try:
                # Parâmetros opcionais
                limit = request.args.get('limit', 100, type=int)
                hours = request.args.get('hours', 24, type=int)
                
                df = self.load_latest_data()
                if df is None or df.empty:
                    return jsonify({'error': 'No data available'}), 404
                
                # Filtrar por sensor
                sensor_data = df[df['sensor_id'] == sensor_id]
                if sensor_data.empty:
                    return jsonify({'error': f'Sensor {sensor_id} not found'}), 404
                
                # Filtrar por tempo se timestamp disponível
                if 'timestamp' in sensor_data.columns:
                    cutoff = datetime.now() - pd.Timedelta(hours=hours)
                    sensor_data = sensor_data[pd.to_datetime(sensor_data['timestamp']) >= cutoff]
                
                # Limitar registros
                sensor_data = sensor_data.tail(limit)
                
                # Converter para lista de dicionários
                history = sensor_data.to_dict('records')
                
                # Converter timestamps
                for record in history:
                    if 'timestamp' in record:
                        record['timestamp'] = pd.to_datetime(record['timestamp']).isoformat()
                
                return jsonify({
                    'sensor_id': sensor_id,
                    'history': history,
                    'count': len(history),
                    'parameters': {
                        'limit': limit,
                        'hours': hours
                    },
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def load_latest_data(self):
        """Carregar dados mais recentes"""
        try:
            processed_path = Path(self.csv_processor.output_path)
            processed_files = list(processed_path.glob("data_processed_*.csv"))
            
            if not processed_files:
                return None
            
            latest_file = max(processed_files, key=lambda f: f.stat().st_mtime)
            return pd.read_csv(latest_file)
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar dados: {e}")
            return None
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Executar a API"""
        self.logger.info(f"Iniciando API em http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    # Instalar Flask se não estiver instalado
    try:
        import flask
    except ImportError:
        print("Instalando Flask...")
        os.system("pip install flask")
    
    api = NodeREDAPI()
    api.run(debug=True)