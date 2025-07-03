# ============================================================================
# Script PowerShell - Sistema de Monitoramento de Esgoto Urbano
# Execução completa automatizada para VS Code
# ============================================================================

param(
    [switch]$SemGerador,
    [switch]$SoInterSCity,
    [switch]$Teste,
    [switch]$Help
)

# Configurações
$PROJETO_DIR = "C:\monitoramento_esgoto"
$SRC_DIR = "$PROJETO_DIR\src"
$LOG_DIR = "$PROJETO_DIR\logs"

# Função para exibir ajuda
function Show-Help {
    Write-Host "🏗️  SISTEMA DE MONITORAMENTO DE ESGOTO URBANO" -ForegroundColor Cyan
    Write-Host "========================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "USO:" -ForegroundColor Yellow
    Write-Host "  .\executar_completo.ps1 [OPÇÕES]"
    Write-Host ""
    Write-Host "OPÇÕES:" -ForegroundColor Yellow
    Write-Host "  -SemGerador      Não inicia gerador de dados (usar AnyLogic)"
    Write-Host "  -SoInterSCity    Inicia apenas o servidor InterSCity"
    Write-Host "  -Teste           Executa apenas testes do sistema"
    Write-Host "  -Help            Mostra esta ajuda"
    Write-Host ""
    Write-Host "EXEMPLOS:" -ForegroundColor Green
    Write-Host "  .\executar_completo.ps1                    # Sistema completo"
    Write-Host "  .\executar_completo.ps1 -SemGerador        # Sem gerador (usar AnyLogic)"
    Write-Host "  .\executar_completo.ps1 -SoInterSCity      # Apenas InterSCity"
    Write-Host "  .\executar_completo.ps1 -Teste             # Apenas testes"
    Write-Host ""
}

# Função para log com timestamp
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

# Função para verificar pré-requisitos
function Test-Prerequisites {
    Write-Log "🔍 Verificando pré-requisitos..." "INFO"
    
    $allOk = $true
    
    # Verificar Python
    try {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match "Python (\d+\.\d+)") {
            Write-Log "✅ Python: $pythonVersion" "SUCCESS"
        } else {
            Write-Log "❌ Python não encontrado" "ERROR"
            $allOk = $false
        }
    } catch {
        Write-Log "❌ Python não instalado" "ERROR"
        $allOk = $false
    }
    
    # Verificar MPI
    try {
        $mpiVersion = mpiexec --version 2>&1
        if ($mpiVersion) {
            Write-Log "✅ MPI disponível" "SUCCESS"
        } else {
            Write-Log "❌ MPI não encontrado" "ERROR"
            $allOk = $false
        }
    } catch {
        Write-Log "❌ MPI não instalado" "ERROR"
        $allOk = $false
    }
    
    # Verificar diretório do projeto
    if (Test-Path $PROJETO_DIR) {
        Write-Log "✅ Diretório do projeto: $PROJETO_DIR" "SUCCESS"
    } else {
        Write-Log "❌ Diretório do projeto não encontrado: $PROJETO_DIR" "ERROR"
        $allOk = $false
    }
    
    # Verificar arquivos Python
    $arquivos = @("sistema_monitoramento.py", "servidor_intersCity.py", "gerador_dados.py")
    foreach ($arquivo in $arquivos) {
        if (Test-Path "$SRC_DIR\$arquivo") {
            Write-Log "✅ $arquivo" "SUCCESS"
        } else {
            Write-Log "❌ $arquivo não encontrado" "ERROR"
            $allOk = $false
        }
    }
    
    # Verificar bibliotecas Python
    try {
        python -c "import mpi4py, numpy, pandas, flask; print('Bibliotecas OK')" 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Log "✅ Bibliotecas Python disponíveis" "SUCCESS"
        } else {
            Write-Log "❌ Algumas bibliotecas Python não estão instaladas" "ERROR"
            Write-Log "   Execute: pip install -r requirements.txt" "WARNING"
            $allOk = $false
        }
    } catch {
        Write-Log "❌ Erro ao verificar bibliotecas Python" "ERROR"
        $allOk = $false
    }
    
    return $allOk
}

