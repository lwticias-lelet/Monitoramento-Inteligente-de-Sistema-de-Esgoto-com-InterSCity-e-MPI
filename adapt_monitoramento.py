import pandas as pd
import datetime
import numpy as np

def adaptar_csv(input_path: str, output_path: str):
    df = pd.read_csv(input_path)
    
    # Definir hora base fixa (exemplo: 2025-07-07 00:00:00)
    base_time = datetime.datetime(2025, 7, 7, 0, 0, 0)
    
    df_adaptado = pd.DataFrame()
    df_adaptado['sensor_id'] = df['sensorId']
    df_adaptado['timestamp'] = df['tempo_min'].apply(lambda x: base_time + datetime.timedelta(minutes=float(x)))
    df_adaptado['flow_rate'] = df['vazao']
    df_adaptado['pressure'] = np.nan  # Sem dado no CSV original
    df_adaptado['temperature'] = df['temperatura']
    df_adaptado['ph_level'] = df['pH']
    df_adaptado['turbidity'] = df['turbidez']
    df_adaptado['is_anomaly'] = df['status'].apply(lambda x: False if x == 'NORMAL' else True)
    df_adaptado['processed_at'] = datetime.datetime.now()
    
    df_adaptado.to_csv(output_path, index=False)
    print(f"Arquivo adaptado salvo em: {output_path}")

if __name__ == "__main__":
    input_csv = r"C:\monitoramento_esgoto\data\csv\monitoramento.csv"
    output_csv = r"C:\monitoramento_esgoto\data\alertas_adaptado.csv"
    adaptar_csv(input_csv, output_csv)
