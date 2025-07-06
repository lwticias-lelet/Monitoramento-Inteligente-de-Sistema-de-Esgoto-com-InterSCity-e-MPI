#!/usr/bin/env python3
"""
Script para adaptar o arquivo monitoramento.csv para o formato do sistema
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def adapt_monitoramento_csv():
    """Adapta o arquivo monitoramento.csv para o formato esperado"""
    
    try:
        # Carregar arquivo original
        print("Carregando arquivo monitoramento.csv...")
        df = pd.read_csv('data/csv/monitoramento.csv')
        
        print(f"✓ Arquivo carregado: {len(df)} registros")
        print(f"✓ Colunas originais: {list(df.columns)}")
        
        # Criar novo DataFrame com colunas padronizadas
        adapted_df = pd.DataFrame()
        
        # Mapear colunas existentes
        print("\nMapeando colunas...")
        
        # Timestamp: converter tempo_min para timestamp real
        base_time = datetime.now()
        adapted_df['timestamp'] = [base_time + timedelta(minutes=float(t)) for t in df['tempo_min']]
        print("✓ timestamp: criado a partir de tempo_min")
        
        # Sensor ID
        adapted_df['sensor_id'] = df['sensorId']
        print("✓ sensor_id: mapeado de sensorId")
        
        # Flow rate (vazão)
        adapted_df['flow_rate'] = df['vazao']
        print("✓ flow_rate: mapeado de vazao")
        
        # Pressure: não existe no original, criar valores simulados baseados na vazão
        adapted_df['pressure'] = (df['vazao'] / 100.0) + np.random.normal(0, 0.1, len(df))
        adapted_df['pressure'] = np.clip(adapted_df['pressure'], 0.5, 5.0)
        print("✓ pressure: simulada baseada na vazão")
        
        # Temperature
        adapted_df['temperature'] = df['temperatura']
        print("✓ temperature: mapeado de temperatura")
        
        # pH Level
        adapted_df['ph_level'] = df['pH']
        print("✓ ph_level: mapeado de pH")
        
        # Turbidity
        adapted_df['turbidity'] = df['turbidez']
        print("✓ turbidity: mapeado de turbidez")
        
        # Location
        adapted_df['location_x'] = df['longitude']
        adapted_df['location_y'] = df['latitude']
        print("✓ location_x/y: mapeado de longitude/latitude")
        
        # Adicionar colunas extras
        adapted_df['status'] = df['status']
        adapted_df['DQO'] = df['DQO']
        adapted_df['OD'] = df['OD']
        adapted_df['coliformes'] = df['coliformes']
        adapted_df['ecoli'] = df['ecoli']
        adapted_df['H2S'] = df['H2S']
        adapted_df['amonia'] = df['amonia']
        adapted_df['qualidade'] = df['qualidade']
        print("✓ Colunas extras preservadas")
        
        # Salvar arquivo adaptado
        output_file = 'data/csv/monitoramento_adapted.csv'
        adapted_df.to_csv(output_file, index=False)
        
        print(f"\n✓ Arquivo adaptado salvo: {output_file}")
        print(f"✓ Registros: {len(adapted_df)}")
        print(f"✓ Colunas finais: {list(adapted_df.columns)}")
        
        # Mostrar estatísticas
        print(f"\n--- Estatísticas dos Dados ---")
        print(f"Sensores únicos: {adapted_df['sensor_id'].nunique()}")
        print(f"IDs dos sensores: {sorted(adapted_df['sensor_id'].unique())}")
        print(f"Período: {adapted_df['timestamp'].min()} até {adapted_df['timestamp'].max()}")
        print(f"Vazão: {adapted_df['flow_rate'].min():.2f} - {adapted_df['flow_rate'].max():.2f}")
        print(f"Temperatura: {adapted_df['temperature'].min():.2f}°C - {adapted_df['temperature'].max():.2f}°C")
        print(f"pH: {adapted_df['ph_level'].min():.2f} - {adapted_df['ph_level'].max():.2f}")
        
        return output_file
        
    except Exception as e:
        print(f"✗ Erro ao adaptar arquivo: {e}")
        return None

if __name__ == "__main__":
    result = adapt_monitoramento_csv()
    
    if result:
        print(f"\n🎉 Sucesso! Agora execute:")
        print(f"python src/data_processing/csv_processor.py {result}")
    else:
        print("❌ Falha na adaptação")