param([switch]$Reset)
if ($Reset) { uv run python -m scripts.seed_db --reset } else { uv run python -m scripts.seed_db }
