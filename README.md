# Attendance System MVP

Milestone 1 includes FastAPI, SQLAlchemy, SQLite, bcrypt password hashing, and login flows for faculty and students.

MVP v3 adds AI attendance summaries, attendance analytics, low-attendance warnings, PDF report generation, email automation logs, and HoD dashboards.

## Setup

```powershell
cd attendance_system
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Seed Demo Users

```powershell
cd backend
python seed.py
```

Demo credentials:

- Faculty: `faculty` / `faculty123`
- HoD: `hod` / `hod123`
- Student: `22EC001` / `22EC001`

## Run Backend

```powershell
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

API docs: http://127.0.0.1:8010/docs

## Run Frontend

```powershell
cd frontend
streamlit run app.py
```

Frontend: http://localhost:8501

If you choose a different backend port, start Streamlit with the matching URL:

```powershell
$env:API_BASE_URL="http://127.0.0.1:8080"
streamlit run app.py
```

## MVP v3 Features

- AI reports: session summaries, low-attendance messages, department summaries.
- Analytics: attendance percentage, 30-day trend comparison, low-attendance detection below 75%.
- Reports: daily/session and weekly department PDFs, stored under `reports/YYYY/MM/` in MinIO when MinIO is available.
- Email automation: session closure emails, low-attendance warnings, and weekly HoD report logs. If SMTP is not configured, messages are logged with `skipped` status for MCP delivery.
- HoD role: login with `hod` / `hod123` after running `python seed.py`.

Local Hugging Face generation is off by default to keep laptop startup fast. Set `AI_ENABLE_LOCAL_MODEL=true` and choose `HF_MODEL_NAME` to enable local text generation.
