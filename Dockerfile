FROM python:3.14-slim as builder

WORKDIR /app

RUN pip install poetry==1.7.1

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root --only main

RUN pip install --upgrade setuptools>=78.1.1 msgpack>=1.2.1

FROM python:3.14-slim

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .

EXPOSE 5000
CMD ["python", "src/app.py"]
