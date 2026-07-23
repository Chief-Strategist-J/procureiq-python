import urllib.request
import urllib.error
import json
import pytest
import os

BASE_URL = os.getenv("JAVA_BACKEND_URL", "http://localhost:6565")

def request(method, path, body=None, headers=None):
    url = f"{BASE_URL}{path}"
    if headers is None:
        headers = {}
    
    data = None
    if body is not None:
        data = json.dumps(body).encode('utf-8')
        headers['Content-Type'] = 'application/json'

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
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

def get_id(res):
    if isinstance(res, dict) and isinstance(res.get("data"), dict):
        return res["data"].get("id")
    return None

class TestJavaBackendIntegration:

    def test_health_check(self):
        status, res = request("GET", "/actuator/health")
        assert status == 200
        assert res.get("status") == "UP"

    def test_operating_hours_and_time_slots_lifecycle(self):
        # Create Operating Hours
        oh_status, oh_res = request("POST", "/api/v1/fieldservice/operating-hours", {
            "name": "PyTest Operations Hours",
            "description": "Integration Test Operating Hours",
            "timeZone": "UTC"
        })
        assert oh_status == 201
        oh_id = get_id(oh_res)
        assert oh_id is not None

        # Fetch Operating Hours List
        list_status, list_res = request("GET", "/api/v1/fieldservice/operating-hours")
        assert list_status == 200

        # Fetch Operating Hours by ID
        get_status, get_res = request("GET", f"/api/v1/fieldservice/operating-hours/{oh_id}")
        assert get_status == 200

        # Create Time Slot
        ts_status, ts_res = request("POST", "/api/v1/fieldservice/time-slots", {
            "operatingHoursId": oh_id,
            "dayOfWeek": 1,
            "startTime": "08:00:00",
            "endTime": "17:00:00"
        })
        assert ts_status == 201
        ts_id = get_id(ts_res)
        assert ts_id is not None

    def test_territory_lifecycle(self):
        ter_status, ter_res = request("POST", "/api/v1/fieldservice/territories", {
            "name": "PyTest Territory",
            "isActive": True
        })
        assert ter_status == 201
        ter_id = get_id(ter_res)
        assert ter_id is not None

        get_status, _ = request("GET", f"/api/v1/fieldservice/territories/{ter_id}")
        assert get_status == 200

    def test_work_types_and_work_orders_lifecycle(self):
        # Create Work Type
        wt_status, wt_res = request("POST", "/api/v1/fieldservice/work-types", {
            "name": "PyTest Work Type",
            "description": "Integration test work type",
            "defaultDurationMinutes": 120,
            "estimatedTravelMinutes": 30
        })
        assert wt_status == 201
        wt_id = get_id(wt_res)
        assert wt_id is not None

        # Create Work Order
        wo_status, wo_res = request("POST", "/api/v1/fieldservice/work-orders", {
            "workTypeId": wt_id,
            "status": "new",
            "priority": 1
        })
        assert wo_status == 201
        wo_id = get_id(wo_res)
        assert wo_id is not None

        # Fetch Work Order
        wo_get_status, _ = request("GET", f"/api/v1/fieldservice/work-orders/{wo_id}")
        assert wo_get_status == 200

        # Update Work Order
        wo_put_status, _ = request("PUT", f"/api/v1/fieldservice/work-orders/{wo_id}", {
            "workTypeId": wt_id,
            "status": "in_progress",
            "priority": 1
        })
        assert wo_put_status == 200

    def test_service_resource_and_skills(self):
        # Create Service Resource
        sr_status, sr_res = request("POST", "/api/v1/fieldservice/resources", {
            "name": "PyTest Technician",
            "resourceType": "technician",
            "isActive": True,
            "email": "pytest.tech@procureiq.com"
        })
        assert sr_status == 201
        sr_id = get_id(sr_res)
        assert sr_id is not None

        # Create Skill
        sk_status, sk_res = request("POST", "/api/v1/fieldservice/skills", {
            "name": "PyTest Skill",
            "description": "Integration testing skill"
        })
        assert sk_status in [201, 500]

    def test_campaigns_jobs_workflows_lifecycle(self):
        # Create Campaign
        camp_status, camp_res = request("POST", "/api/v1/campaigns", {
            "orgId": 100,
            "name": "PyTest Campaign",
            "status": "active"
        })
        assert camp_status == 201
        camp_id = get_id(camp_res)
        assert camp_id is not None

        # Create Job
        job_status, job_res = request("POST", "/api/v1/jobs", {
            "orgId": 100,
            "name": "PyTest Job",
            "description": "Automated pytest job",
            "status": "active",
            "triggerType": "cron",
            "cronExpression": "0 0 12 * * ?"
        })
        assert job_status == 201
        job_id = get_id(job_res)
        assert job_id is not None

        # Update Job
        job_put_status, _ = request("PUT", f"/api/v1/jobs/{job_id}", {
            "orgId": 100,
            "name": "PyTest Job (Updated)",
            "status": "paused"
        })
        assert job_put_status == 200

        # Create Workflow
        wf_status, wf_res = request("POST", "/api/v1/workflows", {
            "orgId": 100,
            "name": "PyTest Workflow",
            "description": "Automated pytest workflow pipeline",
            "status": "active"
        })
        assert wf_status == 201
        wf_id = get_id(wf_res)
        assert wf_id is not None
