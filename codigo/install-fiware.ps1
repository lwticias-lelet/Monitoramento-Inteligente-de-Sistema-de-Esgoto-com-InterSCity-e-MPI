# INSTALADOR FIWARE PARA WINDOWS - VERSÃO SIMPLIFICADA
# Execute como Administrador: .\install-fiware.ps1

Write-Host @"
 INSTALADOR FIWARE PARA WINDOWS
================================

Sistema de Monitoramento de Esgotamento Sanitário
São Luís, Maranhão - Brasil

"@ -ForegroundColor Green

# Verificar se está rodando como administrador
$currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
$isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host " ATENÇÃO: Para melhor resultado, execute como Administrador" -ForegroundColor Yellow
    Write-Host "Mas podemos continuar sem privilégios para algumas partes..." -ForegroundColor Cyan
    $continue = Read-Host "Deseja continuar? (s/n)"
    if ($continue.ToLower() -ne 's') { exit 0 }
}

Write-Host "`n VERIFICANDO SISTEMA..." -ForegroundColor Yellow

# Verificar sistema
Write-Host "Windows: $([System.Environment]::OSVersion.VersionString)"
Write-Host "PowerShell: $($PSVersionTable.PSVersion)"

# Verificar ferramentas
$tools = @{
    "Python" = { python --version 2>$null }
    "Node.js" = { node --version 2>$null }
    "Git" = { git --version 2>$null }
    "Docker" = { docker --version 2>$null }
    "npm" = { npm --version 2>$null }
}

$missing = @()
foreach ($tool in $tools.Keys) {
    try {
        $version = & $tools[$tool]
        Write-Host "✅ $tool`: $version" -ForegroundColor Green
    } catch {
        Write-Host "❌ $tool`: Não encontrado" -ForegroundColor Red
        $missing += $tool
    }
}

# Instalar ferramentas faltando
if ($missing.Count -gt 0) {
    Write-Host "`n INSTALANDO FERRAMENTAS FALTANDO..." -ForegroundColor Yellow
    
    # Instalar Chocolatey se necessário
    if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
        Write-Host " Instalando Chocolatey..." -ForegroundColor Blue
        if ($isAdmin) {
            try {
                Set-ExecutionPolicy Bypass -Scope Process -Force
                [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
                iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
                Write-Host " Chocolatey instalado" -ForegroundColor Green
            } catch {
                Write-Host " Erro ao instalar Chocolatey: $($_.Exception.Message)" -ForegroundColor Red
            }
        } else {
            Write-Host " Chocolatey precisa de privilégios de administrador" -ForegroundColor Yellow
        }
    }
    
    # Instalar cada ferramenta faltando
    foreach ($tool in $missing) {
        Write-Host " Instalando $tool..." -ForegroundColor Blue
        
        if ($isAdmin -and (Get-Command choco -ErrorAction SilentlyContinue)) {
            switch ($tool) {
                "Git" { choco install git -y }
                "Node.js" { choco install nodejs -y }
                "Docker" { choco install docker-desktop -y }
                "Python" { choco install python -y }
            }
        } else {
            Write-Host " Instale manualmente: $tool" -ForegroundColor Cyan
            switch ($tool) {
                "Git" { Write-Host "   Download: https://git-scm.com/download/win" }
                "Node.js" { Write-Host "   Download: https://nodejs.org/en/download/" }
                "Docker" { Write-Host "   Download: https://www.docker.com/products/docker-desktop" }
                "Python" { Write-Host "   Download: https://www.python.org/downloads/" }
            }
        }
    }
}

Write-Host "`n CONFIGURANDO FIWARE COM DOCKER..." -ForegroundColor Yellow

