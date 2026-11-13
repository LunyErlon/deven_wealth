@echo off
chcp 65001 > nul
echo ========================================================
echo   DEVEN WEALTH - COMPILADOR AUTOMATICO DE EXECUTAVEL
echo ========================================================
echo.

REM 1. Localiza ambiente virtual
if exist .venv\Scripts\python.exe (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
    set "PIP_EXE=.venv\Scripts\pip.exe"
) else (
    set "PYTHON_EXE=python"
    set "PIP_EXE=pip"
)

echo [1/3] Verificando e instalando PyInstaller...
%PIP_EXE% install pyinstaller --upgrade

echo.
echo [2/3] Compilando Deven Wealth para Executavel (.exe)...
%PYTHON_EXE% -m PyInstaller --clean --noconsole --name "DevenWealth" ^
  --icon "gerenciador\assets\Logo_Principal.png" ^
  --add-data "gerenciador\assets;assets" ^
  --hidden-import "packaging.version" ^
  --hidden-import "openpyxl" ^
  --hidden-import "matplotlib.backends.backend_qtagg" ^
  --hidden-import "ofxparse" ^
  --hidden-import "yfinance" ^
  --collect-all "qtawesome" ^
  gerenciador\main.py

echo.
if %ERRORLEVEL% equ 0 (
    echo [3/3] Sucesso! Executavel compilado com exito.
    echo Pasta gerada: dist\DevenWealth\DevenWealth.exe
    echo.
    echo Basta compactar a pasta 'dist\DevenWealth' em .zip para distribuir!
) else (
    echo [ERRO] Falha durante a compilação do executavel.
)
echo.
pause
