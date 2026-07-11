import os
import smtplib
from email.message import EmailMessage
from datetime import datetime
from sqlalchemy.orm import Session
from src.features.email.models import ScheduledEmail

def send_gmail_email(recipients: list[str], subject: str, body: str):
    gmail_user = os.getenv("GMAIL_USER")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")

    if not gmail_user or not gmail_password:
        raise ValueError("GMAIL_USER and GMAIL_APP_PASSWORD environment variables must be set")

    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = gmail_user
    msg["To"] = ", ".join(recipients)

    # Send the email via Gmail SMTP
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.send_message(msg)

def schedule_gmail_email(db: Session, recipients: list[str], subject: str, body: str, scheduled_for: datetime):
    db_email = ScheduledEmail(
        recipients=", ".join(recipients),
        subject=subject,
        body=body,
        scheduled_for=scheduled_for,
        status="pending"
    )
    db.add(db_email)
    db.commit()
    db.refresh(db_email)
    return db_email

def list_scheduled(db: Session):
    return db.query(ScheduledEmail).all()

def process_scheduled_emails(db: Session):
    now = datetime.utcnow()
    pending_emails = db.query(ScheduledEmail).filter(
        ScheduledEmail.status == "pending",
        ScheduledEmail.scheduled_for <= now
    ).all()

    for email in pending_emails:
        try:
            recipients_list = [r.strip() for r in email.recipients.split(",") if r.strip()]
            send_gmail_email(recipients_list, email.subject, email.body)
            email.status = "sent"
        except Exception as e:
            email.status = "failed"
            print(f"Failed to send scheduled email {email.id}: {e}")
        finally:
            db.commit()
