FROM nvidia/cuda:12.8.0-cudnn-runtime-ubuntu24.04

# Install required python layers and ffmpeg, then remove the cached package index files.
RUN apt-get update && apt-get install -y \
    python3.12 \
    python3-pip \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install python dependencies first (if requirements.txt doesn't change, Docker caches this when dockerfile is run)
# --break-system-packages to bypass PEP 668 enforcement that doesnt allow pip installs into "global" python environment - google for better explanation.
COPY requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt \
    --extra-index-url https://download.pytorch.org/whl/cu128

# Copy application code
COPY . .

EXPOSE 50052

CMD ["python3.12", "src/main.py"]