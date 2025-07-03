"""
Teste simples do MPI
Para verificar se MPI está funcionando corretamente
"""

from mpi4py import MPI
import time
import numpy as np

def teste_comunicacao_basica():
    """Teste básico de comunicação MPI"""
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    
    print(f"🚀 Processo {rank} de {size} iniciado")
    
    if rank == 0:
        # Master
        print("=" * 50)
        print("TESTE DE COMUNICAÇÃO MPI")
        print("=" * 50)
        print(f"Total de processos: {size}")
        
        # Enviar dados para todos os workers
        dados_teste = {
            'timestamp': time.time(),
            'dados': list(range(10)),
            'comando': 'processar'
        }
        
        print(f"📤 Master: Enviando dados para {size-1} workers...")
        
        for worker_rank in range(1, size):
            comm.send(dados_teste, dest=worker_rank, tag=11)
        
        # Receber resultados
        resultados = []
        for worker_rank in range(1, size):
            resultado = comm.recv(source=worker_rank, tag=22)
            resultados.append(resultado)
            print(f"📥 Master: Resultado recebido do worker {worker_rank}")
        
        print(f"✅ Master: Todos os {len(resultados)} resultados recebidos")
        print("📊 Resumo dos resultados:")
        for i, resultado in enumerate(resultados):
            print(f"   Worker {i+1}: {resultado['processados']} itens processados")
        
        # Finalizar workers
        for worker_rank in range(1, size):
            comm.send({'comando': 'finalizar'}, dest=worker_rank, tag=99)
        
        print("🏁 Teste concluído com sucesso!")
        
    else:
        # Worker
        print(f"🔧 Worker {rank}: Aguardando dados do master...")
        
        while True:
            # Receber dados
            dados = comm.recv(source=0, tag=MPI.ANY_TAG, status=MPI.Status())
            
            comando = dados.get('comando', '')
            
            if comando == 'finalizar':
                print(f"🛑 Worker {rank}: Finalizando...")
                break
            elif comando == 'processar':
                print(f"⚙️  Worker {rank}: Processando dados...")
                
                # Simular processamento
                dados_para_processar = dados.get('dados', [])
                resultado_processamento = []
                
                for item in dados_para_processar:
                    # Simular algum processamento
                    resultado = item ** 2 + rank
                    resultado_processamento.append(resultado)
                    time.sleep(0.1)  # Simular tempo de processamento
                
                # Enviar resultado de volta
                resultado = {
                    'worker_id': rank,
                    'processados': len(resultado_processamento),
                    'resultados': resultado_processamento,
                    'timestamp': time.time()
                }
                
                comm.send(resultado, dest=0, tag=22)
                print(f"✅ Worker {rank}: Dados processados e enviados")

def teste_performance():
    """Teste de performance com arrays NumPy"""
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    
    if rank == 0:
        print("\n" + "=" * 50)
        print("TESTE DE PERFORMANCE COM NUMPY")
        print("=" * 50)
        
        # Criar array grande para testar
        array_size = 1000000
        dados = np.random.random(array_size)
        
        print(f"📊 Processando array de {array_size:,} elementos")
        
        inicio = time.time()
        
        # Dividir dados entre workers
        chunks = np.array_split(dados, size - 1) if size > 1 else [dados]
        
        if size > 1:
            # Enviar chunks para workers
            for i, chunk in enumerate(chunks):
                worker_rank = i + 1
                comm.send(chunk, dest=worker_rank, tag=33)
            
            # Receber resultados processados
            resultados = []
            for worker_rank in range(1, size):
                resultado = comm.recv(source=worker_rank, tag=44)
                resultados.append(resultado)
            
            # Combinar resultados
            resultado_final = np.concatenate(resultados)
        else:
            # Processar tudo no master se não há workers
            resultado_final = dados ** 2 + np.sin(dados)
        
        fim = time.time()
        tempo_total = fim - inicio
        
        print(f"⏱️  Tempo total: {tempo_total:.3f} segundos")
        print(f"📈 Velocidade: {array_size/tempo_total:,.0f} elementos/segundo")
        print(f"✅ Resultado final: média = {np.mean(resultado_final):.6f}")
        
        # Finalizar workers
        if size > 1:
            for worker_rank in range(1, size):
                comm.send(None, dest=worker_rank, tag=99)
    
    else:
        # Worker para teste de performance
        while True:
            dados = comm.recv(source=0, tag=MPI.ANY_TAG, status=MPI.Status())
            
            if dados is None:
                break
            
            # Processar chunk
            resultado = dados ** 2 + np.sin(dados)
            comm.send(resultado, dest=0, tag=44)

def main():
    """Função principal do teste"""
    try:
        print("🧪 Iniciando testes MPI...")
        
        # Teste 1: Comunicação básica
        teste_comunicacao_basica()
        
        # Pequena pausa entre testes
        time.sleep(1)
        
        # Teste 2: Performance
        teste_performance()
        
        print("\n🎉 Todos os testes concluídos com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")

if __name__ == "__main__":
    main()