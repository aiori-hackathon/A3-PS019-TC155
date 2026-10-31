# Deployment

## OCI deployment option: Vercel + OCI

Deploy the Next.js frontend to Vercel and run FastAPI, PostgreSQL, and Caddy on an OCI VM with `docker-compose.oci.yml`. This keeps PostgreSQL and uploaded files on persistent Docker volumes. Use PostgreSQL; the application is not configured for Oracle Database.

The OCI API needs a public DNS hostname with HTTPS. Point an API subdomain (for example, `api.example.com`) at the OCI VM's public IPv4 address. Caddy obtains and renews the HTTPS certificate automatically after DNS resolves and ports 80/443 are reachable.

### Deploy in the requested order

1. Create an OCI VM using an Always Free eligible shape in your home region. Create a public IPv4 address and DNS record for the API hostname. Allow inbound TCP 80 and 443 in OCI network rules; restrict SSH (22) to your own IP.
2. Import/push the repository to Vercel. Set `NEXT_PUBLIC_API_URL` to the planned HTTPS API origin (for example `https://api.example.com`) and `NEXT_PUBLIC_SITE_URL` to the Vercel production origin. Deploy the frontend. The API-dependent features will become live after the backend is started.
3. Install Docker Engine and the Compose plugin on the OCI VM, then copy or clone the repository there.
4. Copy `.env.oci.example` to `.env.oci`. Replace the API domain, exact Vercel origin, database URL/password, and secret with production values. Do not commit `.env.oci`.
5. Start the API and database with `docker compose --env-file .env.oci -f docker-compose.oci.yml up -d --build`. The API runs Alembic migrations on startup; Caddy serves HTTPS on the API domain.
6. Verify `https://<API_DOMAIN>/health` and `https://<API_DOMAIN>/api/v1/health/ready`. Then verify sample listing, upload, scan, evaluation, and report downloads from the Vercel site. If the final Vercel domain differs from the configured one, update `PRIVEXIS_FRONTEND_ORIGIN` and restart the API. If the API URL changed, update `NEXT_PUBLIC_API_URL` in Vercel and redeploy.

Vercel variables (set in Project Settings → Environment Variables):

| Variable | Value |
| --- | --- |
| `NEXT_PUBLIC_API_URL` | Public HTTPS OCI API origin, e.g. `https://api.example.com` |
| `NEXT_PUBLIC_SITE_URL` | Canonical HTTPS Vercel origin |

The OCI stack exposes only Caddy's ports 80/443. FastAPI and PostgreSQL remain private on the Compose network. PostgreSQL data, uploaded files, and Caddy certificates use persistent Docker volumes. Back up the VM and volumes before relying on stored data.

OCI Always Free compute can be reclaimed if it stays below Oracle's published utilization thresholds; free hosting is suitable for a demo but cannot promise uninterrupted uptime. Check that the selected shape is Always Free in your home region before creating it.

## Current evaluator deployment: Vercel + Render Free

The root `render.yaml` Blueprint defines a free Render web service and free PostgreSQL database. Render assigns the API an `onrender.com` HTTPS URL, so a custom domain is not required. Connect this project to a private GitHub repository, create the Blueprint from `render.yaml`, and deploy both resources in the Singapore region.

After Render creates the API service, copy its public URL into the Vercel production environment variable `NEXT_PUBLIC_API_URL`, then redeploy the Vercel project. `PRIVEXIS_FRONTEND_ORIGIN` is set to `https://privexis.vercel.app` in the Blueprint. Check `/health` and `/api/v1/health/ready`, then try sample listing, upload, scan, evaluation, and report downloads from the Vercel site.

Free Render web services sleep after 15 minutes without inbound traffic and can take about a minute to wake. Their local filesystem is ephemeral, so uploaded files and SQLite files do not survive restarts or spin-down. The free PostgreSQL database is limited to 1 GB and expires after 30 days. This setup is for a time-limited demo; keep synthetic datasets in the project and avoid relying on uploaded data or the free database for long-term storage.

## Vercel Python Functions alternative

Vercel can run FastAPI as a Python Function, but the current API stores uploads on disk and expects a relational database. This requires external persistent PostgreSQL and object storage, plus deployment entrypoint and file-storage integration changes. The OCI Docker Compose option above uses the current API storage model with fewer code changes.

## Local containers

`docker compose up --build` starts PostgreSQL, runs Alembic migrations, and starts FastAPI and the Next.js standalone server. Compose credentials are for development only.

## Production security and operations

- Keep `PRIVEXIS_SECRET_KEY` generated and private. Production refuses the development default.
- Set CORS to the exact public frontend origin; do not use wildcard origins with credentials.
- Do not expose PostgreSQL publicly. Back up the database and uploaded files separately.
- Monitor the API health endpoints and test a synthetic sample scan after deployment.
- This repository is deployment-configured, not published. No public URL or OCI resources have been created.
