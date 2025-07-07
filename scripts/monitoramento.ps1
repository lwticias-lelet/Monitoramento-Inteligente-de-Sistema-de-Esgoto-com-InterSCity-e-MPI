# Script para resolver todos os problemas do monitoramento.csv

Write-Host "=== Solucionando Problemas do Monitoramento ===" -ForegroundColor Green

# Verificar se arquivo existe
$csvFile = "data\csv\monitoramento.csv"
if (!(Test-Path $csvFile)) {
    Write-Host "✗ Arquivo não encontrado: $csvFile" -ForegroundColor Red
    Write-Host "Execute primeiro: Copy-Item 'C:\Users\lelet\Models\mapeamento de esgotos\data\monitoramento.csv' 'data\csv\monitoramento.csv'" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Arquivo encontrado: $csvFile" -ForegroundColor Green

# Ativar ambiente virtual
Write-Host "`nAtivando ambiente virtual..." -ForegroundColor Yellow
try {
    & .\venv\Scripts\Activate.ps1
    Write-Host "✓ Ambiente virtual ativado" -ForegroundColor Green
} catch {
    Write-Host "✗ Erro ao ativar ambiente virtual" -ForegroundColor Red
    Write-Host "Execute: .\setup.ps1" -ForegroundColor Yellow
    exit 1
}

# Passo 1: Adaptar CSV
Write-Host "`nPasso 1: Adaptando estrutura do CSV..." -ForegroundColor Yellow
python adapt_monitoramento.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Erro na adaptação do CSV" -ForegroundColor Red
    exit 1
}

Write-Host "✓ CSV adaptado com sucesso!" -ForegroundColor Green

# Passo 2: Processar dados
Write-Host "`nPasso 2: Processando dados..." -ForegroundColor Yellow
python main_simple.py --mode process --file "data\csv\monitoramento_adapted.csv"

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Erro no processamento" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Dados processados com sucesso!" -ForegroundColor Green

# Verificar dados processados
$processedFiles = Get-ChildItem "data\processed\*.csv" -ErrorAction SilentlyContinue
if ($processedFiles) {
    Write-Host "✓ Arquivos processados:" -ForegroundColor Green
    $processedFiles | ForEach-Object { Write-Host "  - $($_.Name)" -ForegroundColor White }
} else {
    Write-Host "⚠ Nenhum arquivo processado encontrado" -ForegroundColor Yellow
}

# Passo 3: Iniciar dashboard
Write-Host "`nPasso 3: Iniciando dashboard..." -ForegroundColor Yellow
Write-Host "📊 Dashboard será aberto em: http://localhost:8050" -ForegroundColor Cyan
Write-Host "⏹️  Pressione Ctrl+C para parar o dashboard" -ForegroundColor Cyan
Write-Host ""

python main_simple.py --mode dashboard