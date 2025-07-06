# Sistema de Monitoramento Inteligente de Esgotamento Sanitário

Este projeto implementa um sistema distribuído de monitoramento para esgotamento sanitário, utilizando conceitos de sistemas distribuídos com MPI e integração com AnyLogic para modelagem de fluxos urbanos.

## 🎯 Objetivos

- Monitoramento em tempo real de sensores de esgotamento sanitário
- Processamento distribuído de dados usando MPI
- Integração com simulações AnyLogic
- Dashboard interativo para visualização
- Detecção automática de anomalias

## 🏗️ Arquitetura do Sistema

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    AnyLogic     │───▶│  CSV Processor  │───▶│   MPI Master    │
│   Simulation    │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                       ┌─────────────────┐            ▼
                       │    Dashboard    │    ┌─────────────────┐
                       │   Visualization │◀───│  MPI Workers    │
                       └─────────────────┘    │  (Distributed)  │
                                              └─────────────────┘
```

## 📁 Estrutura do Projeto

```
sistema-monitoramento-esgoto/
├── src/
│   ├── mpi/                      # Módulos MPI
│   │   ├── master_node.py        # Nó coordenador
│   │   └── worker_node.py        # Nós de processamento
│   ├── data_processing/          # Processamento de dados
│   │   ├── csv_processor.py      # Processador CSV
│   │   └── data_analyzer.py      # Análise de dados
│   ├── anylogic_integration/     # Integração AnyLogic
│   │   └── anylogic_connector.py # Conector para AnyLogic
│   ├── visualization/            # Visualização
│   │   └── dashboard.py          # Dashboard web
│   └── main.py                   # Arquivo principal
├── data/
│   ├── csv/                      # Dados CSV do AnyLogic
│   └── processed/                # Dados processados
├── config/
│   └── config.json               # Configurações do sistema
├── docs/                         # Documentação
├── tests/                        # Testes
├── scripts/                      # Scripts auxiliares
└── requirements.txt              # Dependências Python
```

## 🚀 Instalação e Configuração

### Pré-requisitos

- Python 3.8+
- MPI (Microsoft MPI ou OpenMPI)
- Git

### 1. Clonar o Repositório

```powershell
# No PowerShell do VS Code
git clone https://github.com/seu-usuario/sistema-monitoramento-esgoto.git
cd sistema-monitoramento-esgoto
```

### 2. Criar Ambiente Virtual

```powershell
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
.\venv\Scripts\Activate.ps1

# Se houver erro de execução, execute:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. Instalar Dependências

```powershell
# Instalar dependências Python
pip install -r requirements.txt

# Instalar MPI4PY (pode precisar do Microsoft MPI instalado)
pip install mpi4py
```

### 4. Configurar MPI no Windows

