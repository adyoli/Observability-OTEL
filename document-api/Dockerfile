FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install poetry

RUN poetry config virtualenvs.create false

# Copy only pyproject.toml first to handle dependency changes
COPY pyproject.toml ./

# Generate lock file and install dependencies
RUN poetry lock && poetry install --no-root

RUN mkdir -p /app/uploads

COPY . .

# Start the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
