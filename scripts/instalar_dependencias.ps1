# ============================================================================
# Script de Instalação - Sistema de Monitoramento de Esgoto
# Instala e configura todas as dependências necessárias
# ============================================================================

param(
    [switch]$SkipMPI,
    [switch]$Help
)

function Show-Help {
    Write-Host "🔧 SCRIPT DE INSTALAÇÃO" -ForegroundColor Cyan
    Write-Host "=====================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "USO:" -ForegroundColor Yellow
    Write-Host "  .\instalar_dependencias.ps1 [OPÇÕES]"
    Write-Host ""
    Write-Host "OPÇÕES:" -ForegroundColor Yellow
    Write-Host "  -SkipMPI    Pula instalação do MPI (se já estiver instalado)"
    Write-Host "  -Help       Mostra esta ajuda"
    Write-Host ""
}

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    
    $timestamp = Get-Date -Format "HH:mm:ss"
    $color = switch ($Level) {
        "INFO" { "White" }
        "SUCCESS" { "Green" }
        "WARNING" { "Yellow" }
        "ERROR" { "Red" }
        default { "White" }
    }
    
    Write-Host "[$timestamp] $Message" -ForegroundColor $color
}

function Test-IsAdmin {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Install-Python {
    Write-Log "🐍 Verificando Python..." "INFO"
    
    try {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match "Python (\d+\.\d+)") {
            $version = [Version]$matches[1]
            if ($version -ge [Version]"3.8") {
                Write-Log "✅ Python $($matches[1]) já instalado" "SUCCESS"
                return $true
            } else {
                Write-Log "⚠️  Python $($matches[1]) muito antigo (necessário 3.8+)" "WARNING"
            }
        }
    } catch {
        Write-Log "❌ Python não encontrado" "WARNING"
    }
    
    Write-Log "📥 Baixando Python 3.11..." "INFO"
    Write-Log "   Acesse: https://www.python.org/downloads/" "WARNING"
    Write-Log "   Marque 'Add Python to PATH' durante a instalação!" "WARNING"
    
    return $false
}

function Install-MPI {
    if ($SkipMPI) {
        Write-Log "⏭️  Pulando instalação do MPI conforme solicitado" "WARNING"
        return $true
    }
    
    Write-Log "🔧 Verificando Microsoft MPI..." "INFO"
    
    try {
        $mpiVersion = mpiexec --version 2>&1
        if ($mpiVersion) {
            Write-Log "✅ MPI já instalado" "SUCCESS"
            return $true
        }
    } catch {
        Write-Log "❌ MPI não encontrado" "WARNING"
    }
    
    Write-Log "📥 Para instalar Microsoft MPI:" "INFO"
    Write-Log "   1. Acesse: https://docs.microsoft.com/en-us/message-passing-interface/microsoft-mpi" "WARNING"
    Write-Log "   2. Baixe: msmpisetup.exe e msmpisdk.msi" "WARNING"
    Write-Log "   3. Instale AMBOS na ordem" "WARNING"
    Write-Log "   4. Reinicie o PowerShell após instalação" "WARNING"
    
    return $false
}

function Install-PythonPackages {
    Write-Log "📦 Instalando bibliotecas Python..." "INFO"
    
    $packages = @(
        "mpi4py",
        "numpy",
        "pandas", 
        "matplotlib",
        "flask",
        "requests",
        "python-dotenv"
    )
    
    $failed = @()
    
    foreach ($package in $packages) {
        Write-Log "📦 Instalando $package..." "INFO"
        
        try {
            pip install $package --upgrade 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Log "✅ $package instalado" "SUCCESS"
            } else {
                Write-Log "❌ Falha ao instalar $package" "ERROR"
                $failed += $package
            }
        } catch {
            Write-Log "❌ Erro ao instalar $package" "ERROR"
            $failed += $package
        }
    }
    
    if ($failed.Count -eq 0) {
        Write-Log "✅ Todas as bibliotecas foram instaladas!" "SUCCESS"
        return $true
    } else {
        Write-Log "❌ Falha ao instalar: $($failed -join ', ')" "ERROR"
        return $false
    }
}

