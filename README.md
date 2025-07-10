# 🚰 Sistema de Monitoramento Inteligente de Esgotamento Sanitário

Sistema distribuído para monitoramento em tempo real de redes de esgotamento sanitário utilizando **MPI**, **InterSCity** e **dashboard web interativo**. Desenvolvido para a disciplina de Sistemas Distribuídos da UFMA.

## 👥 Equipe

- **Kaline Maria Carvalho**
- **Letícia Delfino de Araújo** (Gerente do Projeto)
- **Hissa Bárbara Oliveira**

**Professor:** Luiz Henrique Neves Rodrigues  
**Instituição:** Universidade Federal do Maranhão (UFMA)  
**Curso:** Bacharelado Interdisciplinar em Ciência e Tecnologia  
**Disciplina:** Sistemas Distribuídos

## 📋 Índice

- [Sobre o Projeto](#-sobre-o-projeto)
- [Características](#-características)
- [Arquitetura](#-arquitetura)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Como Usar](#-como-usar)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Tecnologias](#-tecnologias)
- [Relatórios de Progresso](#-relatórios-de-progresso)
- [Contribuição](#-contribuição)

## 🎯 Sobre o Projeto

O projeto simula um sistema de monitoramento inteligente para o esgotamento sanitário de São Luís - MA, utilizando conceitos de **sistemas distribuídos** e **cidades inteligentes**. O sistema coleta dados de sensores IoT simulados em pontos críticos da rede de esgoto e processa essas informações de forma distribuída usando **MPI (Message Passing Interface)**.

### Objetivos

**Objetivo Geral:**
Desenvolver uma simulação de monitoramento inteligente do sistema de esgoto de São Luís utilizando a plataforma InterSCity e processamento distribuído com MPI em C.

**Objetivos Específicos:**
- ✅ Instalar e configurar a plataforma InterSCity
- ✅ Simular sensores de monitoramento (nível de água, vazamento, gases, pressão)
- ✅ Implementar comunicação distribuída com MPI
- ✅ Detectar anomalias e gerar alertas
- ✅ Avaliar eficiência da arquitetura distribuída

## 🌟 Características

### 🔍 Monitoramento Inteligente
- **Sensores Simulados**: Nível de água, pressão, temperatura, pH, turbidez
- **Detecção de Anomalias**: Algoritmos estatísticos para identificar padrões anômalos
- **Processamento Distribuído**: Suporte MPI para processamento paralelo
- **Alertas em Tempo Real**: Sistema de notificações para condições críticas

### 📊 Visualização Avançada
- **Dashboard Interativo**: Interface web responsiva com Plotly/Dash
- **Mapas Georreferenciados**: Visualização espacial dos sensores em São Luís
- **Gráficos Temporais**: Análise de tendências e padrões
- **Relatórios Automatizados**: Estatísticas e resumos executivos

### 🔗 Integrações
- **InterSCity**: Plataforma de cidades inteligentes
- **AnyLogic**: Conector para simulações hidráulicas (alternativa desenvolvida)
- **Node-RED**: API REST e MQTT para automação
- **CSV/Excel**: Importação e exportação de dados

### 📡 Parâmetros Monitorados
- **Vazão** (L/s)
- **Pressão** (bar)
- **Temperatura** (°C)
- **pH** (escala 0-14)
- **Turbidez** (NTU)
- **DQO** (Demanda Química de Oxigênio)
- **OD** (Oxigênio Dissolvido)
- **Coliformes e E.coli**
- **H₂S e Amônia**

## 🏗️ Arquitetura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Sensores IoT  │───▶│  Processamento  │───▶│   Dashboard     │
│   (Simulados)   │    │   Distribuído   │    │   Web (Dash)    │
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
│   InterSCity    │    │   Alertas &     │    │   API REST      │
│   Integration   │    │   Notificações  │    │   & MQTT        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📅 Cronograma

O projeto foi executado de acordo com o seguinte cronograma:

| Etapa | Período | Status | Descrição |
|-------|---------|--------|-----------|
| 1. Levantamento de requisitos | 19/05 - 26/05/2025 | ✅ Concluído | Reunião inicial e análise do escopo |
| 2. Instalação e configuração | 27/05 - 06/06/2025 | ✅ Concluído | Setup InterSCity, Docker, MPI |
| 3. Simulação de sensores | 07/06 - 14/07/2025 | ✅ Concluído | Implementação dos sensores IoT |
| 4. Desenvolvimento MPI | 01/07 - 02/07/2025 | ✅ Concluído | Comunicação distribuída |
| 5. Testes e alertas | 03/07 - 07/07/2025 | ✅ Concluído | Validação e detecção de anomalias |
| 6. Relatório final | 05/07 - 21/07/2025 | ✅ Concluído | Documentação e apresentação |
| 7. Apresentação | 07/07 - 09/07/2025 | ✅ Concluído | Demonstração do sistema |

**Progresso Atual:** 100% - Projeto concluído com sucesso! 🎉

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

# 3. Configure os dados (se disponível)
Copy-Item "caminho\para\monitoramento.csv" "data\csv\monitoramento.csv"
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
   sensorId,tempo_min,latitude,longitude,vazao,status,pH,DQO,OD,turbidez,temperatura,coliformes,ecoli,H2S,amonia,qualidade
   SENSOR_001,0.0,-2.5227,-44.2549,45.2,NORMAL,7.1,120.5,8.2,15.0,22.5,1000,100,0.1,0.05,BOA
   ```

3. **Para adaptar dados**, use o adaptador:
   ```bash
   python scripts/adapt_monitoramento.py
   ```

## 🎯 Como Usar

### Modo Completo (Recomendado)

```bash
# Ativar ambiente virtual
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate     # Linux/Mac

# Executar dashboard completo
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

#### 5. Integração com InterSCity
```bash
python interscity_adapter.py
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
├── 📄 interscity_adapter.py     # Adaptador InterSCity
├── 📄 nodered_flows.json        # Fluxos Node-RED
│
├── 📂 config/
│   └── 📄 config.json           # Configurações principais
│
├── 📂 data/
│   ├── 📂 csv/                  # Dados de entrada
│   │   └── 📄 monitoramento.csv # Dataset principal
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
│   │   ├── 📄 worker_node.py   # Nós worker MPI
│   │   └── 📄 processador_mpi.py # Processador MPI
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
├── 📂 logs/                    # Arquivos de log
├── 📂 docs/                    # Documentação adicional
└── 📂 tests/                   # Testes unitários
```

## 💻 Tecnologias

### Backend
- **Python 3.8+** - Linguagem principal
- **MPI4Py** - Processamento distribuído
- **Pandas/NumPy** - Manipulação de dados
- **Flask** - API REST

### Frontend/Visualização
- **Dash/Plotly** - Dashboard interativo
- **Bootstrap** - Interface responsiva
- **Plotly.js** - Gráficos interativos

### Integração
- **InterSCity** - Plataforma de cidades inteligentes
- **Node-RED** - Automação e integração
- **MQTT** - Messaging protocol
- **Docker** - Containerização (InterSCity)

### Processamento Distribuído
- **OpenMPI/Microsoft MPI** - Message Passing Interface
- **Scikit-learn** - Detecção de anomalias
- **Watchdog** - Monitoramento de arquivos

**Métricas do Projeto:**

- **📁 Arquivos de Código**: 35+ arquivos Python/JavaScript
- **📊 Linhas de Código**: ~3.000 LOC
- **🧪 Funcionalidades**: 15+ recursos implementados
- **📈 Cobertura de Testes**: Validação manual completa
- **⚡ Performance**: Processamento distribuído eficiente

### Evolução do Progresso

| Data | Progresso | Módulos Concluídos | Próximos Passos |
|------|-----------|-------------------|-----------------|
| 28/05/2025 | 42% | 3/7 | Instalação e configuração |
| 01/06/2025 | 66% | 4/7 | Desenvolvimento MPI |
| 02/07/2025 | 100% | 7/7 | Testes e apresentação |

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
python scripts/adapt_monitoramento.py
```

#### 4. Script de Resolução Automática

```powershell
# Windows: Execute para resolver problemas comuns
.\scripts\monitoramento.ps1
```

## 🤝 Contribuição

### Para Desenvolvimento

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

## 📞 Suporte e Contato

### Equipe de Desenvolvimento

- **Letícia Delfino de Araújo** (Gerente) - [ld.araujo@discente.com]
- **Kaline Maria Carvalho** - [carvalho.kaline@discente.ufma.br]
- **Hissa Bárbara Oliveira** - [hissa.barbara@discente.ufma.br]

### Professor Orientador
- **Luiz Henrique Neves Rodrigues** - UFMA

## 📜 Licença

Este projeto foi desenvolvido para fins acadêmicos na disciplina de Sistemas Distribuídos da UFMA. 

## 🙏 Agradecimentos

- **Prof. Luiz Henrique Neves Rodrigues** - Orientação e suporte técnico
- **UFMA/CECET** - Infraestrutura e recursos
- **Equipe InterSCity** - Plataforma de cidades inteligentes
- **Comunidade Open Source** - Bibliotecas e ferramentas utilizadas

---

## 🏆 Resultados e Conquistas

**✅ Projeto Concluído com Sucesso!**

- 🎯 **Todos os objetivos alcançados** conforme cronograma
- 📊 **Sistema funcional** com processamento distribuído
- 🌐 **Dashboard interativo** operacional
- 🔗 **Integrações completas** (InterSCity, Node-RED, MQTT)
- 📈 **Detecção de anomalias** implementada
- 🚨 **Sistema de alertas** funcionando
- 📋 **Documentação completa** e detalhada

**🚰 Sistema de Monitoramento de Esgotamento Sanitário**  
*Monitoramento inteligente para infraestrutura crítica urbana*

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Dash](https://img.shields.io/badge/Dash-2.13+-green.svg)](https://dash.plotly.com)
[![MPI](https://img.shields.io/badge/MPI-Compatible-orange.svg)](https://mpi4py.readthedocs.io)
[![InterSCity](https://img.shields.io/badge/InterSCity-Integrated-purple.svg)](https://interscity.org)
[![Status](https://img.shields.io/badge/Status-Completed-success.svg)](/)

**Desenvolvido com ❤️ pela equipe de Sistemas Distribuídos - UFMA 2025**
