FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH=/app
RUN apt-get update && apt-get install -y \
    build-essential \
    libstdc++6 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt
COPY .env .
COPY pytest.ini .
COPY alembic.ini .
COPY discogs_rec_api ./discogs_rec_api
COPY migrations ./migrations
COPY setup_scripts ./setup_scripts
COPY ml ./ml
COPY tests ./tests
COPY streamlit ./streamlit

CMD ["python", "discogs_rec_api/main.py"]
