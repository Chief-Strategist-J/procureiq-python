import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

# Setup in-memory SQLite with StaticPool so the connection is shared and tables are not dropped prematurely
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Patch get_db to return test session
def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Mock the database engine globally before importing app
import src.infra.database
src.infra.database.engine = test_engine
src.infra.database.SessionLocal = TestSessionLocal

from src.infra.database import Base
from src.features.email.models import ScheduledEmail

from src.api.main import app
app.dependency_overrides[src.infra.database.get_db] = override_get_db

from src.features.email.service import process_scheduled_emails

client = TestClient(app)

@pytest.fixture(autouse=True, scope="module")
def setup_db():
    # Setup tables once for the module in memory
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@patch("src.features.email.service.smtplib.SMTP")
@patch.dict("os.environ", {"GMAIL_USER": "test@gmail.com", "GMAIL_APP_PASSWORD": "password123"})
def test_send_email_endpoint(mock_smtp):
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server

    payload = {
        "recipients": ["user1@gmail.com", "user2@gmail.com"],
        "subject": "Test Immediate Email",
        "body": "Hello, this is a test!"
    }
    response = client.post("/api/v1/email/send", json=payload)
    
    assert response.status_code == 200
    assert response.json() == {"status": "success", "message": "Email sent successfully"}
    mock_server.login.assert_called_once_with("test@gmail.com", "password123")
    mock_server.send_message.assert_called_once()

def test_schedule_email_endpoint():
    scheduled_time = (datetime.utcnow() + timedelta(hours=1)).isoformat()
    payload = {
        "recipients": ["user3@gmail.com"],
        "subject": "Test Scheduled Email",
        "body": "This is a scheduled message.",
        "scheduled_for": scheduled_time
    }
    response = client.post("/api/v1/email/schedule", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] is not None
    assert data["subject"] == "Test Scheduled Email"
    assert data["status"] == "pending"

    # List scheduled emails
    list_response = client.get("/api/v1/email/scheduled")
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert len(list_data) == 1
    assert list_data[0]["subject"] == "Test Scheduled Email"

@patch("src.features.email.service.smtplib.SMTP")
@patch.dict("os.environ", {"GMAIL_USER": "test@gmail.com", "GMAIL_APP_PASSWORD": "password123"})
def test_background_scheduler_processing(mock_smtp):
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server

    db = TestSessionLocal()
    # Add a scheduled email in the past
    past_time = datetime.utcnow() - timedelta(minutes=5)
    db_email = ScheduledEmail(
        recipients="user4@gmail.com",
        subject="Past Email",
        body="Should be sent",
        scheduled_for=past_time,
        status="pending"
    )
    db.add(db_email)
    db.commit()
    db.refresh(db_email)

    # Process scheduled emails
    process_scheduled_emails(db)

    # Refresh status
    db.refresh(db_email)
    assert db_email.status == "sent"
    mock_server.send_message.assert_called_once()
    db.close()
