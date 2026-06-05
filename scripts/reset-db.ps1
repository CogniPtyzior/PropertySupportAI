if (Test-Path .\property_support.db) { Remove-Item .\property_support.db }
alembic upgrade head
python -m scripts.seed_db --reset
