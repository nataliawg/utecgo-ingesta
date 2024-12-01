FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

RUN mkdir -p /app/logs /app/ingesta

EXPOSE 5000

CMD ["python", "ingesta.py"]
