# Use a imagem oficial do Python
FROM python:3.9-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia os arquivos necessários para o container
#COPY  app/worker.py .
COPY  app/requirements.txt .
COPY app/Worker.py .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante dos arquivos do diretório app para o diretório de trabalho no contêiner
COPY app/ .

# Comando para executar o script
CMD ["python", "Worker.py"]
