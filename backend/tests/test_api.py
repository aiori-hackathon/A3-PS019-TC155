from backend.app.scanner import CLASSES, NOT_PERSONAL_DATA


def workspace(client, key="a" * 64):
    client.headers.update({"X-Workspace-Key": key})
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 200
    client.headers.update({"X-CSRF-Token": response.json()["csrf_token"]})
    return response.json()


def test_guest_workspace_upload_scan_and_rules(client):
    me = workspace(client)
    assert me["full_name"] == "Local workspace"
    uploaded = client.post("/api/v1/sources/upload", files={"file": ("synthetic.csv", b"email,age,order_id\nperson@example.invalid,29,202610310001\n", "text/csv")})
    assert uploaded.status_code == 200, uploaded.text
    source_id = uploaded.json()["id"]
    scan = client.post(f"/api/v1/sources/{source_id}/scan?sample_limit=1")
    assert scan.status_code == 200 and scan.json()["status"] == "completed"
    assert scan.json()["rows_sampled"] == 1
    findings = client.get("/api/v1/findings").json()
    assert {item["data_class"] for item in findings} == {"C1", "C2"}
    assert all("person@example.invalid" not in item["evidence"] for item in findings)
    rules = client.get("/api/v1/rules").json()
    assert rules["classes"] == CLASSES
    assert rules["not_personal_data"] == NOT_PERSONAL_DATA
    tested = client.post("/api/v1/rules/test", json={"column_name": "contact_email", "sample_value": "user@privexis.io"})
    assert tested.status_code == 200 and tested.json()["matches"][0]["data_class"] == "C2"
    negative = client.post("/api/v1/rules/test", json={"column_name": "order_id", "sample_value": "202610310001"})
    assert negative.status_code == 200 and negative.json()["label"] == NOT_PERSONAL_DATA


def test_workspace_isolation_and_removed_account_routes(client):
    workspace(client, "a" * 64)
    first = client.post("/api/v1/sources/upload", files={"file": ("x.csv", b"order_id\nSYN-1\n", "text/csv")})
    assert first.status_code == 200
    client.headers["X-Workspace-Key"] = "b" * 64
    assert client.get("/api/v1/sources").json() == []
    token = client.get("/api/v1/auth/me").json()["csrf_token"]
    client.headers["X-CSRF-Token"] = token
    assert client.delete(f"/api/v1/sources/{first.json()['id']}").status_code == 404
    assert client.post("/api/v1/auth/login", json={}).status_code == 404
    assert client.post("/api/v1/auth/signup", json={}).status_code == 404
    assert client.get("/api/v1/demo/accounts").status_code == 404


def test_all_ten_samples_load_and_scan(client):
    workspace(client)
    samples = client.get("/api/v1/samples").json()
    assert len(samples) == 10
    assert {sample["kind"] for sample in samples} == {"csv", "sqlite"}
    assert {sample["class_code"] for sample in samples} == set(CLASSES)
    for sample in samples:
        loaded = client.post(f"/api/v1/samples/{sample['id']}/load")
        assert loaded.status_code == 200, loaded.text
        result = client.post(f"/api/v1/sources/{loaded.json()['id']}/scan?sample_limit=20")
        assert result.status_code == 200 and result.json()["status"] == "completed", result.text
        assert result.json()["findings"] >= 1


def test_assistant_and_evaluation_routes(client):
    workspace(client)
    answer = client.post("/api/v1/assistant", json={"question": "What are the five classes?"})
    assert answer.status_code == 200 and all(label in answer.json()["message"] for label in CLASSES)
    metrics = client.get("/api/v1/evaluation").json()
    assert metrics["sample_count"] >= 150
    assert metrics["not_personal_data_label"] == NOT_PERSONAL_DATA
    assert {row["class_code"] for row in metrics["classes"]} == set(CLASSES)


def test_configurable_rule_checklist_persists_and_controls_scans(client):
    workspace(client, "c" * 64)
    defaults = client.get("/api/v1/rules").json()
    assert set(defaults["enabled_classes"]) == set(CLASSES)
    saved = client.put("/api/v1/rules/config", json={"enabled_classes": ["C2"]})
    assert saved.status_code == 200
    assert saved.json()["enabled_classes"] == ["C2"]
    assert client.get("/api/v1/rules").json()["enabled_classes"] == ["C2"]
    assert client.put("/api/v1/rules/config", json={"enabled_classes": ["C6"]}).status_code == 400

    tester = client.post("/api/v1/rules/test", json={"column_name": "date_of_birth", "sample_value": "2001-01-01"})
    assert tester.status_code == 200 and tester.json()["label"] == NOT_PERSONAL_DATA
    upload = client.post("/api/v1/sources/upload", files={"file": ("configurable.csv", b"email,date_of_birth\\nperson@example.invalid,2001-01-01\\n", "text/csv")})
    assert upload.status_code == 200
    scan = client.post(f"/api/v1/sources/{upload.json()['id']}/scan?sample_limit=10")
    assert scan.status_code == 200 and scan.json()["status"] == "completed"
    assert scan.json()["enabled_classes"] == ["C2"]
    findings = client.get("/api/v1/findings").json()
    assert {finding["data_class"] for finding in findings} == {"C2"}


def test_metadata_mapping_and_evidence_gap_workflow(client):
    workspace(client, "d" * 64)
    sample = next(item for item in client.get("/api/v1/samples").json() if item["id"] == "contact_information-csv")
    loaded = client.post(f"/api/v1/samples/{sample['id']}/load")
    assert loaded.status_code == 200
    scanned = client.post(f"/api/v1/sources/{loaded.json()['id']}/scan?sample_limit=20")
    assert scanned.status_code == 200
    finding = next(item for item in client.get("/api/v1/findings").json() if item["column_name"] == "email")
    mapped = client.post("/api/v1/metadata", json={"source_id": loaded.json()["id"], "table_name": "", "column_name": "email", "purpose": "Synthetic evaluation", "retention": ""})
    assert mapped.status_code == 200
    gaps = client.get("/api/v1/evidence-gaps").json()
    assert any(item["id"] == finding["id"] for item in gaps["missing_retention"])
    assert not any(item["id"] == finding["id"] for item in gaps["missing_purpose"])
    reviewed = client.post(f"/api/v1/findings/{finding['id']}/review", json={"decision": "confirmed", "note": "Verified synthetic fixture field."})
    assert reviewed.status_code == 200
    history = client.get(f"/api/v1/findings/{finding['id']}/history").json()
    assert history and history[0]["decision"] == "confirmed"
