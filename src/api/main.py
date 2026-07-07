from fastapi import FastAPI
import os

app = FastAPI(title="ProcureIQ Python Service")

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "database_connected": os.getenv("DATABASE_URL") is not None
    }
