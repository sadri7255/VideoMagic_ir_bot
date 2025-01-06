FROM python:3.9-slim
WORKDIR /app
COPY . .
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get install -y ffmpeg libav-tools
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "bot.py"]
