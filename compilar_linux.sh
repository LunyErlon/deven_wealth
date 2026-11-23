#!/bin/bash
# ========================================================
#   DEVEN WEALTH - Compilador para Linux (Binário ELF)
# ========================================================

echo "========================================================"
echo "   DEVEN WEALTH - COMPILADOR PARA LINUX"
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

echo -e "\n[2/3] Compilando Deven Wealth com PyInstaller para Linux..."
$PYTHON_EXE -m PyInstaller --clean --noconsole --name "DevenWealth" \
    --add-data "gerenciador/assets:assets" \
    --hidden-import "packaging.version" \
    --hidden-import "openpyxl" \
    --hidden-import "matplotlib.backends.backend_qtagg" \
    --hidden-import "ofxparse" \
    --hidden-import "yfinance" \
    --collect-all "qtawesome" \
    gerenciador/main.py

if [ $? -eq 0 ]; then
    echo -e "\n[3/3] Sucesso! Executável Linux compilado com êxito."
    echo "Diretório de saída: dist/DevenWealth/DevenWealth"
    chmod +x dist/DevenWealth/DevenWealth 2>/dev/null
    echo -e "\nPara executar: ./dist/DevenWealth/DevenWealth\n"
else
    echo -e "\n[ERRO] Falha durante a compilação no Linux."
fi
