FROM python:3.13-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN addgroup --system app && adduser --system --group app

COPY requirements/prod.txt requirements/prod.txt
RUN pip install --no-cache-dir -r requirements/prod.txt

COPY . .

RUN SECRET_KEY=build-only python manage.py collectstatic --noinput

USER app

EXPOSE 8080

CMD ["gunicorn", "config.wsgi", "--bind", "0.0.0.0:8080", "--workers", "2", "--access-logfile", "-"]
