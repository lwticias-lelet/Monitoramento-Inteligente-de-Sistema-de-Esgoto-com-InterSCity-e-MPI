#!/usr/bin/env python3
"""
ADAPTADOR INTERSCITY - Sistema de Monitoramento de Esgoto
Integra dados do projeto sem alterar código original
VERSÃO COM URLs CORRIGIDAS POR SERVIÇO
"""

import requests
import json
import pandas as pd
import time
from datetime import datetime
from pathlib import Path
import logging

class InterSCityAdapter:
    """Adaptador para integrar dados do projeto com InterSCity"""
    
    def __init__(self):
        # URLs específicas por serviço
        self.catalog_base = "https://cidadesinteligentes.lsdi.ufma.br/interscity_lh/catalog"
        self.adaptor_base = "https://cidadesinteligentes.lsdi.ufma.br/interscity_lh/adaptor"
        self.collector_base = "https://cidadesinteligentes.lsdi.ufma.br/interscity_lh/collector"
        
        self.project_data_path = Path("data/processed")  # Pasta do seu projeto
        self.capabilities_map = {}
        self.resources_map = {}
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("Adaptador InterSCity inicializado com URLs corrigidas")
        self.logger.info(f"Catalog: {self.catalog_base}")
        self.logger.info(f"Adaptor: {self.adaptor_base}")
        self.logger.info(f"Collector: {self.collector_base}")
    
    def criar_capabilities_esgoto(self):
        """Cria capabilities específicas para monitoramento de esgoto"""
        
        capabilities_esgoto = [
            {
                "name": "vazao_esgoto",
                "description": "Mede a vazão de esgoto em litros por segundo",
                "capability_type": "sensor"
            },
            {
                "name": "pressao_rede",
                "description": "Mede a pressão na rede de esgoto em bar",
                "capability_type": "sensor"
            },
            {
                "name": "temperatura_efluente",
                "description": "Mede a temperatura do efluente em graus Celsius",
                "capability_type": "sensor"
            },
            {
                "name": "ph_esgoto",
                "description": "Mede o pH do esgoto (escala 0-14)",
                "capability_type": "sensor"
            },
            {
                "name": "turbidez_efluente",
                "description": "Mede a turbidez do efluente em NTU",
                "capability_type": "sensor"
            },
            {
                "name": "qualidade_agua",
                "description": "Avalia qualidade geral da água tratada",
                "capability_type": "sensor"
            },
            {
                "name": "dqo_efluente",
                "description": "Demanda Química de Oxigênio do efluente",
                "capability_type": "sensor"
            },
            {
                "name": "nivel_oxigenio",
                "description": "Nível de oxigênio dissolvido na água",
                "capability_type": "sensor"
            }
        ]
        
        for capability in capabilities_esgoto:
            try:
                # URL correta para capabilities
                response = requests.post(
                    f"{self.catalog_base}/capabilities/",
                    json=capability
                )
                
                if response.status_code == 201:
                    cap_data = response.json()
                    self.capabilities_map[capability["name"]] = cap_data["id"]
                    self.logger.info(f"Capability criada: {capability['name']} (ID: {cap_data['id']})")
                elif response.status_code == 400:
                    # Capability já existe
                    self.logger.info(f"Capability já existe: {capability['name']}")
                else:
                    self.logger.error(f"Erro ao criar capability {capability['name']}: {response.status_code}")
                    self.logger.error(f"Response: {response.text}")
                    
            except Exception as e:
                self.logger.error(f"Erro na requisição para {capability['name']}: {e}")
        
        # Buscar capabilities existentes para mapear IDs
        self.buscar_capabilities_existentes()
    
    def buscar_capabilities_existentes(self):
        """Busca capabilities já existentes no InterSCity"""
        try:
            # URL correta para listar capabilities
            response = requests.get(f"{self.catalog_base}/capabilities")
            
            if response.status_code == 200:
                capabilities = response.json()["capabilities"]
                
                # Mapear nomes para IDs
                for cap in capabilities:
                    name = cap["name"]
                    if any(name.startswith(prefix) for prefix in 
                          ["vazao", "pressao", "temperatura", "ph", "turbidez", "qualidade", "dqo", "nivel"]):
                        self.capabilities_map[name] = cap["id"]
                        
                self.logger.info(f"Mapeadas {len(self.capabilities_map)} capabilities existentes")
                
        except Exception as e:
            self.logger.error(f"Erro ao buscar capabilities: {e}")
    
    def criar_recursos_sensores(self, dados_sensores):
        """Cria resources para cada sensor do projeto"""
        
        sensores_unicos = dados_sensores['sensor_id'].unique()
        
        for sensor_id in sensores_unicos:
            # Dados do sensor
            sensor_data = dados_sensores[dados_sensores['sensor_id'] == sensor_id].iloc[0]
            
            resource_json = {
                "data": {
                    "description": f"Sensor de monitoramento de esgoto - {sensor_id}",
                    "capabilities": [
                        "vazao_esgoto",
                        "pressao_rede", 
                        "temperatura_efluente",
                        "ph_esgoto",
                        "turbidez_efluente"
                    ],
                    "status": "active",
                    "lat": float(sensor_data.get('location_y', -2.5227)),  # São Luís default
                    "lon": float(sensor_data.get('location_x', -44.2549))
                }
            }
            
            try:
                # URL correta para resources
                response = requests.post(
                    f"{self.catalog_base}/resources",
                    json=resource_json
                )
                
                if response.status_code == 201:
                    resource = response.json()
                    uuid = resource['data']['uuid']
                    self.resources_map[sensor_id] = uuid
                    
                    self.logger.info(f"Resource criado para sensor {sensor_id}: {uuid}")
                else:
                    self.logger.error(f"Erro ao criar resource para {sensor_id}: {response.status_code}")
                    self.logger.error(f"Response: {response.text}")
                    
            except Exception as e:
                self.logger.error(f"Erro na criação do resource {sensor_id}: {e}")
    
    def converter_dados_projeto_para_interscity(self, df):
        """Converte dados do projeto para formato InterSCity"""
        
        dados_convertidos = []
        
        # Mapeamento de qualidade texto para número
        qualidade_map = {
            'RUIM': 1,
            'REGULAR': 2,
            'BOA': 3,
            'EXCELENTE': 4,
            'PÉSSIMA': 0,
            'ÓTIMA': 5
        }
        
        for _, row in df.iterrows():
            # Timestamp no formato ISO
            timestamp = row.get('timestamp', datetime.now().isoformat())
            if pd.isna(timestamp):
                timestamp = datetime.now().isoformat()
            elif not isinstance(timestamp, str):
                timestamp = pd.to_datetime(timestamp).isoformat()
            
            # Dados por capability
            data_entry = {
                "data": [
                    {
                        "vazao_esgoto": float(row.get('flow_rate', 0)),
                        "pressao_rede": float(row.get('pressure', 0)),
                        "temperatura_efluente": float(row.get('temperature', 20)),
                        "ph_esgoto": float(row.get('ph_level', 7)),
                        "turbidez_efluente": float(row.get('turbidity', 0)),
                        "timestamp": timestamp
                    }
                ]
            }
            
            # Adicionar dados extras se disponíveis
            if 'qualidade' in row and not pd.isna(row['qualidade']):
                qualidade_texto = str(row['qualidade']).upper().strip()
                qualidade_valor = qualidade_map.get(qualidade_texto, 2)  # Default = REGULAR
                data_entry["data"][0]["qualidade_agua"] = qualidade_valor
            
            if 'DQO' in row and not pd.isna(row['DQO']):
                data_entry["data"][0]["dqo_efluente"] = float(row['DQO'])
            
            if 'OD' in row and not pd.isna(row['OD']):
                data_entry["data"][0]["nivel_oxigenio"] = float(row['OD'])
            
            dados_convertidos.append({
                "sensor_id": row['sensor_id'],
                "data": data_entry
            })
        
        return dados_convertidos
    
    def enviar_dados_para_interscity(self, dados_convertidos):
        """Envia dados convertidos para InterSCity"""
        
        for entrada in dados_convertidos:
            sensor_id = entrada["sensor_id"]
            data = entrada["data"]
            
            if sensor_id not in self.resources_map:
                self.logger.warning(f"Sensor {sensor_id} não tem resource mapeado")
                continue
            
            uuid = self.resources_map[sensor_id]
            
            try:
                # URL CORRETA para envio de dados - usando ADAPTOR
                response = requests.post(
                    f"{self.adaptor_base}/resources/{uuid}/data/monitoramento_esgoto",
                    json=data
                )
                
                if response.status_code == 201:
                    self.logger.info(f"✅ Dados enviados para sensor {sensor_id}")
                else:
                    self.logger.error(f"❌ Erro ao enviar dados para {sensor_id}: {response.status_code}")
                    self.logger.error(f"Response: {response.text}")
                    
                    # Tentar endpoint alternativo se 404
                    if response.status_code == 404:
                        self.logger.info(f"Tentando endpoint alternativo para {sensor_id}...")
                        response_alt = requests.post(
                            f"{self.adaptor_base}/resources/{uuid}/data/environment_monitoring",
                            json=data
                        )
                        if response_alt.status_code == 201:
                            self.logger.info(f"✅ Dados enviados via endpoint alternativo para {sensor_id}")
                        else:
                            self.logger.error(f"❌ Endpoint alternativo também falhou: {response_alt.status_code}")
                    
            except Exception as e:
                self.logger.error(f"Erro no envio para {sensor_id}: {e}")
    
    def carregar_dados_projeto(self):
        """Carrega dados mais recentes do projeto"""
        
        if not self.project_data_path.exists():
            self.logger.error(f"Pasta do projeto não encontrada: {self.project_data_path}")
            return None
        
        # Buscar arquivo processado mais recente
        arquivos_csv = list(self.project_data_path.glob("data_processed_*.csv"))
        
        if not arquivos_csv:
            # Buscar arquivo adaptado como fallback
            arquivo_adaptado = Path("data/csv/monitoramento_adapted.csv")
            if arquivo_adaptado.exists():
                arquivos_csv = [arquivo_adaptado]
            else:
                self.logger.warning("Nenhum arquivo de dados encontrado")
                return None
        
        # Arquivo mais recente
        arquivo_mais_recente = max(arquivos_csv, key=lambda f: f.stat().st_mtime)
        
        try:
            df = pd.read_csv(arquivo_mais_recente)
            self.logger.info(f"Dados carregados: {arquivo_mais_recente.name} ({len(df)} registros)")
            return df
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar dados: {e}")
            return None
    
    def processar_integracao_completa(self):
        """Executa integração completa: cria capabilities, resources e envia dados"""
        
        self.logger.info("=== INICIANDO INTEGRAÇÃO COM INTERSCITY ===")
        
        # 1. Carregar dados do projeto
        df = self.carregar_dados_projeto()
        if df is None:
            return False
        
        # 2. Criar capabilities
        self.logger.info("Criando capabilities...")
        self.criar_capabilities_esgoto()
        
        # 3. Criar resources para sensores
        self.logger.info("Criando resources...")
        self.criar_recursos_sensores(df)
        
        # 4. Converter dados
        self.logger.info("Convertendo dados...")
        dados_convertidos = self.converter_dados_projeto_para_interscity(df)
        
        # 5. Enviar dados (apenas uma amostra para evitar sobrecarga)
        self.logger.info("Enviando dados de amostra...")
        # Enviar apenas os primeiros 5 registros por sensor para teste
        amostra_dados = {}
        for entrada in dados_convertidos:
            sensor_id = entrada["sensor_id"]
            if sensor_id not in amostra_dados:
                amostra_dados[sensor_id] = 0
            if amostra_dados[sensor_id] < 5:  # Máximo 5 registros por sensor
                self.enviar_dados_para_interscity([entrada])
                amostra_dados[sensor_id] += 1
        
        self.logger.info("=== INTEGRAÇÃO CONCLUÍDA ===")
        return True
    
    def executar_monitoramento_continuo(self, intervalo_segundos=300):
        """Executa monitoramento contínuo - verifica novos dados a cada intervalo"""
        
        self.logger.info(f"Iniciando monitoramento contínuo (intervalo: {intervalo_segundos}s)")
        
        ultimo_arquivo = None
        
        while True:
            try:
                # Verificar se há arquivo novo
                df = self.carregar_dados_projeto()
                
                if df is not None:
                    arquivo_atual = max(self.project_data_path.glob("data_processed_*.csv"), 
                                      key=lambda f: f.stat().st_mtime, default=None)
                    
                    if arquivo_atual != ultimo_arquivo:
                        self.logger.info("Novo arquivo detectado - processando...")
                        
                        # Converter e enviar apenas dados novos (amostra)
                        dados_convertidos = self.converter_dados_projeto_para_interscity(df)
                        
                        # Enviar amostra
                        amostra_dados = {}
                        for entrada in dados_convertidos:
                            sensor_id = entrada["sensor_id"]
                            if sensor_id not in amostra_dados:
                                amostra_dados[sensor_id] = 0
                            if amostra_dados[sensor_id] < 3:  # 3 registros por sensor
                                self.enviar_dados_para_interscity([entrada])
                                amostra_dados[sensor_id] += 1
                        
                        ultimo_arquivo = arquivo_atual
                    
                time.sleep(intervalo_segundos)
                
            except KeyboardInterrupt:
                self.logger.info("Monitoramento interrompido pelo usuário")
                break
            except Exception as e:
                self.logger.error(f"Erro no monitoramento: {e}")
                time.sleep(60)  # Aguardar 1 minuto antes de tentar novamente
    
    def verificar_dados_no_interscity(self, sensor_id):
        """Verifica se dados foram enviados corretamente para o InterSCity"""
        
        if sensor_id not in self.resources_map:
            self.logger.error(f"Sensor {sensor_id} não encontrado no mapeamento")
            return None
        
        uuid = self.resources_map[sensor_id]
        
        try:
            # URL CORRETA para buscar dados - usando COLLECTOR
            response = requests.post(f"{self.collector_base}/resources/{uuid}/data")
            
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"Dados recuperados para {sensor_id}:")
                print(json.dumps(data, indent=2))
                return data
            else:
                self.logger.error(f"Erro ao recuperar dados: {response.status_code}")
                self.logger.error(f"Response: {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Erro na verificação: {e}")
            return None
    
    def listar_resources_criados(self):
        """Lista todos os resources criados"""
        try:
            response = requests.get(f"{self.catalog_base}/resources")
            
            if response.status_code == 200:
                resources = response.json()["resources"]
                
                self.logger.info("📋 Resources no InterSCity:")
                for resource in resources:
                    if "esgoto" in resource.get("description", "").lower():
                        self.logger.info(f"  - {resource['description']}: {resource['uuid']}")
                
                return resources
            else:
                self.logger.error(f"Erro ao listar resources: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Erro ao listar resources: {e}")
            return []

