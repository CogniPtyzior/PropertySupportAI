#!/usr/bin/env sh
set -e

if [ ! -f /tmp/property_support.db ]; then
  cp /app/property_support_seed.db /tmp/property_support.db
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8001}"
