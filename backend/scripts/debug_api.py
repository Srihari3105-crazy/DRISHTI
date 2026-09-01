"""Quick debug: check patient create and screening endpoints"""
import urllib.request, json, urllib.error

BASE = "http://127.0.0.1:8000"

def req(method, path, body=None, token=None):
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"}
    if token: headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except:
            return e.code, {"raw": e.read().decode()}

# Login
s, body = req("POST", "/api/v1/auth/login", {"phone": "+919999000001", "password": "drishti123"})
tok = body["access_token"]
print(f"Login: {s}")

# Create patient - debug exact error
s, body = req("POST", "/api/v1/patients", {
    "name": "Test Patient Debug",
    "age": 55,
    "gender": "M",
    "mobile": "+917900000099",
    "district_id": "DIST01",
    "block_id": "BLK01",
}, token=tok)
print(f"Create patient: {s}")
print("Response:", json.dumps(body, indent=2))

if "id" in body:
    pid = body["id"]
    # Screening debug
    s, body = req("POST", "/api/v1/screenings", {
        "patient_id": pid,
        "eye": "OD",
        "image_hash": "a" * 64,
        "quality_score": 0.92,
        "quality_defects": [],
        "severity_level": 3,
        "dme_risk": 0.65,
        "rule_trace": [{"rule_id": "ICDR-3.1", "met": True, "description": "test", "zones": ["zone_1"]}],
        "efs_score": 0.78,
        "captured_at": "2026-08-31T10:00:00Z",
    }, token=tok)
    print(f"\nScreening: {s}")
    print("Response:", json.dumps(body, indent=2))

    # Duplicate
    s, body = req("POST", "/api/v1/screenings", {
        "patient_id": pid,
        "eye": "OD",
        "image_hash": "a" * 64,
        "quality_score": 0.92,
        "quality_defects": [],
        "severity_level": 3,
        "rule_trace": [],
        "efs_score": 0.75,
        "captured_at": "2026-08-31T11:00:00Z",
    }, token=tok)
    print(f"\nDuplicate screening: {s}")
    print("Response:", json.dumps(body, indent=2))