# ============================================================================
# FUNÇÕES DE USO
# ============================================================================

def integração_única():
    """Executa integração uma única vez"""
    adapter = InterSCityAdapter()
    sucesso = adapter.processar_integracao_completa()
    
    if sucesso:
        print("\n✅ Integração realizada com sucesso!")
        print("🔗 Dados do seu projeto agora estão disponíveis no InterSCity")
        
        # Listar resources criados
        print("\n📋 Listando resources criados:")
        adapter.listar_resources_criados()
        
        # Verificar um sensor como exemplo
        if adapter.resources_map:
            sensor_exemplo = list(adapter.resources_map.keys())[0]
            print(f"\n📊 Verificando dados do sensor {sensor_exemplo}:")
            adapter.verificar_dados_no_interscity(sensor_exemplo)
    else:
        print("❌ Erro na integração")

def monitoramento_contínuo():
    """Executa monitoramento contínuo"""
    adapter = InterSCityAdapter()
    
    # Setup inicial
    print("🔧 Configuração inicial...")
    sucesso = adapter.processar_integracao_completa()
    
    if sucesso:
        print("✅ Setup concluído - iniciando monitoramento...")
        adapter.executar_monitoramento_continuo(intervalo_segundos=300)  # 5 minutos
    else:
        print("❌ Erro na configuração inicial")

