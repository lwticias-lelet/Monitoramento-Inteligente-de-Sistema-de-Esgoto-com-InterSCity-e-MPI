"""
Servidor Mock da Plataforma InterSCity

"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, render_template_string, jsonify, request
import json
import threading
import time
from datetime import datetime
from pathlib import Path
from config.config import DATA_DIR, INTERSITY_CONFIG, setup_directories

app = Flask(__name__)

class InterSCityPlatform:
    """Plataforma InterSCity simulada"""
    
    def __init__(self):
        self.sensores_registrados = {}
        self.dados_recebidos = []
        self.alertas_ativos = []
        self.estatisticas = {
            'uptime_inicio': datetime.now(),
            'total_mensagens': 0,
            'alertas_processados': 0,
            'ciclos_processados': 0,
            'ultimo_ciclo': None
        }
        
        # Configurar diretórios
        setup_directories()
        
        # Iniciar monitor de dados em background
        self.monitor_ativo = True
        self.monitor_thread = threading.Thread(target=self.monitor_dados_mpi, daemon=True)
        self.monitor_thread.start()
        
        print("🌐 Plataforma InterSCity inicializada")
    
    def monitor_dados_mpi(self):
        """Monitora dados recebidos do sistema MPI"""
        arquivo_relatorios = DATA_DIR / 'relatorios_intersCity.jsonl'
        ultimo_tamanho = 0
        
        while self.monitor_ativo:
            try:
                if arquivo_relatorios.exists():
                    tamanho_atual = arquivo_relatorios.stat().st_size
                    
                    if tamanho_atual > ultimo_tamanho:
                        # Ler novos dados
                        with open(arquivo_relatorios, 'r', encoding='utf-8') as f:
                            f.seek(ultimo_tamanho)
                            novas_linhas = f.readlines()
                        
                        for linha in novas_linhas:
                            try:
                                relatorio = json.loads(linha.strip())
                                self.processar_relatorio_mpi(relatorio)
                            except json.JSONDecodeError:
                                continue
                        
                        ultimo_tamanho = tamanho_atual
                
                time.sleep(10)  # Verificar a cada 10 segundos
                
            except Exception as e:
                print(f"Erro no monitor MPI: {e}")
                time.sleep(30)
    
    def processar_relatorio_mpi(self, relatorio):
        """Processa relatório recebido do sistema MPI"""
        ciclo = relatorio.get('ciclo', '?')
        self.estatisticas['ultimo_ciclo'] = ciclo
        self.estatisticas['ciclos_processados'] += 1
        
        # Processar dados de sensores
        dados_resumo = relatorio.get('dados_resumo', {})
        total_sensores = dados_resumo.get('total_sensores', 0)
        
        # Atualizar sensores registrados
        for i in range(total_sensores):
            sensor_id = f"SENSOR_{i:03d}"
            if sensor_id not in self.sensores_registrados:
                self.auto_registrar_sensor(sensor_id)
        
        # Processar alertas
        alertas_info = relatorio.get('alertas', {})
        novos_alertas = alertas_info.get('detalhes', [])
        
        for alerta_data in novos_alertas:
            self.processar_alerta_automatico(alerta_data)
        
        # Atualizar estatísticas
        self.estatisticas['total_mensagens'] += dados_resumo.get('total_leituras', 0)
        
        # Log de atividade
        status = relatorio.get('sistema_status', 'UNKNOWN')
        print(f"📡 InterSCity: Relatório MPI recebido - Ciclo {ciclo} ({status})")
        
        if novos_alertas:
            print(f"🚨 InterSCity: {len(novos_alertas)} novos alertas processados")
    
    def auto_registrar_sensor(self, sensor_id):
        """Registra sensor automaticamente"""
        self.sensores_registrados[sensor_id] = {
            'id': sensor_id,
            'tipo': 'esgoto',
            'status': 'ATIVO',
            'registro_automatico': True,
            'timestamp_registro': datetime.now().isoformat(),
            'ultima_comunicacao': datetime.now().isoformat()
        }
        
        print(f"🔧 InterSCity: Sensor {sensor_id} auto-registrado")
    
    def processar_alerta_automatico(self, alerta_data):
        """Processa alerta automaticamente"""
        alerta = {
            'id': f"ALERT_{len(self.alertas_ativos):05d}",
            'timestamp': datetime.now().isoformat(),
            'sensor_id': alerta_data.get('sensor_id'),
            'tipo': alerta_data.get('tipo'),
            'vazao': alerta_data.get('vazao'),
            'severidade': self.calcular_severidade(alerta_data),
            'localizacao': alerta_data.get('localizacao', [0, 0]),
            'processado_por': alerta_data.get('processado_por', 'Sistema MPI'),
            'status': 'ATIVO',
            'origem': 'MPI_AUTO'
        }
        
        self.alertas_ativos.append(alerta)
        self.estatisticas['alertas_processados'] += 1
        
        # Acionar resposta baseada na severidade
        self.acionar_resposta_automatica(alerta)
        
        # Salvar log do alerta
        self.salvar_log_alerta(alerta)
    
    def calcular_severidade(self, alerta_data):
        """Calcula severidade do alerta"""
        tipo = alerta_data.get('tipo', '').upper()
        vazao = float(alerta_data.get('vazao', 0))
        
        if 'CRITICO' in tipo:
            return 'CRITICA'
        elif 'VAZAMENTO' in tipo:
            return 'CRITICA' if vazao > 800 else 'ALTA'
        elif 'ENTUPIMENTO' in tipo:
            return 'CRITICA' if vazao < 30 else 'ALTA'
        elif 'ALTO' in tipo:
            return 'ALTA'
        else:
            return 'MEDIA'
    
    def acionar_resposta_automatica(self, alerta):
        """Aciona resposta automática baseada na severidade"""
        severidade = alerta['severidade']
        sensor_id = alerta['sensor_id']
        tipo = alerta['tipo']
        
        if severidade == 'CRITICA':
            print(f"🚨 InterSCity: EMERGÊNCIA - {sensor_id} ({tipo})")
            print("📞 InterSCity: Acionando Defesa Civil e equipes de emergência")
            print("🚑 InterSCity: Protocolo de emergência ativado")
        elif severidade == 'ALTA':
            print(f"⚠️  InterSCity: ALERTA ALTO - {sensor_id} ({tipo})")
            print("📋 InterSCity: Criando ticket de manutenção urgente")
            print("📱 InterSCity: SMS enviado para supervisor de área")
        else:
            print(f"ℹ️  InterSCity: Alerta médio - {sensor_id} ({tipo})")
            print("📧 InterSCity: Email enviado para equipe técnica")
    
    def salvar_log_alerta(self, alerta):
        """Salva log detalhado do alerta"""
        log_alertas = DATA_DIR / 'alertas_intersCity.jsonl'
        with open(log_alertas, 'a', encoding='utf-8') as f:
            f.write(json.dumps(alerta, ensure_ascii=False) + '\n')
    
    def gerar_relatorio_status(self):
        """Gera relatório completo de status"""
        uptime_segundos = (datetime.now() - self.estatisticas['uptime_inicio']).total_seconds()
        
        # Contadores de alertas por severidade
        alertas_por_severidade = {}
        for alerta in self.alertas_ativos:
            if alerta.get('status') == 'ATIVO':
                sev = alerta.get('severidade', 'UNKNOWN')
                alertas_por_severidade[sev] = alertas_por_severidade.get(sev, 0) + 1
        
        # Estatísticas de sensores
        sensores_ativos = len([s for s in self.sensores_registrados.values() 
                              if s.get('status') == 'ATIVO'])
        
        return {
            'timestamp': datetime.now().isoformat(),
            'uptime': {
                'segundos': uptime_segundos,
                'minutos': round(uptime_segundos / 60, 1),
                'horas': round(uptime_segundos / 3600, 2)
            },
            'sensores': {
                'registrados': len(self.sensores_registrados),
                'ativos': sensores_ativos
            },
            'dados': {
                'mensagens_processadas': self.estatisticas['total_mensagens'],
                'ciclos_processados': self.estatisticas['ciclos_processados'],
                'ultimo_ciclo': self.estatisticas['ultimo_ciclo']
            },
            'alertas': {
                'total_processados': self.estatisticas['alertas_processados'],
                'ativos': len([a for a in self.alertas_ativos if a.get('status') == 'ATIVO']),
                'por_severidade': alertas_por_severidade
            },
            'sistema': {
                'status': 'OPERACIONAL',
                'versao': '1.0',
                'modo': 'DESENVOLVIMENTO'
            }
        }
    
    def listar_alertas_recentes(self, limite=10):
        """Lista alertas mais recentes"""
        alertas_ordenados = sorted(
            self.alertas_ativos,
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )
        return alertas_ordenados[:limite]
    
    def finalizar(self):
        """Finaliza a plataforma"""
        self.monitor_ativo = False
        print("🛑 InterSCity: Plataforma finalizada")

# Instância global da plataforma
platform = InterSCityPlatform()

# Rotas da API REST
@app.route('/')
def dashboard():
    """Dashboard principal da plataforma"""
    status = platform.gerar_relatorio_status()
    alertas_recentes = platform.listar_alertas_recentes(5)
    
    html_template = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>InterSCity - Dashboard de Monitoramento</title>
        <meta http-equiv="refresh" content="15">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: #333;
            }
            .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
            
            .header { 
                background: rgba(255,255,255,0.95); 
                padding: 30px; 
                border-radius: 15px; 
                text-align: center; 
                margin-bottom: 30px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            }
            .header h1 { color: #667eea; font-size: 2.5em; margin-bottom: 10px; }
            .header h2 { color: #666; font-size: 1.2em; font-weight: normal; }
            
            .stats-grid { 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
                gap: 20px; 
                margin-bottom: 30px; 
            }
            
            .stat-card { 
                background: rgba(255,255,255,0.95); 
                padding: 25px; 
                border-radius: 15px; 
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                transition: transform 0.3s ease;
            }
            .stat-card:hover { transform: translateY(-5px); }
            
            .stat-value { 
                font-size: 2.5em; 
                font-weight: bold; 
                margin-bottom: 10px;
            }
            .stat-label { color: #666; font-size: 0.9em; text-transform: uppercase; letter-spacing: 1px; }
            
            .operacional { color: #28a745; }
            .alerta { color: #ffc107; }
            .critico { color: #dc3545; }
            .info { color: #17a2b8; }
            
            .alert-section { 
                background: rgba(255,255,255,0.95); 
                padding: 25px; 
                border-radius: 15px; 
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }
            
            .alert-item { 
                padding: 15px; 
                margin: 10px 0; 
                border-radius: 10px; 
                border-left: 5px solid;
            }
            .alert-critica { background: #f8d7da; border-color: #dc3545; }
            .alert-alta { background: #fff3cd; border-color: #ffc107; }
            .alert-media { background: #d1ecf1; border-color: #17a2b8; }
            
            .footer { 
                text-align: center; 
                color: rgba(255,255,255,0.8); 
                margin-top: 30px; 
                font-size: 0.9em;
            }
            
            .status-indicator {
                display: inline-block;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-right: 8px;
            }
            .status-ok { background: #28a745; }
            .status-warning { background: #ffc107; }
            .status-error { background: #dc3545; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🌐 InterSCity Platform</h1>
                <h2>Sistema de Monitoramento de Esgoto Urbano</h2>
                <p><strong>Última atualização:</strong> {{ status.timestamp[:19] }}</p>
                <p><span class="status-indicator status-ok"></span>Sistema Operacional</p>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value operacional">{{ status.sensores.registrados }}</div>
                    <div class="stat-label">Sensores Registrados</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-value info">{{ status.sensores.ativos }}</div>
                    <div class="stat-label">Sensores Ativos</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-value {{ 'critico' if status.alertas.ativos > 0 else 'operacional' }}">
                        {{ status.alertas.ativos }}
                    </div>
                    <div class="stat-label">Alertas Ativos</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-value info">{{ status.dados.mensagens_processadas }}</div>
                    <div class="stat-label">Mensagens Processadas</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-value operacional">{{ status.dados.ciclos_processados }}</div>
                    <div class="stat-label">Ciclos Processados</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-value info">{{ status.uptime.minutos }}</div>
                    <div class="stat-label">Uptime (minutos)</div>
                </div>
            </div>
            
            {% if status.alertas.ativos > 0 %}
            <div class="alert-section">
                <h3>🚨 Alertas Recentes</h3>
                {% for alerta in alertas_recentes %}
                <div class="alert-item alert-{{ alerta.severidade.lower() }}">
                    <strong>{{ alerta.sensor_id }}</strong> - {{ alerta.tipo }}
                    <br><small>Vazão: {{ "%.1f"|format(alerta.vazao) }} L/s | 
                    {{ alerta.timestamp[:19] }} | 
                    Severidade: {{ alerta.severidade }}</small>
                </div>
                {% endfor %}
            </div>
            {% endif %}
            
            <div class="alert-section">
                <h3>📊 Resumo por Severidade</h3>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value critico">{{ status.alertas.por_severidade.get('CRITICA', 0) }}</div>
                        <div class="stat-label">Críticos</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value alerta">{{ status.alertas.por_severidade.get('ALTA', 0) }}</div>
                        <div class="stat-label">Altos</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value info">{{ status.alertas.por_severidade.get('MEDIA', 0) }}</div>
                        <div class="stat-label">Médios</div>
                    </div>
                </div>
            </div>
            
            <div class="footer">
                <p>🔄 Dashboard atualiza automaticamente a cada 15 segundos</p>
                <p>💻 Desenvolvido para VS Code + PowerShell | ⏹️ Para parar: Ctrl+C no terminal</p>
                <p>📊 Último ciclo MPI: {{ status.dados.ultimo_ciclo or 'Aguardando...' }}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(html_template, status=status, alertas_recentes=alertas_recentes)

@app.route('/api/status')
def api_status():
    """API para obter status da plataforma"""
    return jsonify(platform.gerar_relatorio_status())

@app.route('/api/alertas')
def api_alertas():
    """API para obter alertas"""
    limite = request.args.get('limite', 20, type=int)
    alertas = platform.listar_alertas_recentes(limite)
    return jsonify({'alertas': alertas, 'total': len(alertas)})

@app.route('/api/sensores')
def api_sensores():
    """API para obter informações dos sensores"""
    return jsonify({
        'sensores': platform.sensores_registrados,
        'total': len(platform.sensores_registrados)
    })

@app.route('/health')
def health_check():
    """Health check para monitoramento"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'uptime_seconds': (datetime.now() - platform.estatisticas['uptime_inicio']).total_seconds()
    })

def main():
    """Função principal do servidor"""
    print("🌐 Iniciando Plataforma InterSCity...")
    print(f"📊 Dashboard: http://localhost:{INTERSITY_CONFIG['port']}")
    print(f"🔌 API: http://localhost:{INTERSITY_CONFIG['port']}/api/")
    print("⏹️  Para parar: Ctrl+C")
    print("-" * 60)
    
    try:
        app.run(
            host=INTERSITY_CONFIG['host'], 
            port=INTERSITY_CONFIG['port'], 
            debug=False,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\n🛑 Servidor InterSCity finalizado")
    finally:
        platform.finalizar()

if __name__ == '__main__':
    main()