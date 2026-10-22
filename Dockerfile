FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock /app/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-install-project --no-dev

COPY genomeproperties /app/genomeproperties
COPY web /app/web
COPY config /app/config
COPY manage.py /app/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev

ARG DJANGO_FORCE_SCRIPT_NAME=
ARG DJANGO_STATIC_URL=/static/
ENV DJANGO_FORCE_SCRIPT_NAME=$DJANGO_FORCE_SCRIPT_NAME \
    DJANGO_STATIC_URL=$DJANGO_STATIC_URL \
    DJANGO_SECRET_KEY=build-only \
    DJANGO_DEBUG=false \
    DJANGO_ALLOWED_HOSTS=localhost

RUN mkdir -p /app/staticfiles \
    && uv run python manage.py collectstatic --noinput

FROM python:3.13-slim AS runtime

RUN groupadd -r gp && useradd -r -g gp -u 10001 gp

WORKDIR /app

COPY --from=builder --chown=gp:gp /app /app

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

USER 10001

EXPOSE 8000

CMD ["gunicorn", "--bind", ":8000", "--workers=4", "--access-logfile=-", "--log-file=-", "genomeproperties.wsgi"]
