# Database schema

The application uses SQLAlchemy declarative models and Alembic revisions. `DATABASE_URL` selects PostgreSQL or the local SQLite development fallback.

| Entity | Purpose | Key relationships |
| --- | --- | --- |
| Organization | Tenant boundary | Owns users, sources, scans, findings, metadata, and audit events |
| User | Workspace identity used by the current API; legacy credential columns remain for schema compatibility | Belongs to one organization |
| Session | Legacy session table retained for schema compatibility; current browser workspaces do not use it | Belongs to a user |
| RuleConfiguration | Enabled personal-data class detectors for the workspace | One checklist per organization |
| Source | Name, type, generated artifact path, size | Belongs to one organization |
| Scan | Status, bounded sample count, inspected columns, rule version, enabled class checklist snapshot | Belongs to source and organization |
| Finding | Candidate class, confidence, rule, value-free evidence, current review state | Belongs to source, scan, organization |
| MetadataMapping | Organization-declared purpose and retention by source/table/column | Belongs to source and organization |
| ReviewEvent | Append-only decision and note history | References finding and reviewer |
| AuditEvent | Security/workflow event without raw sample values | Scoped to organization and actor |

Foreign keys and organization indexes support isolation and cleanup. Review events preserve prior decisions; the finding row contains the current decision. Source removal deletes its uploaded artifact and database-related scan data (on PostgreSQL and where SQLite foreign-key constraints are enforced).

Apply revisions with `alembic -c backend/alembic.ini upgrade head`. Do not reset or downgrade a database with user data without a reviewed backup and migration plan.
