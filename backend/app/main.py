import csv
import hashlib
import hmac
import io
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.orm import Session as DBSession

from .config import ENVIRONMENT, FRONTEND_ORIGIN, MAX_UPLOAD_MB, SAMPLE_ROWS, SECRET_KEY, UPLOAD_DIR
from .db import Base, engine, get_db
from .models import AuditEvent, Finding, MetadataMapping, Organization, ReviewEvent, RuleConfiguration, Scan, Source, User
from .scanner import (
    CLASSES,
    CLASS_DESCRIPTIONS,
    NOT_PERSONAL_DATA,
    RULES_CATALOG,
    RULE_VERSION,
    classify,
    evaluate,
    evaluate_cases,
    inspect_schema,
    load_ground_truth,
    scan_source,
)

if ENVIRONMENT == "production" and (len(SECRET_KEY) < 32 or SECRET_KEY.startswith("development")):
    raise RuntimeError("PRIVEXIS_SECRET_KEY must be a secure random value in production")

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_DIR = Path(__file__).resolve().parents[1] / "data" / "demo_files"
app = FastAPI(title="Privexis API", version="0.1.0", docs_url=None if ENVIRONMENT == "production" else "/api/docs")

allowed_origins = [
    FRONTEND_ORIGIN,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
allowed_origins = list(dict.fromkeys(allowed_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
class RuleTestInput(BaseModel):
    column_name: str
    sample_value: str = ""

class RuleConfigurationInput(BaseModel):
    enabled_classes: list[str] = Field(min_length=1, max_length=5)

class ReviewInput(BaseModel):
    decision: str
    note: str = Field(default="", max_length=2000)
    reclassify: str | None = None

class MappingInput(BaseModel):
    source_id: int
    table_name: str = Field(default="", max_length=180)
    column_name: str = Field(min_length=1, max_length=180)
    purpose: str = Field(default="", max_length=500)
    retention: str = Field(default="", max_length=300)

def digest(raw: str) -> str: return hashlib.sha256(raw.encode()).hexdigest()

def current_user(request: Request, db: DBSession = Depends(get_db)) -> User:
    workspace_key = request.headers.get("x-workspace-key", "").strip()
    if re.fullmatch(r"[0-9a-fA-F]{64}", workspace_key):
        email = f"workspace-{digest(workspace_key)}@anonymous.privexis.local"
        user = db.scalar(select(User).where(User.email == email))
        if not user:
            org = Organization(name=f"Local workspace {digest(workspace_key)[:10]}", is_demo=False)
            db.add(org)
            db.flush()
            user = User(
                organization_id=org.id,
                email=email,
                full_name="Local workspace",
                password_hash=digest(f"disabled-credential:{workspace_key}"),
                role="organization_admin",
                verified=True,
                active=True,
            )
            db.add(user)
            db.commit()
        request.state.is_guest = True
        request.state.guest_key = workspace_key
        return user

    raise HTTPException(401, "A browser-local workspace key is required. Open the site and refresh.")

def csrf(request: Request, user: User = Depends(current_user)) -> User:
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        expected = hmac.new(SECRET_KEY.encode(), request.state.guest_key.encode(), hashlib.sha256).hexdigest()
        header = request.headers.get("x-csrf-token", "")
        if not hmac.compare_digest(header, expected):
            raise HTTPException(403, "The workspace request token is invalid. Refresh and try again.")
    return user

def need_role(user: User, roles: set[str]):
    if user.role not in roles: raise HTTPException(403, "Your role does not allow this action.")

def owned_source(db: DBSession, user: User, source_id: int) -> Source:
    result = db.scalar(select(Source).where(Source.id == source_id, Source.organization_id == user.organization_id))
    if not result: raise HTTPException(404, "Source not found.")
    return result

def enabled_classes_for(db: DBSession, user: User) -> set[str]:
    config = db.scalar(select(RuleConfiguration).where(RuleConfiguration.organization_id == user.organization_id))
    if config is None:
        return set(CLASSES)
    return {code for code in config.enabled_classes if code in CLASSES}

def audit(db: DBSession, user: User, action: str, resource: str, resource_id: str):
    db.add(AuditEvent(organization_id=user.organization_id, user_id=user.id, action=action, resource_type=resource, resource_id=resource_id))

@app.get("/health")
def health(): return {"status": "ok", "service": "privexis-api"}

@app.get("/api/v1/health/ready")
def ready(db: DBSession = Depends(get_db)):
    try: db.execute(select(1)); return {"status": "ready"}
    except Exception: raise HTTPException(503, "Database unavailable.")

def sample_catalog() -> list[dict]:
    try:
        return json.loads((SAMPLE_DIR / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise HTTPException(503, "Synthetic sample datasets are unavailable.")

@app.get("/api/v1/samples")
def list_samples(user: User = Depends(current_user)):
    return sample_catalog()

@app.post("/api/v1/samples/{sample_id}/load")
def load_sample(sample_id: str, user: User = Depends(csrf), db: DBSession = Depends(get_db)):
    sample = next((item for item in sample_catalog() if item.get("id") == sample_id), None)
    if not sample:
        raise HTTPException(404, "Synthetic sample not found.")
    source_path = (SAMPLE_DIR / sample["filename"]).resolve()
    if source_path.parent != SAMPLE_DIR.resolve() or not source_path.is_file():
        raise HTTPException(404, "Synthetic sample file is unavailable.")
    safe_path = UPLOAD_DIR / f"{uuid.uuid4().hex}{source_path.suffix}"
    safe_path.write_bytes(source_path.read_bytes())
    source = Source(organization_id=user.organization_id, name=source_path.name, kind=sample["kind"], file_path=str(safe_path), size_bytes=safe_path.stat().st_size)
    db.add(source)
    db.flush()
    audit(db, user, "sample.loaded", "source", str(source.id))
    db.commit()
    return {"id": source.id, "name": source.name, "kind": source.kind}

@app.get("/api/v1/auth/me")
def me(request: Request, user: User = Depends(current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name or "",
        "role": user.role,
        "organization_id": user.organization_id,
        "mfa_enabled": user.mfa_enabled,
        "csrf_token": hmac.new(SECRET_KEY.encode(), request.state.guest_key.encode(), hashlib.sha256).hexdigest(),
    }

@app.get("/api/v1/sources")
def list_sources(user: User = Depends(current_user), db: DBSession = Depends(get_db)):
    values = db.scalars(select(Source).where(Source.organization_id == user.organization_id).order_by(Source.created_at.desc())).all()
    return [{"id": x.id, "name": x.name, "kind": x.kind, "size_bytes": x.size_bytes, "created_at": x.created_at.isoformat()} for x in values]

@app.post("/api/v1/sources/upload")
async def upload_source(file: UploadFile = File(...), user: User = Depends(csrf), db: DBSession = Depends(get_db)):
    need_role(user, {"organization_admin", "analyst"})
    name = (file.filename or "upload.csv").replace("\\", "/").split("/")[-1]
    suffix = Path(name).suffix.lower()
    if suffix not in {".csv", ".db", ".sqlite", ".sqlite3"}: raise HTTPException(400, "Upload a .csv or SQLite database file.")
    kind = "csv" if suffix == ".csv" else "sqlite"
    safe_path = UPLOAD_DIR / f"{uuid.uuid4().hex}{suffix}"
    total = 0
    try:
        with safe_path.open("wb") as out:
            while chunk := await file.read(1024 * 1024):
                total += len(chunk)
                if total > MAX_UPLOAD_MB * 1024 * 1024: raise HTTPException(413, f"File exceeds the {MAX_UPLOAD_MB} MB upload limit.")
                out.write(chunk)
        if kind == "sqlite":
            import sqlite3
            try:
                check = sqlite3.connect(f"file:{safe_path.as_posix()}?mode=ro", uri=True); check.execute("SELECT name FROM sqlite_master LIMIT 1"); check.close()
            except sqlite3.Error: raise HTTPException(400, "The uploaded file is not a readable SQLite database.")
        else:
            with safe_path.open("r", encoding="utf-8-sig") as test: test.read(4096)
    except UnicodeDecodeError: safe_path.unlink(missing_ok=True); raise HTTPException(400, "CSV must be UTF-8 encoded.")
    except Exception:
        safe_path.unlink(missing_ok=True); raise
    finally: await file.close()
    source = Source(organization_id=user.organization_id, name=name[:180], kind=kind, file_path=str(safe_path), size_bytes=total)
    db.add(source); db.flush(); audit(db, user, "source.uploaded", "source", str(source.id)); db.commit()
    return {"id": source.id, "name": source.name, "kind": source.kind}

@app.delete("/api/v1/sources/{source_id}")
def delete_source(source_id: int, request: Request, user: User = Depends(csrf), db: DBSession = Depends(get_db)):
    need_role(user, {"organization_admin", "analyst"}); source = owned_source(db, user, source_id)
    Path(source.file_path).unlink(missing_ok=True); db.delete(source); audit(db, user, "source.deleted", "source", str(source_id)); db.commit(); return {"ok": True}

@app.get("/api/v1/sources/{source_id}/schema")
def source_schema(source_id: int, user: User = Depends(current_user), db: DBSession = Depends(get_db)):
    source = owned_source(db, user, source_id)
    try: return {"source_id": source.id, "source": source.name, "kind": source.kind, "tables": inspect_schema(source.kind, Path(source.file_path))}
    except (ValueError, OSError) as exc: raise HTTPException(422, str(exc))

@app.post("/api/v1/sources/{source_id}/scan")
def run_scan(source_id: int, sample_limit: int = Query(default=SAMPLE_ROWS, ge=1, le=5000), user: User = Depends(csrf), db: DBSession = Depends(get_db)):
    need_role(user, {"organization_admin", "analyst"}); source = owned_source(db, user, source_id)
    active_classes = enabled_classes_for(db, user)
    scan = Scan(organization_id=user.organization_id, source_id=source.id, status="running", rule_version=RULE_VERSION, enabled_classes=sorted(active_classes)); db.add(scan); db.flush()
    try:
        records, rows, columns = scan_source(source.kind, Path(source.file_path), sample_rows=sample_limit, enabled_classes=active_classes); scan.rows_sampled = rows; scan.inspected_columns = columns
        for item in records: db.add(Finding(organization_id=user.organization_id, scan_id=scan.id, source_id=source.id, **item))
        scan.status = "completed"
    except (ValueError, OSError) as exc:
        scan.status = "failed"; scan.error_message = str(exc)
    audit(db, user, "scan.completed" if scan.status == "completed" else "scan.failed", "scan", str(scan.id)); db.commit()
    return {"id": scan.id, "status": scan.status, "inspected_columns": scan.inspected_columns, "rows_sampled": scan.rows_sampled,
            "findings": len(records) if scan.status == "completed" else 0, "enabled_classes": scan.enabled_classes, "error": scan.error_message}

@app.get("/api/v1/scans")
def list_scans(user: User = Depends(current_user), db: DBSession = Depends(get_db)):
    scans = db.scalars(select(Scan).where(Scan.organization_id == user.organization_id).order_by(Scan.created_at.desc()).limit(100)).all()
    output = []
    for s in scans:
        findings_count = db.scalar(select(func.count(Finding.id)).where(Finding.scan_id == s.id)) or 0
        src = db.get(Source, s.source_id)
        output.append({
            "id": s.id,
            "source_id": s.source_id,
            "source_name": src.name if src else "Removed source",
            "status": s.status,
            "inspected_columns": s.inspected_columns,
            "rows_sampled": s.rows_sampled,
            "rule_version": s.rule_version,
            "enabled_classes": s.enabled_classes,
            "findings_count": findings_count,
            "error_message": s.error_message,
            "created_at": s.created_at.isoformat(),
        })
    return output

@app.get("/api/v1/scans/{scan_id}")
def get_scan(scan_id: int, user: User = Depends(current_user), db: DBSession = Depends(get_db)):
    scan = db.scalar(select(Scan).where(Scan.id == scan_id, Scan.organization_id == user.organization_id))
    if not scan: raise HTTPException(404, "Scan record not found.")
    src = db.get(Source, scan.source_id)
    findings = db.scalars(select(Finding).where(Finding.scan_id == scan.id)).all()
    return {
        "id": scan.id,
        "source_id": scan.source_id,
        "source_name": src.name if src else "Removed source",
        "status": scan.status,
        "inspected_columns": scan.inspected_columns,
        "rows_sampled": scan.rows_sampled,
        "rule_version": scan.rule_version,
        "enabled_classes": scan.enabled_classes,
        "error_message": scan.error_message,
        "created_at": scan.created_at.isoformat(),
        "findings": [finding_json(f, src) for f in findings],
    }

def finding_json(f: Finding, source: Source | None, mapping: MetadataMapping | None = None):
    return {"id": f.id, "scan_id": f.scan_id, "source_id": f.source_id, "source": source.name if source else "Removed source", "table_name": f.table_name, "column_name": f.column_name, "data_class": f.data_class, "class_name": CLASSES.get(f.data_class, f.data_class), "confidence": f.confidence, "rule_id": f.rule_id, "evidence": f.evidence, "review_status": f.review_status, "review_note": f.review_note, "purpose": mapping.purpose if mapping else "", "retention": mapping.retention if mapping else "", "created_at": f.created_at.isoformat()}

@app.get("/api/v1/findings")
def list_findings(status: str | None = None, q: str | None = None, user: User = Depends(current_user), db: DBSession = Depends(get_db)):
    query = select(Finding).where(Finding.organization_id == user.organization_id).order_by(Finding.created_at.desc()).limit(500)
    if status: query = query.where(Finding.review_status == status)
    values = db.scalars(query).all(); output = []
    for finding in values:
        if q and q.casefold() not in f"{finding.column_name} {finding.table_name} {finding.data_class}".casefold(): continue
        source = db.get(Source, finding.source_id)
        mapping = db.scalar(select(MetadataMapping).where(MetadataMapping.organization_id == user.organization_id, MetadataMapping.source_id == finding.source_id, MetadataMapping.table_name == finding.table_name, MetadataMapping.column_name == finding.column_name))
        output.append(finding_json(finding, source, mapping))
    return output

@app.post("/api/v1/findings/{finding_id}/review")
def review(finding_id: int, payload: ReviewInput, user: User = Depends(csrf), db: DBSession = Depends(get_db)):
    need_role(user, {"organization_admin", "analyst", "reviewer"})
    finding = db.scalar(select(Finding).where(Finding.id == finding_id, Finding.organization_id == user.organization_id))
    if not finding: raise HTTPException(404, "Finding not found.")
    if payload.decision not in {"confirmed", "rejected", "uncertain"}: raise HTTPException(400, "Choose confirmed, rejected, or uncertain.")
    if payload.reclassify and payload.reclassify not in CLASSES: raise HTTPException(400, "Unknown data class.")
    if payload.decision != "uncertain" and len(payload.note.strip()) < 4: raise HTTPException(400, "Add a short review note to support this decision.")
    finding.review_status = payload.decision; finding.review_note = payload.note.strip()
    if payload.reclassify: finding.data_class = payload.reclassify
    db.add(ReviewEvent(organization_id=user.organization_id, finding_id=finding.id, user_id=user.id, decision=payload.decision, note=payload.note.strip()))
    audit(db, user, "finding.reviewed", "finding", str(finding_id)); db.commit(); return {"ok": True}

@app.get("/api/v1/findings/{finding_id}/history")
def review_history(finding_id: int, user: User = Depends(current_user), db: DBSession = Depends(get_db)):
    finding = db.scalar(select(Finding).where(Finding.id == finding_id, Finding.organization_id == user.organization_id))
    if not finding: raise HTTPException(404, "Finding not found.")
    events = db.scalars(select(ReviewEvent).where(ReviewEvent.finding_id == finding_id, ReviewEvent.organization_id == user.organization_id).order_by(ReviewEvent.created_at.desc())).all()
    return [{"decision": e.decision, "note": e.note, "user_id": e.user_id, "created_at": e.created_at.isoformat()} for e in events]

@app.get("/api/v1/metadata")
def list_metadata(user: User = Depends(current_user), db: DBSession = Depends(get_db)):
    values = db.scalars(select(MetadataMapping).where(MetadataMapping.organization_id == user.organization_id).order_by(MetadataMapping.created_at.desc())).all()
    return [{"id": x.id, "source_id": x.source_id, "source": db.get(Source, x.source_id).name if db.get(Source, x.source_id) else "Removed source", "table_name": x.table_name, "column_name": x.column_name, "purpose": x.purpose, "retention": x.retention} for x in values]

@app.post("/api/v1/metadata")
def save_metadata(payload: MappingInput, user: User = Depends(csrf), db: DBSession = Depends(get_db)):
    need_role(user, {"organization_admin", "analyst"}); source = owned_source(db, user, payload.source_id)
    found = db.scalar(select(MetadataMapping).where(MetadataMapping.organization_id == user.organization_id, MetadataMapping.source_id == source.id, MetadataMapping.table_name == payload.table_name, MetadataMapping.column_name == payload.column_name))
    if found: found.purpose = payload.purpose.strip(); found.retention = payload.retention.strip()
    else: db.add(MetadataMapping(organization_id=user.organization_id, source_id=source.id, table_name=payload.table_name, column_name=payload.column_name, purpose=payload.purpose.strip(), retention=payload.retention.strip()))
    audit(db, user, "metadata.saved", "source", str(source.id)); db.commit(); return {"ok": True}

@app.get("/api/v1/rules")
def list_rules(user: User = Depends(current_user), db: DBSession = Depends(get_db)):
    active_classes = enabled_classes_for(db, user)
    return {
        "version": RULE_VERSION,
        "classes": CLASSES,
        "descriptions": CLASS_DESCRIPTIONS,
        "not_personal_data": NOT_PERSONAL_DATA,
        "enabled_classes": sorted(active_classes),
        "rules": [{**rule, "enabled": rule["data_class"] in active_classes} for rule in RULES_CATALOG],
    }

@app.put("/api/v1/rules/config")
def update_rule_configuration(payload: RuleConfigurationInput, user: User = Depends(csrf), db: DBSession = Depends(get_db)):
    unknown = set(payload.enabled_classes) - set(CLASSES)
    if unknown:
        raise HTTPException(400, f"Unknown class code(s): {', '.join(sorted(unknown))}.")
    enabled = list(dict.fromkeys(payload.enabled_classes))
    if not enabled:
        raise HTTPException(400, "Enable at least one class rule.")
    config = db.scalar(select(RuleConfiguration).where(RuleConfiguration.organization_id == user.organization_id))
    if config:
        config.enabled_classes = enabled
    else:
        config = RuleConfiguration(organization_id=user.organization_id, enabled_classes=enabled)
        db.add(config)
    audit(db, user, "rules.configured", "rule_configuration", str(user.organization_id))
    db.commit()
    return {"enabled_classes": enabled, "version": RULE_VERSION}

@app.post("/api/v1/rules/test")
def test_rule(payload: RuleTestInput, user: User = Depends(current_user), db: DBSession = Depends(get_db)):
    col = payload.column_name.strip()
    vals = [payload.sample_value.strip()] if payload.sample_value.strip() else []
    matches = classify(col, vals, enabled_classes_for(db, user))
    return {
        "column_name": col,
        "sample_value": payload.sample_value,
        "matches": matches,
        "matched": len(matches) > 0,
        "label": CLASSES[matches[0]["data_class"]] if matches else NOT_PERSONAL_DATA,
        "details": [
            {
                "data_class": m["data_class"],
                "class_name": CLASSES.get(m["data_class"], m["data_class"]),
                "confidence": m["confidence"],
                "rule_id": m["rule_id"],
                "evidence": m["evidence"],
            }
            for m in matches
        ],
    }

@app.get("/api/v1/evidence-gaps")
def evidence_gaps(user: User = Depends(current_user), db: DBSession = Depends(get_db)):
    org = user.organization_id
    findings = db.scalars(select(Finding).where(Finding.organization_id == org)).all()
    mappings = {
        (m.source_id, m.table_name, m.column_name): m
        for m in db.scalars(select(MetadataMapping).where(MetadataMapping.organization_id == org)).all()
    }
    
    missing_purpose = []
    missing_retention = []
    pending_review = []
    
    for f in findings:
        source = db.get(Source, f.source_id)
        source_name = source.name if source else "Removed source"
        mapping = mappings.get((f.source_id, f.table_name, f.column_name))
        has_purpose = bool(mapping and mapping.purpose.strip())
        has_retention = bool(mapping and mapping.retention.strip())
        
        item = {
            "id": f.id,
            "source_id": f.source_id,
            "source_name": source_name,
            "table_name": f.table_name,
            "column_name": f.column_name,
            "data_class": f.data_class,
            "class_name": CLASSES.get(f.data_class, f.data_class),
            "confidence": f.confidence,
            "review_status": f.review_status,
            "purpose": mapping.purpose if mapping else "",
            "retention": mapping.retention if mapping else "",
        }
        
        if not has_purpose:
            missing_purpose.append(item)
        if not has_retention:
            missing_retention.append(item)
        if f.review_status == "pending":
            pending_review.append(item)

    total = len(findings)
    total_checks = total * 2
    gaps_count = len(missing_purpose) + len(missing_retention)
    completeness_score = round(((total_checks - gaps_count) / total_checks * 100), 1) if total_checks > 0 else 100.0

    return {
        "completeness_score": completeness_score,
        "total_findings": total,
        "counts": {
            "missing_purpose": len(missing_purpose),
            "missing_retention": len(missing_retention),
            "pending_review": len(pending_review),
        },
        "missing_purpose": missing_purpose,
        "missing_retention": missing_retention,
        "pending_review": pending_review,
    }

@app.get("/api/v1/evaluation")
def get_evaluation(user: User = Depends(current_user)):
    cases = load_ground_truth()
    eval_result = evaluate_cases(cases)
    return {
        "dataset": "Privexis reproducible synthetic ground truth",
        "synthetic": True,
        "not_personal_data_label": NOT_PERSONAL_DATA,
        "rule_version": RULE_VERSION,
        **eval_result,
    }

@app.post("/api/v1/evaluation/custom")
async def custom_evaluation(file: UploadFile = File(...), user: User = Depends(csrf)):
    content = (await file.read()).decode("utf-8-sig", errors="replace")
    reader = csv.reader(io.StringIO(content))
    header = next(reader, None)
    if not header:
        raise HTTPException(400, "Uploaded CSV file is empty.")
    
    header_lower = [h.strip().lower() for h in header]
    col_idx = header_lower.index("column_name") if "column_name" in header_lower else 0
    val_idx = header_lower.index("sample_value") if "sample_value" in header_lower else (1 if len(header_lower) > 1 else 0)
    label_idx = header_lower.index("true_class") if "true_class" in header_lower else (header_lower.index("label") if "label" in header_lower else (2 if len(header_lower) > 2 else -1))

    cases = []
    for row in reader:
        if not row or not any(row):
            continue
        col = row[col_idx].strip() if col_idx < len(row) else ""
        val = [row[val_idx].strip()] if (val_idx < len(row) and row[val_idx].strip()) else []
        label = row[label_idx].strip().upper() if (label_idx >= 0 and label_idx < len(row) and row[label_idx].strip()) else None
        if label not in CLASSES:
            label = None
        if col:
            cases.append((col, val, label))

    if not cases:
        raise HTTPException(400, "No valid test cases found in uploaded CSV.")

    eval_result = evaluate_cases(cases)
    return {
        "dataset": file.filename or "Custom uploaded evaluation dataset",
        "synthetic": False,
        "rule_version": RULE_VERSION,
        **eval_result,
    }

@app.get("/api/v1/dashboard")
def dashboard(user: User = Depends(current_user), db: DBSession = Depends(get_db)):
    org = user.organization_id
    total_sources = db.scalar(select(func.count(Source.id)).where(Source.organization_id == org)) or 0
    completed_scans = db.scalar(select(func.count(Scan.id)).where(Scan.organization_id == org, Scan.status == "completed")) or 0
    failed_scans = db.scalar(select(func.count(Scan.id)).where(Scan.organization_id == org, Scan.status == "failed")) or 0
    total_findings = db.scalar(select(func.count(Finding.id)).where(Finding.organization_id == org)) or 0
    pending_findings = db.scalar(select(func.count(Finding.id)).where(Finding.organization_id == org, Finding.review_status == "pending")) or 0
    confirmed_findings = db.scalar(select(func.count(Finding.id)).where(Finding.organization_id == org, Finding.review_status == "confirmed")) or 0
    rejected_findings = db.scalar(select(func.count(Finding.id)).where(Finding.organization_id == org, Finding.review_status == "rejected")) or 0
    total_fields = db.scalar(select(func.sum(Scan.inspected_columns)).where(Scan.organization_id == org)) or 0

    mappings = {(m.source_id, m.table_name, m.column_name): m for m in db.scalars(select(MetadataMapping).where(MetadataMapping.organization_id == org)).all()}
    all_findings = db.scalars(select(Finding).where(Finding.organization_id == org)).all()
    missing_purpose = sum(1 for f in all_findings if not (mappings.get((f.source_id, f.table_name, f.column_name)) and mappings.get((f.source_id, f.table_name, f.column_name)).purpose.strip()))
    missing_retention = sum(1 for f in all_findings if not (mappings.get((f.source_id, f.table_name, f.column_name)) and mappings.get((f.source_id, f.table_name, f.column_name)).retention.strip()))

    class_counts = {}
    for code in CLASSES:
        class_counts[code] = sum(1 for f in all_findings if f.data_class == code)

    scans = db.scalars(select(Scan).where(Scan.organization_id == org).order_by(Scan.created_at.desc()).limit(6)).all()
    recent_pending = db.scalars(select(Finding).where(Finding.organization_id == org, Finding.review_status == "pending").order_by(Finding.created_at.desc()).limit(6)).all()

    return {
        "counts": {
            "sources": total_sources,
            "scans": completed_scans,
            "failed_scans": failed_scans,
            "fields_scanned": total_fields,
            "findings": total_findings,
            "pending": pending_findings,
            "confirmed": confirmed_findings,
            "rejected": rejected_findings,
            "missing_purpose": missing_purpose,
            "missing_retention": missing_retention,
        },
        "class_counts": class_counts,
        "recent_scans": [
            {
                "id": s.id,
                "status": s.status,
                "source": db.get(Source, s.source_id).name if db.get(Source, s.source_id) else "Removed source",
                "inspected_columns": s.inspected_columns,
                "rows_sampled": s.rows_sampled,
                "created_at": s.created_at.isoformat(),
            }
            for s in scans
        ],
        "pending_findings": [finding_json(f, db.get(Source, f.source_id)) for f in recent_pending],
        "classes": CLASSES,
    }

@app.get("/api/v1/reports/inventory.csv")
def export_inventory(user: User = Depends(current_user), db: DBSession = Depends(get_db)):
    findings = db.scalars(select(Finding).where(Finding.organization_id == user.organization_id).order_by(Finding.id)).all()
    stream = io.StringIO(); writer = csv.writer(stream); writer.writerow(["source", "table", "column", "class", "confidence", "review_status", "rule", "evidence"])
    def safe_cell(value):
        text = str(value or "")
        return "'" + text if text.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")) else text
    for item in findings:
        source = db.get(Source, item.source_id); writer.writerow([safe_cell(value) for value in [source.name if source else "Removed", item.table_name, item.column_name, item.data_class, item.confidence, item.review_status, item.rule_id, item.evidence]])
    return StreamingResponse(iter([stream.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=privexis-inventory.csv"})

@app.get("/api/v1/reports/gaps.csv")
def export_gaps(user: User = Depends(current_user), db: DBSession = Depends(get_db)):
    findings = db.scalars(select(Finding).where(Finding.organization_id == user.organization_id).order_by(Finding.id)).all()
    mappings = {(m.source_id, m.table_name, m.column_name): m for m in db.scalars(select(MetadataMapping).where(MetadataMapping.organization_id == user.organization_id)).all()}
    stream = io.StringIO(); writer = csv.writer(stream)
    writer.writerow(["Source", "Table", "Column", "Class", "Review Status", "Missing Purpose", "Missing Retention"])
    for f in findings:
        mapping = mappings.get((f.source_id, f.table_name, f.column_name))
        has_p = bool(mapping and mapping.purpose.strip())
        has_r = bool(mapping and mapping.retention.strip())
        if not has_p or not has_r:
            source = db.get(Source, f.source_id)
            writer.writerow([source.name if source else "Removed", f.table_name, f.column_name, f.data_class, f.review_status, "YES" if not has_p else "NO", "YES" if not has_r else "NO"])
    return StreamingResponse(iter([stream.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=privexis-evidence-gaps.csv"})

@app.get("/api/v1/reports/reviews.csv")
def export_reviews(user: User = Depends(current_user), db: DBSession = Depends(get_db)):
    events = db.scalars(select(ReviewEvent).where(ReviewEvent.organization_id == user.organization_id).order_by(ReviewEvent.created_at.desc())).all()
    stream = io.StringIO(); writer = csv.writer(stream)
    writer.writerow(["Event ID", "Finding ID", "User ID", "Decision", "Note", "Timestamp"])
    for e in events:
        writer.writerow([e.id, e.finding_id, e.user_id, e.decision, e.note, e.created_at.isoformat()])
    return StreamingResponse(iter([stream.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=privexis-review-history.csv"})

@app.get("/api/v1/reports/summary.html")
def export_summary_html(user: User = Depends(current_user), db: DBSession = Depends(get_db)):
    org = db.get(Organization, user.organization_id)
    findings = db.scalars(select(Finding).where(Finding.organization_id == user.organization_id)).all()
    scans = db.scalars(select(Scan).where(Scan.organization_id == user.organization_id)).all()
    sources = db.scalars(select(Source).where(Source.organization_id == user.organization_id)).all()
    mappings = { (m.source_id, m.table_name, m.column_name): m for m in db.scalars(select(MetadataMapping).where(MetadataMapping.organization_id == user.organization_id)).all() }
    
    missing_purpose = sum(1 for f in findings if not (mappings.get((f.source_id, f.table_name, f.column_name)) and mappings.get((f.source_id, f.table_name, f.column_name)).purpose.strip()))
    missing_retention = sum(1 for f in findings if not (mappings.get((f.source_id, f.table_name, f.column_name)) and mappings.get((f.source_id, f.table_name, f.column_name)).retention.strip()))
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Privexis - Privacy Evidence Audit Report</title>
<style>
body {{ font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; background: #090B12; color: #F2F4FA; margin: 0; padding: 40px; line-height: 1.6; }}
.header {{ border-bottom: 2px solid #292E3B; padding-bottom: 24px; margin-bottom: 32px; display: flex; justify-content: space-between; align-items: flex-end; }}
.brand {{ font-size: 24px; font-weight: 800; letter-spacing: 0.1em; color: #9B83E8; }}
.sub {{ color: #A1A8B8; font-size: 13px; }}
.grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 32px; }}
.card {{ background: #10131D; border: 1px solid #292E3B; border-radius: 8px; padding: 20px; }}
.card small {{ color: #A1A8B8; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; }}
.card strong {{ display: block; font-size: 28px; margin-top: 8px; color: #F2F4FA; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 16px; font-size: 13px; }}
th, td {{ border-bottom: 1px solid #292E3B; padding: 12px; text-align: left; }}
th {{ background: #171B27; color: #A1A8B8; font-size: 11px; text-transform: uppercase; }}
.chip {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; background: #211D30; color: #C4B4FA; border: 1px solid #4A3C6A; }}
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; }}
.badge-confirmed {{ background: #17231F; color: #9FD0B8; }}
.badge-pending {{ background: #231E18; color: #D4B27A; }}
.badge-rejected {{ background: #25191E; color: #DFA0A4; }}
.disclaimer {{ margin-top: 40px; padding: 16px; border: 1px solid #343140; border-radius: 6px; background: #12151E; color: #A1A8B8; font-size: 12px; }}
@media print {{ body {{ background: #fff; color: #000; padding: 20px; }} .card {{ border-color: #ccc; }} th {{ background: #eee; color: #333; }} }}
</style>
</head>
<body>
<div class="header">
  <div>
    <div class="brand">PRIVEXIS PRIVACY EVIDENCE INTELLIGENCE</div>
    <div class="sub">Organization: {org.name if org else 'Workspace'} &bull; Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</div>
  </div>
  <div style="text-align: right;">
    <button onclick="window.print()" style="background: #9B83E8; color: #10131D; border: 0; padding: 8px 16px; border-radius: 6px; font-weight: bold; cursor: pointer;">Print / Save as PDF</button>
  </div>
</div>

<div class="grid">
  <div class="card"><small>Registered Sources</small><strong>{len(sources)}</strong></div>
  <div class="card"><small>Completed Scans</small><strong>{len(scans)}</strong></div>
  <div class="card"><small>Discovered Candidate Fields</small><strong>{len(findings)}</strong></div>
  <div class="card"><small>Missing Declarations</small><strong>{missing_purpose + missing_retention}</strong></div>
</div>

<h2>Discovered Personal Data Candidates</h2>
<table>
  <thead>
    <tr>
      <th>Source</th>
      <th>Table</th>
      <th>Column Name</th>
      <th>Class</th>
      <th>Confidence</th>
      <th>Review Status</th>
      <th>Purpose</th>
      <th>Retention</th>
    </tr>
  </thead>
  <tbody>
    {''.join(f'<tr><td>{(db.get(Source, f.source_id).name if db.get(Source, f.source_id) else "Removed")}</td><td>{f.table_name or "—"}</td><td><strong>{f.column_name}</strong></td><td><span class="chip">{f.data_class}</span></td><td>{f.confidence}</td><td><span class="badge badge-{f.review_status}">{f.review_status}</span></td><td>{(mappings.get((f.source_id, f.table_name, f.column_name)).purpose if mappings.get((f.source_id, f.table_name, f.column_name)) else "<span style=\'color:#D7AD62;\'>Missing</span>")}</td><td>{(mappings.get((f.source_id, f.table_name, f.column_name)).retention if mappings.get((f.source_id, f.table_name, f.column_name)) else "<span style=\'color:#D7AD62;\'>Missing</span>")}</td></tr>' for f in findings) if findings else '<tr><td colspan="8">No candidate findings recorded.</td></tr>'}
  </tbody>
</table>

<div class="disclaimer">
  <strong>Technical Evidence Notice:</strong> Privexis surfaces candidate fields and declared metadata based on configured technical rules and bounded sampling. Findings are technical indicators requiring human review and do not constitute legal advice, a definitive determination of lawful basis, or certification of regulatory compliance.
</div>
</body>
</html>"""
    return Response(content=html, media_type="text/html")

@app.get("/api/v1/reports/summary.json")
def export_summary(user: User = Depends(current_user), db: DBSession = Depends(get_db)):
    return {"generated_at": datetime.now(timezone.utc).isoformat(), "organization_id": user.organization_id, "synthetic": True, "counts": {"sources": db.scalar(select(func.count(Source.id)).where(Source.organization_id == user.organization_id)) or 0, "findings": db.scalar(select(func.count(Finding.id)).where(Finding.organization_id == user.organization_id)) or 0}, "evaluation": evaluate(), "limitations": ["Findings are technical candidates and require human review.", "This report does not determine legal compliance or lawful basis."]}

@app.post("/api/v1/assistant")
def assistant(payload: dict, user: User = Depends(current_user)):
    question = str(payload.get("question", ""))[:1000].strip()
    if not question:
        raise HTTPException(400, "Enter a question for the assistant.")
    normalized = re.sub(r"[^a-z0-9 ]+", " ", question.lower())
    guidance = [
        (("scan", "upload", "source", "csv", "sqlite", "file"), "To scan a source, open Data Sources, upload a UTF-8 CSV or SQLite file, or choose one of the 10 synthetic samples. Select Add & run scan, or use Start a scan on a registered source. SQLite inputs are opened read-only."),
        (("class", "identity", "contact", "government", "financial", "location", "aadhaar", "pan", "upi"), "Privexis uses five classes: C1 Personal identity (name, date of birth, gender, age); C2 Contact information (email, phone); C3 Government identifiers (Aadhaar, PAN, passport, voter ID, driving licence); C4 Financial information (bank account, IFSC, card number, UPI ID); and C5 Location / address (postal address, PIN code, coordinates). Matches to none are labelled not personal data."),
        (("not personal", "look alike", "lookalike", "order id", "negative"), "A field is labelled not personal data when none of the five class rules match. The evaluation includes look-alikes such as order IDs with long numeric values, so precision can be measured against false positives."),
        (("precision", "recall", "evaluation", "ground truth", "label"), "Evaluation compares predictions to the committed synthetic ground_truth.csv file. Precision is TP / (TP + FP); recall is TP / (TP + FN). The report shows each of the five classes separately and includes negatives; these fixture metrics are not production accuracy claims."),
        (("purpose", "retention", "metadata", "gap", "missing"), "Open Metadata to record an organization's declared purpose and retention for a source field. Evidence Gap Analysis highlights findings that still lack either declaration; the sample metadata template includes deliberately blank fields."),
        (("search", "find", "inventory", "field"), "Use the search box in the top navigation to search features or findings. Finding searches open the inventory and match source, table, field, class, and rule identifiers."),
        (("review", "confirm", "reject", "decision"), "Open the Personal Data Inventory or Evidence Review Center, choose a candidate, and record Confirm, Reject, or Uncertain with a short note. Review history retains the decision trail."),
        (("report", "export", "download", "csv", "json"), "Reports can be downloaded from Reports Center or from the inventory export action. Available exports include the finding inventory, evidence gaps, review history, and a JSON summary."),
        (("privacy", "raw value", "sample value", "store", "security"), "Scans process bounded samples locally on the API. Raw sample values are not stored in finding records; findings keep field identifiers, rule IDs, confidence, and a short evidence summary. Only synthetic samples are included with the project."),
        (("generator", "synthetic", "dataset", "sample"), "The committed backend/data/generate_synthetic_datasets.py script uses a fixed seed to create 10 CSV/SQLite fixtures plus a separate labelled evaluation set. Run it with python -m backend.data.generate_synthetic_datasets."),
    ]
    best = max(guidance, key=lambda item: sum(1 for term in item[0] if term in normalized))
    score = sum(1 for term in best[0] if term in normalized)
    message = best[1] if score else "I can help with starting scans, the five classes, not-personal-data look-alikes, evaluation, search, review, metadata gaps, and exports. Tell me which part you are working on."
    return {"available": True, "mode": "local-guidance", "message": message, "disclaimer": "Local product guidance; no external AI provider is configured."}
