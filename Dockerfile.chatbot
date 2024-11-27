FROM python:3.10-slim

WORKDIR /app

COPY bin/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bin/ollamarama.py .

CMD ["python", "ollamarama.py"]