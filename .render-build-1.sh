#!/usr/bin/env bash
set -o errexit echo "==== USING CUSTOM BUILD SCRIPT ====" 
# Explicitly call system python from Render’s install location 
PYTHON_BIN=$(which python3 || which python) 
if [ -z "$PYTHON_BIN" ]; 
then echo "Python not found in PATH, checking /opt/render" 
PYTHON_BIN=$(find /opt/render/project -type f -name python3 | head -n 1) fi 

echo "Using Python binary at: $PYTHON_BIN" $PYTHON_BIN -m ensurepip --upgrade $PYTHON_BIN -m pip install --upgrade pip setuptools wheel 
$PYTHON_BIN -m pip install numpy==1.26.4 pandas==2.0.3 
$PYTHON_BIN -m pip install scikit-learn==1.3.2 
$PYTHON_BIN -m pip install --no-use-pep517 scikit-surprise==1.1.3 
$PYTHON_BIN -m pip install uvicorn==0.23.2 fastapi==0.107.0