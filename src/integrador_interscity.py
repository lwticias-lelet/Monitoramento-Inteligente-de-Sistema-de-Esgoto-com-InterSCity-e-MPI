import requests
import pandas as pd

# URL do adaptador InterSCity (ajuste conforme seu endpoint)
url_adaptor = "https://cidadesinteligentes.lsdi.ufma.br/interscity_lh/adaptor"

# Carregar CSV dos alertas gerados pelo MPI
df = pd.read_csv("data/alertas.csv")  

for _, row in df.iterrows():
    payload = {
        "sensorId": row.get("sensorId", ""),
        "alert": row.get("status", ""),  
        "value": row.get("vazao", 0),  
        
    }
    try:
        response = requests.post(url_adaptor, json=payload)
        print(f"Enviado: {payload} - Status: {response.status_code}")
    except Exception as e:
        print(f"Erro ao enviar dados: {e}")
