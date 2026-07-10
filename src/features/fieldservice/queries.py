from sqlalchemy import text
from sqlalchemy.orm import Session

def find_candidates_for_appointment(db: Session, appointment_id: int):
    """
    Executes the FSL candidate matching query.
    Matches active service resources who have primary territory membership in the appointment's territory,
    have the required skill level for the appointment's work type, and have no overlapping absences
    during the appointment's scheduled start and end times.
    """
    query = text("""
        SELECT DISTINCT sr.id, sr.name, sr.user_id, sr.service_crew_id, sr.resource_type, sr.is_active 
        FROM service_resources sr
        JOIN service_resource_skills srs ON sr.id = srs.service_resource_id
        JOIN service_territory_members stm ON sr.id = stm.service_resource_id
        JOIN service_territories st ON stm.service_territory_id = st.id
        JOIN service_appointments sa ON sa.id = :appointment_id
        WHERE sr.is_active = true
          AND srs.skill_id = sa.work_type_id
          AND srs.skill_level >= 1
          AND stm.service_territory_id = sa.service_territory_id
          AND stm.territory_type = 'primary'
          AND NOT EXISTS (
              SELECT 1 FROM resource_absences ra
              WHERE ra.service_resource_id = sr.id
                AND ra.start_time <= sa.scheduled_end
                AND ra.end_time >= sa.scheduled_start
          )
    """)
    result = db.execute(query, {"appointment_id": appointment_id})
    # Map raw rows to dicts
    return [
        {
            "id": row[0],
            "name": row[1],
            "user_id": row[2],
            "service_crew_id": row[3],
            "resource_type": row[4],
            "is_active": row[5]
        }
        for row in result.fetchall()
    ]
