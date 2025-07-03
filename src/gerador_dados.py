"""
Gerador de Dados para Simulação de Sensores
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import csv
import random
import math
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from config.config import DADOS_ANYLOGIC, setup_directories

class GeradorDados:
    """Gerador de dados simulados para sensores de esgoto"""
    
    def __init__(self):
        self.executando = False
        self.thread_geracao = None
        self.sensores_config = self.configurar_sensores()
        self.contador_ciclos = 0
        
        # Garantir que diretórios existem
        setup_directories()
    
    def configurar_sensores(self):
        """Configura sensores virtuais com características diferentes"""
        sensores = []
        
        comportamentos = ['normal', 'instavel', 'problematico']
        
        for i in range(10):
            sensor = {
                'id': f'SENSOR_{i:03d}',
                'latitude': -23.5 + (i * 0.015),
                'longitude': -46.6 + (i * 0.012),
                'vazao_base': 180 + (i * 25),  # 180 a 405 L/s
                'comportamento': random.choice(comportamentos),
                'fator_ruido': random.uniform(0.8, 1.2),
                'tendencia_anomalia': random.uniform(0.01, 0.08)  # 1% a 8%
            }
            sensores.append(sensor)
        
        return sensores
    
    def calcular_vazao_sensor(self, sensor, timestamp_atual):
        """Calcula vazão realística para um sensor"""
        # Hora do dia para padrão circadiano
        hora_do_dia = timestamp_atual.hour + timestamp_atual.minute / 60.0
        
        # Padrões circadianos (picos manhã e noite)
        pico_manha = math.exp(-((hora_do_dia - 7.5) ** 2) / 8)
        pico_noite = math.exp(-((hora_do_dia - 19.5) ** 2) / 8)
        fator_circadiano = 0.6 + 0.4 * (pico_manha + pico_noite)
        
        # Vazão base com padrão temporal
        vazao_base = sensor['vazao_base'] * fator_circadiano
        
        # Ruído baseado no comportamento
        if sensor['comportamento'] == 'normal':
            ruido = random.gauss(0, 10) * sensor['fator_ruido']
            prob_anomalia = sensor['tendencia_anomalia'] * 0.5
        elif sensor['comportamento'] == 'instavel':
            ruido = random.gauss(0, 20) * sensor['fator_ruido']
            prob_anomalia = sensor['tendencia_anomalia'] * 1.0
        else:  # problematico
            ruido = random.gauss(0, 35) * sensor['fator_ruido']
            prob_anomalia = sensor['tendencia_anomalia'] * 2.0
        
        # Simular anomalias ocasionais
        fator_anomalia = 1.0
        status = "NORMAL"
        
        if random.random() < prob_anomalia:
            tipo_anomalia = random.choices(
                ['entupimento', 'vazamento', 'pico_temporario'],
                weights=[0.4, 0.3, 0.3],
                k=1
            )[0]
            
            if tipo_anomalia == 'entupimento':
                fator_anomalia = random.uniform(0.1, 0.4)
                status = "ENTUPIMENTO"
            elif tipo_anomalia == 'vazamento':
                fator_anomalia = random.uniform(2.0, 4.0)
                status = "VAZAMENTO"
            else:  # pico temporário
                fator_anomalia = random.uniform(1.3, 2.0)
                status = "PICO_TEMPORARIO"
        
        # Calcular vazão final
        vazao_final = max(0, vazao_base * fator_anomalia + ruido)
        
        return vazao_final, status
    
    def gerar_dados_estaticos(self, duracao_horas=2):
        """Gera conjunto estático de dados para teste"""
        print(f"🔧 Gerando dados estáticos para {duracao_horas} horas...")
        
        try:
            with open(DADOS_ANYLOGIC, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Cabeçalho
                writer.writerow(['timestamp', 'sensor_id', 'latitude', 'longitude', 'vazao', 'status'])
                
                # Gerar dados
                timestamp_base = datetime.now()
                total_minutos = int(duracao_horas * 60)
                total_registros = 0
                
                for minuto in range(total_minutos):
                    timestamp_atual = timestamp_base + timedelta(minutes=minuto)
                    
                    for sensor in self.sensores_config:
                        vazao, status = self.calcular_vazao_sensor(sensor, timestamp_atual)
                        
                        writer.writerow([
                            timestamp_atual.strftime('%Y-%m-%d %H:%M:%S'),
                            sensor['id'],
                            f"{sensor['latitude']:.6f}",
                            f"{sensor['longitude']:.6f}",
                            f"{vazao:.2f}",
                            status
                        ])
                        
                        total_registros += 1
                    
                    # Progresso
                    if (minuto + 1) % 30 == 0:
                        print(f"📈 Progresso: {minuto + 1}/{total_minutos} minutos")
            
            print(f"✅ Dados estáticos gerados!")
            print(f"📊 Total de registros: {total_registros}")
            print(f"📁 Arquivo: {DADOS_ANYLOGIC}")
            print(f"🎯 Sensores configurados:")
            
            for sensor in self.sensores_config:
                print(f"   {sensor['id']}: {sensor['comportamento']} "
                      f"(Base: {sensor['vazao_base']:.0f} L/s, "
                      f"Anomalias: {sensor['tendencia_anomalia']*100:.1f}%)")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao gerar dados: {e}")
            return False
    
    def gerar_dados_continuo(self):
        """Gera dados continuamente simulando AnyLogic em tempo real"""
        print("🔄 GERAÇÃO CONTÍNUA ATIVADA")
        print("   Simulando AnyLogic em tempo real")
        print("   Pressione Ctrl+C ou chame stop() para parar")
        print(f"   Arquivo: {DADOS_ANYLOGIC}")
        print("-" * 60)
        
        try:
            # Inicializar arquivo com cabeçalho
            with open(DADOS_ANYLOGIC, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'sensor_id', 'latitude', 'longitude', 'vazao', 'status'])
            
            self.contador_ciclos = 0
            inicio = time.time()
            
            while self.executando:
                timestamp_atual = datetime.now()
                
                # Gerar dados para todos os sensores
                registros_ciclo = []
                anomalias_detectadas = []
                
                for sensor in self.sensores_config:
                    vazao, status = self.calcular_vazao_sensor(sensor, timestamp_atual)
                    
                    registro = [
                        timestamp_atual.strftime('%Y-%m-%d %H:%M:%S'),
                        sensor['id'],
                        f"{sensor['latitude']:.6f}",
                        f"{sensor['longitude']:.6f}",
                        f"{vazao:.2f}",
                        status
                    ]
                    
                    registros_ciclo.append(registro)
                    
                    if status != "NORMAL":
                        anomalias_detectadas.append(f"{sensor['id']}:{status}")
                
                # Salvar no arquivo
                with open(DADOS_ANYLOGIC, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerows(registros_ciclo)
                
                self.contador_ciclos += 1
                tempo_decorrido = time.time() - inicio
                
                # Log do ciclo
                print(f"📊 Ciclo {self.contador_ciclos:03d}: "
                      f"{len(self.sensores_config)} sensores → "
                      f"{timestamp_atual.strftime('%H:%M:%S')} "
                      f"(⏱️ {tempo_decorrido:.0f}s)")
                
                # Reportar anomalias
                if anomalias_detectadas:
                    print(f"🔴 Anomalias detectadas: {', '.join(anomalias_detectadas)}")
                
                # Relatório a cada 10 ciclos
                if self.contador_ciclos % 10 == 0:
                    self.relatorio_status(tempo_decorrido)
                
                time.sleep(30)  # Novo ciclo a cada 30 segundos
                
        except Exception as e:
            print(f"❌ Erro na geração contínua: {e}")
        finally:
            self.executando = False
            print(f"\n⏹️  Geração contínua finalizada")
            print(f"📊 Total de ciclos: {self.contador_ciclos}")
            print(f"⏱️  Tempo total: {time.time() - inicio:.1f}s")
    
    def relatorio_status(self, tempo_decorrido):
        """Gera relatório de status da geração"""
        print(f"📋 RELATÓRIO - Ciclo {self.contador_ciclos}")
        print(f"   ⏱️  Tempo decorrido: {tempo_decorrido:.1f}s")
        print(f"   📊 Registros gerados: {self.contador_ciclos * len(self.sensores_config)}")
        print(f"   📁 Tamanho do arquivo: {DADOS_ANYLOGIC.stat().st_size if DADOS_ANYLOGIC.exists() else 0} bytes")
        
        # Verificar comportamento dos sensores
        comportamentos = {}
        for sensor in self.sensores_config:
            comp = sensor['comportamento']
            comportamentos[comp] = comportamentos.get(comp, 0) + 1
        
        print(f"   🎯 Distribuição: {dict(comportamentos)}")
    
    def iniciar_continuo(self):
        """Inicia geração contínua em thread separada"""
        if self.executando:
            print("⚠️  Geração já está em execução!")
            return False
        
        self.executando = True
        self.thread_geracao = threading.Thread(target=self.gerar_dados_continuo, daemon=True)
        self.thread_geracao.start()
        
        print("✅ Geração contínua iniciada em background")
        return True
    
    def parar_continuo(self):
        """Para a geração contínua"""
        if not self.executando:
            print("⚠️  Geração não está em execução!")
            return False
        
        self.executando = False
        if self.thread_geracao:
            self.thread_geracao.join(timeout=5)
        
        print("✅ Geração contínua parada")
        return True
    
    def verificar_dados_existentes(self):
        """Verifica dados existentes"""
        if not DADOS_ANYLOGIC.exists():
            print("📝 Nenhum arquivo de dados encontrado")
            return False
        
        try:
            with open(DADOS_ANYLOGIC, 'r', encoding='utf-8') as f:
                linhas = f.readlines()
            
            if len(linhas) <= 1:
                print("📝 Arquivo existe mas está vazio")
                return False
            
            print(f"📊 DADOS EXISTENTES:")
            print(f"   📁 Arquivo: {DADOS_ANYLOGIC}")
            print(f"   📏 Total de linhas: {len(linhas)}")
            print(f"   📊 Registros de dados: {len(linhas) - 1}")
            print(f"   💾 Tamanho: {DADOS_ANYLOGIC.stat().st_size} bytes")
            
            # Mostrar amostra
            print("   📋 Primeiras linhas:")
            for i, linha in enumerate(linhas[:3]):
                print(f"     {i}: {linha.strip()}")
            
            if len(linhas) > 3:
                print("     ...")
                print(f"     {len(linhas)-1}: {linhas[-1].strip()}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao verificar dados: {e}")
            return False
    
    def limpar_dados(self):
        """Remove arquivos de dados"""
        try:
            if DADOS_ANYLOGIC.exists():
                DADOS_ANYLOGIC.unlink()
                print(f"🗑️  Removido: {DADOS_ANYLOGIC}")
                return True
            else:
                print("📝 Nenhum arquivo para remover")
                return False
        except Exception as e:
            print(f"❌ Erro ao remover dados: {e}")
            return False

def menu_interativo():
    """Menu interativo para o gerador"""
    gerador = GeradorDados()
    
    while True:
        print("\n" + "=" * 60)
        print("🏗️  GERADOR DE DADOS - SISTEMA DE MONITORAMENTO")
        print("=" * 60)
        print("1. 📊 Gerar dados estáticos (2 horas)")
        print("2. 🔄 Iniciar geração contínua")
        print("3. ⏹️  Parar geração contínua")
        print("4. 📋 Verificar dados existentes")
        print("5. 🗑️  Limpar dados")
        print("6. 📈 Status da geração")
        print("7. ❌ Sair")
        print("=" * 60)
        
        try:
            opcao = input("📝 Escolha uma opção (1-7): ").strip()
            
            if opcao == '1':
                print("\n🔧 Gerando dados estáticos...")
                if gerador.gerar_dados_estaticos():
                    print("\n✅ Dados gerados! Pode executar o sistema MPI agora.")
                
            elif opcao == '2':
                print("\n🔄 Iniciando geração contínua...")
                gerador.iniciar_continuo()
                
            elif opcao == '3':
                print("\n⏹️  Parando geração contínua...")
                gerador.parar_continuo()
                
            elif opcao == '4':
                print("\n📋 Verificando dados...")
                gerador.verificar_dados_existentes()
                
            elif opcao == '5':
                print("\n🗑️  Limpando dados...")
                gerador.limpar_dados()
                
            elif opcao == '6':
                print(f"\n📈 STATUS:")
                print(f"   Executando: {'✅' if gerador.executando else '❌'}")
                print(f"   Ciclos: {gerador.contador_ciclos}")
                print(f"   Sensores configurados: {len(gerador.sensores_config)}")
                
            elif opcao == '7':
                if gerador.executando:
                    gerador.parar_continuo()
                print("👋 Saindo...")
                break
                
            else:
                print("❌ Opção inválida! Digite um número de 1 a 7.")
                
        except KeyboardInterrupt:
            if gerador.executando:
                gerador.parar_continuo()
            print("\n👋 Saindo...")
            break
        except Exception as e:
            print(f"❌ Erro: {e}")

if __name__ == "__main__":
    menu_interativo()