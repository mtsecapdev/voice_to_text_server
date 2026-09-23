FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (if requirements.txt doesn't change, Docker caches this when dockerfile is run)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    --extra-index-url https://download.pytorch.org/whl/cu128

# Copy application code
COPY . .

EXPOSE 50052

CMD ["python", "src/main.py"]