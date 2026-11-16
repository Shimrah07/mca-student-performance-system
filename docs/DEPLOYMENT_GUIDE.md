# Production Deployment Architecture & Operational Runbook

**System:** AI-Based Student Performance Prediction & Academic Support System  
**Target Environment:** Cloud PaaS (Frontend: Vercel / Netlify; Backend: Render / Railway / Fly.io; Database: Managed MySQL 8.0)  

---

## 1. Recommended Production Architecture

```
┌───────────────────────────────────────────────┐
│              CDN Edge / Hosting               │
│       Vercel / Netlify (Static SPA)           │
│   Environment: VITE_API_URL=https://api...    │
└──────────────────────┬────────────────────────┘
                       │ HTTPS
                       ▼
┌───────────────────────────────────────────────┐
│        Containerized Python Service           │
│    Render / Railway (FastAPI + Uvicorn)       │
│  - Python 3.11 / 3.12 / 3.14 Runtime          │
│  - ML Model Artifacts in ml/artifacts/mca/    │
│  - CORS Restricted to Frontend Domain         │
└──────────────────────┬────────────────────────┘
                       │ TLS 1.3 / Port 3306
                       ▼
┌───────────────────────────────────────────────┐
│             Managed Cloud MySQL 8.0           │
│         (Railway / Aiven / PlanetScale)       │
│  - Database: mca_academic_system              │
│  - Non-root user: mca_app                     │
│  - Automated Point-in-Time Backups            │
└───────────────────────────────────────────────┘
```

---

## 2. Configuration & Environment Variables

### 2.1 Backend Environment (`backend/.env` / Cloud Secrets)
| Variable | Required | Description | Production Example |
|---|---|---|---|
| `APP_ENV` | Yes | Runtime environment identifier | `production` |
| `DB_HOST` | Yes | Managed MySQL hostname | `mysql.railway.internal` |
| `DB_PORT` | Yes | MySQL port | `3306` |
| `DB_NAME` | Yes | Production database name | `mca_academic_system` |
| `DB_USER` | Yes | Application database user | `mca_app_prod` |
| `DB_PASSWORD` | Yes | Strong generated password | *[SUPPLIED BY SECRET MANAGER]* |
| `DATABASE_URL` | Optional | Direct connection string | `mysql+pymysql://user:pass@host:3306/db` |
| `CORS_ORIGINS` | Yes | Allowed client origins (comma-separated) | `https://mca-intelligence.vercel.app` |

### 2.2 Frontend Environment (`frontend/.env` / Cloud Secrets)
| Variable | Required | Description | Production Example |
|---|---|---|---|
| `VITE_API_URL` | Yes | Public HTTPS URL of the FastAPI backend | `https://api-mca-system.onrender.com` |

---

## 3. Step-by-Step Deployment Runbook

### Phase A: Database Provisioning
1. Provision a managed MySQL 8.0 instance on the chosen cloud provider (e.g. Railway, Aiven, or AWS RDS).
2. Create dedicated database `mca_academic_system`.
3. Create dedicated non-root application user with least-privilege permissions:
   ```sql
   CREATE USER 'mca_app_prod'@'%' IDENTIFIED BY 'STRONG_SECRET_HERE';
   GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, INDEX ON mca_academic_system.* TO 'mca_app_prod'@'%';
   FLUSH PRIVILEGES;
   ```
4. Initialize the approved 13 MCA tables and canonical curriculum using the controlled seeder:
   ```bash
   python -m app.seeders.mca_curriculum_seeder
   ```
   *Note: Do NOT run the demo seeder in production unless spinning up a dedicated demonstration environment.*

### Phase B: Backend Deployment (e.g., Render / Railway)
1. Set Root Directory: `backend`.
2. Build Command:
   ```bash
   pip install --upgrade pip && pip install -r requirements.txt
   ```
3. Start Command:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2
   ```
4. Verify Model Artifacts: Ensure `ml/artifacts/mca/` is tracked in the Git repository so the `.joblib` and `.json` files are deployed alongside the application code.
5. Verify Health: Send request to `https://<backend-url>/health` and `https://<backend-url>/health/db`.

### Phase C: Frontend Deployment (e.g., Vercel / Netlify)
1. Set Root Directory: `frontend`.
2. Build Command: `npm run build`.
3. Output Directory: `dist`.
4. Configure Environment Variable: `VITE_API_URL=https://<your-backend-domain>`.
5. Add single-page application redirect rule (e.g. `/* /index.html 200` in `_redirects` or `vercel.json`) to support client-side routing.

---

## 4. Security & Production Checklist

- [x] Wildcard CORS (`*`) is disabled in production; only explicit HTTPS frontend origins are permitted.
- [x] Passwords and credentials are never stored in version control or displayed in `/health/db`.
- [x] Database user follows least privilege (no `DROP DATABASE` or global administrative permissions).
- [x] SQL injection is prevented through SQLAlchemy ORM parameterized queries.
- [x] Input payloads are validated by strict Pydantic v2 schemas.
- [x] Prototype disclaimers regarding synthetic model training are active across all responses.