# Verificar se Docker está disponível
if (Get-Command docker -ErrorAction SilentlyContinue) {
    try {
        docker info 2>$null | Out-Null
        Write-Host " Docker está rodando" -ForegroundColor Green
        
        # Criar docker-compose.yml
        Write-Host " Criando docker-compose.yml..." -ForegroundColor Blue
        
        $dockerCompose = @"
version: '3.8'
services:
  mongodb:
    image: mongo:6.0
    hostname: mongodb
    container_name: fiware-mongodb
    ports:
      - "27017:27017"
    command: --nojournal
    volumes:
      - mongodb_data:/data/db
    networks:
      - fiware

  orion:
    image: fiware/orion:3.10.1
    hostname: orion
    container_name: fiware-orion
    depends_on:
      - mongodb
    ports:
      - "1026:1026"
    command: -dbhost mongodb -logLevel DEBUG
    networks:
      - fiware

  mosquitto:
    image: eclipse-mosquitto:2.0
    hostname: mosquitto
    container_name: fiware-mosquitto
    ports:
      - "1883:1883"
      - "9001:9001"
    volumes:
      - mosquitto_data:/mosquitto/data
    networks:
      - fiware

  iot-agent:
    image: fiware/iotagent-mqtt:2.4.0
    hostname: iot-agent
    container_name: fiware-iot-agent
    depends_on:
      - mongodb
      - mosquitto
      - orion
    ports:
      - "4041:4041"
    environment:
      - IOTA_CB_HOST=orion
      - IOTA_CB_PORT=1026
      - IOTA_NORTH_PORT=4041
      - IOTA_REGISTRY_TYPE=mongodb
      - IOTA_MONGO_HOST=mongodb
      - IOTA_MONGO_PORT=27017
      - IOTA_MONGO_DB=iotagent
      - IOTA_MQTT_HOST=mosquitto
      - IOTA_MQTT_PORT=1883
      - IOTA_PROVIDER_URL=http://iot-agent:4041
    networks:
      - fiware

volumes:
  mongodb_data:
  mosquitto_data:

networks:
  fiware:
    driver: bridge
"@
        
        $dockerCompose | Out-File "docker-compose-fiware.yml" -Encoding UTF8
        Write-Host " docker-compose-fiware.yml criado" -ForegroundColor Green
        
        # Baixar e iniciar FIWARE
        Write-Host "`n Iniciando FIWARE..." -ForegroundColor Yellow
        Write-Host " Isso pode demorar alguns minutos..." -ForegroundColor Cyan
        
        docker-compose -f docker-compose-fiware.yml up -d
        
        # Aguardar inicialização
        Write-Host " Aguardando serviços inicializarem..." -ForegroundColor Cyan
        Start-Sleep -Seconds 30
        
        # Testar Orion
        $maxRetries = 5
        $success = $false
        
        for ($i = 1; $i -le $maxRetries; $i++) {
            try {
                $response = Invoke-RestMethod -Uri "http://localhost:1026/version" -TimeoutSec 10
                Write-Host " Orion Context Broker funcionando!" -ForegroundColor Green
                Write-Host " Versão: $($response.orion.version)" -ForegroundColor Blue
                $success = $true
                break
            } catch {
                Write-Host " Tentativa $i/$maxRetries - Aguardando Orion..." -ForegroundColor Yellow
                Start-Sleep -Seconds 15
            }
        }
        
        if ($success) {
            Write-Host "`n FIWARE INSTALADO COM SUCESSO!" -ForegroundColor Green
            
            Write-Host "`n SERVIÇOS DISPONÍVEIS:" -ForegroundColor Cyan
            Write-Host " Orion Context Broker: http://localhost:1026" -ForegroundColor White
            Write-Host " MQTT Broker: localhost:1883" -ForegroundColor White
            Write-Host " IoT Agent: http://localhost:4041" -ForegroundColor White
            Write-Host " MongoDB: localhost:27017" -ForegroundColor White
            
            Write-Host "`n TESTE RÁPIDO:" -ForegroundColor Yellow
            
            # Teste da API
            try {
                $testEntity = @{
                    id = "SensorTeste"
                    type = "WaterSensor"
                    flow_rate = @{ value = 45.5; type = "Number" }
                    location = @{ 
                        value = @{ type = "Point"; coordinates = @(-44.2549, -2.5227) }
                        type = "geo:json" 
                    }
                }
                
                $testJson = $testEntity | ConvertTo-Json -Depth 5
                Invoke-RestMethod -Uri "http://localhost:1026/v2/entities" -Method Post -Body $testJson -ContentType "application/json" | Out-Null
                
                $entity = Invoke-RestMethod -Uri "http://localhost:1026/v2/entities/SensorTeste"
                Write-Host " Teste da API: Entidade criada e consultada!" -ForegroundColor Green
                
                Invoke-RestMethod -Uri "http://localhost:1026/v2/entities/SensorTeste" -Method Delete | Out-Null
                Write-Host " Teste da API: Entidade removida!" -ForegroundColor Green
                
            } catch {
                Write-Host " Teste da API falhou: $($_.Exception.Message)" -ForegroundColor Yellow
            }
            
            Write-Host "`n PRÓXIMOS PASSOS:" -ForegroundColor Cyan
            Write-Host "1.  Criar adaptadores para seu sistema atual"
            Write-Host "2.  Integrar CSV processor com FIWARE"
            Write-Host "3.  Integrar MQTT publisher com FIWARE"
            Write-Host "4.  Expandir dashboard para consumir FIWARE"
            
            Write-Host "`n COMANDOS ÚTEIS:" -ForegroundColor Blue
            Write-Host "Parar FIWARE: docker-compose -f docker-compose-fiware.yml down"
            Write-Host "Iniciar FIWARE: docker-compose -f docker-compose-fiware.yml up -d"
            Write-Host "Ver status: docker-compose -f docker-compose-fiware.yml ps"
            Write-Host "Ver logs: docker-compose -f docker-compose-fiware.yml logs [serviço]"
            
        } else {
            Write-Host " FIWARE não iniciou corretamente" -ForegroundColor Red
            Write-Host " Verifique os logs: docker-compose -f docker-compose-fiware.yml logs" -ForegroundColor Yellow
        }
        
    } catch {
        Write-Host " Docker não está rodando: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host " Inicie o Docker Desktop e tente novamente" -ForegroundColor Yellow
    }
} else {
    Write-Host " Docker não encontrado" -ForegroundColor Red
    Write-Host " Instale Docker Desktop: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
}

Write-Host "`n Instalação completa!" -ForegroundColor Green
Write-Host " Arquivo criado: docker-compose-fiware.yml" -ForegroundColor Blue

Read-Host "`nPressione Enter para finalizar"
