# Architecture

## Components

- Next.js App Router renders public product pages and the browser-local workspace.
- FastAPI validates inputs, scopes records to the workspace key, invokes ingestion/scanning services, and returns structured results.
- SQLAlchemy stores workspace identities, source registrations, scans, findings, field mappings, review events, and audit events. The model retains legacy user credential/session columns for database migration compatibility; no login or signup routes use them.
- SQLite is the local application database and supported SQL source fixture. Alembic manages the application schema.
- Uploaded source artifacts live in a private server directory; the application database stores their generated storage path and source metadata.

## Data flow and boundaries

The browser creates a random 256-bit workspace key and sends it with API requests. The API derives an isolated workspace identity from that key. Writes require an HMAC CSRF token. The API applies extension and size checks, stores uploads under generated server filenames, and associates them with the workspace. CSV parsing or read-only SQLite schema/sample queries run locally. Findings retain field names, class candidates, confidence, rule version, and value-free evidence summaries; raw sample values are not stored in findings or ordinary logs.

The source database/file is distinct from the Privexis application database. SQLite sources are opened using `mode=ro`; browser-provided file paths and SQL are never executed.

## Deployment and limitations

Docker Compose starts the database, applies migrations, and launches the API and website. The application exposes no account registration or sign-in flow. Scanning runs synchronously with a bounded sample. Public deployment needs operational controls such as distributed throttling, private upload retention, monitoring, and an independent security review.
