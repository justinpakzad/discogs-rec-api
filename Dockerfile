FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH=/app
ENV UV_NO_DEV=1

COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

RUN apt-get update && apt-get install -y \
    build-essential \
    libstdc++6 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock* ./
RUN uv sync --locked
ENV PATH="/app/.venv/bin:$PATH"

COPY .env .
COPY pytest.ini .
COPY alembic.ini .
COPY discogs_rec_api ./discogs_rec_api
COPY migrations ./migrations
COPY setup_scripts ./setup_scripts
COPY ml ./ml
COPY tests ./tests
COPY streamlit ./streamlit


CMD ["uv", "run", "python", "discogs_rec_api/main.py"]

