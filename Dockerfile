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

# Mark repo path as safe for git (required for bind mounts)
RUN git config --global --add safe.directory /atlas

# Copy project (will be overridden by bind mount at runtime)
COPY . /atlas

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Start Atlas
CMD ["python", "run.py"]