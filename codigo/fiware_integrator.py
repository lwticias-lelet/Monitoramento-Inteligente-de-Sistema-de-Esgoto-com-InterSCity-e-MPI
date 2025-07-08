import requests
import pandas as pd
import json
from datetime import datetime
from pathlib import Path

class FIWAREIntegrator:
    def __init__(self):
        self.orion_url = "http://localhost:1026"
        self.headers = {"Content-Type": "application/json"}
        
    def test_connection(self):
        try:
            response = requests.get(f"{self.orion_url}/version")
            print(f" FIWARE conectado: {response.json()['orion']['version']}")
            return True
        except:
            print(" FIWARE não disponível")
            return False
    
    def send_sensor_data(self, sensor_id, data):
        entity = {
            "id": f"WaterSensor_{sensor_id}",
            "type": "WaterSensor",
            "flow_rate": {"value": float(data.get("flow_rate", 0)), "type": "Number"},
            "pressure": {"value": float(data.get("pressure", 0)), "type": "Number"},
            "temperature": {"value": float(data.get("temperature", 0)), "type": "Number"},
            "ph_level": {"value": float(data.get("ph_level", 7)), "type": "Number"},
            "status": {"value": str(data.get("status", "NORMAL")), "type": "Text"},
            "timestamp": {"value": datetime.now().isoformat(), "type": "DateTime"}
        }
        
        try:
            response = requests.post(f"{self.orion_url}/v2/entities", 
                                   json=entity, headers=self.headers)
            if response.status_code == 201:
                print(f" Sensor {sensor_id} enviado para FIWARE")
                return True
            elif response.status_code == 422:
                # Atualizar se já existe
                updates = {k: v for k, v in entity.items() if k != "id" and k != "type"}
                response = requests.patch(f"{self.orion_url}/v2/entities/{entity['id']}/attrs",
                                        json=updates, headers=self.headers)
                print(f" Sensor {sensor_id} atualizado no FIWARE")
                return True
        except Exception as e:
            print(f" Erro ao enviar {sensor_id}: {e}")
        return False
    
    def process_csv_file(self, csv_file):
        try:
            df = pd.read_csv(csv_file)
            print(f" Processando: {csv_file}")
            print(f" Registros: {len(df)}")
            
            success = 0
            for _, row in df.iterrows():
                sensor_id = row.get("sensor_id", "unknown")
                if self.send_sensor_data(sensor_id, row.to_dict()):
                    success += 1
            
            print(f" Enviados: {success}/{len(df)} sensores")
            return success
        except Exception as e:
            print(f" Erro: {e}")
            return 0

if __name__ == "__main__":
    integrator = FIWAREIntegrator()
    
    if integrator.test_connection():
        # Processar dados existentes
        data_path = Path("data/processed")
        if data_path.exists():
            csv_files = list(data_path.glob("*.csv"))
            if csv_files:
                latest = max(csv_files, key=lambda f: f.stat().st_mtime)
                integrator.process_csv_file(str(latest))
            else:
                print(" Nenhum CSV em data/processed/")
        else:
            print(" Diretório data/processed/ não existe")
    
    print("\n PRÓXIMOS PASSOS:")
    print("1. Executar: python run_dashboard.py")
    print("2. Acessar: http://localhost:1026/v2/entities")
    print("3. Integrar com Node-RED")