1. Baixe e instale o Microsoft MPI:
   - [MS-MPI v10.1.2](https://www.microsoft.com/en-us/download/details.aspx?id=100593)
   - Instale tanto o Runtime quanto o SDK

2. Verifique a instalação:
```powershell
mpiexec --version
```

### 5. Configurar Diretórios

```powershell
# Criar estrutura de diretórios
python src/main.py --create-sample
```

## 🔧 Configuração

Edite o arquivo `config/config.json` para ajustar:

- Caminhos dos arquivos CSV do AnyLogic
- Número de processos MPI
- Thresholds de alertas
- Configurações do dashboard

## 🎮 Como Usar

### Modo Standalone (Recomendado para desenvolvimento)

```powershell
# Executar sistema completo
python src/main.py --mode standalone

# Criar dados de exemplo
python src/main.py --create-sample

# Verificar status
python src/main.py --status
```

### Modo Distribuído (MPI)

```powershell
# Executar com 4 processos
mpiexec -n 4 python src/main.py --mode mpi
```

### Apenas Dashboard

```powershell
# Executar apenas o dashboard
python src/main.py --mode dashboard
```

### Apenas Conector AnyLogic

```powershell
# Executar apenas o monitoramento de arquivos
python src/main.py --mode connector
```

## 🔗 Integração com GitHub

### Configurar Repositório

```powershell
# Adicionar arquivos ao git
git add .

# Fazer commit inicial
git commit -m "feat: implementação inicial do sistema de monitoramento"

# Criar repositório no GitHub e adicionar origin
git remote add origin https://github.com/seu-usuario/sistema-monitoramento-esgoto.git

# Enviar para GitHub
git push -u origin main
```

### Workflow de Desenvolvimento

```powershell
# Criar nova branch para funcionalidade
git checkout -b feature/nova-funcionalidade

# Fazer mudanças e commit
git add .
git commit -m "feat: adicionar nova funcionalidade"

# Push da branch
git push origin feature/nova-funcionalidade

# Criar Pull Request no GitHub
```

## 📊 Integração com AnyLogic

### 1. Configurar Exportação no AnyLogic

No seu modelo AnyLogic, configure a exportação CSV com as seguintes colunas:

```csv
timestamp,sensor_id,flow_rate,pressure,temperature,ph_level,turbidity,location_x,location_y
```

### 2. Configurar Caminho de Exportação

1. No AnyLogic, configure a exportação para: `data/csv/anylogic_export.csv`
2. Ou ajuste o caminho em `config/config.json`

### 3. Exemplo de Código AnyLogic

```java
// No AnyLogic, para exportar dados
String csvLine = String.format("%s,%s,%.2f,%.2f,%.2f,%.2f,%.2f,%.6f,%.6f",
    getCurrentTime(),
    sensor.getId(),
    sensor.getFlowRate(),
    sensor.getPressure(),
    sensor.getTemperature(),
    sensor.getPH(),
    sensor.getTurbidity(),
    sensor.getLocationX(),
    sensor.getLocationY()
);

// Adicionar ao arquivo CSV
exportToCSV(csvLine);
```

## 🎯 Funcionalidades Principais

### Processamento Distribuído
- Coordenação via MPI Master/Worker
- Processamento paralelo de grandes volumes de dados
- Balanceamento automático de carga

### Monitoramento em Tempo Real
- Detecção automática de novos arquivos CSV
- Processamento incremental
- Alertas em tempo real

### Dashboard Interativo
- Visualização em tempo real
- Mapas de sensores
- Gráficos de séries temporais
- Lista de alertas ativos

### Detecção de Anomalias
- Métodos estatísticos (IQR, Z-score)
- Thresholds configuráveis
- Classificação por severidade

## 🐛 Solução de Problemas

### Erro de MPI

```powershell
# Se mpiexec não for reconhecido
$env:PATH += ";C:\Program Files\Microsoft MPI\Bin"

# Ou reinstale o Microsoft MPI
```

### Erro de Permissão no PowerShell

```powershell
# Alterar política de execução
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Dashboard não Carrega

1. Verifique se há dados processados em `data/processed/`
2. Execute: `python src/main.py --create-sample`
3. Verifique logs em `logs/`

## 📈 Monitoramento e Logs

### Visualizar Logs

```powershell
# Logs do sistema
Get-Content logs/system_*.log -Tail 50

# Logs em tempo real
Get-Content logs/system_*.log -Wait
```

### Dashboard

Acesse: `http://localhost:8050`

- **Cards superiores**: Estatísticas em tempo real
- **Controles**: Filtros por sensor e período
- **Gráficos**: Vazão vs Pressão, Temperatura vs pH
- **Mapa**: Localização dos sensores
- **Alertas**: Lista de anomalias detectadas

## 🧪 Testes

```powershell
# Executar testes
python -m pytest tests/

# Testes com cobertura
python -m pytest tests/ --cov=src

# Teste específico
python -m pytest tests/test_csv_processor.py
```

## 📚 Documentação Adicional

- [Configuração MPI](docs/mpi-setup.md)
- [Integração AnyLogic](docs/anylogic-integration.md)
- [API do Dashboard](docs/dashboard-api.md)
- [Guia de Desenvolvimento](docs/development-guide.md)

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'feat: adicionar funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.

## 📞 Suporte

- **Issues**: [GitHub Issues](https://github.com/seu-usuario/sistema-monitoramento-esgoto/issues)
- **Email**: seu-email@exemplo.com
- **Documentação**: [Wiki do Projeto](https://github.com/seu-usuario/sistema-monitoramento-esgoto/wiki)

## 🔄 Próximas Versões

- [ ] Integração com banco de dados
- [ ] API REST para integração externa
- [ ] Alertas por email/SMS
- [ ] Machine Learning para predição
- [ ] Interface mobile
- [ ] Relatórios automatizados

---

**Desenvolvido para monitoramento inteligente de sistemas de esgotamento sanitário** 🚰