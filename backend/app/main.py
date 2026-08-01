from fastapi import FastAPI

app = FastAPI(title="Customer Complaint Management")

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
