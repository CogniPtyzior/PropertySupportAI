FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

COPY pyproject.toml README.md alembic.ini ./
COPY app ./app
COPY alembic ./alembic
COPY scripts ./scripts

RUN pip install --upgrade pip && pip install -e .

ENV DATABASE_URL=sqlite:///./property_support_seed.db
RUN alembic upgrade head && python -m scripts.seed_db --reset

ENV DATABASE_URL=sqlite:////tmp/property_support.db
RUN chmod +x scripts/start_demo.sh

EXPOSE 8001
CMD ["sh", "scripts/start_demo.sh"]
