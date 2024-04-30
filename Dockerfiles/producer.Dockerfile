# Use a imagem oficial do Python
FROM python:3.9-slim

# Define o diretório de trabalho no contêiner
WORKDIR /app

# Instala dependências do projeto
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante dos arquivos do diretório app para o diretório de trabalho no contêiner
COPY app/ .

# Copia o arquivo DadosFraude.json para o diretório de trabalho no contêiner
COPY app/DadosFraude.json .

EXPOSE 5000

# Executa a aplicação
CMD ["python", "Producer.py"]