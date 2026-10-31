# Optional OCI deployment

This alternate deployment runs the FastAPI service, PostgreSQL, and Caddy on an Oracle Cloud Infrastructure VM. It uses PostgreSQL, not Oracle Database. The repository’s current evaluator deployment remains Vercel + Render Free; see [the main deployment guide](../../docs/DEPLOYMENT.md).

## Requirements

- An OCI VM with a public IPv4 address.
- A DNS name pointing to the VM, such as `api.example.com`.
- Inbound TCP 80 and 443 allowed in OCI network rules; restrict SSH (22) to your own IP.
- Docker Engine and the Docker Compose plugin installed on the VM.

## Configure and start

From the repository root, copy the template and replace every placeholder:

```sh
cp deploy/oci/.env.example deploy/oci/.env
```

Set a random `PRIVEXIS_SECRET_KEY`, a strong `POSTGRES_PASSWORD`, the database URL, the API DNS name, and the exact Vercel origin. Keep `deploy/oci/.env` private and out of Git.

Start the stack from the repository root:

```sh
docker compose --env-file deploy/oci/.env -f deploy/oci/docker-compose.yml up -d --build
```

Compose runs FastAPI database migrations at startup. Caddy obtains and renews the HTTPS certificate after DNS resolves and ports 80/443 are reachable. PostgreSQL, uploads, and Caddy certificates use persistent Docker volumes; back them up separately.

Set Vercel’s `NEXT_PUBLIC_API_URL` to `https://<API_DOMAIN>` and redeploy the frontend. Verify `/health` and `/api/v1/health/ready` before demonstrating scans.

OCI Always Free compute may be reclaimed if it stays below Oracle’s published utilization thresholds. Confirm the selected shape is Always Free in your home region before provisioning.
