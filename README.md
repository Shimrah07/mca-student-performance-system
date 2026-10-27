# AI-Based Student Performance Prediction & Academic Support System

**MCA 3rd Semester Minor Project**
Department of Computer Applications, UIT-RGPV (Autonomous), Bhopal
Academic Session: 2026–27

---

## Project Overview

A web-based application that uses machine learning to:

1. Predict a student's overall performance category — **Excellent, Good, Average, or Needs Improvement**
2. Identify weak academic areas (subject-wise or factor-wise)
3. Generate supportive, rule-based academic recommendations

The system integrates a React frontend, a FastAPI backend, a MySQL database, and a trained Scikit-learn model. Model training and evaluation are done offline; the deployed application only loads the saved model to make predictions.

> **Important:** This system provides model-based estimates and supportive guidance only. It does not guarantee future marks, diagnose students, or replace teachers.

---

## Team

| Name | Role |
|---|---|
| Shimrah Ahmed | (TBD) |
| Hazra Bano | (TBD) |
| Navashirin Khan | (TBD) |

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React.js (Vite), HTML, CSS, JavaScript |
| Backend / API | FastAPI (Python) |
| Machine Learning | Scikit-learn |
| Data Processing | Pandas, NumPy |
| Database | MySQL with SQLAlchemy |
| Charts | Recharts or Chart.js |
| Development | Antigravity, Git & GitHub |
| Deployment | Cloud hosting (provider TBD) |

---

## Project Structure

```
AI-Student-Performance-System/
├── docs/               # Approved reference documents (do not modify)
├── ml/
│   ├── notebooks/      # Jupyter notebooks: EDA, training, evaluation (offline)
│   ├── data/           # Dataset files — gitignored (may contain private data)
│   └── models/         # Saved model + preprocessing pipeline — gitignored
├── backend/
│   ├── app/
│   │   ├── main.py     # FastAPI entry point
│   │   ├── config.py   # Settings from environment variables
│   │   ├── database.py # SQLAlchemy engine and session
│   │   ├── routers/    # API route definitions
│   │   ├── models/     # SQLAlchemy ORM table definitions
│   │   ├── schemas/    # Pydantic request/response schemas
│   │   └── services/   # Business logic (prediction, weak-area, recommendations)
│   ├── .env.example    # Template for required environment variables
│   └── requirements.txt
└── frontend/           # React application (Vite)
    └── src/
        ├── pages/      # Page-level components
        ├── components/ # Reusable UI components
        └── api/        # HTTP calls to the backend
```

---

## Local Development Setup

### Prerequisites

- Python 3.14+
- Node.js v18+
- MySQL 8+ (running locally or remote)
- Git

### 1. Clone the Repository

```bash
git clone <your-github-url>
cd AI-Student-Performance-System
```

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment (Windows PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Create your local .env file (copy from template, then fill in real values)
copy .env.example .env
# Edit .env with your MySQL credentials — NEVER commit .env to Git

# Start the backend development server
uvicorn app.main:app --reload
```

The API will be available at: `http://localhost:8000`
Health check: `http://localhost:8000/health`
Interactive API docs: `http://localhost:8000/docs`

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will be available at: `http://localhost:5173`

### 4. Database Setup

- Create a MySQL database (name, host, user, and password go into `backend/.env`)
- Database tables will be created automatically when the backend starts (once ORM models are defined)

---

## Development Status

| Stage | Description | Status |
|---|---|---|
| Stage 0 | Project foundation (Git, structure, scaffold) | 🔄 In progress |
| Stage 1 | Dataset selection and EDA | ⏳ Pending |
| Stage 2 | ML pipeline (offline training and evaluation) | ⏳ Pending |
| Stage 3 | Backend skeleton (FastAPI + SQLAlchemy) | ⏳ Pending |
| Stage 4 | Prediction endpoint + weak-area logic | ⏳ Pending |
| Stage 5 | React frontend (forms, results, charts) | ⏳ Pending |
| Stage 6 | Integration, testing, polish | ⏳ Pending |

---

## Important Notes

- **Never commit `.env` files.** They contain database passwords. Use `.env.example` as a template.
- **Dataset files** (`ml/data/`) and **model artifacts** (`ml/models/`) are gitignored.
- The `docs/` folder contains approved project reference documents. Do not modify them.
- Predictions are estimates only — not guarantees of academic performance.

---

## Reference Documents

Located in `docs/`:
- Week II — Literature Survey
- Week III — Software Requirements Specification (SRS)
- Week IV — System Design