function Test-Installation {
    Write-Log "🧪 Testando instalação..." "INFO"
    
    $tests = @()
    
    # Teste Python
    try {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match "Python (\d+\.\d+)") {
            $tests += "✅ Python: $($matches[1])"
        } else {
            $tests += "❌ Python: Não detectado"
        }
    } catch {
        $tests += "❌ Python: Erro"
    }
    
    # Teste MPI
    try {
        mpiexec --version 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            $tests += "✅ MPI: Funcionando"
        } else {
            $tests += "❌ MPI: Não funciona"
        }
    } catch {
        $tests += "❌ MPI: Não instalado"
    }
    
    # Teste bibliotecas
    try {
        python -c "import mpi4py, numpy, pandas, flask; print('OK')" 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            $tests += "✅ Bibliotecas: Todas disponíveis"
        } else {
            $tests += "❌ Bibliotecas: Algumas faltando"
        }
    } catch {
        $tests += "❌ Bibliotecas: Erro de teste"
    }
    
    Write-Log "📋 RESULTADO DOS TESTES:" "INFO"
    foreach ($test in $tests) {
        Write-Log "   $test" "INFO"
    }
    
    $allPassed = $tests | Where-Object { $_ -like "❌*" }
    return ($allPassed.Count -eq 0)
}

function Create-ProjectStructure {
    Write-Log "📁 Criando estrutura do projeto..." "INFO"
    
    $baseDir = "C:\monitoramento_esgoto"
    $dirs = @(
        "$baseDir",
        "$baseDir\src",
        "$baseDir\config", 
        "$baseDir\data",
        "$baseDir\logs",
        "$baseDir\docs",
        "$baseDir\scripts",
        "$baseDir\.vscode",
        "C:\temp"
    )
    
    foreach ($dir in $dirs) {
        if (!(Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Log "📁 Criado: $dir" "SUCCESS"
        } else {
            Write-Log "📁 Existe: $dir" "INFO"
        }
    }
    
    Write-Log "✅ Estrutura do projeto criada em: $baseDir" "SUCCESS"
}

function Main {
    Write-Host ""
    Write-Host "============================================================================" -ForegroundColor Cyan
    Write-Host "🔧 INSTALADOR - SISTEMA DE MONITORAMENTO DE ESGOTO" -ForegroundColor Cyan
    Write-Host "============================================================================" -ForegroundColor Cyan
    Write-Host ""
    
    if ($Help) {
        Show-Help
        return
    }
    
    # Verificar se é admin (para algumas instalações)
    if (!(Test-IsAdmin)) {
        Write-Log "⚠️  Executando sem privilégios de administrador" "WARNING"
        Write-Log "   Algumas instalações podem falhar" "WARNING"
    }
    
    $allOk = $true
    
    # 1. Instalar/verificar Python
    if (!(Install-Python)) {
        $allOk = $false
    }
    
    # 2. Instalar/verificar MPI
    if (!(Install-MPI)) {
        $allOk = $false
    }
    
    # 3. Instalar bibliotecas Python
    if (!(Install-PythonPackages)) {
        $allOk = $false
    }
    
    # 4. Criar estrutura do projeto
    Create-ProjectStructure
    
    # 5. Testar instalação
    Write-Host ""
    if (Test-Installation) {
        Write-Log "🎉 INSTALAÇÃO CONCLUÍDA COM SUCESSO!" "SUCCESS"
        Write-Host ""
        Write-Host "PRÓXIMOS PASSOS:" -ForegroundColor Yellow
        Write-Host "1. Copie os arquivos Python para C:\monitoramento_esgoto\src\" -ForegroundColor White
        Write-Host "2. Execute: cd C:\monitoramento_esgoto" -ForegroundColor White
        Write-Host "3. Execute: python src\executar_sistema.py" -ForegroundColor White
        Write-Host ""
    } else {
        Write-Log "❌ Instalação com problemas" "ERROR"
        Write-Host ""
        Write-Host "RESOLVER PROBLEMAS:" -ForegroundColor Red
        Write-Host "1. Instale manualmente Python 3.8+ e MPI" -ForegroundColor White
        Write-Host "2. Reinicie o PowerShell" -ForegroundColor White
        Write-Host "3. Execute este script novamente" -ForegroundColor White
        Write-Host ""
    }
}

# Executar
Main