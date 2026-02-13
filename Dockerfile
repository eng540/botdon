FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app

ENV BOT_TOKEN=CHANGE_ME
ENV RATE_LIMIT_SECONDS=10

CMD ["python", "app/main.py"]