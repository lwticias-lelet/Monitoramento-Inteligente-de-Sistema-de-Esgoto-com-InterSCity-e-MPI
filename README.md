# 🚰 Sistema de Monitoramento de Esgotamento Sanitário

Sistema inteligente para monitoramento em tempo real de redes de esgotamento sanitário com processamento distribuído, detecção de anomalias e dashboard interativo.

## 📋 Índice

- [Características](#-características)
- [Arquitetura](#-arquitetura)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Uso](#-uso)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [API e Integrações](#-api-e-integrações)
- [Dashboard](#-dashboard)
- [Desenvolvimento](#-desenvolvimento)
- [Troubleshooting](#-troubleshooting)

## 🌟 Características

### 🔍 Monitoramento Inteligente
- **Detecção de Anomalias**: Algoritmos estatísticos para identificar padrões anômalos
- **Processamento Distribuído**: Suporte MPI para processamento paralelo
- **Tempo Real**: Monitoramento contínuo com atualizações automáticas
- **Alertas Automáticos**: Sistema de notificações para condições críticas

### 📊 Visualização Avançada
- **Dashboard Interativo**: Interface web responsiva com Plotly/Dash
- **Mapas Georreferenciados**: Visualização espacial dos sensores
- **Gráficos Temporais**: Análise de tendências e padrões
- **Relatórios Automatizados**: Estatísticas e resumos executivos

### 🔗 Integrações
- **AnyLogic**: Conector para simulações hidráulicas
- **Node-RED**: API REST e MQTT para automação
- **CSV/Excel**: Importação e exportação de dados
- **Notificações**: Email, SMS, Slack, Telegram

### 📡 Parâmetros Monitorados
- **Vazão** (L/s)
- **Pressão** (bar)
- **Temperatura** (°C)
- **pH**
- **Turbidez** (NTU)
- **DQO, OD, Coliformes, E.coli**
- **H₂S, Amônia**

## 🏗️ Arquitetura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AnyLogic      │───▶│  Processamento  │───▶│   Dashboard     │
│   Simulator     │    │   Distribuído   │    │   Web (Dash)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CSV Files     │    │   MPI Workers   │    │   Visualização  │
│   Data Input    │    │   Anomaly Det.  │    │   Tempo Real    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Node-RED      │    │   Alertas &     │    │   API REST      │
│   Integration   │    │   Notificações  │    │   & MQTT        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Instalação

### Pré-requisitos

- **Python 3.8+**
- **Node.js 16+** (para Node-RED)
- **Git**
- **Microsoft MPI** (Windows) ou **OpenMPI** (Linux/Mac)

### Instalação Rápida

#### Windows (PowerShell como Administrador)

```powershell
# 1. Clone o repositório
git clone https://github.com/seu-usuario/sistema-monitoramento-esgoto.git
cd sistema-monitoramento-esgoto

# 2. Execute o setup automatizado
.\scripts\setup.ps1

# 3. Configure os dados (opcional)
Copy-Item "C:\caminho\para\seus\dados\monitoramento.csv" "data\csv\monitoramento.csv"
```

#### Linux/Mac

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/sistema-monitoramento-esgoto.git
cd sistema-monitoramento-esgoto

# 2. Crie ambiente virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instale dependências
pip install -r requirements.txt

# 4. Configure diretórios
mkdir -p data/{csv,processed,notifications} logs
```

### Instalação Manual das Dependências

```bash
# Dependências Python principais
pip install mpi4py pandas numpy plotly dash scikit-learn flask paho-mqtt

# Para desenvolvimento
pip install pytest black flake8

# Node-RED (opcional)
npm install -g node-red
```

## ⚙️ Configuração

### Arquivo de Configuração Principal

Edite `config/config.json`:

```json
{
  "system": {
    "name": "Sistema de Monitoramento de Esgotamento Sanitário",
    "version": "1.0.0",
    "debug": true
  },
  "mpi": {
    "num_processes": 4,
    "master_rank": 0
  },
  "data": {
    "csv_input_path": "data/csv/",
    "processed_output_path": "data/processed/",
    "batch_size": 1000,
    "update_interval": 60
  },
  "monitoring": {
    "alert_thresholds": {
      "flow_rate_max": 100.0,
      "pressure_max": 5.0,
      "temperature_max": 35.0,
      "ph_min": 6.0,
      "ph_max": 8.5,
      "turbidity_max": 50.0
    }
  },
  "visualization": {
    "dashboard_port": 8050,
    "update_interval": 5000
  }
}
```

### Configuração de Dados

1. **Coloque seus arquivos CSV** em `data/csv/`
2. **Estrutura esperada**:
   ```csv
   timestamp,sensor_id,flow_rate,pressure,temperature,ph_level,turbidity,location_x,location_y
   2024-01-01 10:00:00,SENSOR_001,45.2,2.3,22.5,7.1,15.0,-44.2549,-2.5227
   ```

3. **Para dados no formato diferente**, use o adaptador:
   ```bash
   python scripts/adapt_monitoramento.py
   ```

## 🎯 Uso

### Modo Completo (Recomendado)

```bash
# Ativar ambiente virtual
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate     # Linux/Mac

# Executar sistema completo
python run_dashboard.py
```

**Acesse**: http://localhost:8050

### Modos Específicos

#### 1. Apenas Dashboard
```bash
python run_dashboard.py
```

#### 2. Processamento Distribuído (MPI)
```bash
mpiexec -n 4 python src/main.py --mode mpi
```

#### 3. Modo Standalone (sem MPI)
```bash
python scripts/main_simple.py --mode both
```

#### 4. Processar arquivo específico
```bash
python scripts/main_simple.py --mode process --file "data/csv/monitoramento.csv"
```

### Integração com Node-RED

```bash
# 1. Iniciar integrações
python src/integration/nodered_integration.py

# 2. Em outra janela, iniciar Node-RED
node-red

# 3. Acessar Node-RED: http://localhost:1880
# 4. Importar fluxo: nodered_flows.json
```

## 📁 Estrutura do Projeto

```
sistema-monitoramento-esgoto/
├── 📄 README.md
├── 📄 requirements.txt
├── 📄 run_dashboard.py          # Dashboard principal
├── 📄 nodered_flows.json        # Fluxos Node-RED
│
├── 📂 config/
│   └── 📄 config.json           # Configurações principais
│
├── 📂 data/
│   ├── 📂 csv/                  # Dados de entrada
│   ├── 📂 processed/            # Dados processados
│   └── 📂 notifications/        # Alertas e notificações
│
├── 📂 scripts/
│   ├── 📄 setup.ps1            # Setup Windows
│   ├── 📄 main_simple.py       # Versão simplificada
│   ├── 📄 adapt_monitoramento.py # Adaptador CSV
│   └── 📄 monitoramento.ps1    # Script resolução problemas
│
├── 📂 src/
│   ├── 📂 api/
│   │   ├── 📄 nodered_api.py   # API REST para Node-RED
│   │   └── 📄 mqtt_publisher.py # Publisher MQTT
│   │
│   ├── 📂 data_processing/
│   │   └── 📄 csv_processor.py # Processador principal
│   │
│   ├── 📂 mpi/
│   │   ├── 📄 master_node.py   # Nó master MPI
│   │   └── 📄 worker_node.py   # Nós worker MPI
│   │
│   ├── 📂 anylogic_integration/
│   │   └── 📄 anylogic_connector.py # Conector AnyLogic
│   │
│   ├── 📂 visualization/
│   │   └── 📄 dashboard.py     # Dashboard Dash/Plotly
│   │
│   ├── 📂 integration/
│   │   └── 📄 nodered_integration.py # Integração completa
│   │
│   └── 📄 main.py              # Sistema principal
│
└── 📂 logs/                    # Arquivos de log
```

## 🔌 API e Integrações

### API REST Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/api/health` | Status do sistema |
| `GET` | `/api/sensors` | Lista de sensores |
| `GET` | `/api/sensor/{id}/latest` | Dados mais recentes do sensor |
| `GET` | `/api/sensor/{id}/history` | Histórico do sensor |
| `GET` | `/api/alerts` | Alertas ativos |
| `GET` | `/api/statistics` | Estatísticas gerais |
| `POST` | `/api/data/process` | Processar novos dados |

### Tópicos MQTT

| Tópico | Descrição |
|--------|-----------|
| `esgoto/sensores/{sensor_id}` | Dados dos sensores |
| `esgoto/alertas` | Alertas do sistema |
| `esgoto/estatisticas` | Estatísticas gerais |
| `esgoto/health` | Status do sistema |

### Exemplo de Uso da API

```python
import requests

# Verificar status
response = requests.get('http://localhost:5000/api/health')
print(response.json())

# Obter dados de sensor
response = requests.get('http://localhost:5000/api/sensor/SENSOR_001/latest')
data = response.json()
```

## 📊 Dashboard

### Funcionalidades Principais

- **📈 Gráficos Interativos**: Plotly.js com zoom, pan, seleção
- **🗺️ Mapa Georreferenciado**: Localização dos sensores em tempo real
- **⚡ Atualização Automática**: Dados atualizados a cada 30 segundos
- **🔍 Filtros Avançados**: Por sensor, período, status
- **🚨 Alertas Visuais**: Indicadores de anomalias em tempo real
- **📱 Responsivo**: Funciona em desktop, tablet e mobile

### Capturas de Tela

#### Dashboard Principal
```
┌─────────────────────────────────────────────────────────┐
│ 🚰 Sistema de Monitoramento de Esgotamento Sanitário   │
├─────────┬─────────┬─────────┬─────────────────────────┤
│ 📍 12   │ ⚠️ 3    │ 📊 1,245│ ⏰ 14:30:25            │
│Sensores │ Alertas │Registros│ Última Atualização      │
├─────────┴─────────┴─────────┴─────────────────────────┤
│ 🎛️ Filtros: [Sensor ▼] [Período ▼] [Status ▼]        │
├─────────────────────┬───────────────────────────────────┤
│ 📈 Vazão vs Pressão │ 🌡️ Temperatura e pH             │
│                     │                                   │
├─────────────────────┼───────────────────────────────────┤
│ 🗺️ Mapa Sensores    │ 🚨 Alertas Recentes              │
│                     │ • Sensor 003 - Alta Pressão      │
│                     │ • Sensor 007 - pH Anômalo        │
└─────────────────────┴───────────────────────────────────┘
```

## 💻 Desenvolvimento

### Configuração do Ambiente de Desenvolvimento

```bash
# Instalar dependências de desenvolvimento
pip install -e .
pip install pytest black flake8 pre-commit

# Configurar pre-commit hooks
pre-commit install

# Executar testes
pytest tests/ -v

# Formatação de código
black src/ scripts/
flake8 src/ scripts/
```

### Estrutura de Testes

```bash
pytest tests/test_csv_processor.py    # Testes do processador
pytest tests/test_dashboard.py        # Testes do dashboard
pytest tests/test_api.py              # Testes da API
pytest tests/ --cov=src              # Cobertura de testes
```

### Contribuindo

1. **Fork** o repositório
2. **Crie** uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. **Push** para a branch (`git push origin feature/AmazingFeature`)
5. **Abra** um Pull Request

## 🔧 Troubleshooting

### Problemas Comuns

#### 1. Erro: "Arquivo monitoramento.csv não encontrado"

```bash
# Solução: Verificar localização do arquivo
ls data/csv/
# Se não existir, copie seus dados para data/csv/
```

#### 2. Erro: "ModuleNotFoundError: No module named 'mpi4py'"

```bash
# Solução: Instalar MPI e mpi4py
# Windows: Baixar Microsoft MPI
# Linux: sudo apt-get install openmpi-bin libopenmpi-dev
pip install mpi4py
```

#### 3. Dashboard não carrega dados

```bash
# Verificar se há dados processados
ls data/processed/
# Se vazio, processar dados primeiro
python scripts/main_simple.py --mode process --file "data/csv/seu_arquivo.csv"
```

#### 4. Porta 8050 já em uso

```bash
# Matar processo na porta
# Windows:
netstat -ano | findstr :8050
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:8050 | xargs kill -9
```

#### 5. Problemas com Node-RED

```bash
# Reinstalar Node-RED
npm uninstall -g node-red
npm install -g node-red

# Verificar versão Node.js
node --version  # Deve ser 16+
```

### Script de Resolução Automática

```powershell
# Windows: Execute para resolver problemas comuns
.\scripts\monitoramento.ps1
```

### Logs e Debugging

```bash
# Verificar logs do sistema
tail -f logs/system_$(date +%Y%m%d).log

# Debug do dashboard
python run_dashboard.py --debug

# Testar API manualmente
curl http://localhost:5000/api/health
```

## 📞 Suporte

### Documentação Adicional

- **API Reference**: `/docs` (quando servidor rodando)
- **Node-RED Flows**: `nodered_flows.json`
- **Configurações**: `config/config.json`

### Contato

- **Email**: seu-email@dominio.com
- **Issues**: [GitHub Issues](https://github.com/seu-usuario/repo/issues)
- **Wiki**: [GitHub Wiki](https://github.com/seu-usuario/repo/wiki)

### Status do Projeto

- ✅ **Estável**: Processamento de dados CSV
- ✅ **Estável**: Dashboard web interativo
- ✅ **Estável**: Detecção de anomalias
- ✅ **Beta**: Integração Node-RED
- ⚠️ **Alpha**: Processamento MPI distribuído
- 🚧 **Em Desenvolvimento**: Notificações avançadas

---

## 📜 Licença

Este projeto está licenciado sob a **MIT License** - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🙏 Agradecimentos

- **Equipe AnyLogic** - Integração de simulação
- **Plotly/Dash** - Framework de visualização
- **Node-RED** - Plataforma de integração
- **MPI Community** - Processamento distribuído

---

**🚰 Sistema de Monitoramento de Esgotamento Sanitário**  
*Monitoramento inteligente para infraestrutura crítica*

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Dash](https://img.shields.io/badge/Dash-2.13+-green.svg)](https://dash.plotly.com)
[![MPI](https://img.shields.io/badge/MPI-Compatible-orange.svg)](https://mpi4py.readthedocs.io)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
