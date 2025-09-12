
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libssl-dev \
    curl \
    make \
 && rm -rf /var/lib/apt/lists/*


ENV POETRY_VERSION=2.1.0 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

RUN curl -sSL https://install.python-poetry.org | python3 - \
 && ln -s ${POETRY_HOME}/bin/poetry /usr/local/bin/poetry

COPY pyproject.toml poetry.lock ./ 
RUN poetry lock && poetry install --no-root --no-ansi --verbose

COPY . .

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
