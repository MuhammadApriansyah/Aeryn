FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install Node.js for PM2
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g pm2@5.3.0

WORKDIR /app

# Copy project files
COPY requirements.txt .
COPY . .

# Install Python dependencies with uv
RUN uv venv venv-proot
ENV PATH="/app/venv-proot/bin:$PATH"
RUN uv pip install -r requirements.txt

# Build Rust engine
RUN apt-get update && apt-get install -y pkg-config libssl-dev
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:$PATH"
RUN cd aeryn-engine && maturin develop --release

# Expose port
EXPOSE 3010

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3010/health || exit 1

# Start with PM2
CMD ["pm2-runtime", "ecosystem.config.js"]
