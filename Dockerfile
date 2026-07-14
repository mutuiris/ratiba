# Build wheels so the runtime image needs no compiler
FROM python:3.13-slim AS builder

WORKDIR /build

COPY requirements/prod.txt .
RUN pip wheel --no-cache-dir --wheel-dir /build/wheels -r prod.txt

# Runtime
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN addgroup --system app && adduser --system --group app

COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/*.whl && rm -rf /wheels

COPY --chown=app:app . .
RUN chmod +x entrypoint.sh && mkdir -p staticfiles && chown app:app staticfiles

USER app

EXPOSE 8080

ENTRYPOINT ["./entrypoint.sh"]
