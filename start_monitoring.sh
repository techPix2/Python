#!/bin/bash

# TechPix Monitoring Starter
# Versão: 1.0
# Descrição: Instala dependências e inicia o sistema de monitoramento

# --------------------------
# Configurações
# --------------------------
PYTHON_EXEC="python3"  # Use python3 ou python dependendo do seu sistema
REQUIREMENTS_FILE="requirements.txt"
MAIN_SCRIPT="index.py"

# --------------------------
# Funções auxiliares
# --------------------------
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

check_python() {
    if ! command -v $PYTHON_EXEC &> /dev/null; then
        log "ERRO: Python não está instalado. Por favor instale Python 3.7 ou superior."
        exit 1
    fi
}

install_dependencies() {
    log "Instalando dependências Python..."
    $PYTHON_EXEC -m pip install --upgrade pip
    $PYTHON_EXEC -m pip install -r $REQUIREMENTS_FILE
}

# --------------------------
# Execução principal
# --------------------------
log "Iniciando setup do TechPix Monitoring..."

# Verifica Python
check_python

# Instala dependências
install_dependencies

# Inicia o sistema
log "Iniciando o sistema de monitoramento..."
$PYTHON_EXEC $MAIN_SCRIPT

log "Script concluído."