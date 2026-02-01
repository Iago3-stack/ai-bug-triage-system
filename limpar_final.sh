#!/bin/bash
# Remove todos os arquivos .py EXCETO o home.py
find . -maxdepth 1 -type f -name "*.py" ! -name "home.py" -exec git rm {} \;

# Remove todos os outros arquivos que não sejam o requirements.txt ou o próprio script
find . -maxdepth 1 -type f ! -name "home.py" ! -name "requirements.txt" ! -name "limpar_final.sh" ! -name ".gitignore" -exec git rm {} \;

# Registra a limpeza no Git
git commit -m "clean: removendo scripts antigos e mantendo apenas a IA de Triagem"
git push origin main
