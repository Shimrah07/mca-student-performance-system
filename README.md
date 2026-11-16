# AI-Based Student Performance Prediction & Academic Support System

**Master of Computer Applications (MCA) — 3rd Semester Minor Project**  
**Department of Computer Applications**  
**University Institute of Technology — RGPV (Autonomous), Bhopal**  
**Academic Session:** 2026–27  

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.0-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-8.0-646CFF?logo=vite&logoColor=white)](https://vitejs.dev)
[![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.6+-F7931E?logo=scikitlearn&logoColor=white)](https://scikit-learn.org)
[![Test Suite](https://img.shields.io/badge/Tests-234%20Passed-brightgreen)](docs/TESTING_REPORT.md)
[![Lint](https://img.shields.io/badge/oxlint-0%20warnings-brightgreen)](frontend/)

---

## 1. Executive Summary & Academic Objectives

The **AI-Based Student Performance Prediction & Academic Support System** is an educational data mining and decision-support platform designed specifically for the Master of Computer Applications (MCA) curriculum at UIT-RGPV (Autonomous), Bhopal.

Traditional academic evaluations rely on post-facto semester examinations when it is too late to provide formative assistance. This system enables **early, point-in-time performance forecasting**:
1. **Four-Tier Performance Trajectory**: Evaluates student progress into four actionable categories:
   - **Excellent** ($\ge 8.5\text{ CGPA}$)
   - **Good** ($7.0\text{–}8.4\text{ CGPA}$)
   - **Average** ($5.5\text{–}6.9\text{ CGPA}$)
   - **Needs Improvement** ($< 5.5\text{ CGPA}$)
2. **Dual-Scope Inference Architecture**:
   - **Subject-Level Assessment**: Point-in-time performance prediction for a single registered course using attendance and continuous internal assessments (MST-1, MST-2, assignments, lab records, vivas).
   - **Semester-Level Assessment**: Holistic semester forecast aggregating academic features across all active course registrations and incorporating finalized prior-semester results.
3. **Strict Point-in-Time Temporal Cutoff**: Enforces deterministic temporal boundary timestamps ($t \le t_{\text{cutoff}}$). Snapshots recorded after the cutoff and target-semester final exam marks are strictly excluded to prevent data leakage.
4. **Immutable Audit Persistence**: Every prediction is logged in an append-only MySQL audit repository (`mca_prediction_records`) preserving the exact feature vector, model version, and class probabilities.
5. **Calibrated Synthetic Dataset Training**: Machine learning pipelines were trained on synthetic MCA datasets (6,370 subject records and 1,200 semester records) calibrated to UIT-RGPV academic distributions.

---

## 2. Project Team

| Name | Role / Focus Area | Department & Institution |
|---|---|---|
| **Shimrah Ahmed** | Frontend Architecture, Minimal UI/UX, API Client Integration | MCA, Dept. of Computer Applications, UIT-RGPV Bhopal |
| **Hazra Bano** | Backend Engineering, Database Schema & ORM Architecture | MCA, Dept. of Computer Applications, UIT-RGPV Bhopal |
| **Navashirin Khan** | Machine Learning Pipelines, Feature Adapters & Evaluation | MCA, Dept. of Computer Applications, UIT-RGPV Bhopal |

---

## 3. Technology Stack

| Subsystem | Technology | Purpose & Implementation Details |
|---|---|---|
| **Frontend Client** | React 19, Vite 8, Vanilla CSS | Minimal sidebar navigation, warm ivory canvas (`#F5F6F2`), responsive mobile drawer, animated probability bars. |
| **Backend REST API** | FastAPI, Uvicorn, Pydantic v2 | High-throughput asynchronous API, strict schema validation, dependency injection, and health diagnostic probes. |
| **Database & ORM** | MySQL 8.0, SQLAlchemy 2.0, PyMySQL | 13 approved MCA tables, connection pooling (`pool_pre_ping`), relational foreign key cascades, and revisioned snapshots. |
| **Machine Learning** | Scikit-learn 1.6+, NumPy, Pandas | Dual classification pipelines (Logistic Regression and Random Forest), group-based cross-validation, and `.joblib` serialization. |
| **Testing & QA** | Pytest, Oxlint | 234 automated test cases (144 MCA tests + 90 core/legacy tests), 0 lint errors/warnings. |

---

## 4. Repository Structure

```
AI-Student-Performance-System/
├── docs/                               # Comprehensive Technical Documentation
│   ├── PROJECT_ARCHITECTURE.md         # Component diagrams, data flow & lifecycle
│   ├── DATABASE_DESIGN.md              # 13 MCA tables, schemas, constraints & ER diagram
│   ├── ML_METHODOLOGY.md               # Preprocessing, anti-leakage guards & metrics
│   ├── API_DOCUMENTATION.md            # OpenAPI endpoints, schemas & error handling
│   ├── TESTING_REPORT.md               # Automated test execution results (234 tests) & platform verification
│   ├── DEPLOYMENT_GUIDE.md             # Cloud deployment runbook & production configurations
│   ├── KNOWN_LIMITATIONS.md            # Academic prototype notice & scope boundaries
│   ├── Literature_Survey_...pdf        # Approved Week II literature survey document
│   ├── Week_III_SRS_...pdf             # Approved Week III software requirements specification
│   └── Week_IV_System_Design_...pdf    # Approved Week IV system design report
├── ml/
│   ├── artifacts/mca/                  # Pinned Model Artifacts for Inference
│   │   ├── subject_level_pipeline.joblib   # Logistic Regression pipeline
│   │   ├── subject_level_metadata.json     # Feature names, algorithm metadata
│   │   ├── semester_level_pipeline.joblib  # Random Forest pipeline
│   │   └── semester_level_metadata.json    # Feature names, algorithm metadata
│   ├── data/synthetic/                 # Calibrated Synthetic Datasets (Phase 3A)
│   │   ├── mca_synthetic_subject_level.csv # 6,370 subject rows
│   │   ├── mca_synthetic_semester_level.csv# 1,200 semester rows
│   │   └── README_MCA_SYNTHETIC_DATASET.md # Data calibration documentation
│   └── src/                            # Machine Learning Source Code
│       ├── mca_predictor.py            # Unified model loading & inference service
│       ├── mca_feature_adapter.py      # Schema bridge between Phase 2E and ML input vectors
│       ├── mca_trainer.py              # Training script for dual pipelines
│       ├── mca_dataset_loader.py       # Group-based synthetic dataset loader
│       └── mca_compat.py               # OS environment compatibility stubs
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI application instance, CORS & routers
│   │   ├── config.py                   # Environment settings & masked URL properties
│   │   ├── database.py                 # SQLAlchemy engine, session maker & init_db(mca_only)
│   │   ├── constants/mca_curriculum.py # Canonical 26-course autonomous curriculum catalogue
│   │   ├── models/mca/                 # 13 MCA ORM Models (Programs, Courses, Snapshots, Records)
│   │   ├── schemas/mca.py              # Pydantic v2 validation & response schemas
│   │   ├── services/                   # Feature extraction & prediction persistence
│   │   │   ├── mca_feature_extraction.py   # Point-in-time extraction engine
│   │   │   └── mca_prediction_service.py   # Dual inference orchestration & audit logging
│   │   ├── seeders/                    # Curriculum and Demonstration seeders
│   │   └── routers/                    # Curriculum & prediction endpoint routers
│   ├── tests/                          # Automated backend test suites (234 test cases)
│   ├── requirements.txt                # Pinned Python package dependencies
│   └── .env.example                    # Template environment variables
├── frontend/
│   ├── src/
│   │   ├── components/                 # Minimal Sidebar, TopBar, Dashboard, Forms
│   │   │   ├── Sidebar.jsx             # Persistent left navigation & mobile drawer
│   │   │   ├── TopBar.jsx              # Search pill, breadcrumb & session pill
│   │   │   ├── mca/                    # MCA Overview, Curriculum, Forms & Result Card
│   │   │   └── common/Icons.jsx        # Lightweight SVG icon system
│   │   ├── api/mcaApi.js               # Dedicated backend REST API client
│   │   ├── constants/mcaCurriculum.js  # Offline fallback curriculum data
│   │   ├── App.jsx                     # Master application shell
│   │   ├── App.css                     # Minimal card styling & responsive rules
│   │   └── index.css                   # Global tokens, typography & warm ivory layout
│   ├── package.json                    # Node dependencies & scripts
│   ├── vite.config.js                  # Vite configuration
│   └── .env.example                    # Frontend environment template
├── .gitignore                          # Production-ready gitignore rules
└── README.md                           # Master Project Documentation
```

---

## 5. Canonical MCA Curriculum Roster (26 Courses)

The database and API are initialized with the canonical 26-course autonomous curriculum:
- **Semester 1 (7 courses)**: MCA108 (Operating System), MCA109 (Computer Organization & Architecture), MCA110 (Data Structures), MCA111 (Mathematical Foundations), MCA112 (Elective 1: Cloud/Web), MCA113 (Programming in C Lab), MCA114 (Data Structures Lab).
- **Semester 2 (7 courses)**: DBMS, Software Engineering, Object-Oriented Programming (Java), Analysis & Design of Algorithms, Elective 2, DBMS Lab, Java Lab.
- **Semester 3 (7 courses)**: MCA301 (Computer Networks), MCA302 (Artificial Intelligence), MCA303 (Full Stack Development), MCA304 (Elective 3), MCA305 (Elective 4), MCA306 (Minor Project), MCA307 (Full Stack Lab).
- **Semester 4 (5 courses)**: Major Project, Comprehensive Viva Voce, Technical Seminar, Elective 5, Elective 6.

*Note: In strict compliance with academic honesty, Semesters 1 and 3 use verified course codes from published scheme notifications. Semesters 2 and 4 course codes are marked as `"—"` and credits as `"TBC"` pending university board publication.*

---

## 6. Installation & Local Setup

### 6.1 Prerequisites
- Python 3.11, 3.12, or 3.14
- Node.js 18+ and npm
- MySQL Server 8.0+

### 6.2 Backend Setup
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd AI-Student-Performance-System/backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. Configure environment variables:
   ```bash
   # Copy template
   cp .env.example .env
   ```
   Edit `.env` with your local MySQL credentials:
   ```env
   DB_HOST=localhost
   DB_PORT=3306
   DB_NAME=mca_academic_system
   DB_USER=mca_app
   DB_PASSWORD=your_actual_password
   APP_ENV=development
   ```
5. Initialize database tables and seed curriculum:
   ```bash
   python -m app.seeders.mca_curriculum_seeder
   ```
6. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   API is accessible at `http://127.0.0.1:8000` (Docs: `http://127.0.0.1:8000/docs`).

### 6.3 Frontend Setup
1. Open a separate terminal and navigate to `frontend/`:
   ```bash
   cd AI-Student-Performance-System/frontend
   ```
2. Install packages:
   ```bash
   npm install
   ```
3. Configure environment:
   ```bash
   cp .env.example .env
   # Default: VITE_API_URL=http://localhost:8000
   ```
4. Start the Vite development server:
   ```bash
   npm run dev -- --host 127.0.0.1 --port 5173
   ```
   Application is accessible at `http://127.0.0.1:5173`.

---

## 7. Running the Automated Test Suite

Execute the complete backend test suite:
```bash
cd backend
python -m pytest tests/test_mca_curriculum.py \
                 tests/test_mca_curriculum_api.py \
                 tests/test_mca_curriculum_seeder.py \
                 tests/test_mca_demo_seeder.py \
                 tests/test_mca_feature_extraction_and_persistence.py \
                 tests/test_mca_ml_pipeline.py \
                 tests/test_mca_models.py \
                 tests/test_mca_predictions_api.py -v
```

Execute frontend linting and production build:
```bash
cd frontend
npm run lint    # oxlint: 0 warnings, 0 errors
npm run build   # vite build: 29 modules transformed
```

---

## 8. Academic Integrity & Synthetic Data Disclaimer

> [!WARNING]
> **Prototype Demonstration Notice**: The machine learning models in this system were trained exclusively on synthetic MCA datasets generated to mirror UIT-RGPV grading distributions. They do not contain real student records. Predictions generated by this system are academic prototypes for educational research and must **never** be used for official university grading, disciplinary actions, or administrative decisions.
