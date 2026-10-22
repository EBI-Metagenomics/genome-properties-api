# Genome Properties API

GraphQL API for the Genome Properties resource. The service is a Django 5.2 application on Python 3.12+, backed by SQLite.

## Local setup

```bash
uv sync
export DATABASE_PATH=/path/to/genome_properties.db
uv run python manage.py runserver
```

GraphiQL is available at [http://127.0.0.1:8000/graphql/](http://127.0.0.1:8000/graphql/). A liveness probe is at `/health/`.

The SQLite file is not stored in git. Place it at `genome_properties.db` in the project root, or set `DATABASE_PATH`.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `DJANGO_SECRET_KEY` | insecure dev key | Django secret |
| `DJANGO_DEBUG` | `true` | Debug / GraphiQL extras |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Host allow-list |
| `POD_IP` | empty | Pod IP from the K8s downward API; appended to `ALLOWED_HOSTS` for kubelet probes |
| `DJANGO_FORCE_SCRIPT_NAME` | empty | Sub-path, e.g. `/genomeproperties/api` |
| `DJANGO_STATIC_URL` | `/static/` | Static URL |
| `DJANGO_CORS_ALLOW_ALL` | same as debug | Open CORS |
| `DJANGO_CORS_ALLOWED_ORIGINS` | localhost:3000 | CORS origins |
| `DATABASE_PATH` | `./genome_properties.db` | SQLite file |

## Docker

```bash
docker build -t genome-properties-api:local .
docker run --rm -p 8000:8000 \
  -e DATABASE_PATH=/data/genome_properties.db \
  -v /path/to/genome_properties.db:/data/genome_properties.db:ro \
  genome-properties-api:local
```

Images are published to `dockerhub.ebi.ac.uk/microbiome-informatics/containers/genome-properties-api` via the GitHub Actions workflows in `.github/workflows/`.