# Função para criar diretórios necessários
function Initialize-Directories {
    Write-Log "📁 Criando diretórios necessários..." "INFO"
    
    $dirs = @("$PROJETO_DIR\data", "$PROJETO_DIR\logs", "C:\temp")
    
    foreach ($dir in $dirs) {
        if (!(Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Log "📁 Criado: $dir" "SUCCESS"
        }
    }
}

# Função para executar testes
function Start-Tests {
    Write-Log "🧪 Executando testes do sistema..." "INFO"
    
    Set-Location $PROJETO_DIR
    
    Write-Log "🧪 Teste MPI..." "INFO"
    mpiexec -n 4 python src\teste_mpi.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Log "✅ Testes concluídos com sucesso!" "SUCCESS"
        return $true
    } else {
        Write-Log "❌ Falha nos testes" "ERROR"
        return $false
    }
}

# Função para iniciar InterSCity
function Start-InterSCity {
    Write-Log "🌐 Iniciando servidor InterSCity..." "INFO"
    
    Set-Location $PROJETO_DIR
    
    $job = Start-Job -ScriptBlock {
        Set-Location $using:PROJETO_DIR
        python src\servidor_intersCity.py
    }
    
    # Aguardar servidor inicializar
    Start-Sleep -Seconds 3
    
    # Verificar se está rodando
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000/health" -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Log "✅ InterSCity iniciado com sucesso" "SUCCESS"
            Write-Log "🌍 Dashboard: http://localhost:5000" "INFO"
            
            # Tentar abrir no navegador
            try {
                Start-Process "http://localhost:5000"
                Write-Log "📊 Dashboard aberto no navegador" "SUCCESS"
            } catch {
                Write-Log "📊 Abra manualmente: http://localhost:5000" "WARNING"
            }
            
            return $job
        }
    } catch {
        Write-Log "❌ Erro ao verificar InterSCity" "ERROR"
        Stop-Job -Job $job
        Remove-Job -Job $job
        return $null
    }
}

# Função para iniciar gerador de dados
function Start-DataGenerator {
    Write-Log "📈 Iniciando gerador de dados..." "INFO"
    
    # Verificar se já existem dados
    if ((Test-Path "C:\temp\dados_sensores.csv") -and ((Get-Item "C:\temp\dados_sensores.csv").Length -gt 100)) {
        Write-Log "📊 Dados existentes encontrados, não iniciando gerador" "WARNING"
        return $null
    }
    
    $job = Start-Job -ScriptBlock {
        Set-Location $using:PROJETO_DIR
        # Simular entrada para geração contínua
        "2" | python src\gerador_dados.py
    }
    
    Start-Sleep -Seconds 2
    Write-Log "✅ Gerador de dados iniciado" "SUCCESS"
    return $job
}

# Função para iniciar sistema MPI
function Start-MPISystem {
    Write-Log "🚀 Iniciando sistema MPI..." "INFO"
    
    Set-Location $PROJETO_DIR
    
    $job = Start-Job -ScriptBlock {
        Set-Location $using:PROJETO_DIR
        mpiexec -n 4 python src\sistema_monitoramento.py
    }
    
    Start-Sleep -Seconds 2
    Write-Log "✅ Sistema MPI iniciado com 4 processos" "SUCCESS"
    return $job
}

# Função para monitorar jobs
function Monitor-Jobs {
    param($Jobs)
    
    Write-Log "📊 Monitorando componentes do sistema..." "INFO"
    Write-Log "⏹️  Pressione Ctrl+C para parar o sistema" "WARNING"
    
    try {
        while ($true) {
            $running = 0
            $failed = 0
            
            foreach ($job in $Jobs) {
                if ($job -and (Get-Job -Id $job.Id -ErrorAction SilentlyContinue)) {
                    if ($job.State -eq "Running") {
                        $running++
                    } elseif ($job.State -eq "Failed") {
                        $failed++
                        Write-Log "❌ Job $($job.Name) falhou" "ERROR"
                    }
                }
            }
            
            $timestamp = Get-Date -Format "HH:mm:ss"
            Write-Host "[$timestamp] 📊 Status: $running componentes rodando, $failed com erro" -ForegroundColor Cyan
            
            # Verificar arquivos de log
            if (Test-Path "$LOG_DIR\sistema_rank_0.log") {
                $logSize = (Get-Item "$LOG_DIR\sistema_rank_0.log").Length
                Write-Host "[$timestamp] 📝 Log master: $logSize bytes" -ForegroundColor Gray
            }
            
            Start-Sleep -Seconds 30
        }
    } catch {
        Write-Log "🛑 Monitoramento interrompido" "WARNING"
    }
}

