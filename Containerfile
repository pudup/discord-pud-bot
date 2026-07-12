FROM python:3.13.5-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

COPY . /opt/disc_bot

WORKDIR /opt/disc_bot

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /disc_bot

CMD ["python3", "main.py"]