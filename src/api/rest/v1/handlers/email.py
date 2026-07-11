from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel, EmailStr
from src.infra.database import get_db
from src.features.email.service import send_gmail_email, schedule_gmail_email, list_scheduled

router = APIRouter(prefix="/api/v1/email")

class EmailSendRequest(BaseModel):
    recipients: list[EmailStr]
    subject: str
    body: str

class EmailScheduleRequest(BaseModel):
    recipients: list[EmailStr]
    subject: str
    body: str
    scheduled_for: datetime

@router.post("/send")
def send_email_endpoint(payload: EmailSendRequest):
    try:
        send_gmail_email(
            recipients=payload.recipients,
            subject=payload.subject,
            body=payload.body
        )
        return {"status": "success", "message": "Email sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/schedule")
def schedule_email_endpoint(payload: EmailScheduleRequest, db: Session = Depends(get_db)):
    try:
        db_email = schedule_gmail_email(
            db=db,
            recipients=payload.recipients,
            subject=payload.subject,
            body=payload.body,
            scheduled_for=payload.scheduled_for
        )
        return {
            "id": db_email.id,
            "recipients": [r.strip() for r in db_email.recipients.split(",")],
            "subject": db_email.subject,
            "body": db_email.body,
            "scheduled_for": db_email.scheduled_for.isoformat(),
            "status": db_email.status,
            "created_at": db_email.created_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/scheduled")
def get_scheduled_emails_endpoint(db: Session = Depends(get_db)):
    try:
        emails = list_scheduled(db)
        return [
            {
                "id": email.id,
                "recipients": [r.strip() for r in email.recipients.split(",")],
                "subject": email.subject,
                "body": email.body,
                "scheduled_for": email.scheduled_for.isoformat(),
                "status": email.status,
                "created_at": email.created_at.isoformat()
            }
            for email in emails
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
