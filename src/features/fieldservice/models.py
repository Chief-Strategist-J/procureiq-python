from sqlalchemy import Column, BigInteger, String, Boolean, DateTime, ForeignKey, Integer, SmallInteger
from sqlalchemy.orm import relationship
from src.infra.database import Base

class ServiceResource(Base):
    __tablename__ = 'service_resources'

    id = Column(BigInteger, primary_key=True)
    name = Column(String, nullable=False)
    user_id = Column(BigInteger, nullable=True)
    service_crew_id = Column(BigInteger, nullable=True)
    resource_type = Column(String, nullable=False, default='technician')
    is_active = Column(Boolean, nullable=False, default=True)

class ServiceResourceSkill(Base):
    __tablename__ = 'service_resource_skills'

    id = Column(BigInteger, primary_key=True)
    service_resource_id = Column(BigInteger, ForeignKey('service_resources.id'), nullable=False)
    skill_id = Column(BigInteger, nullable=False)
    skill_level = Column(SmallInteger, nullable=False, default=1)
    valid_from = Column(DateTime, nullable=False)
    valid_to = Column(DateTime, nullable=True)

class ServiceTerritoryMember(Base):
    __tablename__ = 'service_territory_members'

    id = Column(BigInteger, primary_key=True)
    service_territory_id = Column(BigInteger, nullable=False)
    service_resource_id = Column(BigInteger, ForeignKey('service_resources.id'), nullable=False)
    operating_hours_id = Column(BigInteger, nullable=True)
    territory_type = Column(String, nullable=False, default='primary')
    travel_mode = Column(String, nullable=False, default='driving')

class ServiceAppointment(Base):
    __tablename__ = 'service_appointments'

    id = Column(BigInteger, primary_key=True)
    parent_record_type = Column(String, nullable=False)
    parent_record_id = Column(BigInteger, nullable=False)
    account_id = Column(BigInteger, nullable=True)
    contact_id = Column(BigInteger, nullable=True)
    service_territory_id = Column(BigInteger, nullable=True)
    work_type_id = Column(BigInteger, nullable=True)
    status = Column(String, nullable=False, default='none')
    scheduled_start = Column(DateTime, nullable=True)
    scheduled_end = Column(DateTime, nullable=True)
    arrival_window_start = Column(DateTime, nullable=True)
    arrival_window_end = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    created_at = Column(DateTime, primary_key=True, nullable=False)

class ResourceAbsence(Base):
    __tablename__ = 'resource_absences'

    id = Column(BigInteger, primary_key=True)
    service_resource_id = Column(BigInteger, ForeignKey('service_resources.id'), nullable=False)
    absence_type = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(String, nullable=False, default='approved')
