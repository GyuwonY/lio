FROM python:3.13-slim-bookworm AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip pip-tools

COPY requirements.in .

RUN pip-compile -o requirements.txt requirements.in && \
    pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY . . 

FROM python:3.13-slim-bookworm

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages

COPY --from=builder /app /app

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
