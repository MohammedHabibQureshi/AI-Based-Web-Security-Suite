FROM python:3.11-slim

# Install system dependencies required for WeasyPrint, psycopg2 and git
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    git \
    python3-dev \
    # WeasyPrint PDF layout engine library requirements
    libpango-1.0-0 \
    libharfbuzz-gobject0 \
    libjpeg-dev \
    libopenjp2-7-dev \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
