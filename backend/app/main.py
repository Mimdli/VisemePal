from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import api_router
from app.config import BACKEND_DIR, settings
from app.db import Base, SessionLocal, engine
from app.models import Lesson, PracticeRecord, RecommendationPlan, User  # noqa: F401
from app.schemas import HealthOut
from app.seed import seed_if_empty
from app.services.ise import has_ise_credentials

STATIC_DIR = BACKEND_DIR / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "audio").mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)


@app.get("/", include_in_schema=False)
def dev_console():
    return FileResponse(STATIC_DIR / "web" / "index.html")


@app.get("/health", response_model=HealthOut, tags=["system"])
def health() -> HealthOut:
    return HealthOut(
        name=settings.app_name,
        ise_ready=has_ise_credentials(),
        llm_ready=bool(settings.llm_api_key.strip()),
    )


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
