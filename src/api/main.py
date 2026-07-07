from fastapi import FastAPI, Depends
import os
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.infra.database import get_db

app = FastAPI(title="ProcureIQ Python Service")

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "database_connected": os.getenv("DATABASE_URL") is not None
    }

@app.get("/db-check")
def check_db(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "connected",
            "message": "Successfully connected to the database"
        }
    except Exception as e:
        return {
            "status": "disconnected",
            "error": str(e)
        }

