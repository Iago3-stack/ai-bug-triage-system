import os
import json
from datetime import datetime
from shutil import copy2

# Pasta onde estão os arquivos JSON
pasta = "dados"  # ajuste para a pasta correta
backup = True    # define se quer criar backup antes de alterar

# Função para converter datas
def converter_datas(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str):
                # tenta detectar datas YYYY-MM-DD
                for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
                    try:
                        dt = datetime.strptime(v, fmt)
                        obj[k] = dt.strftime("%d/%m/%Y")
                        break
                    except ValueError:
                        continue
            else:
                converter_datas(v)
    elif isinstance(obj, list):
        for item in obj:
            converter_datas(item)

# Processa arquivos JSON
for arquivo in os.listdir(pasta):
    if arquivo.endswith(".json"):
        caminho = os.path.join(pasta, arquivo)
        
        # Faz backup se necessário
        if backup:
            copy2(caminho, caminho + ".bak")
        
        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)
        
        converter_datas(dados)
        
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)

print("✅ Todas as datas foram convertidas para DD/MM/YYYY com segurança!")
