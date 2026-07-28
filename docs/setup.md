# Setup notes

Use `.env.example` as the configuration contract. `python -m scripts.seed` is idempotent enough for a clean demo database; delete/recreate the Docker volume for a full reset. SQLite is used only by isolated tests. The API exposes `/health`, `/health/database`, and `/health/vision`.

