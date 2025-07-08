#!/usr/bin/env python3
import pandas as pd
from pathlib import Path
from datetime import datetime

def generate_processed():
    input_path = Path("codigo/data/csv/monitoramento_adapted.csv")
    output_dir = Path("codigo/data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not input_path.exists():
        print(f"Arquivo adaptado não encontrado: {input_path}")
        return
    
    df = pd.read_csv(input_path)
    
    # Aqui você pode adicionar processamento extra, se desejar
    
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"data_processed_{timestamp_str}.csv"
    df.to_csv(output_path, index=False)
    print(f"Arquivo processed gerado: {output_path}")
    
if __name__ == "__main__":
    generate_processed()
