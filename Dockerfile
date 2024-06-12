# Use a imagem base do Python
FROM python:3.12-slim
WORKDIR /app

# Copie os arquivos de requisitos para o contêiner
COPY ["src/app", "src/app/."]
COPY ["src/instance", "src/instance/."]
COPY ["src/run.py", "src/run.py"]
COPY ["requirements.txt", "requirements.txt"]

# Instale as dependências
RUN pip install -r requirements.txt

# Exponha a porta que o Flask usa
EXPOSE 5000

# Comando para rodar a aplicação
CMD ["python", "src/run.py"]
