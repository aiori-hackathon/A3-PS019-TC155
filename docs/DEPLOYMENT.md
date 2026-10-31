# Deployment

## Live evaluator demo

| Component | Live URL | Hosting |
| --- | --- | --- |
| Frontend | [privexis.vercel.app](https://privexis.vercel.app/) | Vercel |
| API | [Readiness status](https://privexis-api.onrender.com/api/v1/health/ready) | Render Free web service |
| API reference | [Endpoint guide](API.md) | OpenAPI UI is disabled in production |
| Database | PostgreSQL 17 | Render Free Postgres |

The Render Blueprint is `render.yaml` at the repository root. It provisions the API and database in Singapore, generates the API secret, sets the Vercel CORS origin, and runs database migrations when the container starts. The frontend’s production and preview `NEXT_PUBLIC_API_URL` variables point to the Render API.

### Free-tier behavior

- Render spins down an idle free web service after 15 minutes; waking it may take about a minute.
- The web service has an ephemeral filesystem. Uploaded files and local SQLite databases disappear after restarts, redeploys, or spin-down. Use the managed Postgres database for relational application state.
- Free Postgres is limited to 1 GB and expires 30 days after creation. Back up data you need and upgrade or migrate before expiry.
- This setup is suitable for a hackathon demo with synthetic data, not durable production hosting.

## Local Docker Compose

From the repository root:

```powershell
docker compose up --build
```

This starts the frontend, API, and local PostgreSQL database. The development Compose credentials are not for production.

## Optional OCI deployment

The API can also run on an OCI VM with PostgreSQL and Caddy. The application uses PostgreSQL, not Oracle Database. See [the OCI deployment guide](../deploy/oci/README.md) and [OCI Compose files](../deploy/oci/).
