FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .

# Install dependencies directly
RUN pip install --no-cache-dir \
    alembic \
    fastapi \
    sqlalchemy \
    psycopg2-binary \
    asyncpg \
    "pydantic[email]" \
    pydantic-settings \
    uvicorn \
    python-dotenv \
    "python-jose[cryptography]" \
    "passlib[bcrypt]" \
    "bcrypt==4.0.1" \
    cloudinary \
    slowapi \
    httpx \
    fastapi-mail \
    python-multipart

COPY . .

RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
