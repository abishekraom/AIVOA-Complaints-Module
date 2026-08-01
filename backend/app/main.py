from fastapi import FastAPI

from app.api.routes.auth import router as auth_router

app = FastAPI(title="Customer Complaint Management")
app.include_router(auth_router)

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