# Função para parar todos os jobs
function Stop-AllJobs {
    param($Jobs)
    
    Write-Log "🛑 Finalizando sistema..." "WARNING"
    
    foreach ($job in $Jobs) {
        if ($job -and (Get-Job -Id $job.Id -ErrorAction SilentlyContinue)) {
            Write-Log "🔄 Parando job: $($job.Name)" "INFO"
            Stop-Job -Job $job
            Remove-Job -Job $job -Force
        }
    }
    
    Write-Log "🏁 Sistema finalizado" "SUCCESS"
}

# Função principal
function Main {
    # Mostrar banner
    Write-Host ""
    Write-Host "============================================================================" -ForegroundColor Cyan
    Write-Host "🏗️  SISTEMA DE MONITORAMENTO DE ESGOTO URBANO" -ForegroundColor Cyan
    Write-Host "   Integração: AnyLogic + MPI + InterSCity" -ForegroundColor Cyan
    Write-Host "   Ambiente: VS Code + PowerShell" -ForegroundColor Cyan
    Write-Host "============================================================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Verificar parâmetros
    if ($Help) {
        Show-Help
        return
    }
    
    # Verificar pré-requisitos
    if (!(Test-Prerequisites)) {
        Write-Log "❌ Pré-requisitos não atendidos. Execute com -Help para mais informações." "ERROR"
        return
    }
    
    # Inicializar diretórios
    Initialize-Directories
    
    # Modo de teste
    if ($Teste) {
        if (Start-Tests) {
            Write-Log "🎉 Todos os testes passaram!" "SUCCESS"
        } else {
            Write-Log "❌ Falha nos testes" "ERROR"
        }
        return
    }
    
    # Variáveis para jobs
    $jobs = @()
    
    try {
        # Iniciar InterSCity
        $intersCity = Start-InterSCity
        if ($intersCity) {
            $jobs += $intersCity
        } else {
            Write-Log "❌ Falha ao iniciar InterSCity" "ERROR"
            return
        }
        
        # Iniciar gerador de dados (se necessário)
        if (!$SemGerador -and !$SoInterSCity) {
            $gerador = Start-DataGenerator
            if ($gerador) {
                $jobs += $gerador
            }
            
            Start-Sleep -Seconds 5
        }
        
        # Iniciar sistema MPI (se não for só InterSCity)
        if (!$SoInterSCity) {
            $mpiSystem = Start-MPISystem
            if ($mpiSystem) {
                $jobs += $mpiSystem
            } else {
                Write-Log "❌ Falha ao iniciar sistema MPI" "ERROR"
                Stop-AllJobs $jobs
                return
            }
        }
        
        # Mostrar status inicial
        Write-Host ""
        Write-Host "============================================================================" -ForegroundColor Green
        Write-Host "🚀 SISTEMA INICIADO COM SUCESSO!" -ForegroundColor Green
        Write-Host "============================================================================" -ForegroundColor Green
        Write-Host "📊 Dashboard InterSCity: http://localhost:5000" -ForegroundColor Yellow
        Write-Host "🔍 Logs do sistema: $LOG_DIR" -ForegroundColor Yellow
        Write-Host "📁 Dados salvos: $PROJETO_DIR\data" -ForegroundColor Yellow
        
        if (!$SemGerador) {
            Write-Host "📈 Gerador de dados: ATIVO" -ForegroundColor Yellow
        } else {
            Write-Host "⚠️  IMPORTANTE: Inicie o AnyLogic para gerar dados" -ForegroundColor Red
        }
        
        Write-Host "⏹️  Para parar: Pressione Ctrl+C" -ForegroundColor Red
        Write-Host "============================================================================" -ForegroundColor Green
        Write-Host ""
        
        # Monitorar sistema
        Monitor-Jobs $jobs
        
    } catch {
        Write-Log "❌ Erro durante execução: $($_.Exception.Message)" "ERROR"
    } finally {
        Stop-AllJobs $jobs
    }
}

# Executar função principal
Main