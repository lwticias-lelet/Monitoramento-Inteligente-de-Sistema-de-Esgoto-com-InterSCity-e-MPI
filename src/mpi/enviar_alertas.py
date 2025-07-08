import csv
import json
import requests

# URL do endpoint Collector do InterSCity (ajuste se necessário)
URL_COLLECTOR = "https://cidadesinteligentes.lsdi.ufma.br/interscity_lh/collector"

# Caminho do arquivo CSV
CSV_PATH = "data/alertas.csv"

def enviar_alerta(dado):
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(URL_COLLECTOR, json=dado, headers=headers, timeout=10)  # Timeout 10s
        if response.status_code in (200, 201):
            print("Alerta enviado:", dado)
        else:
            print(f"Falha ao enviar alerta: {response.status_code} - {response.text}")
    except requests.exceptions.Timeout:
        print("Erro: Timeout na requisição ao InterSCity.")
    except requests.exceptions.ConnectionError:
        print("Erro: Não foi possível conectar ao InterSCity.")
    except Exception as e:
        print(f"Erro na requisição: {e}")

def main():
    try:
        with open(CSV_PATH, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Verifique se o CSV tem exatamente esses nomes de colunas
                # Ajuste os nomes caso sejam diferentes no seu arquivo CSV
                dado = {
                    "sensorId": row.get("sensorId", ""),
                    "tempo_min": float(row.get("tempo_min", 0) or 0),
                    "latitude": float(row.get("latitude", 0) or 0),
                    "longitude": float(row.get("longitude", 0) or 0),
                    "vazao": float(row.get("vazao", 0) or 0),
                    "status": row.get("status", ""),
                    "pH": float(row.get("pH", 0) or 0),
                    "DQO": float(row.get("DQO", 0) or 0),
                    "OD": float(row.get("OD", 0) or 0),
                    "turbidez": float(row.get("turbidez", 0) or 0),
                    "temperatura": float(row.get("temperatura", 0) or 0),
                    "coliformes": float(row.get("coliformes", 0) or 0),
                    "ecoli": float(row.get("ecoli", 0) or 0),
                    "H2S": float(row.get("H2S", 0) or 0),
                    "amonia": float(row.get("amonia", 0) or 0),
                    "qualidade": row.get("qualidade", "")
                }
                enviar_alerta(dado)
    except FileNotFoundError:
        print(f"Arquivo não encontrado: {CSV_PATH}")
    except Exception as e:
        print(f"Erro ao ler o arquivo CSV: {e}")

if __name__ == "__main__":
    main()
