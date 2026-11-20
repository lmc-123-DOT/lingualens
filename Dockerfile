FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LINGUALENS_HOST=0.0.0.0 \
    LINGUALENS_DATA=/data \
    LINGUALENS_REQUIRE_AUTH=1 \
    PORT=8000

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /data

EXPOSE 8000

CMD ["sh", "-c", "python server.py --host 0.0.0.0 --port ${PORT:-8000}"]
