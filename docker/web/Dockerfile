FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app/src

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    gosu \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

RUN addgroup --system django && \
    adduser --system --ingroup django django

COPY docker/web/entrypoint.sh /entrypoint.sh
COPY docker/web/download_static.sh /app/download_static.sh
RUN sed -i 's/\r$//' /entrypoint.sh /app/download_static.sh && \
    chmod +x /entrypoint.sh /app/download_static.sh

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]


FROM base AS development

ENV DJANGO_SETTINGS_MODULE=config.settings.development

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/base.txt requirements/development.txt requirements/
RUN pip install -r requirements/development.txt

COPY . .

RUN mkdir -p /app/src/static/vendor && \
    /app/download_static.sh && \
    chown -R django:django /app

CMD ["python", "src/manage.py", "runserver", "0.0.0.0:8000"]


FROM base AS production

ENV DJANGO_SETTINGS_MODULE=config.settings.production

COPY requirements/base.txt requirements/production.txt requirements/
RUN pip install -r requirements/production.txt

COPY src/ ./src/

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && mkdir -p /app/src/static/vendor \
    && /app/download_static.sh \
    && apt-get purge -y curl \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* \
    && chown -R django:django /app

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
