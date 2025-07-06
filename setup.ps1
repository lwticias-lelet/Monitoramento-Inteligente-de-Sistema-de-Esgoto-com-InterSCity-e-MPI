# Setup Script para Sistema de Monitoramento de Esgotamento Sanitário
# Execute com: .\setup.ps1

Write-Host "=== Sistema de Monitoramento de Esgotamento Sanitário ===" -ForegroundColor Green
Write-Host "Iniciando configuração do ambiente..." -ForegroundColor Yellow

# Verificar se Python está instalado
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python não encontrado. Instale o Python 3.8+ antes de continuar." -ForegroundColor Red
    exit 1
}

# Verificar se Git está instalado
try {
    $gitVersion = git --version 2>&1
    Write-Host "✓ Git encontrado: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Git não encontrado. Instale o Git antes de continuar." -ForegroundColor Red
    exit 1
}

# Criar ambiente virtual
Write-Host "`nCriando ambiente virtual..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "✓ Ambiente virtual já existe" -ForegroundColor Green
} else {
    python -m venv venv
    Write-Host "✓ Ambiente virtual criado" -ForegroundColor Green
}

# Ativar ambiente virtual
Write-Host "Ativando ambiente virtual..." -ForegroundColor Yellow
try {
    & .\venv\Scripts\Activate.ps1
    Write-Host "✓ Ambiente virtual ativado" -ForegroundColor Green
} catch {
    Write-Host "Erro ao ativar ambiente virtual. Configurando política de execução..." -ForegroundColor Yellow
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
    & .\venv\Scripts\Activate.ps1
    Write-Host "✓ Ambiente virtual ativado" -ForegroundColor Green
}

# Atualizar pip
Write-Host "Atualizando pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Instalar dependências
Write-Host "Instalando dependências..." -ForegroundColor Yellow
pip install -r requirements.txt

# Verificar se MPI está disponível
Write-Host "`nVerificando MPI..." -ForegroundColor Yellow
try {
    $mpiVersion = mpiexec --version 2>&1
    Write-Host "✓ MPI encontrado: $mpiVersion" -ForegroundColor Green
} catch {
    Write-Host "⚠ MPI não encontrado. Funcionalidades distribuídas não estarão disponíveis." -ForegroundColor Yellow
    Write-Host "Para instalar MPI no Windows:" -ForegroundColor Cyan
    Write-Host "1. Baixe Microsoft MPI v10.1.2 (Runtime + SDK)" -ForegroundColor Cyan
    Write-Host "2. URL: https://www.microsoft.com/en-us/download/details.aspx?id=100593" -ForegroundColor Cyan
}

# Criar diretórios necessários
Write-Host "`nCriando estrutura de diretórios..." -ForegroundColor Yellow

$directories = @(
    "data\csv",
    "data\processed",
    "data\notifications",
    "logs",
    "tests",
    "docs"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "✓ Criado: $dir" -ForegroundColor Green
    } else {
        Write-Host "✓ Já existe: $dir" -ForegroundColor Green
    }
}

# Criar dados de exemplo
Write-Host "`nCriando dados de exemplo..." -ForegroundColor Yellow
python src\main.py --create-sample

# Verificar status do sistema
Write-Host "`nVerificando status do sistema..." -ForegroundColor Yellow
python src\main.py --status

# Inicializar repositório Git se necessário
if (!(Test-Path ".git")) {
    Write-Host "`nInicializando repositório Git..." -ForegroundColor Yellow
    git init
    
    # Configurar arquivo .gitignore se não existir
    if (!(Test-Path ".gitignore")) {
        Write-Host "Criando .gitignore..." -ForegroundColor Yellow
        # O conteúdo do .gitignore já foi criado no artifact anterior
    }
    
    Write-Host "✓ Repositório Git inicializado" -ForegroundColor Green
    Write-Host "Para conectar ao GitHub:" -ForegroundColor Cyan
    Write-Host "1. Crie um repositório no GitHub" -ForegroundColor Cyan
    Write-Host "2. Execute: git remote add origin https://github.com/seu-usuario/repo.git" -ForegroundColor Cyan
    Write-Host "3. Execute: git add . && git commit -m 'Initial commit' && git push -u origin main" -ForegroundColor Cyan
}

Write-Host "`n=== Configuração Concluída! ===" -ForegroundColor Green
Write-Host "`nPara iniciar o sistema:" -ForegroundColor Cyan
Write-Host "• Modo completo:    python src\main.py --mode standalone" -ForegroundColor White
Write-Host "• Apenas dashboard: python src\main.py --mode dashboard" -ForegroundColor White
Write-Host "• Com MPI:          mpiexec -n 4 python src\main.py --mode mpi" -ForegroundColor White
Write-Host "`nDashboard estará disponível em: http://localhost:8050" -ForegroundColor Cyan

Write-Host "`nPressione qualquer tecla para continuar..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")