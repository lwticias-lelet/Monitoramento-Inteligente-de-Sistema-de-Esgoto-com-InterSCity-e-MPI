"""
Sistema de Monitoramento de Esgoto com MPI
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from mpi4py import MPI
import numpy as np
import pandas as pd
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from config.config import *

class Logger:
    """Sistema de logging personalizado para MPI"""
    
    def __init__(self, rank, size):
        self.rank = rank
        self.size = size
        
        # Configurar logging
        log_file = LOGS_DIR / f"sistema_rank_{rank}.log"
        
        logging.basicConfig(
            level=getattr(logging, LOGGING_CONFIG["level"]),
            format=LOGGING_CONFIG["format"],
            datefmt=LOGGING_CONFIG["date_format"],
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(f"Rank{rank}")
    
    def info(self, message):
        self.logger.info(message, extra={'rank': self.rank})
    
    def warning(self, message):
        self.logger.warning(message, extra={'rank': self.rank})
    
    def error(self, message):
        self.logger.error(message, extra={'rank': self.rank})
    
    def debug(self, message):
        self.logger.debug(message, extra={'rank': self.rank})

class DetectorAnomalias:
    """Classe para detecção de anomalias em sensores"""
    
    def __init__(self):
        self.historico_sensores = {}
        self.config = ANOMALIA_CONFIG
    
    def adicionar_leitura(self, sensor_id, vazao):
        """Adiciona nova leitura ao histórico"""
        if sensor_id not in self.historico_sensores:
            self.historico_sensores[sensor_id] = []
        
        self.historico_sensores[sensor_id].append(float(vazao))
        
        # Manter apenas últimas N leituras
        max_hist = self.config["max_historico"]
        if len(self.historico_sensores[sensor_id]) > max_hist:
            self.historico_sensores[sensor_id] = self.historico_sensores[sensor_id][-max_hist:]
    
    def detectar_anomalia(self, sensor_id, vazao_atual):
        """Detecta anomalias baseado no histórico"""
        vazao_atual = float(vazao_atual)
        
        # Adicionar leitura atual
        self.adicionar_leitura(sensor_id, vazao_atual)
        
        # Verificar se tem histórico suficiente
        if sensor_id not in self.historico_sensores:
            return False, "SEM_HISTORICO"
        
        historico = self.historico_sensores[sensor_id]
        if len(historico) < self.config["min_historico"]:
            return False, "HISTORICO_INSUFICIENTE"
        
        # Análise estatística
        historico_array = np.array(historico[:-1])  # Excluir leitura atual
        media = np.mean(historico_array)
        desvio = np.std(historico_array)
        
        if desvio == 0:
            return False, "SENSOR_CONSTANTE"
        
        # Calcular z-score
        z_score = abs(vazao_atual - media) / desvio
        
        # Classificar anomalia
        if z_score > self.config["threshold_critico"]:
            if vazao_atual > media:
                return True, "VAZAMENTO_CRITICO"
            else:
                return True, "ENTUPIMENTO_CRITICO"
        elif z_score > self.config["threshold_desvio"]:
            if vazao_atual > media:
                return True, "VAZAMENTO_ALTO"
            else:
                return True, "ENTUPIMENTO_ALTO"
        
        return False, "NORMAL"

class LeitorDados:
    """Classe para leitura de dados do AnyLogic"""
    
    def __init__(self, logger):
        self.logger = logger
        self.ultimo_tamanho = 0
    
    def ler_dados_anylogic(self):
        """Lê dados gerados pelo AnyLogic"""
        try:
            if not DADOS_ANYLOGIC.exists():
                return []
            
            # Verificar se arquivo mudou
            tamanho_atual = DADOS_ANYLOGIC.stat().st_size
            if tamanho_atual == self.ultimo_tamanho:
                return []  # Sem dados novos
            
            self.ultimo_tamanho = tamanho_atual
            
            # Ler CSV
            df = pd.read_csv(DADOS_ANYLOGIC, encoding='utf-8')
            
            # Verificar estrutura
            if len(df.columns) >= 5:
                if 'timestamp' not in df.columns:
                    df.columns = ['timestamp', 'sensor_id', 'latitude', 'longitude', 'vazao'] + list(df.columns[5:])
            
            # Retornar dados recentes
            if len(df) > 100:
                df = df.tail(100)
            
            return df.to_dict('records')
            
        except Exception as e:
            self.logger.error(f"Erro ao ler dados do AnyLogic: {e}")
            return []

class SistemaMonitoramento:
    """Sistema principal de monitoramento"""
    
    def __init__(self):
        # Configurar MPI
        self.comm = MPI.COMM_WORLD
        self.rank = self.comm.Get_rank()
        self.size = self.comm.Get_size()
        
        # Configurar componentes
        self.logger = Logger(self.rank, self.size)
        self.detector = DetectorAnomalias()
        self.leitor = LeitorDados(self.logger)
        
        # Estado do sistema
        self.alertas_totais = []
        self.ciclos_executados = 0
        self.inicio_sistema = datetime.now()
        
        self.logger.info(f"Sistema inicializado - Processo {self.rank}/{self.size}")
    
    def processo_master(self):
        """Processo master - coordena operações"""
        self.logger.info("=== PROCESSO MASTER INICIADO ===")
        self.logger.info(f"Workers disponíveis: {self.size - 1}")
        self.logger.info(f"Configuração: {SISTEMA_CONFIG}")
        
        try:
            for ciclo in range(1, SISTEMA_CONFIG["ciclos_monitoramento"] + 1):
                self.ciclos_executados = ciclo
                self.logger.info(f"--- CICLO {ciclo:03d} ---")
                
                # 1. Ler dados do AnyLogic
                dados_sensores = self.leitor.ler_dados_anylogic()
                
                if not dados_sensores:
                    self.logger.warning("Nenhum dado novo do AnyLogic")
                    time.sleep(5)
                    continue
                
                self.logger.info(f"Processando {len(dados_sensores)} leituras")
                
                # 2. Processar com workers ou localmente
                alertas_ciclo = self.processar_dados_distribuido(dados_sensores, ciclo)
                
                # 3. Consolidar resultados
                self.processar_alertas(alertas_ciclo, ciclo)
                
                # 4. Comunicar com InterSCity
                self.comunicar_intersCity(dados_sensores, alertas_ciclo, ciclo)
                
                # 5. Salvar dados
                self.salvar_dados_ciclo(dados_sensores, alertas_ciclo, ciclo)
                
                # 6. Relatório de progresso
                if ciclo % 10 == 0:
                    self.relatorio_progresso(ciclo)
                
                time.sleep(SISTEMA_CONFIG["intervalo_ciclo"])
                
        except KeyboardInterrupt:
            self.logger.info("Sistema interrompido pelo usuário")
        except Exception as e:
            self.logger.error(f"Erro crítico no master: {e}")
        finally:
            self.finalizar_workers()
            self.gerar_relatorio_final()
    
    def processar_dados_distribuido(self, dados_sensores, ciclo):
        """Distribui processamento entre workers"""
        if self.size == 1:
            # Sem workers, processar tudo no master
            return self.processar_dados_local(dados_sensores)
        
        # Dividir dados entre workers
        chunks = np.array_split(dados_sensores, self.size - 1)
        alertas_total = []
        
        # Enviar dados para workers
        for i, chunk in enumerate(chunks):
            if len(chunk) > 0:
                worker_rank = i + 1
                dados_worker = {
                    'ciclo': ciclo,
                    'dados': chunk.tolist(),
                    'timestamp': datetime.now().isoformat()
                }
                self.comm.send(dados_worker, dest=worker_rank, tag=10)
        
        # Receber resultados
        for worker_rank in range(1, self.size):
            try:
                resultado = self.comm.recv(source=worker_rank, tag=20)
                if resultado and 'alertas' in resultado:
                    alertas_total.extend(resultado['alertas'])
                    self.logger.debug(f"Worker {worker_rank}: {len(resultado['alertas'])} alertas")
            except Exception as e:
                self.logger.error(f"Erro ao receber dados do worker {worker_rank}: {e}")
        
        return alertas_total
    
    def processar_dados_local(self, dados_sensores):
        """Processa dados localmente (sem workers)"""
        alertas = []
        
        for sensor_data in dados_sensores:
            sensor_id = sensor_data.get('sensor_id', 'UNKNOWN')
            vazao = sensor_data.get('vazao', 0)
            
            # Detectar anomalia
            tem_anomalia, tipo_anomalia = self.detector.detectar_anomalia(sensor_id, vazao)
            
            if tem_anomalia and tipo_anomalia not in ['SEM_HISTORICO', 'HISTORICO_INSUFICIENTE']:
                alerta = {
                    'sensor_id': sensor_id,
                    'tipo': tipo_anomalia,
                    'vazao': float(vazao),
                    'timestamp': datetime.now().isoformat(),
                    'localizacao': [
                        float(sensor_data.get('latitude', 0)),
                        float(sensor_data.get('longitude', 0))
                    ],
                    'processado_por': f"Master {self.rank}"
                }
                alertas.append(alerta)
        
        return alertas
    
    def processo_worker(self):
        """Processo worker - processa dados regionais"""
        regiao = f"Região {self.rank}"
        self.logger.info(f"Worker iniciado - {regiao}")
        
        detector_local = DetectorAnomalias()
        
        try:
            while True:
                # Aguardar dados do master
                try:
                    dados = self.comm.recv(source=0, tag=10, status=MPI.Status())
                except:
                    break
                
                if dados is None:
                    self.logger.info("Sinal de finalização recebido")
                    break
                
                ciclo = dados.get('ciclo', 0)
                sensores = dados.get('dados', [])
                
                self.logger.info(f"Processando {len(sensores)} sensores do ciclo {ciclo}")
                
                # Processar dados
                alertas = []
                for sensor_data in sensores:
                    sensor_id = sensor_data.get('sensor_id', 'UNKNOWN')
                    vazao = sensor_data.get('vazao', 0)
                    
                    tem_anomalia, tipo = detector_local.detectar_anomalia(sensor_id, vazao)
                    
                    if tem_anomalia and tipo not in ['SEM_HISTORICO', 'HISTORICO_INSUFICIENTE']:
                        alerta = {
                            'sensor_id': sensor_id,
                            'tipo': tipo,
                            'vazao': float(vazao),
                            'timestamp': datetime.now().isoformat(),
                            'localizacao': [
                                float(sensor_data.get('latitude', 0)),
                                float(sensor_data.get('longitude', 0))
                            ],
                            'processado_por': f"Worker {self.rank} ({regiao})"
                        }
                        alertas.append(alerta)
                
                # Enviar resultados
                resultado = {
                    'ciclo': ciclo,
                    'alertas': alertas,
                    'worker_id': self.rank,
                    'sensores_processados': len(sensores),
                    'regiao': regiao
                }
                
                self.comm.send(resultado, dest=0, tag=20)
                self.logger.info(f"Ciclo {ciclo} processado: {len(alertas)} alertas")
                
        except Exception as e:
            self.logger.error(f"Erro no worker: {e}")
    
    def processar_alertas(self, alertas_ciclo, ciclo):
        """Processa e categoriza alertas"""
        if not alertas_ciclo:
            self.logger.info("✅ Sistema operando normalmente")
            return
        
        # Categorizar alertas
        criticos = [a for a in alertas_ciclo if 'CRITICO' in a.get('tipo', '')]
        altos = [a for a in alertas_ciclo if 'ALTO' in a.get('tipo', '')]
        
        self.logger.warning(f"🚨 {len(alertas_ciclo)} ALERTAS DETECTADOS:")
        self.logger.warning(f"   Críticos: {len(criticos)}")
        self.logger.warning(f"   Altos: {len(altos)}")
        
        # Log detalhado dos alertas
        for alerta in alertas_ciclo:
            emoji = "🔴" if "CRITICO" in alerta['tipo'] else "🟡"
            self.logger.warning(
                f"  {emoji} {alerta['sensor_id']}: {alerta['tipo']} "
                f"(Vazão: {alerta['vazao']:.1f} L/s)"
            )
        
        self.alertas_totais.extend(alertas_ciclo)
    
    def comunicar_intersCity(self, dados, alertas, ciclo):
        """Simula comunicação com InterSCity"""
        relatorio = {
            'timestamp': datetime.now().isoformat(),
            'ciclo': ciclo,
            'sistema_id': f"MPI_{self.size}proc",
            'dados_resumo': {
                'total_sensores': len(set([d.get('sensor_id') for d in dados])),
                'total_leituras': len(dados),
                'vazao_media': float(np.mean([float(d.get('vazao', 0)) for d in dados])),
            },
            'alertas': {
                'total': len(alertas),
                'criticos': len([a for a in alertas if 'CRITICO' in a.get('tipo', '')]),
                'detalhes': alertas
            },
            'sistema_status': 'ALERTA' if alertas else 'OPERACIONAL'
        }
        
        # Salvar relatório para InterSCity
        arquivo_intersCity = DATA_DIR / 'relatorios_intersCity.jsonl'
        with open(arquivo_intersCity, 'a', encoding='utf-8') as f:
            f.write(json.dumps(relatorio, ensure_ascii=False) + '\n')
        
        self.logger.info(f"📡 Relatório enviado para InterSCity (Ciclo {ciclo})")
    
    def salvar_dados_ciclo(self, dados, alertas, ciclo):
        """Salva dados do ciclo"""
        dados_ciclo = {
            'ciclo': ciclo,
            'timestamp': datetime.now().isoformat(),
            'rank_processador': self.rank,
            'dados_sensores': dados,
            'alertas_detectados': alertas,
            'estatisticas': {
                'total_sensores': len(set([d.get('sensor_id') for d in dados])),
                'historico_sensores': len(self.detector.historico_sensores)
            }
        }
        
        arquivo_ciclo = DATA_DIR / f'ciclo_{ciclo:03d}.json'
        with open(arquivo_ciclo, 'w', encoding='utf-8') as f:
            json.dump(dados_ciclo, f, ensure_ascii=False, indent=2)
    
    def relatorio_progresso(self, ciclo):
        """Gera relatório de progresso"""
        tempo_decorrido = (datetime.now() - self.inicio_sistema).total_seconds()
        
        self.logger.info("📊 RELATÓRIO DE PROGRESSO")
        self.logger.info(f"   Ciclos executados: {ciclo}")
        self.logger.info(f"   Tempo decorrido: {tempo_decorrido:.1f}s")
        self.logger.info(f"   Alertas totais: {len(self.alertas_totais)}")
        self.logger.info(f"   Sensores monitorados: {len(self.detector.historico_sensores)}")
    
    def finalizar_workers(self):
        """Envia sinal de finalização para workers"""
        for worker_rank in range(1, self.size):
            self.comm.send(None, dest=worker_rank, tag=10)
        self.logger.info("Sinal de finalização enviado para todos os workers")
    
    def gerar_relatorio_final(self):
        """Gera relatório final do sistema"""
        tempo_total = (datetime.now() - self.inicio_sistema).total_seconds()
        
        self.logger.info("=" * 60)
        self.logger.info("RELATÓRIO FINAL DO SISTEMA")
        self.logger.info("=" * 60)
        self.logger.info(f"Tempo total de execução: {tempo_total:.1f}s")
        self.logger.info(f"Ciclos executados: {self.ciclos_executados}")
        self.logger.info(f"Total de alertas: {len(self.alertas_totais)}")
        self.logger.info(f"Sensores monitorados: {len(self.detector.historico_sensores)}")
        
        # Estatísticas de alertas
        if self.alertas_totais:
            tipos_alertas = {}
            for alerta in self.alertas_totais:
                tipo = alerta.get('tipo', 'UNKNOWN')
                tipos_alertas[tipo] = tipos_alertas.get(tipo, 0) + 1
            
            self.logger.info("Distribuição de alertas por tipo:")
            for tipo, quantidade in tipos_alertas.items():
                self.logger.info(f"  {tipo}: {quantidade}")
        
        # Salvar relatório final
        relatorio_final = {
            'timestamp_final': datetime.now().isoformat(),
            'tempo_execucao_segundos': tempo_total,
            'ciclos_executados': self.ciclos_executados,
            'alertas_totais': len(self.alertas_totais),
            'sensores_monitorados': len(self.detector.historico_sensores),
            'configuracao_sistema': SISTEMA_CONFIG,
            'detalhes_alertas': self.alertas_totais
        }
        
        arquivo_final = DATA_DIR / 'relatorio_final.json'
        with open(arquivo_final, 'w', encoding='utf-8') as f:
            json.dump(relatorio_final, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Relatório final salvo em: {arquivo_final}")
        self.logger.info("Sistema finalizado com sucesso")

def main():
    """Função principal"""
    # Configurar diretórios
    setup_directories()
    
    # Inicializar sistema
    sistema = SistemaMonitoramento()
    
    if sistema.rank == 0:
        sistema.processo_master()
    else:
        sistema.processo_worker()

if __name__ == "__main__":
    main()