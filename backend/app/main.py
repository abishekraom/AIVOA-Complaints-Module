from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router

app = FastAPI(title="Customer Complaint Management")
app.include_router(auth_router)
app.include_router(users_router)

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
