from mpi4py import MPI
import pandas as pd

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

if rank == 0:
    df = pd.read_csv("data/csv/monitoramento.csv")

    chunks = [df.iloc[i::size] for i in range(size)]
else:
    chunks = None

# Distribui os dados entre os processos
local_df = comm.scatter(chunks, root=0)

# Aqui você pode processar os dados locais
print(f"[Processo {rank}] Processando {len(local_df)} registros...")

# Exemplo: Filtrar eventos com status crítico
local_alertas = local_df[local_df["status"].isin(["VAZAMENTO", "ENTUPIMENTO"])]

# Recolhe os resultados no rank 0
alertas_totais = comm.gather(local_alertas, root=0)

if rank == 0:
    df_final = pd.concat(alertas_totais)
    df_final.to_csv("data/alertas.csv", index=False)
    print("Alertas salvos em data/alertas.csv")
