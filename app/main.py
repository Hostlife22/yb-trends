from fastapi import FastAPI

from app.api.routes_trends import router as trends_router
from app.config import settings

app = FastAPI(title=settings.app_name)
app.include_router(trends_router)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
