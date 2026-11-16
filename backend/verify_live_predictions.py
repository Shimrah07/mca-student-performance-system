"""
backend/verify_live_predictions.py

Phase 4.6 — Live HTTP Verification of MCA FastAPI Prediction and History Endpoints.
Starts the FastAPI server, sends HTTP requests over localhost:8000, verifies
persistence in MySQL mca_prediction_records, and gracefully shuts down.
"""

import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error

API_BASE = "http://127.0.0.1:8000"
CUTOFF_TIMESTAMP = "2025-09-20T00:00:00Z"


def make_request(method: str, path: str, data: dict = None) -> tuple[int, dict]:
    url = f"{API_BASE}{path}"
    headers = {"Content-Type": "application/json"} if data else {}
    body = json.dumps(data).encode("utf-8") if data else None

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            status_code = response.status
            resp_body = json.loads(response.read().decode("utf-8"))
            return status_code, resp_body
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8")
        try:
            return exc.code, json.loads(err_body)
        except Exception:
            return exc.code, {"raw": err_body}
    except Exception as exc:
        return 0, {"error": str(exc)}


def main():
    print("=" * 70)
    print("PHASE 4.6 — LIVE PREDICTION API HTTP VERIFICATION")
    print("=" * 70)

    # 1. Start uvicorn server as a subprocess
    python_exe = sys.executable
    cmd = [python_exe, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"]
    print(f"Starting server: {' '.join(cmd)}")
    server_proc = subprocess.Popen(
        cmd,
        cwd=os.path.dirname(os.path.abspath(__file__)),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        # 2. Wait for server to become responsive
        print("Waiting for server to become healthy...")
        started = False
        for attempt in range(30):
            time.sleep(1)
            code, resp = make_request("GET", "/health")
            if code == 200 and resp.get("status") == "ok":
                print(f"Server is ready! (attempt {attempt+1})")
                started = True
                break

        if not started:
            print("Server failed to start in time. Checking stderr:")
            server_proc.terminate()
            stdout, stderr = server_proc.communicate(timeout=5)
            print("STDOUT:", stdout.decode("utf-8", errors="replace"))
            print("STDERR:", stderr.decode("utf-8", errors="replace"))
            sys.exit(1)

        # 3. Check health and DB
        print("\n--- 1. Health Checks ---")
        code, health = make_request("GET", "/health")
        print(f"GET /health: {code} -> {health}")

        code, health_db = make_request("GET", "/health/db")
        print(f"GET /health/db: {code} -> {health_db}")
        assert code == 200 and health_db.get("database_connected") is True

        code, curr = make_request("GET", "/api/mca/curriculum")
        print(f"GET /api/mca/curriculum: {code} -> Program: {curr.get('program_code')}, Total Semesters: {curr.get('total_semesters')}")
        assert code == 200

        # 4. Subject-Level Predictions
        print("\n--- 2. Subject-Level Predictions ---")
        # Student A (registration 1: MCA108)
        payload_subj_a = {
            "registration_id": 1,
            "student_id": 1,
            "cutoff_timestamp": CUTOFF_TIMESTAMP,
        }
        code_subj_a, resp_subj_a = make_request("POST", "/api/mca/predictions/subject", payload_subj_a)
        print(f"POST /api/mca/predictions/subject (Student A): {code_subj_a}")
        print(f"  Prediction ID : {resp_subj_a.get('prediction_id')}")
        print(f"  Course        : {resp_subj_a.get('course_code')} ({resp_subj_a.get('course_name')})")
        print(f"  Predicted Tier: {resp_subj_a.get('predicted_tier')}")
        print(f"  Confidence    : {resp_subj_a.get('confidence')}")
        print(f"  Model Name    : {resp_subj_a.get('model_name')}")
        print(f"  Probabilities : {resp_subj_a.get('probabilities')}")
        assert code_subj_a == 200
        pred_id_subj_a = resp_subj_a["prediction_id"]

        # Student B (registration 5: MCA108)
        payload_subj_b = {
            "registration_id": 5,
            "student_id": 2,
            "cutoff_timestamp": CUTOFF_TIMESTAMP,
        }
        code_subj_b, resp_subj_b = make_request("POST", "/api/mca/predictions/subject", payload_subj_b)
        print(f"\nPOST /api/mca/predictions/subject (Student B): {code_subj_b}")
        print(f"  Prediction ID : {resp_subj_b.get('prediction_id')}")
        print(f"  Course        : {resp_subj_b.get('course_code')} ({resp_subj_b.get('course_name')})")
        print(f"  Predicted Tier: {resp_subj_b.get('predicted_tier')}")
        print(f"  Confidence    : {resp_subj_b.get('confidence')}")
        print(f"  Model Name    : {resp_subj_b.get('model_name')}")
        print(f"  Probabilities : {resp_subj_b.get('probabilities')}")
        assert code_subj_b == 200
        pred_id_subj_b = resp_subj_b["prediction_id"]

        # 5. Semester-Level Predictions
        print("\n--- 3. Semester-Level Predictions ---")
        # Student A (student_id 1, sem 1)
        payload_sem_a = {
            "student_id": 1,
            "target_semester": 1,
            "cutoff_timestamp": CUTOFF_TIMESTAMP,
        }
        code_sem_a, resp_sem_a = make_request("POST", "/api/mca/predictions/semester", payload_sem_a)
        print(f"POST /api/mca/predictions/semester (Student A): {code_sem_a}")
        print(f"  Prediction ID : {resp_sem_a.get('prediction_id')}")
        print(f"  Target Sem    : {resp_sem_a.get('target_semester')}")
        print(f"  Predicted Tier: {resp_sem_a.get('predicted_tier')}")
        print(f"  Confidence    : {resp_sem_a.get('confidence')}")
        print(f"  Model Name    : {resp_sem_a.get('model_name')}")
        print(f"  Probabilities : {resp_sem_a.get('probabilities')}")
        assert code_sem_a == 200
        pred_id_sem_a = resp_sem_a["prediction_id"]

        # Student B (student_id 2, sem 1)
        payload_sem_b = {
            "student_id": 2,
            "target_semester": 1,
            "cutoff_timestamp": CUTOFF_TIMESTAMP,
        }
        code_sem_b, resp_sem_b = make_request("POST", "/api/mca/predictions/semester", payload_sem_b)
        print(f"\nPOST /api/mca/predictions/semester (Student B): {code_sem_b}")
        print(f"  Prediction ID : {resp_sem_b.get('prediction_id')}")
        print(f"  Target Sem    : {resp_sem_b.get('target_semester')}")
        print(f"  Predicted Tier: {resp_sem_b.get('predicted_tier')}")
        print(f"  Confidence    : {resp_sem_b.get('confidence')}")
        print(f"  Model Name    : {resp_sem_b.get('model_name')}")
        print(f"  Probabilities : {resp_sem_b.get('probabilities')}")
        assert code_sem_b == 200
        pred_id_sem_b = resp_sem_b["prediction_id"]

        # 6. Retrieve Predictions by ID
        print("\n--- 4. Prediction History by ID ---")
        for pid in [pred_id_subj_a, pred_id_subj_b, pred_id_sem_a, pred_id_sem_b]:
            code, resp = make_request("GET", f"/api/mca/predictions/{pid}")
            print(f"GET /api/mca/predictions/{pid}: {code} -> Tier: {resp.get('predicted_tier')}, Scope: {resp.get('scope')}, Student: {resp.get('student_id')}")
            assert code == 200

        # 7. List Predictions by Student
        print("\n--- 5. Predictions by Student ---")
        code, st_a_preds = make_request("GET", "/api/mca/predictions/student/1")
        print(f"GET /api/mca/predictions/student/1: {code} -> {len(st_a_preds)} records retrieved")
        assert code == 200 and len(st_a_preds) >= 2

        code, st_b_preds = make_request("GET", "/api/mca/predictions/student/2")
        print(f"GET /api/mca/predictions/student/2: {code} -> {len(st_b_preds)} records retrieved")
        assert code == 200 and len(st_b_preds) >= 2

        # 8. Direct MySQL Persistence Verification
        print("\n--- 6. Direct MySQL Database Persistence Verification ---")
        from app.database import SessionLocal
        from app.models import MCAPredictionRecord
        db = SessionLocal()
        persisted_records = db.query(MCAPredictionRecord).order_by(MCAPredictionRecord.id.asc()).all()
        print(f"Total rows in MySQL mca_prediction_records: {len(persisted_records)}")
        for r in persisted_records:
            print(f"  Row {r.id}: Student={r.student_id}, Reg={r.registration_id}, Course={r.course_id}, Tier={r.predicted_tier}, Model={r.model_name}, Cutoff={r.cutoff_timestamp.isoformat()}")
        db.close()
        assert len(persisted_records) == 4

        print("\n" + "=" * 70)
        print("ALL LIVE HTTP PREDICTION AND AUDIT VERIFICATIONS PASSED SUCCESSFULLY!")
        print("=" * 70)

    finally:
        print("Shutting down FastAPI server...")
        server_proc.terminate()
        try:
            server_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_proc.kill()
        print("FastAPI server stopped.")


if __name__ == "__main__":
    main()
