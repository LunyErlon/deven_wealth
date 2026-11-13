# ========================================================
#   DEVEN WEALTH - Script de Compilação Automática (.exe)
# ========================================================

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "   DEVEN WEALTH - COMPILADOR PARA EXECUTÁVEL (.EXE)" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan

$PythonExe = if (Test-Path ".\.venv\Scripts\python.exe") { ".\.venv\Scripts\python.exe" } else { "python" }
$PipExe    = if (Test-Path ".\.venv\Scripts\pip.exe") { ".\.venv\Scripts\pip.exe" } else { "pip" }

Write-Host "`n[1/3] Verificando e instalando PyInstaller..." -ForegroundColor Green
& $PipExe install pyinstaller --upgrade

Write-Host "`n[2/3] Compilando Deven Wealth com PyInstaller..." -ForegroundColor Green
& $PythonExe -m PyInstaller --clean --noconsole --name "DevenWealth" `
    --icon "gerenciador\assets\Logo_Principal.png" `
    --add-data "gerenciador\assets;assets" `
    --hidden-import "packaging.version" `
    --hidden-import "openpyxl" `
    --hidden-import "matplotlib.backends.backend_qtagg" `
    --hidden-import "ofxparse" `
    --hidden-import "yfinance" `
    --collect-all "qtawesome" `
    gerenciador\main.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[3/3] Sucesso! Executável compilado." -ForegroundColor Green
    Write-Host "Pasta de saída: dist\DevenWealth\DevenWealth.exe" -ForegroundColor Yellow
    Write-Host "Para distribuir, basta compactar a pasta 'dist\DevenWealth' em um arquivo .zip e enviar aos usuários ou publicar no GitHub Releases!`n" -ForegroundColor Cyan
} else {
    Write-Host "`n[ERRO] Ocorreu uma falha durante a compilação." -ForegroundColor Red
}
