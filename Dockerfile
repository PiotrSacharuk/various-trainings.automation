FROM python:3.12-slim AS builder
WORKDIR /app
RUN pip install poetry && poetry config virtualenvs.create false
COPY pyproject.toml poetry.lock ./
RUN poetry install --only=main --no-interaction --no-ansi

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .

RUN useradd -m appuser
USER appuser

ENV FLASK_HOST=0.0.0.0
ENV FLASK_PORT=5000
ENV FLASK_DEBUG=False

CMD python -m flask --app src.main:app run --host=${FLASK_HOST} --port=${FLASK_PORT}
