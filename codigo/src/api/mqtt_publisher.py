#!/usr/bin/env python3
"""
Integração MQTT para Node-RED
Adicione como: codigo/src/api/mqtt_publisher.py
"""

import json
import time
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging
import sys

# Para instalar: pip install paho-mqtt
try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("Instalando paho-mqtt...")
    import os
    os.system("pip install paho-mqtt")
    import paho.mqtt.client as mqtt

# Adicionar diretório src ao path
sys.path.append(str(Path(__file__).parent.parent))

from data_processing.csv_processor import CSVProcessor

class MQTTPublisher:
    """Publicador MQTT para integração com Node-RED"""
    
    def __init__(self, config_path: str = "config/config.json"):
        self.config_path = config_path
        
        # Configurações MQTT
        self.mqtt_broker = "localhost"  # Ou seu broker MQTT
        self.mqtt_port = 1883
        self.mqtt_topics = {
            'sensors': 'esgoto/sensores',
            'alerts': 'esgoto/alertas',
            'statistics': 'esgoto/estatisticas',
            'health': 'esgoto/health'
        }
        
        # Inicializar processador
        self.csv_processor = CSVProcessor(config_path)
        
        # Configurar cliente MQTT
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Estado da conexão
        self.connected = False
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback quando conecta ao broker MQTT"""
        if rc == 0:
            self.connected = True
            self.logger.info(f"Conectado ao broker MQTT: {self.mqtt_broker}:{self.mqtt_port}")
            
            # Publicar mensagem de health
            self.publish_health_status("connected")
        else:
            self.logger.error(f"Falha na conexão MQTT: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback quando desconecta do broker MQTT"""
        self.connected = False
        self.logger.warning("Desconectado do broker MQTT")
    
    def on_publish(self, client, userdata, mid):
        """Callback quando mensagem é publicada"""
        self.logger.debug(f"Mensagem publicada: {mid}")
    
    def connect(self):
        """Conectar ao broker MQTT"""
        try:
            self.client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.client.loop_start()
            
            # Aguardar conexão
            timeout = 10
            while not self.connected and timeout > 0:
                time.sleep(1)
                timeout -= 1
            
            if not self.connected:
                raise Exception("Timeout na conexão MQTT")
                
        except Exception as e:
            self.logger.error(f"Erro ao conectar MQTT: {e}")
            raise
    
    def disconnect(self):
        """Desconectar do broker MQTT"""
        if self.connected:
            self.publish_health_status("disconnecting")
            self.client.loop_stop()
            self.client.disconnect()
    
    def publish_message(self, topic: str, payload: dict, retain: bool = False):
        """Publicar mensagem MQTT"""
        if not self.connected:
            self.logger.warning("Cliente MQTT não conectado")
            return False
        
        try:
            # Adicionar timestamp
            payload['timestamp'] = datetime.now().isoformat()
            
            # Converter para JSON
            json_payload = json.dumps(payload, ensure_ascii=False, default=str)
            
            # Publicar
            result = self.client.publish(topic, json_payload, qos=1, retain=retain)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.logger.debug(f"Publicado em {topic}: {len(json_payload)} bytes")
                return True
            else:
                self.logger.error(f"Erro ao publicar em {topic}: {result.rc}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro na publicação MQTT: {e}")
            return False
    
    def publish_health_status(self, status: str):
        """Publicar status de saúde do sistema"""
        health_data = {
            'status': status,
            'service': 'Monitoramento Esgotamento Sanitário',
            'version': '1.0.0',
            'uptime': time.time()
        }
        
        self.publish_message(self.mqtt_topics['health'], health_data, retain=True)
    
    def publish_sensor_data(self, sensor_data: dict):
        """Publicar dados de sensor específico"""
        topic = f"{self.mqtt_topics['sensors']}/{sensor_data.get('sensor_id', 'unknown')}"
        
        payload = {
            'sensor_id': sensor_data.get('sensor_id'),
            'flow_rate': sensor_data.get('flow_rate'),
            'pressure': sensor_data.get('pressure'),
            'temperature': sensor_data.get('temperature'),
            'ph_level': sensor_data.get('ph_level'),
            'turbidity': sensor_data.get('turbidity'),
            'location': {
                'x': sensor_data.get('location_x'),
                'y': sensor_data.get('location_y')
            },
            'quality_score': sensor_data.get('data_quality_score'),
            'is_anomaly': sensor_data.get('is_anomaly', False)
        }
        
        self.publish_message(topic, payload)
    
    def publish_alert(self, alert_data: dict):
        """Publicar alerta"""
        payload = {
            'alert_type': 'sensor_anomaly',
            'sensor_id': alert_data.get('sensor_id'),
            'severity': 'high' if alert_data.get('anomaly_count', 0) > 2 else 'medium',
            'parameters': {
                'flow_rate': alert_data.get('flow_rate'),
                'pressure': alert_data.get('pressure'),
                'temperature': alert_data.get('temperature'),
                'ph_level': alert_data.get('ph_level')
            },
            'anomaly_details': {
                'count': alert_data.get('anomaly_count'),
                'flow_rate_anomaly': alert_data.get('flow_rate_anomaly', False),
                'pressure_anomaly': alert_data.get('pressure_anomaly', False),
                'temperature_anomaly': alert_data.get('temperature_anomaly', False)
            }
        }
        
        self.publish_message(self.mqtt_topics['alerts'], payload)
    
    def publish_statistics(self, stats_data: dict):
        """Publicar estatísticas do sistema"""
        self.publish_message(self.mqtt_topics['statistics'], stats_data, retain=True)
    
    def load_and_publish_data(self):
        """Carregar dados mais recentes e publicar"""
        try:
            # Carregar dados processados
            processed_path = Path(self.csv_processor.output_path)
            processed_files = list(processed_path.glob("data_processed_*.csv"))
            
            if not processed_files:
                self.logger.warning("Nenhum arquivo processado encontrado")
                return
            
            # Arquivo mais recente
            latest_file = max(processed_files, key=lambda f: f.stat().st_mtime)
            df = pd.read_csv(latest_file)
            
            if df.empty:
                self.logger.warning("Arquivo de dados vazio")
                return
            
            # Publicar dados por sensor
            sensors = df['sensor_id'].unique() if 'sensor_id' in df.columns else []
            
            for sensor_id in sensors:
                sensor_data = df[df['sensor_id'] == sensor_id]
                
                # Dados mais recentes do sensor
                latest_record = sensor_data.iloc[-1].to_dict()
                self.publish_sensor_data(latest_record)
                
                # Verificar se há alertas
                if latest_record.get('is_anomaly', False):
                    self.publish_alert(latest_record)
            
            # Publicar estatísticas gerais
            stats = {
                'total_records': len(df),
                'total_sensors': len(sensors),
                'total_alerts': df['is_anomaly'].sum() if 'is_anomaly' in df.columns else 0,
                'data_file': str(latest_file),
                'processing_summary': self.csv_processor.get_processing_summary()
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
            
            self.publish_statistics(stats)
            
            self.logger.info(f"Dados publicados: {len(df)} registros, {len(sensors)} sensores")
            
        except Exception as e:
            self.logger.error(f"Erro ao publicar dados: {e}")
    
    def run_continuous(self, interval: int = 60):
        """Executar publicação contínua"""
        self.logger.info(f"Iniciando publicação MQTT a cada {interval} segundos")
        
        try:
            self.connect()
            
            while True:
                self.load_and_publish_data()
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.logger.info("Interrompido pelo usuário")
        except Exception as e:
            self.logger.error(f"Erro na execução contínua: {e}")
        finally:
            self.disconnect()

if __name__ == "__main__":
    # Exemplo de uso
    publisher = MQTTPublisher()
    
    # Executar uma vez
    try:
        publisher.connect()
        publisher.load_and_publish_data()
        publisher.disconnect()
    except Exception as e:
        print(f"Erro: {e}")
    
    # Ou executar continuamente
    # publisher.run_continuous(interval=30)