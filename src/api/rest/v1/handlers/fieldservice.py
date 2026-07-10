from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.infra.database import get_db
from src.features.fieldservice.queries import find_candidates_for_appointment

router = APIRouter(prefix="/api/v1/fieldservice")

@router.get("/appointments/{appointment_id}/candidates")
def get_candidates(appointment_id: int, db: Session = Depends(get_db)):
    try:
        candidates = find_candidates_for_appointment(db, appointment_id)
        return {
            "status": "success",
            "code": 200,
            "data": candidates,
            "error": None
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
