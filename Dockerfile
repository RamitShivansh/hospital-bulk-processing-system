FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

RUN mkdir -p /app/logs && chmod 777 /app/logs

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--log-level", "info", "--access-logfile", "-", "--error-logfile", "-", "run:app"]
