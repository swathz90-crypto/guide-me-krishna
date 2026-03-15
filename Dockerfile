FROM python:3.11-slim

# Minimal system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install CPU-only torch first (tiny vs full torch = 800MB vs 3GB)
RUN pip install --no-cache-dir \
    "torch==2.2.2" \
    "torchvision==0.17.2" \
    --index-url https://download.pytorch.org/whl/cpu

# Install remaining deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

RUN chmod +x start.sh

EXPOSE 8000

CMD ["bash", "start.sh"]
