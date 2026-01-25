FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /atlas

# System dependencies
RUN apt update && apt install -y \
    ffmpeg \
    git \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project
COPY . /atlas

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Start Atlas
CMD ["python", "run.py"]
