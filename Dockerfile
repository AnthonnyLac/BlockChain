# Use a imagem base do Python
FROM python:3.12-slim

# Defina o diretório de trabalho no contêiner
WORKDIR /src

# Copie os arquivos de requisitos para o contêiner
COPY requirements.txt requirements.txt

# Instale as dependências
RUN pip install -r requirements.txt


# Copiar o arquivos principais para o conteiner
COPY src/main.py .
COPY templates/ templates/
COPY site.db .

# Exponha a porta que o Flask usa
EXPOSE 5000

# Comando para rodar a aplicação
CMD ["python", "main.py"]
