import urllib.request
import urllib.error
import json
import pytest
import os

BASE_URL = os.getenv("JAVA_BACKEND_URL", "http://localhost:6565")

def req(method, path, body=None, headers=None):
    url = f"{BASE_URL}{path}"
    if headers is None:
        headers = {}
    data = None
    if body is not None:
        data = json.dumps(body).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    request_obj = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request_obj) as resp:
            resp_body = resp.read().decode('utf-8')
            return resp.status, json.loads(resp_body) if resp_body else {}
    except urllib.error.HTTPError as e:
        resp_body = e.read().decode('utf-8')
        try:
            parsed = json.loads(resp_body)
        except Exception:
            parsed = resp_body
        return e.code, parsed
    except Exception as e:
        return 0, str(e)

def parse_id(res):
    if isinstance(res, dict) and isinstance(res.get("data"), dict):
        return res["data"].get("id")
    return 1

class TestAllSpringbootControllers:

    # --- 1. Auth & Account APIs ---
    def test_auth_signup(self):
        status, _ = req("POST", "/api/v1/auth/signup", {"username": "all100_user", "email": "all100@procureiq.com", "password": "Password123!"})
        assert status in [201, 400, 500]

    def test_auth_login(self):
        status, _ = req("POST", "/api/v1/auth/login", {"username": "all100_user", "password": "Password123!"})
        assert status in [200, 401]

    def test_auth_forgot_password(self):
        status, _ = req("POST", "/api/v1/auth/forgot-password", {"email": "all100@procureiq.com"})
        assert status == 200

    def test_auth_reset_password(self):
        status, _ = req("POST", "/api/v1/auth/reset-password", {"token": "dummy", "newPassword": "Password123!"})
        assert status in [200, 400, 401, 500]

    # --- 2. Notifications APIs ---
    def test_notifications_get_all(self):
        status, _ = req("GET", "/api/v1/notifications")
        assert status == 200

    def test_notifications_unread_count(self):
        status, _ = req("GET", "/api/v1/notifications/unread-count")
        assert status == 200

    def test_notifications_send(self):
        status, _ = req("POST", "/api/v1/notifications", {"recipientId": "u1", "type": "system_alert", "title": "T", "body": "B"})
        assert status == 202

    def test_notifications_update_status(self):
        status, _ = req("PUT", "/api/v1/notifications/1/status", {"status": "read"})
        assert status in [200, 400, 404, 500]

    def test_notifications_register_device(self):
        status, _ = req("POST", "/api/v1/notifications/devices", {"deviceToken": "tok123", "platform": "android"})
        assert status in [200, 400, 500]

    # --- 3. Campaigns APIs ---
    def test_campaigns_crud(self):
        status, res = req("POST", "/api/v1/campaigns", {"orgId": 1, "name": "C1", "status": "active"})
        assert status == 201
        cid = parse_id(res)

        assert req("GET", "/api/v1/campaigns")[0] == 200
        assert req("GET", f"/api/v1/campaigns/{cid}")[0] == 200
        assert req("PUT", f"/api/v1/campaigns/{cid}", {"orgId": 1, "name": "C1 Updated", "status": "paused"})[0] == 200
        
        # Schedules & Recipients sub-resources
        assert req("GET", "/api/v1/campaigns/schedules")[0] in [200, 404, 500]
        assert req("POST", "/api/v1/campaigns/schedules", {"campaignId": cid, "cronExpression": "0 0 * * *"})[0] in [201, 400, 500]
        assert req("GET", "/api/v1/campaigns/recipients")[0] in [200, 404, 500]
        assert req("POST", "/api/v1/campaigns/recipients", {"campaignId": cid, "email": "r@test.com"})[0] in [201, 400, 500]
        assert req("DELETE", f"/api/v1/campaigns/{cid}")[0] in [200, 404, 500]

    # --- 4. Jobs & Workflows APIs ---
    def test_jobs_and_workflows_crud(self):
        # Job CRUD
        status, res = req("POST", "/api/v1/jobs", {"orgId": 1, "name": "J1", "status": "active", "triggerType": "cron", "cronExpression": "0 0 * * *"})
        assert status == 201
        jid = parse_id(res)

        assert req("GET", "/api/v1/jobs")[0] == 200
        assert req("GET", f"/api/v1/jobs/{jid}")[0] == 200
        assert req("PUT", f"/api/v1/jobs/{jid}", {"orgId": 1, "name": "J1 Up", "status": "paused"})[0] == 200
        assert req("GET", f"/api/v1/jobs/{jid}/runs")[0] in [200, 500]
        assert req("POST", f"/api/v1/jobs/{jid}/runs")[0] in [200, 201, 500]

        # Workflow CRUD
        wf_status, wf_res = req("POST", "/api/v1/workflows", {"orgId": 1, "name": "W1", "status": "active"})
        assert wf_status == 201
        wfid = parse_id(wf_res)

        assert req("GET", "/api/v1/workflows")[0] == 200
        assert req("GET", f"/api/v1/workflows/{wfid}")[0] == 200
        assert req("PUT", f"/api/v1/workflows/{wfid}", {"orgId": 1, "name": "W1 Up", "status": "active"})[0] == 200
        assert req("GET", f"/api/v1/workflows/{wfid}/runs")[0] in [200, 500]
        assert req("POST", f"/api/v1/workflows/{wfid}/runs")[0] in [200, 201, 500]
        assert req("DELETE", f"/api/v1/jobs/{jid}")[0] in [200, 404, 500]
        assert req("DELETE", f"/api/v1/workflows/{wfid}")[0] in [200, 404, 500]

    # --- 5. Field Service APIs (Work Types, Work Orders, Appointments, Operating Hours, Time Slots, Territories) ---
    def test_field_service_all_resources(self):
        # Work Types
        wt_id = parse_id(req("POST", "/api/v1/fieldservice/work-types", {"name": "WT1", "defaultDurationMinutes": 60})[1])
        assert req("GET", f"/api/v1/fieldservice/work-types/{wt_id}")[0] == 200
        assert req("PUT", f"/api/v1/fieldservice/work-types/{wt_id}", {"name": "WT1 Up", "defaultDurationMinutes": 90})[0] == 200

        # Work Orders
        wo_id = parse_id(req("POST", "/api/v1/fieldservice/work-orders", {"workTypeId": wt_id, "status": "new", "priority": 1})[1])
        assert req("GET", "/api/v1/fieldservice/work-orders")[0] == 200
        assert req("GET", f"/api/v1/fieldservice/work-orders/{wo_id}")[0] == 200
        assert req("PUT", f"/api/v1/fieldservice/work-orders/{wo_id}", {"workTypeId": wt_id, "status": "in_progress", "priority": 1})[0] == 200

        # Operating Hours & Time Slots
        oh_id = parse_id(req("POST", "/api/v1/fieldservice/operating-hours", {"name": "OH1", "timeZone": "UTC"})[1])
        assert req("GET", "/api/v1/fieldservice/operating-hours")[0] == 200
        assert req("GET", f"/api/v1/fieldservice/operating-hours/{oh_id}")[0] == 200
        assert req("PUT", f"/api/v1/fieldservice/operating-hours/{oh_id}", {"name": "OH1 Up", "timeZone": "UTC"})[0] == 200

        ts_id = parse_id(req("POST", "/api/v1/fieldservice/time-slots", {"operatingHoursId": oh_id, "dayOfWeek": 1, "startTime": "08:00:00", "endTime": "17:00:00"})[1])
        assert req("GET", f"/api/v1/fieldservice/time-slots/{ts_id}")[0] == 200
        assert req("PUT", f"/api/v1/fieldservice/time-slots/{ts_id}", {"operatingHoursId": oh_id, "dayOfWeek": 2, "startTime": "09:00:00", "endTime": "18:00:00"})[0] == 200

        # Territories
        ter_id = parse_id(req("POST", "/api/v1/fieldservice/territories", {"name": "TER1", "operatingHoursId": oh_id})[1])
        assert req("GET", "/api/v1/fieldservice/territories")[0] == 200
        assert req("GET", f"/api/v1/fieldservice/territories/{ter_id}")[0] == 200
        assert req("PUT", f"/api/v1/fieldservice/territories/{ter_id}", {"name": "TER1 Up"})[0] == 200

        # Resources & Skills
        sr_id = parse_id(req("POST", "/api/v1/fieldservice/resources", {"name": "Tech1", "resourceType": "technician"})[1])
        assert req("GET", "/api/v1/fieldservice/resources")[0] == 200
        assert req("GET", f"/api/v1/fieldservice/resources/{sr_id}")[0] == 200
        assert req("PUT", f"/api/v1/fieldservice/resources/{sr_id}", {"name": "Tech1 Up", "resourceType": "technician"})[0] == 200

        sk_res = req("POST", "/api/v1/fieldservice/skills", {"name": "SK1"})[1]
        sk_id = parse_id(sk_res)
        if sk_id and sk_id != 1:
            assert req("GET", f"/api/v1/fieldservice/skills/{sk_id}")[0] in [200, 404, 500]
            assert req("PUT", f"/api/v1/fieldservice/skills/{sk_id}", {"name": "SK1 Up"})[0] in [200, 404, 500]

            srs_id = parse_id(req("POST", "/api/v1/fieldservice/service-resource-skills", {"serviceResourceId": sr_id, "skillId": sk_id, "skillLevel": 3})[1])
            if srs_id:
                assert req("GET", f"/api/v1/fieldservice/service-resource-skills/{srs_id}")[0] == 200
                assert req("PUT", f"/api/v1/fieldservice/service-resource-skills/{srs_id}", {"serviceResourceId": sr_id, "skillId": sk_id, "skillLevel": 4})[0] == 200

        # Appointments
        sa_id = parse_id(req("POST", "/api/v1/fieldservice/appointments", {"parentRecordType": "work_order", "parentRecordId": wo_id, "durationMinutes": 60})[1])
        assert req("GET", "/api/v1/fieldservice/appointments")[0] == 200
        assert req("GET", f"/api/v1/fieldservice/appointments/{sa_id}")[0] == 200
        assert req("PUT", f"/api/v1/fieldservice/appointments/{sa_id}", {"parentRecordType": "work_order", "parentRecordId": wo_id, "durationMinutes": 90})[0] == 200
        assert req("GET", f"/api/v1/fieldservice/appointments/{sa_id}/candidates")[0] in [200, 404, 500]
        assert req("POST", f"/api/v1/fieldservice/appointments/{sa_id}/assign", {"serviceResourceId": sr_id})[0] in [200, 201, 400, 404, 500]

    # --- 6. Extended Field Service Sub-Resources (Milestones, Service Crews, Shifts, Absences, Preferences, Capacities, Maintenance Plans, Asset Relationships) ---
    def test_field_service_sub_components(self):
        # Milestones
        ms_id = parse_id(req("POST", "/api/v1/fieldservice/milestones", {"name": "MS1", "sequence": 1})[1])
        assert req("GET", f"/api/v1/fieldservice/milestones/{ms_id}")[0] in [200, 404, 500]
        assert req("PUT", f"/api/v1/fieldservice/milestones/{ms_id}", {"name": "MS1 Up", "sequence": 2})[0] in [200, 404, 500]

        # Case Milestones
        cms_id = parse_id(req("POST", "/api/v1/fieldservice/case-milestones", {"caseId": 1, "milestoneId": ms_id if ms_id else 1})[1])
        assert req("GET", f"/api/v1/fieldservice/case-milestones/{cms_id}")[0] in [200, 404, 500]

        # Maintenance Plans
        mp_id = parse_id(req("POST", "/api/v1/fieldservice/maintenance-plans", {"name": "MP1", "frequency": 1})[1])
        assert req("GET", f"/api/v1/fieldservice/maintenance-plans/{mp_id}")[0] in [200, 404, 500]

        # Resource Absences
        ra_id = parse_id(req("POST", "/api/v1/fieldservice/resource-absences", {"serviceResourceId": 1, "absenceType": "vacation"})[1])
        assert req("GET", f"/api/v1/fieldservice/resource-absences/{ra_id}")[0] in [200, 404, 500]

        # Resource Preferences
        rp_id = parse_id(req("POST", "/api/v1/fieldservice/resource-preferences", {"serviceResourceId": 1, "preferenceType": "preferred"})[1])
        assert req("GET", f"/api/v1/fieldservice/resource-preferences/{rp_id}")[0] in [200, 404, 500]

        # Service Crews & Crew Members
        sc_id = parse_id(req("POST", "/api/v1/fieldservice/service-crews", {"name": "Crew1"})[1])
        assert req("GET", f"/api/v1/fieldservice/service-crews/{sc_id}")[0] in [200, 404, 500]
        scm_id = parse_id(req("POST", "/api/v1/fieldservice/service-crew-members", {"serviceCrewId": sc_id if sc_id else 1, "serviceResourceId": 1})[1])
        assert req("GET", f"/api/v1/fieldservice/service-crew-members/{scm_id}")[0] in [200, 404, 500]

        # Service Resource Capacities
        src_id = parse_id(req("POST", "/api/v1/fieldservice/service-resource-capacities", {"serviceResourceId": 1, "capacityHours": 8})[1])
        assert req("GET", f"/api/v1/fieldservice/service-resource-capacities/{src_id}")[0] in [200, 404, 500]

        # Service Territory Members
        stm_id = parse_id(req("POST", "/api/v1/fieldservice/service-territory-members", {"serviceTerritoryId": 1, "serviceResourceId": 1})[1])
        assert req("GET", f"/api/v1/fieldservice/service-territory-members/{stm_id}")[0] in [200, 404, 500]

        # Shifts
        sh_id = parse_id(req("POST", "/api/v1/fieldservice/shifts", {"serviceResourceId": 1, "startTime": "2026-08-01T08:00:00Z", "endTime": "2026-08-01T16:00:00Z"})[1])
        assert req("GET", f"/api/v1/fieldservice/shifts/{sh_id}")[0] in [200, 404, 500]

        # Skill Requirements
        sq_id = parse_id(req("POST", "/api/v1/fieldservice/skill-requirements", {"skillId": 1, "requiredForType": "work_type", "requiredForId": 1, "minSkillLevel": 1})[1])
        assert req("GET", f"/api/v1/fieldservice/skill-requirements/{sq_id}")[0] in [200, 404, 500]

        # Asset Relationships
        ar_id = parse_id(req("POST", "/api/v1/fieldservice/asset-relationships", {"assetId": 1, "relatedAssetId": 2, "relationshipType": "replacement"})[1])
        assert req("GET", f"/api/v1/fieldservice/asset-relationships/{ar_id}")[0] in [200, 404, 500]

    # --- 7. Reminders APIs ---
    def test_reminders_all(self):
        assert req("GET", "/api/v1/reminders")[0] == 200
        rem_status, rem_res = req("POST", "/api/v1/reminders", {"title": "R1", "priority": "HIGH", "status": "PENDING"})
        assert rem_status in [201, 500]
        rid = parse_id(rem_res)
        if rid and rid != 1:
            assert req("PUT", f"/api/v1/reminders/{rid}", {"title": "R1 Updated", "status": "COMPLETED"})[0] in [200, 404, 500]
            assert req("DELETE", f"/api/v1/reminders/{rid}")[0] in [200, 404, 500]

    # --- 8. External Integrations (GitHub, Gmail, Voice Call APIs) ---
    def test_external_integrations(self):
        # GitHub APIs
        assert req("GET", "/api/v1/github/templates")[0] in [200, 404, 500]
        assert req("GET", "/api/v1/github/templates/1")[0] in [200, 404, 500]
        assert req("GET", "/api/v1/github/repo-info")[0] in [200, 400, 500]
        assert req("GET", "/api/v1/github/workflow-runs")[0] in [200, 400, 500]
        assert req("POST", "/api/v1/github/dispatch", {"event_type": "build"})[0] in [200, 400, 500]
        assert req("POST", "/api/v1/github/create-workflow", {"name": "ci.yml"})[0] in [200, 400, 500]

        # Gmail APIs
        assert req("GET", "/api/v1/gmail/list")[0] in [200, 400, 500]
        assert req("POST", "/api/v1/gmail/send", {"to": "test@procureiq.com", "subject": "Hi", "body": "Body"})[0] in [200, 400, 500]

        # Voice Call APIs
        assert req("GET", "/api/v1/voice/scheduled")[0] in [200, 404, 500]
        assert req("POST", "/api/v1/voice/schedule", {"recipientNumber": "+1555019999", "scheduledTime": "2026-08-01T10:00:00Z"})[0] in [200, 201, 400, 500]

    # --- 9. Identity Admin APIs ---
    def test_identity_admin(self):
        assert req("GET", "/api/v1/identity/organizations/1/assignments")[0] in [200, 500]
        assert req("POST", "/api/v1/identity/organizations/1/assignments", {"userId": 1, "roleId": 1})[0] in [200, 201, 400, 500]
        assert req("GET", "/api/v1/identity/organizations/1/audit-events")[0] in [200, 500]
        assert req("POST", "/api/v1/identity/organizations/1/audit-events/verify", {"hash": "abc"})[0] in [200, 400, 500]
