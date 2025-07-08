import pandas as pd
import os
from datetime import datetime

def adaptar_alertas_para_dashboard(input_file, output_dir):
    try:
        # Verifica se o arquivo de entrada existe
        if not os.path.exists(input_file):
            print(f"Arquivo não encontrado: {input_file}")
            return

        # Lê o CSV de alertas
        df = pd.read_csv(input_file)

        # Mapeamento de colunas
        df_dashboard = pd.DataFrame()
        df_dashboard["timestamp"] = pd.to_datetime("2025-07-07") + pd.to_timedelta(df["tempo_min"], unit="m")
        df_dashboard["sensor_id"] = df["sensorId"]
        df_dashboard["flow_rate"] = df["vazao"]
        df_dashboard["pressure"] = df["dqo"] / 100  # exemplo de proxy para pressão
        df_dashboard["temperature"] = df["temperatura"]
        df_dashboard["ph_level"] = df["ph"]
        df_dashboard["turbidity"] = df["turbidez"]
        df_dashboard["location_x"] = df["longitude"]
        df_dashboard["location_y"] = df["latitude"]
        df_dashboard["is_anomaly"] = df["status"].isin(["VAZAMENTO", "ENTUPIMENTO"])
        df_dashboard["processed_at"] = datetime.now()

        # Criação do diretório de saída se necessário
        os.makedirs(output_dir, exist_ok=True)

        # Nome do novo arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"data_processed_{timestamp}.csv")

        # Salvando
        df_dashboard.to_csv(output_file, index=False)
        print(f"✅ Arquivo gerado: {output_file}")

    except Exception as e:
        print(f"❌ Erro ao processar arquivo: {e}")

if __name__ == "__main__":
    input_file = "data/alertas_adaptado.csv"
    output_dir = "data/processed"
    adaptar_alertas_para_dashboard(input_file, output_dir)
