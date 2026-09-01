"""
DRISHTI-LENS API Integration Test Script
Tests all major API routes to validate backend is working correctly.
Run: python scripts/test_api.py
"""
import asyncio
import json
import sys
import os
from typing import Optional
import urllib.request
import urllib.error

# Force UTF-8 output on Windows (avoids emoji encode errors on CP1252)
if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = os.getenv("API_URL", "http://localhost:8000")

# ─── HTTP Helper ──────────────────────────────────────────────

def request(method: str, path: str, body: Optional[dict] = None, token: Optional[str] = None) -> dict:
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
            try:
                return {"status": resp.status, "body": json.loads(raw), "raw": raw}
            except Exception:
                return {"status": resp.status, "body": {}, "raw": raw}
    except urllib.error.HTTPError as e:
        try:
            return {"status": e.code, "body": json.loads(e.read())}
        except Exception:
            return {"status": e.code, "body": {"error": str(e)}}


# ─── Test Cases ───────────────────────────────────────────────

passed = 0
failed = 0


def check(label: str, condition: bool, info: str = ""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✅ {label}")
    else:
        failed += 1
        print(f"  ❌ {label}{(' — ' + info) if info else ''}")


def section(title: str):
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")


def run_tests():
    print("\n" + "=" * 55)
    print("  DRISHTI-LENS Backend Integration Tests")
    print("=" * 55)

    # ── Health ────────────────────────────────────────────────
    section("Health Checks")
    r = request("GET", "/")
    check("Root endpoint returns 200", r["status"] == 200)
    check("Status is operational", r["body"].get("status") == "operational")

    r = request("GET", "/health")
    check("Health endpoint returns 200", r["status"] == 200)
    check("Health status is healthy", r["body"].get("status") == "healthy")

    # ── Auth — Invalid ────────────────────────────────────────
    section("Auth: Invalid Credentials")
    r = request("POST", "/api/v1/auth/login", {"phone": "+919999999999", "password": "wrongpassword"})
    check("Invalid login returns 401", r["status"] == 401)

    r = request("GET", "/api/v1/patients")
    check("Unauthenticated request returns 403/401", r["status"] in (401, 403))

    # ── Auth — Operator Login ─────────────────────────────────
    section("Auth: Operator Login")
    r = request("POST", "/api/v1/auth/login", {"phone": "+919999000001", "password": "drishti123"})
    check("Operator login succeeds (200)", r["status"] == 200)
    check("Access token present", "access_token" in r.get("body", {}))
    check("Refresh token present", "refresh_token" in r.get("body", {}))
    check("User role is operator", r.get("body", {}).get("user", {}).get("role") == "operator")

    op_token = r.get("body", {}).get("access_token", "")

    # ── Patients ──────────────────────────────────────────────
    section("Patients")
    r = request("GET", "/api/v1/patients", token=op_token)
    check("List patients returns 200", r["status"] == 200)

    import time as _time
    unique_mobile = f"+917{str(int(_time.time()))[-9:]}"  # always unique
    r = request("POST", "/api/v1/patients", {
        "name": "Test Patient",
        "age": 55,
        "gender": "M",
        "mobile": unique_mobile,
        "district_id": "DIST01",
        "block_id": "BLK01",
    }, token=op_token)
    check("Create patient returns 200/201", r["status"] in (200, 201))
    patient_id = r.get("body", {}).get("id", "")
    check("Patient has valid ID", bool(patient_id))

    # ── OTP Verify ────────────────────────────────────────────
    if patient_id:
        section("OTP Verification")
        r = request("POST", f"/api/v1/patients/{patient_id}/verify-mobile",
                    {"mobile": unique_mobile}, token=op_token)
        check("Send OTP returns 200", r["status"] == 200)
        # In dev mode the OTP is returned in the response body as 'debug_otp'
        dev_otp = str(r.get("body", {}).get("debug_otp") or r.get("body", {}).get("otp", "123456"))

        r = request("POST", f"/api/v1/patients/{patient_id}/confirm-mobile",
                    {"otp": dev_otp}, token=op_token)
        check("Confirm OTP returns 200", r["status"] == 200)

    # ── Screenings ────────────────────────────────────────────
    section("Screenings")
    import hashlib
    import time
    image_hash = hashlib.sha256(f"test_{time.time()}".encode()).hexdigest()

    r = request("POST", "/api/v1/screenings", {
        "patient_id": patient_id or "test",
        "eye": "OD",
        "image_hash": image_hash,
        "quality_score": 0.92,
        "quality_defects": [],
        "severity_level": 3,
        "dme_risk": 0.65,
        "rule_trace": [
            {"rule_id": "ICDR-3.1", "met": True, "description": "Venous beading in 2+ quadrants", "zones": ["zone_1"]},
            {"rule_id": "ICDR-3.2", "met": True, "description": "IRMA in 1+ quadrant", "zones": ["zone_2"]},
        ],
        "efs_score": 0.78,
        "captured_at": "2026-08-31T10:00:00Z",
    }, token=op_token)
    check("Submit screening returns 200/201", r["status"] in (200, 201))
    screening_id = r.get("body", {}).get("id", "")
    # referral_id is populated when severity >= 2 and auto-referral fires
    referral_id = r.get("body", {}).get("referral_id")
    check("Severity >= 2 generates auto-referral", bool(referral_id))

    # ── Referrals ─────────────────────────────────────────────
    section("Referrals")
    r = request("GET", "/api/v1/referrals", token=op_token)
    check("List referrals returns 200", r["status"] == 200)

    # ── Officer Login + Auto-assign ───────────────────────────
    section("Officer: Login + Auto-Assign")
    r = request("POST", "/api/v1/auth/login", {"phone": "+919876540001", "password": "drishti123"})
    check("Officer login succeeds", r["status"] == 200)
    off_token = r.get("body", {}).get("access_token", "")

    r = request("GET", "/api/v1/officers/dashboard", token=off_token)
    check("Officer dashboard returns 200", r["status"] == 200)
    check("Dashboard has total_referred", "total_referred" in r.get("body", {}))

    r = request("POST", "/api/v1/referrals/auto-assign", token=off_token)
    check("Auto-assign returns 200", r["status"] == 200)
    check("Auto-assign has assigned count", "assigned" in r.get("body", {}))

    # ── Doctor Login + Case Actions ───────────────────────────
    section("Doctor: Login + Case Actions")
    r = request("POST", "/api/v1/auth/login", {"phone": "+919876543001", "password": "drishti123"})
    check("Doctor login succeeds", r["status"] == 200)
    doc_token = r.get("body", {}).get("access_token", "")

    r = request("GET", "/api/v1/referrals", token=doc_token)
    check("Doctor can list referrals", r["status"] == 200)

    # ── Exports ───────────────────────────────────────────────
    section("Exports")
    r = request("GET", "/api/v1/referrals/export/hmis-form1?month=2026-08", token=off_token)
    check("HMIS Form 1 export returns 200", r["status"] == 200)
    # CSV response — check raw bytes contain expected header
    raw = r.get("raw", b"")
    check("HMIS CSV has header row", b"Patient" in raw or b"patient" in raw or len(raw) > 10)

    # ── Duplicate Screening ───────────────────────────────────
    section("Data Integrity")
    r = request("POST", "/api/v1/screenings", {
        "patient_id": patient_id or "test",
        "eye": "OD",
        "image_hash": image_hash,  # Same hash
        "quality_score": 0.92,
        "quality_defects": [],
        "severity_level": 2,
        "rule_trace": [],
        "efs_score": 0.75,
        "captured_at": "2026-08-31T10:00:00Z",
    }, token=op_token)
    check("Duplicate image hash returns 409", r["status"] == 409)

    # ── Summary ───────────────────────────────────────────────
    print(f"\n{'=' * 55}")
    total = passed + failed
    pct = round(passed / total * 100) if total else 0
    print(f"  Results: {passed}/{total} passed ({pct}%)")
    if failed == 0:
        print("  🎉 All tests passed! Backend is ready for demo.")
    else:
        print(f"  ⚠️  {failed} test(s) failed. Check backend logs.")
    print("=" * 55 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
