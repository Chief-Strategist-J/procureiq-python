from sqlalchemy import Column, Integer, String, Text, DateTime, func
from src.infra.database import Base

class ScheduledEmail(Base):
    __tablename__ = 'scheduled_emails'

    id = Column(Integer, primary_key=True, autoincrement=True)
    recipients = Column(Text, nullable=False)  # Comma-separated email addresses
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    scheduled_for = Column(DateTime, nullable=False)
    status = Column(String(50), nullable=False, default='pending')  # pending, sent, failed
    created_at = Column(DateTime, nullable=False, default=func.now())
