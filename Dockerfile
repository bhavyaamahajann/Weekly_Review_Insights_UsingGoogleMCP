FROM python:3.11-slim-bookworm

# Prevent python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install dependencies
# We install the CPU version of torch to avoid the massive CUDA-enabled package
# which exceeds memory and storage limits on build servers.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Pre-download the SentenceTransformer model to speed up runtime starts and avoid downloading it dynamically
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-large-en-v1.5')"

# Download SpaCy models if presidio needs them (presidio-analyzer default is en_core_web_sm)
RUN python -m spacy download en_core_web_sm

# Copy the rest of the application
COPY . .

# Build the React frontend production assets
RUN npm run build


# Expose port (Flask API & Frontend web server)
EXPOSE 5000

CMD ["sh", "-c", "gunicorn api.index:app --bind 0.0.0.0:${PORT:-5000}"]


