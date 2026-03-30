FROM python:3.11-slim

WORKDIR /app

# Install system deps for unstructured + pypdf
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 libmagic-dev curl poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
