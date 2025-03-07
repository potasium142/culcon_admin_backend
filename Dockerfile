FROM docker.io/python:3.10.15-slim-bookworm

WORKDIR /workdir

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    libpq-dev \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . .

ENTRYPOINT ["fastapi", "run", "main.py"]

