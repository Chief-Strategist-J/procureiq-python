import requests
import json
import time

BASE_URL = "https://procureiq-springboot.onrender.com"

def test_endpoint(method, path, payload=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    print(f"[{method}] {url} ... ", end="")
    try:
        if method == "POST":
            r = requests.post(url, json=payload, headers=headers, timeout=15)
        elif method == "PUT":
            r = requests.put(url, json=payload, headers=headers, timeout=15)
        elif method == "GET":
            r = requests.get(url, headers=headers, timeout=15)
        elif method == "DELETE":
            r = requests.delete(url, headers=headers, timeout=15)
        
        print(f"Status: {r.status_code}")
        if r.status_code in [200, 201]:
            try:
                data = r.json()
                print(f"  Response: {json.dumps(data, indent=2)}")
                return data.get("data")
            except:
                print(f"  Raw: {r.text}")
        else:
            print(f"  Error: {r.text}")
    except Exception as e:
        print(f"Failed: {e}")
    return None

def run_tests():
    print("=== STARTING FIELD SERVICE API CALLS ===")
    
    # 1. Operating Hours
    oh_req = {"name": "Render HQ Hours", "timezone": "America/New_York"}
    oh = test_endpoint("POST", "/api/v1/fieldservice/operating-hours", oh_req)
    if oh and "id" in oh:
        oh_id = oh["id"]
        test_endpoint("GET", f"/api/v1/fieldservice/operating-hours/{oh_id}")
        test_endpoint("PUT", f"/api/v1/fieldservice/operating-hours/{oh_id}", {"name": "Updated Render HQ Hours", "timezone": "UTC"})
    
    # 2. Service Territory
    if oh:
        st_req = {"name": "New York Region", "parentTerritoryId": None, "operatingHoursId": oh_id, "isActive": True}
        st = test_endpoint("POST", "/api/v1/fieldservice/territories", st_req)
        if st and "id" in st:
            st_id = st["id"]
            test_endpoint("GET", f"/api/v1/fieldservice/territories/{st_id}")

    # 3. Work Type
    wt_req = {"name": "Hardware Installation", "defaultDurationMinutes": 90, "estimatedTravelMinutes": 30}
    wt = test_endpoint("POST", "/api/v1/fieldservice/work-types", wt_req)
    if wt and "id" in wt:
        wt_id = wt["id"]
        test_endpoint("GET", f"/api/v1/fieldservice/work-types/{wt_id}")

    # 4. Work Order (Auto-creates Service Appointment)
    if wt:
        wo_req = {"accountId": None, "workTypeId": wt_id, "status": "new", "priority": 1}
        wo = test_endpoint("POST", "/api/v1/fieldservice/work-orders", wo_req)
        if wo and "id" in wo:
            wo_id = wo["id"]
            test_endpoint("GET", f"/api/v1/fieldservice/work-orders/{wo_id}")

    # 5. Service Resource
    sr_req = {"name": "Technician Alice", "userId": None, "serviceCrewId": None, "resourceType": "technician", "isActive": True}
    sr = test_endpoint("POST", "/api/v1/fieldservice/resources", sr_req)
    if sr and "id" in sr:
        sr_id = sr["id"]
        test_endpoint("GET", f"/api/v1/fieldservice/resources/{sr_id}")

    print("=== COMPLETED ===")

if __name__ == "__main__":
    run_tests()
