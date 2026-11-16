# FastAPI REST API Documentation

**Base URL:** `http://localhost:8000` (Local Development)  
**API Specification:** OpenAPI 3.1.0 (`/openapi.json`)  
**Interactive Docs:** Swagger UI (`/docs`), ReDoc (`/redoc`)  

---

## 1. System Endpoints

### 1.1 Application Health Check
- **Endpoint:** `GET /health`
- **Summary:** Verify API service operational readiness.
- **Response (200 OK):**
```json
{
  "status": "ok",
  "message": "API is running",
  "environment": "development"
}
```

### 1.2 Database Connectivity Check
- **Endpoint:** `GET /health/db`
- **Summary:** Verify MySQL engine connectivity with credential masking.
- **Response (200 OK):**
```json
{
  "database_connected": true,
  "message": "Database connection successful",
  "database_url": "mysql+pymysql://mca_app:***@localhost:3306/mca_academic_system"
}
```

---

## 2. Curriculum Endpoints

### 2.1 Complete Curriculum Catalogue
- **Endpoint:** `GET /api/mca/curriculum`
- **Summary:** Retrieve all 4 semesters and 26 canonical courses.
- **Response (200 OK):**
```json
{
  "program": {
    "program_code": "MCA",
    "program_name": "Master of Computer Applications",
    "duration_semesters": 4
  },
  "semesters": [
    {
      "semester_number": 1,
      "academic_focus": "Foundations of Computing, Systems & Core Programming",
      "courses": [
        {
          "course_code": "MCA108",
          "course_name": "Operating System",
          "course_type": "theory",
          "credits": 4,
          "elective_group": null,
          "is_code_verified": true
        }
      ]
    }
  ]
}
```

### 2.2 Semester-Specific Roster
- **Endpoint:** `GET /api/mca/semesters/{semester_number}`
- **Parameters:** `semester_number` (Path, integer, 1 to 4).
- **Responses:**
  - `200 OK`: Single-semester curriculum object.
  - `404 Not Found`: If `semester_number` < 1 or > 4.
```json
{
  "detail": "Semester 5 not found. Valid MCA semesters are 1 through 4."
}
```

---

## 3. Prediction & Audit Endpoints

### 3.1 Subject-Level Prediction
- **Endpoint:** `POST /api/mca/predictions/subject`
- **Request Body (`McaSubjectPredictionApiRequest`):**
```json
{
  "registration_id": 1,
  "cutoff_timestamp": "2025-09-20T00:00:00Z",
  "student_id": 1
}
```
- **Validation Rules:**
  - `registration_id`: Positive integer (required).
  - `cutoff_timestamp`: ISO 8601 datetime (required).
  - `student_id`: Optional positive integer; validated against registration ownership.
- **Response (200 OK):**
```json
{
  "prediction_id": 1,
  "scope": "subject",
  "student_id": 1,
  "registration_id": 1,
  "course_id": 1,
  "course_code": "MCA108",
  "course_name": "Operating System",
  "target_semester": 1,
  "predicted_tier": "Good",
  "confidence": 0.5895,
  "probabilities": {
    "Excellent": 0.1245,
    "Good": 0.5895,
    "Average": 0.2104,
    "Needs Improvement": 0.0756
  },
  "cutoff_timestamp": "2025-09-20T00:00:00",
  "model_name": "mca_subject_logistic_regression",
  "model_version": "1.0.0",
  "synthetic_data_warning": "WARNING: This prediction was produced by a prototype model trained exclusively on synthetic data (Phase 3A). It must NOT be used for actual academic decisions.",
  "created_at": "2026-11-16T10:45:00"
}
```

### 3.2 Semester-Level Prediction
- **Endpoint:** `POST /api/mca/predictions/semester`
- **Request Body (`McaSemesterPredictionApiRequest`):**
```json
{
  "student_id": 1,
  "target_semester": 1,
  "cutoff_timestamp": "2025-09-20T00:00:00Z"
}
```
- **Response (200 OK):**
```json
{
  "prediction_id": 3,
  "scope": "semester",
  "student_id": 1,
  "registration_id": null,
  "course_id": null,
  "course_code": null,
  "course_name": null,
  "target_semester": 1,
  "predicted_tier": "Excellent",
  "confidence": 0.7410,
  "probabilities": {
    "Excellent": 0.7410,
    "Good": 0.1850,
    "Average": 0.0520,
    "Needs Improvement": 0.0220
  },
  "cutoff_timestamp": "2025-09-20T00:00:00",
  "model_name": "mca_semester_random_forest",
  "model_version": "1.0.0",
  "created_at": "2026-11-16T10:45:00"
}
```

### 3.3 Get Prediction Audit Record by ID
- **Endpoint:** `GET /api/mca/predictions/{prediction_id}`
- **Responses:**
  - `200 OK`: Full persisted prediction record including `input_snapshot_json`.
  - `404 Not Found`: If `prediction_id` does not exist.

### 3.4 List Student Prediction History
- **Endpoint:** `GET /api/mca/predictions/student/{student_id}?limit=50`
- **Parameters:** `student_id` (Path, integer), `limit` (Query, integer, default 50).
- **Response (200 OK):** Array of historical prediction records ordered newest first.

---

## 4. Error Status Codes & Responses

| Status Code | Meaning | Example Condition |
|---|---|---|
| **404 Not Found** | Target entity missing | `registration_id` or `prediction_id` not found in database |
| **422 Unprocessable Content** | Input validation failure | Missing required fields, cutoff in future, or zero eligible snapshots |
| **500 Internal Server Error** | System or persistence fault | Database transaction failure during audit logging |
| **503 Service Unavailable** | External dependency offline | MySQL connection refused, or model `.joblib` file missing |
