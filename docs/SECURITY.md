# Security notes

- Browser-local workspace keys are random 256-bit values. The API derives separate workspace identities from the key and requires an HMAC CSRF token on writes.
- CORS is restricted to configured frontend and localhost origins. Configure a random `PRIVEXIS_SECRET_KEY` of at least 32 characters for deployments.
- Upload size is bounded; CSV scanning samples a configurable maximum number of rows. SQLite connections use read-only mode. Findings retain field names and rule evidence summaries, not sampled raw values.
- No login, signup, password, or demo-account routes are provided. The browser workspace key is stored in local storage; clearing it removes access to the associated workspace.
- The assistant supplies local product guidance. It does not call an external AI provider.

The public evaluator demo is hosted at [privexis.vercel.app](https://privexis.vercel.app/) with its API on Render Free. It is intended for synthetic data only and does not provide legal compliance conclusions. Uploaded files are removed when their source is deleted, but Render Free storage is ephemeral and can be cleared on restarts, redeploys, or spin-down. This demo is not configured for real personal data or production retention needs. Production use would need controls such as distributed throttling, managed identity, durable private storage, operational monitoring, and a reviewed retention policy.
