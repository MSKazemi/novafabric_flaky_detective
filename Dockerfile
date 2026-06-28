# Flaky Detective API container.
# NovaFabric is public on PyPI, so it installs like any other dependency.
#
# Build:  docker build -t flaky-detective .
# Run:    docker run --rm -p 8000:8000 flaky-detective
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install the API and all deps (novafabric>=0.58, fastapi, uvicorn, pydantic) from PyPI.
COPY pyproject.toml ./
COPY src/ ./src/
RUN pip install .

EXPOSE 8000
CMD ["uvicorn", "flaky_detective.api:app", "--host", "0.0.0.0", "--port", "8000"]
