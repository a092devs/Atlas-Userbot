FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /atlas

RUN apt update && apt install -y \
    ffmpeg \
    git \
    ca-certificates \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

RUN git config --global --add safe.directory /atlas

COPY . /atlas

# IMPORTANT: force latest yt-dlp
RUN pip install --no-cache-dir -U pip yt-dlp \
    && pip install --no-cache-dir -r requirements.txt

CMD ["python", "run.py"]
