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

# Optional: build the learning-station database from upstream public datasets.
# The data is not committed to git; it is assembled inside the image at build
# time so a personal Render deployment gets the full 学习站台. Set the build arg
# WITH_LEXICON=0 to skip it (the rest of the app still works).
ARG WITH_LEXICON=1
RUN if [ "$WITH_LEXICON" = "1" ]; then \
      python fetch_lexicon_data.py && python build_lexicon.py \
      || echo "lexicon build skipped (download or build failed)"; \
    fi

EXPOSE 8000

CMD ["sh", "-c", "python server.py --host 0.0.0.0 --port ${PORT:-8000}"]
