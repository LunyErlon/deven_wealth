#!/bin/bash
# ========================================================
#   DEVEN WEALTH - Compilador para macOS (.app)
# ========================================================

echo "========================================================"
echo "   DEVEN WEALTH - COMPILADOR PARA MACOS"
echo "========================================================"

if [ -d ".venv" ]; then
    PYTHON_EXE=".venv/bin/python"
    PIP_EXE=".venv/bin/pip"
else
    PYTHON_EXE="python3"
    PIP_EXE="pip3"
fi

echo -e "\n[1/3] Verificando e instalando PyInstaller..."
$PIP_EXE install pyinstaller --upgrade

echo -e "\n[2/3] Compilando Deven Wealth para macOS (.app)..."
$PYTHON_EXE -m PyInstaller --clean --noconsole --name "DevenWealth" \
    --windowed \
    --icon "gerenciador/assets/Logo_Principal.png" \
    --add-data "gerenciador/assets:assets" \
    --hidden-import "packaging.version" \
    --hidden-import "openpyxl" \
    --hidden-import "matplotlib.backends.backend_qtagg" \
    --hidden-import "ofxparse" \
    --hidden-import "yfinance" \
    --collect-all "qtawesome" \
    gerenciador/main.py

if [ $? -eq 0 ]; then
    echo -e "\n[3/3] Sucesso! Pacote DevenWealth.app gerado com êxito."
    echo "Diretório de saída: dist/DevenWealth.app (ou dist/DevenWealth/)"
    echo -e "\nPara empacotar em .zip preservando links simbólicos no Mac:"
    echo "cd dist && zip -r -y DevenWealth-macOS.zip DevenWealth.app\n"
else
    echo -e "\n[ERRO] Falha durante a compilação no macOS."
fi