def verificar_status():
    """Verifica status atual no InterSCity"""
    adapter = InterSCityAdapter()
    
    # Buscar capabilities existentes
    adapter.buscar_capabilities_existentes()
    
    print("📋 Capabilities mapeadas:")
    for name, cap_id in adapter.capabilities_map.items():
        print(f"  - {name}: {cap_id}")
    
    # Listar resources
    print("\n📋 Resources disponíveis:")
    adapter.listar_resources_criados()

# ============================================================================
# EXECUÇÃO PRINCIPAL
# ============================================================================

if __name__ == "__main__":
    print("🚀 ADAPTADOR INTERSCITY - Sistema de Monitoramento de Esgoto")
    print("=" * 60)
    print("VERSÃO COM URLs CORRIGIDAS POR SERVIÇO")
    print(f"🔗 Catalog: https://cidadesinteligentes.lsdi.ufma.br/interscity_lh/catalog")
    print(f"📤 Adaptor: https://cidadesinteligentes.lsdi.ufma.br/interscity_lh/adaptor")
    print(f"📥 Collector: https://cidadesinteligentes.lsdi.ufma.br/interscity_lh/collector")
    
    print("\nEscolha uma opção:")
    print("1. Integração única (executar uma vez)")
    print("2. Monitoramento contínuo (fica rodando)")
    print("3. Verificar status no InterSCity")
    
    opcao = input("\nOpção (1-3): ").strip()
    
    if opcao == "1":
        integração_única()
    elif opcao == "2":
        monitoramento_contínuo()
    elif opcao == "3":
        verificar_status()
    else:
        print("❌ Opção inválida")

