#!/usr/bin/env python3
"""
Conector InterSCity para sensores de esgotamento sanitário
"""

import requests
import json
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

class InterSCityConnector:
    """Conector para plataforma InterSCity"""
    
    def __init__(self, api_url="http://api.playground.interscity.org"):
        self.api_url = api_url
        self.headers = {'Content-Type': 'application/json'}
        self.logger = logging.getLogger(__name__)
        
        # Cache para UUIDs dos recursos
        self.resource_uuids = {}
        
        self.logger.info("InterSCity Connector inicializado")
    
    def create_capabilities(self):
        """Criar capabilities necessárias para monitoramento de esgoto"""
        capabilities = [
            {
                "name": "flow_rate",
                "description": "Mede a vazão em litros por segundo",
                "capability_type": "sensor"
            },
            {
                "name": "pressure",
                "description": "Mede a pressão em bar",
                "capability_type": "sensor"
            },
            {
                "name": "temperature",
                "description": "Mede a temperatura da água em graus Celsius",
                "capability_type": "sensor"
            },
            {
                "name": "ph_level",
                "description": "Mede o nível de pH da água",
                "capability_type": "sensor"
            },
            {
                "name": "turbidity",
                "description": "Mede a turbidez da água em NTU",
                "capability_type": "sensor"
            },
            {
                "name": "water_quality",
                "description": "Monitora qualidade geral da água",
                "capability_type": "sensor"
            }
        ]
        
        created_capabilities = []
        for capability in capabilities:
            try:
                response = requests.post(
                    f"{self.api_url}/catalog/capabilities/",
                    headers=self.headers,
                    json=capability
                )
                
                if response.status_code in [201, 400]:  # 400 pode ser "já existe"
                    created_capabilities.append(capability["name"])
                    self.logger.info(f"Capability criada/verificada: {capability['name']}")
                else:
                    self.logger.warning(f"Erro ao criar capability {capability['name']}: {response.status_code}")
                    
            except Exception as e:
                self.logger.error(f"Erro ao criar capability {capability['name']}: {e}")
        
        return created_capabilities
    
    def create_sensor_resource(self, sensor_id: str, location_x: float, location_y: float, description: str = None) -> Optional[str]:
        """Criar recurso (sensor) no InterSCity"""
        
        if not description:
            description = f"Sensor de monitoramento de esgoto {sensor_id}"
        
        resource_data = {
            "data": {
                "description": description,
                "capabilities": [
                    "flow_rate",
                    "pressure", 
                    "temperature",
                    "ph_level",
                    "turbidity",
                    "water_quality"
                ],
                "status": "active",
                "lat": location_y,  # InterSCity usa lat/lon
                "lon": location_x
            }
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/catalog/resources",
                headers=self.headers,
                json=resource_data
            )
            
            if response.status_code == 201:
                resource = response.json()
                uuid = resource['data']['uuid']
                self.resource_uuids[sensor_id] = uuid
                
                self.logger.info(f"Recurso criado para sensor {sensor_id}: {uuid}")
                return uuid
            else:
                self.logger.error(f"Erro ao criar recurso: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Erro ao criar recurso para sensor {sensor_id}: {e}")
            return None
    
    def send_sensor_data(self, sensor_id: str, data: Dict[str, Any]) -> bool:
        """Enviar dados do sensor para InterSCity"""
        
        # Verificar se temos UUID do recurso
        if sensor_id not in self.resource_uuids:
            self.logger.error(f"UUID não encontrado para sensor {sensor_id}")
            return False
        
        uuid = self.resource_uuids[sensor_id]
        timestamp = datetime.now().isoformat() + "Z"
        
        # Preparar dados no formato InterSCity
        interscity_data = {
            "data": []
        }
        
        # Adicionar cada medição
        sensor_reading = {"timestamp": timestamp}
        
        if 'flow_rate' in data:
            sensor_reading['flow_rate'] = float(data['flow_rate'])
        
        if 'pressure' in data:
            sensor_reading['pressure'] = float(data['pressure'])
        
        if 'temperature' in data:
            sensor_reading['temperature'] = float(data['temperature'])
        
        if 'ph_level' in data:
            sensor_reading['ph_level'] = float(data['ph_level'])
        
        if 'turbidity' in data:
            sensor_reading['turbidity'] = float(data['turbidity'])
        
        # Determinar qualidade da água baseado em anomalias
        if 'is_anomaly' in data:
            sensor_reading['water_quality'] = 0 if data['is_anomaly'] else 1
        
        interscity_data["data"].append(sensor_reading)
        
        try:
            # Enviar para InterSCity
            response = requests.post(
                f"{self.api_url}/adaptor/resources/{uuid}/data/environment_monitoring",
                headers=self.headers,
                json=interscity_data
            )
            
            if response.status_code == 201:
                self.logger.debug(f"Dados enviados para sensor {sensor_id}")
                return True
            else:
                self.logger.error(f"Erro ao enviar dados: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao enviar dados para sensor {sensor_id}: {e}")
            return False
    
    def get_sensor_data(self, sensor_id: str) -> Optional[Dict[str, Any]]:
        """Buscar dados do sensor no InterSCity"""
        
        if sensor_id not in self.resource_uuids:
            return None
        
        uuid = self.resource_uuids[sensor_id]
        
        try:
            response = requests.post(
                f"{self.api_url}/collector/resources/{uuid}/data"
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Erro ao buscar dados: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Erro ao buscar dados do sensor {sensor_id}: {e}")
            return None
    
    def list_capabilities(self) -> List[Dict[str, Any]]:
        """Listar todas as capabilities disponíveis"""
        try:
            response = requests.get(f"{self.api_url}/catalog/capabilities")
            
            if response.status_code == 200:
                return response.json().get('capabilities', [])
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"Erro ao listar capabilities: {e}")
            return []
    
    def list_resources(self) -> List[Dict[str, Any]]:
        """Listar todos os recursos"""
        try:
            response = requests.get(f"{self.api_url}/catalog/resources")
            
            if response.status_code == 200:
                return response.json().get('resources', [])
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"Erro ao listar recursos: {e}")
            return []