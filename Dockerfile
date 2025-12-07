FROM python:3.10-slim as builder
WORKDIR /app
RUN pip install poetry && poetry config virtualenvs.create false
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev --no-interaction --no-ansi

FROM python:3.10-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .

RUN useradd -m appuser
USER appuser

CMD ["python", "src/main.py"]
