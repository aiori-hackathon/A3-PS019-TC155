# Security notes

- Browser-local workspace keys are random 256-bit values. The API derives separate workspace identities from the key and requires an HMAC CSRF token on writes.
- CORS is restricted to configured frontend and localhost origins. Configure a random `PRIVEXIS_SECRET_KEY` of at least 32 characters for deployments.
- Upload size is bounded; CSV scanning samples a configurable maximum number of rows. SQLite connections use read-only mode. Findings retain field names and rule evidence summaries, not sampled raw values.
- No login, signup, password, or demo-account routes are provided. The browser workspace key is stored in local storage; clearing it removes access to the associated workspace.
- The assistant supplies local product guidance. It does not call an external AI provider.

This application is intended for local evaluation with synthetic or otherwise authorized data. It does not provide legal compliance conclusions or managed retention/deletion of uploaded files beyond the source removal action. A public multi-user deployment would need additional controls such as distributed throttling, managed identity, operational monitoring, and a reviewed retention policy.
