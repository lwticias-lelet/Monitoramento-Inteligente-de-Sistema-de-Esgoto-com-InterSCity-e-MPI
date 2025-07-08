#!/usr/bin/env python3
"""
Script de integração completa com Node-RED
Execute este script para iniciar todas as integrações
"""

import os
import sys
import time
import json
import threading
import subprocess
from pathlib import Path

def install_dependencies():
    """Instalar dependências necessárias"""
    print("🔧 Instalando dependências...")
    
    dependencies = [
        "flask",
        "paho-mqtt"
    ]
    
    for dep in dependencies:
        try:
            __import__(dep.replace('-', '_'))
            print(f"✓ {dep} já instalado")
        except ImportError:
            print(f"📦 Instalando {dep}...")
            subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)

def check_nodered():
    """Verificar se Node-RED está disponível"""
    try:
        result = subprocess.run(["node-red", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Node-RED encontrado: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ Node-RED não encontrado")
    print("📥 Para instalar Node-RED:")
    print("1. Instale Node.js: https://nodejs.org/")
    print("2. Execute: npm install -g node-red")
    return False

def start_api_server():
    """Iniciar servidor da API REST"""
    print("🚀 Iniciando API REST...")
    
    try:
        # Importar e executar API
        sys.path.append(str(Path(__file__).parent.parent))
        from api.nodered_api import NodeREDAPI
        
        api = NodeREDAPI()
        api.run(host='0.0.0.0', port=5000, debug=False)
        
    except Exception as e:
        print(f"❌ Erro ao iniciar API: {e}")

def start_mqtt_publisher():
    """Iniciar publicador MQTT"""
    print("📡 Iniciando publicador MQTT...")
    
    try:
        sys.path.append(str(Path(__file__).parent.parent))
        from api.mqtt_publisher import MQTTPublisher
        
        publisher = MQTTPublisher()
        publisher.run_continuous(interval=30)
        
    except Exception as e:
        print(f"❌ Erro ao iniciar MQTT: {e}")

def create_nodered_flow_file():
    """Criar arquivo de fluxo para importar no Node-RED"""
    flow_data = {
        "flows": [
            {
                "id": "main_flow",
                "type": "tab",
                "label": "Monitoramento Esgoto",
                "disabled": False,
                "info": "Sistema de monitoramento de esgotamento sanitário"
            },
            {
                "id": "http_health",
                "type": "http request",
                "z": "main_flow",
                "name": "API Health Check",
                "method": "GET",
                "ret": "obj",
                "url": "http://localhost:5000/api/health",
                "x": 300,
                "y": 100,
                "wires": [["debug_health"]]
            },
            {
                "id": "inject_health",
                "type": "inject",
                "z": "main_flow",
                "name": "Check Health",
                "repeat": "30",
                "crontab": "",
                "once": True,
                "x": 100,
                "y": 100,
                "wires": [["http_health"]]
            },
            {
                "id": "debug_health",
                "type": "debug",
                "z": "main_flow",
                "name": "Health Status",
                "active": True,
                "x": 500,
                "y": 100,
                "wires": []
            },
            {
                "id": "mqtt_sensors",
                "type": "mqtt in",
                "z": "main_flow",
                "name": "Sensor Data",
                "topic": "esgoto/sensores/+",
                "qos": "1",
                "broker": "mqtt_broker",
                "x": 100,
                "y": 200,
                "wires": [["process_sensor_mqtt"]]
            },
            {
                "id": "process_sensor_mqtt",
                "type": "function",
                "z": "main_flow",
                "name": "Process MQTT Sensor",
                "func": "try {\n    const data = JSON.parse(msg.payload);\n    \n    msg.sensor_id = data.sensor_id;\n    msg.data = data;\n    \n    if (data.is_anomaly) {\n        node.status({fill: 'red', shape: 'ring', text: `ALERTA - ${data.sensor_id}`});\n        msg.alert = true;\n    } else {\n        node.status({fill: 'green', shape: 'dot', text: `OK - ${data.sensor_id}`});\n        msg.alert = false;\n    }\n    \n    return msg;\n} catch (e) {\n    node.error(`Erro ao processar MQTT: ${e.message}`);\n    return null;\n}",
                "x": 300,
                "y": 200,
                "wires": [["debug_mqtt_data"]]
            },
            {
                "id": "debug_mqtt_data",
                "type": "debug",
                "z": "main_flow",
                "name": "MQTT Data",
                "active": True,
                "x": 500,
                "y": 200,
                "wires": []
            },
            {
                "id": "mqtt_broker",
                "type": "mqtt-broker",
                "name": "Local MQTT",
                "broker": "localhost",
                "port": "1883",
                "clientid": "",
                "usetls": False,
                "compatmode": False,
                "keepalive": "60",
                "cleansession": True,
                "birthTopic": "",
                "birthQos": "0",
                "birthPayload": "",
                "closeTopic": "",
                "closeQos": "0",
                "closePayload": "",
                "willTopic": "",
                "willQos": "0",
                "willPayload": ""
            }
        ]
    }
    
    flow_file = Path("nodered_flows.json")
    with open(flow_file, 'w', encoding='utf-8') as f:
        json.dump(flow_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Arquivo de fluxo criado: {flow_file}")
    print("📝 Para importar no Node-RED:")
    print("1. Acesse http://localhost:1880")
    print("2. Menu → Import → select a file to import")
    print(f"3. Selecione o arquivo: {flow_file}")

def print_instructions():
    """Imprimir instruções de uso"""
    print("\n" + "="*60)
    print("🔗 INTEGRAÇÃO COM NODE-RED")
    print("="*60)
    print("\n📋 PASSOS PARA INTEGRAÇÃO COMPLETA:")
    print("\n1. 🐍 SISTEMA PYTHON:")
    print("   ✓ API REST rodando em: http://localhost:5000")
    print("   ✓ MQTT publisher ativo")
    print("   ✓ Processamento de dados ativo")
    
    print("\n2. 🟢 NODE-RED:")
    print("   • Acesse: http://localhost:1880")
    print("   • Importe o arquivo: nodered_flows.json")
    print("   • Configure broker MQTT se necessário")
    
    print("\n3. 📡 ENDPOINTS DISPONÍVEIS:")
    print("   • GET  /api/health - Status do sistema")
    print("   • GET  /api/sensors - Lista de sensores")
    print("   • GET  /api/sensor/{id}/latest - Dados do sensor")
    print("   • GET  /api/alerts - Alertas ativos")
    print("   • POST /api/data/process - Processar dados")
    
    print("\n4. 📨 TÓPICOS MQTT:")
    print("   • esgoto/sensores/{sensor_id} - Dados dos sensores")
    print("   • esgoto/alertas - Alertas do sistema")
    print("   • esgoto/estatisticas - Estatísticas gerais")
    print("   • esgoto/health - Status do sistema")
    
    print("\n5. 🔧 EXEMPLOS DE USO NO NODE-RED:")
    print("   • HTTP Request nodes para consumir API")
    print("   • MQTT In nodes para receber dados")
    print("   • Function nodes para processar dados")
    print("   • Dashboard nodes para visualização")
    
    print("\n6. 🚨 NOTIFICAÇÕES:")
    print("   • Instale nodes para notificações:")
    print("   • npm install node-red-node-email")
    print("   • npm install node-red-contrib-telegram")
    print("   • npm install node-red-contrib-slack")
    
    print("\n" + "="*60)

def main():
    """Função principal"""
    print("🚀 INICIANDO INTEGRAÇÃO NODE-RED")
    print("="*50)
    
    # Verificar dependências
    install_dependencies()
    
    # Verificar Node-RED
    if not check_nodered():
        print("\n⚠️  Node-RED não encontrado. Instale antes de continuar.")
        return
    
    # Criar arquivo de fluxo
    create_nodered_flow_file()
    
    # Imprimir instruções
    print_instructions()
    
    print("\n🔄 Escolha o modo de execução:")
    print("1. API REST apenas")
    print("2. MQTT Publisher apenas") 
    print("3. Ambos (recomendado)")
    print("4. Apenas criar arquivos e sair")
    
    choice = input("\nEscolha (1-4): ").strip()
    
    if choice == "1":
        start_api_server()
    elif choice == "2":
        start_mqtt_publisher()
    elif choice == "3":
        # Executar ambos em threads
        api_thread = threading.Thread(target=start_api_server, daemon=True)
        mqtt_thread = threading.Thread(target=start_mqtt_publisher, daemon=True)
        
        api_thread.start()
        time.sleep(2)  # Aguardar API iniciar
        mqtt_thread.start()
        
        try:
            print("\n✅ Integração ativa!")
            print("🔗 API: http://localhost:5000")
            print("📡 MQTT: localhost:1883")
            print("\n⏹️  Pressione Ctrl+C para parar")
            
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n⏹️  Parando integração...")
    elif choice == "4":
        print("\n✅ Arquivos criados. Execute manualmente:")
        print("python src/api/nodered_api.py")
        print("python src/api/mqtt_publisher.py")
    else:
        print("❌ Opção inválida")

if __name__ == "__main__":
    main()