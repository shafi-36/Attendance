import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.attendance import router as attendance_router
from app.api.auth import router as auth_router
from app.api.analytics import router as analytics_router
from app.api.email_logs import router as email_logs_router
from app.api.reports import router as reports_router
from app.api.sessions import router as sessions_router
from app.api.students import router as students_router
from app.core.database import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up Attendance System API…")
    init_db()
    logger.info("Database initialised")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="Attendance System API",
    version="2.0.0",
    description="AI-powered attendance management with face recognition",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(students_router)
app.include_router(sessions_router)
app.include_router(attendance_router)
app.include_router(analytics_router)
app.include_router(reports_router)
app.include_router(email_logs_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "version": "2.0.0"}
