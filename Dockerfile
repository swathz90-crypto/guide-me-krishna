FROM python:3.11-slim

# Minimal system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Pin numpy first before anything else installs it
RUN pip install --no-cache-dir "numpy==1.26.4"

# Install CPU-only torch
RUN pip install --no-cache-dir \
    "torch==2.2.2" \
    "torchvision==0.17.2" \
    --index-url https://download.pytorch.org/whl/cpu

# Install remaining deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Force numpy back to 1.x in case anything upgraded it
RUN pip install --no-cache-dir "numpy==1.26.4"

# Copy source
COPY . .

RUN chmod +x start.sh

EXPOSE 8000

CMD ["bash", "start.sh"]
