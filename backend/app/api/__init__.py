from fastapi import APIRouter

from app.api import evaluate, lessons, recommend, records, visemes

api_router = APIRouter()
api_router.include_router(lessons.router)
api_router.include_router(evaluate.router)
api_router.include_router(visemes.router)
api_router.include_router(recommend.router)
api_router.include_router(records.router)
