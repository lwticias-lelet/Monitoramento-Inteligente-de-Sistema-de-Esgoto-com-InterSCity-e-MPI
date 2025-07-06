pra rodar local :
.\venv\Scripts\Activate.ps1
pip install dash-bootstrap-components
pip install -r requirements.txt 
# Passo 1: Adaptar o CSV
python adapt_monitoramento.py

# Passo 2: Processar dados adaptados
python main_simple.py --mode process --file "data/csv/monitoramento_adapted.csv"

# Passo 3: Iniciar dashboard
python main_simple.py --mode dashboard


USANDO MPI