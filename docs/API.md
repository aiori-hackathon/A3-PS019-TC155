# API overview

All endpoints are under `/api/v1`. The browser supplies a random `X-Workspace-Key` for isolated local workspaces; write requests also use the `X-CSRF-Token` returned by `GET /auth/me`. There are no account creation, login, or password routes.

- `GET /health`, `GET /health/ready`: service and database health.
- `GET /auth/me`: initialize/read the current browser-local workspace and CSRF token.
- `GET /samples`, `POST /samples/{sample_id}/load`: list and add one of ten committed synthetic CSV/SQLite fixtures.
- `GET/POST /sources`, `POST /sources/upload`, `DELETE /sources/{id}`: source registry and upload.
- `GET /sources/{id}/schema`, `POST /sources/{id}/scan?sample_limit=500`: inspect and scan; sample limit is 1–5,000.
- `GET /findings`, `POST /findings/{id}/review`, `GET /evidence-gaps`: review and metadata gap workflows.
- `GET/POST /metadata`: declared purpose/retention mappings.
- `GET /rules`, `POST /rules/test`: five-class taxonomy and rule tester, reflecting the current workspace checklist.
- `PUT /rules/config`: enable one or more class detectors for this workspace. New scans snapshot the enabled class list in their scan record.
- `GET /evaluation`: reproducible labelled evaluation metrics.
- `POST /assistant`: local product guidance; source data is not sent to an external provider.
- `GET /reports/inventory.csv`, `GET /reports/summary.json`: exports.

CSV is UTF-8 with a header row. SQLite sources are opened read-only. Uploaded files remain on the API host until removed from the source registry.
