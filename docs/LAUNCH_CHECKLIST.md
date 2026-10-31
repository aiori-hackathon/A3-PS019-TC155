# Deployment and validation status

| Component | Status | URL / evidence |
| --- | --- | --- |
| Vercel frontend | Live | [privexis.vercel.app](https://privexis.vercel.app/) |
| Render API | Live | [privexis-api.onrender.com](https://privexis-api.onrender.com/) |
| API/database readiness | Healthy at last check | [Readiness endpoint](https://privexis-api.onrender.com/api/v1/health/ready) returns `{"status":"ready"}` |
| GitHub evaluation repository | Updated | [aiori-hackathon/A3-PS019-TC155](https://github.com/aiori-hackathon/A3-PS019-TC155) |

The Render web service and PostgreSQL database use the Free plan. See [deployment limits](DEPLOYMENT.md#free-tier-behavior) before relying on persisted files or data.

## Feature validation

| Area | Status | Evidence |
| --- | --- | --- |
| Privexis brand and favicon | Implemented | Supplied artwork assets |
| Public site and metadata | Implemented | Next.js production build |
| Browser-local workspace | Implemented | Guest key isolation and CSRF API tests |
| CSV/SQLite scan workflow | Implemented | Bounded rows; SQLite opened read-only |
| Five-class taxonomy | Implemented | Rules tester and labelled evaluation set |
| Ten synthetic sample files | Implemented | Five classes × CSV and SQLite, scanned by tests |
| Review and purpose/retention mapping | Implemented | API workflow and gap reporting |
| Search and local assistant | Implemented | Feature results and findings search; local guidance |
| Evaluation and reports | Implemented | Per-class precision/recall/F1 and exports |
| External AI provider | Not implemented | Assistant answers from local guidance only |
| Public deployment | Live | Vercel frontend + Render API; production API health and CORS verified |
