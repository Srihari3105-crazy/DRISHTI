# DRISHTI-LENS — Offline-First Diabetic Retinopathy Screening MVP

> **Capture → Grade → Refer → Assign → Schedule → Visit → Close**

A complete DR screening loop for rural India, built for SIH 2026.  
Runs entirely on a laptop + 2 Android phones. No cloud dependency.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DRISHTI-LENS MVP                         │
│                                                             │
│  📱 Flutter App         🖥️ FastAPI Backend    🌐 Next.js     │
│  ─────────────────      ──────────────────   ───────────── │
│  Camera → Quality Gate  PostgreSQL + NATS    Officer Portal │
│  On-device Grading      JWT Auth + RBAC      Doctor Queue   │
│  Offline SQLite Queue   Referral State FSM   HMIS Export    │
│  Background Sync        Mock Notifications   Lesion Overlay │
└─────────────────────────────────────────────────────────────┘
```

**Tech Stack:** Flutter + ONNX Runtime Mobile · FastAPI · PostgreSQL · Next.js · Tailwind · Docker

---

## Quick Start (Demo)

### Prerequisites
- Docker Desktop running
- Node.js 20+
- Python 3.11+ (for scripts only)

### 1. Start Backend + Database

```bash
# From project root
docker compose up -d postgres nats
docker compose up backend
```

### 2. Seed Demo Data

```bash
cd backend
pip install -r requirements.txt
python scripts/seed.py
```

After seeding, credentials are printed:

| Role     | Phone           | Password     |
|----------|-----------------|-------------|
| Admin    | +919999000000   | admin123    |
| Operator | +919999000001   | drishti123  |
| Officer  | +919876540001   | drishti123  |
| Doctor   | +919876543001   | drishti123  |

### 3. Start Frontend

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

### 4. Run API Tests

```bash
cd backend
python scripts/test_api.py
```

---

## Project Structure

```
SIH_2026 code/
├── backend/                    # FastAPI
│   ├── core/
│   │   ├── config.py           # Pydantic Settings
│   │   ├── database.py         # Async SQLAlchemy
│   │   ├── security.py         # JWT + bcrypt
│   │   └── events.py           # Async event bus
│   ├── models/                 # SQLAlchemy ORM
│   │   ├── user.py             # Users + roles
│   │   ├── patient.py          # Patient registry
│   │   ├── screening.py        # Fundus + grading
│   │   ├── referral.py         # Referral FSM
│   │   ├── hospital.py         # Facility registry
│   │   ├── doctor.py           # Doctor profiles
│   │   ├── notification.py     # Reminder logs
│   │   └── officer.py          # Jurisdiction
│   ├── schemas/                # Pydantic v2 validation
│   ├── services/
│   │   ├── referral_service.py # State machine + auto-assign
│   │   ├── notification_service.py # Mock reminders
│   │   ├── doctor_verify_service.py # CSV lookup
│   │   └── export_service.py   # HMIS CSV
│   ├── api/                    # FastAPI routers
│   │   ├── auth.py             # Login + refresh
│   │   ├── patients.py         # CRUD + OTP
│   │   ├── screenings.py       # Sync from app
│   │   ├── referrals.py        # Queue + actions
│   │   ├── doctors.py          # Register + list
│   │   ├── officers.py         # Dashboard + stats
│   │   └── exports.py          # HMIS Form 1
│   ├── assets/seed/            # CSV seed data
│   ├── scripts/
│   │   ├── seed.py             # Full demo seed
│   │   └── test_api.py         # Integration tests
│   ├── main.py                 # Entry point
│   └── requirements.txt
│
├── frontend/                   # Next.js 15 App Router
│   └── src/
│       ├── lib/
│       │   ├── api.ts          # Axios + JWT interceptors
│       │   ├── auth.tsx        # Auth context + hooks
│       │   └── types.ts        # Shared TypeScript types
│       └── app/
│           ├── login/          # Login page
│           └── dashboard/
│               ├── officer/    # Stats + referral table
│               ├── doctor/     # My queue + filters
│               ├── referrals/  # Full queue + pagination
│               │   └── [id]/   # Case detail + modals
│               ├── auto-assign/ # One-click bulk assign
│               ├── patients/   # Patient list + search
│               └── exports/    # HMIS CSV download
│
├── mobile/                     # Flutter 3.24+
│   └── lib/
│       ├── core/
│       │   ├── constants.dart  # Config + thresholds
│       │   ├── theme.dart      # Material 3 dark
│       │   └── router.dart     # go_router
│       └── features/
│           ├── auth/           # Login + JWT secure storage
│           ├── patient/        # List + register
│           ├── capture/        # Camera + quality gate + grading
│           ├── referral/       # Queue + background sync
│           └── settings/       # Sync status + model info
│
└── docker-compose.yml          # PostgreSQL + NATS + Backend + Frontend
```

---

## API Reference

### Base URL: `http://localhost:8000/api/v1`

All protected endpoints require `Authorization: Bearer <token>`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Login (phone + password) |
| POST | `/auth/refresh` | Refresh access token |
| GET | `/patients` | List patients (search/filter) |
| POST | `/patients` | Register patient |
| POST | `/patients/{id}/verify-mobile` | Send OTP |
| POST | `/patients/{id}/confirm-mobile` | Verify OTP |
| POST | `/screenings` | Submit screening (auto-refers if severity ≥ 2) |
| GET | `/referrals` | List referrals (filter by state) |
| GET | `/referrals/{id}` | Get referral detail |
| POST | `/referrals/auto-assign` | Bulk auto-assign queued referrals |
| POST | `/referrals/{id}/assign` | Manually assign to doctor |
| POST | `/referrals/{id}/schedule` | Schedule appointment |
| POST | `/referrals/{id}/visit` | Mark visited + close |
| POST | `/referrals/{id}/retake` | Request image retake |
| GET | `/referrals/{id}/notifications` | Reminder log |
| GET | `/officers/dashboard` | Stats: closure rate, counts, severity breakdown |
| GET | `/officers/hospitals` | List hospitals in jurisdiction |
| GET | `/doctors` | List doctors in district |
| POST | `/doctors/register` | Doctor self-registration (CSV verify) |
| GET | `/referrals/export/hmis-form1` | HMIS CSV export |

---

## Referral State Machine

```
QUEUED → ASSIGNED → SCHEDULED → REMINDERS_ACTIVE → VISITED → CLOSED
                 ↘ QUEUED (retake requested)
```

- **QUEUED**: Auto-created when screening severity ≥ 2
- **ASSIGNED**: Officer manual or auto-assign to doctor
- **SCHEDULED**: Doctor sets date + hospital
- **REMINDERS_ACTIVE**: 48h + 2h SMS/WhatsApp reminders fired
- **VISITED**: Doctor marks patient attended
- **CLOSED**: System closes, logs visit notes

---

## AI Grading (MVP Mode)

The MVP uses **mock inference** — real models slot in with no code changes:

| Component | Mock | Production |
|-----------|------|-----------|
| Quality Gate | Random score 0.6–0.98 | TFLite `quality_gate_v1.tflite` (4.8MB) |
| 7-class Lesion Seg | Mock RLE strings | ONNX `lesion_sev_v1.onnx` (18.2MB) |
| ICDR Rule Engine | Hardcoded per severity | Same rule engine, real masks input |
| EFS Score | Random 0.65–0.95 | Composite from model outputs |
| DME Risk | Random per severity | Binary classifier head |

To enable real models:
1. Place `.tflite` and `.onnx` in `mobile/assets/models/`
2. Uncomment model packages in `pubspec.yaml`
3. Replace mock logic in `capture_bloc.dart` with inference calls

---

## Demo Walkthrough

### Recommended Demo Flow (10 minutes)

1. **📱 Flutter App** (Operator's phone)
   - Login as Operator
   - Register a new patient
   - Capture fundus (quality gate shows GOOD/RETAKE in real-time)
   - Grade shows Severe NPDR → auto-refer fires

2. **🖥️ Officer Portal** (`http://localhost:3000`)
   - Login as Officer → Officer Dashboard
   - See referral stats + severity distribution
   - Click **Auto-Assign** → assigns to available ophthalmologist

3. **🩺 Doctor Portal**
   - Login as Doctor → My Queue
   - Open case → see ICDR rule trace, EFS badge, lesion types
   - Schedule appointment → reminder log activates
   - Mark Visited → referral closes

4. **📊 HMIS Export**
   - Officer → Export → Download CSV
   - Show NPCBVI Form 1 columns

---

## Environment Variables

```bash
# Backend (.env or docker-compose.yml)
DATABASE_URL=postgresql+asyncpg://drishti:drishti_dev@postgres:5432/drishti_lens
JWT_SECRET=your-32-char-secret-key-here
JWT_ALGO=HS256
ACCESS_TOKEN_EXPIRE_MIN=30
REFRESH_TOKEN_EXPIRE_DAYS=7
UPLOAD_DIR=./uploads
DOCTOR_CSV_PATH=./assets/seed/doctors.csv
HOSPITAL_CSV_PATH=./assets/seed/hospitals.csv
OFFICER_CSV_PATH=./assets/seed/officers.csv

# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Mobile (lib/core/constants.dart)
# Change apiBaseUrl to your laptop's IP on the local network
```

---

## MVP Scope

| ✅ In MVP | ❌ Deferred to v2 |
|-----------|-----------------|
| On-device quality gate | Real TFLite model OTA update |
| Mock grading (drop-in ready) | WhatsApp Business API |
| Referral FSM + auto-assign | IVR, SMS delivery |
| Doctor portal (schedule + visit) | ABDM consent artefacts |
| Officer dashboard + closure % | Longitudinal registry |
| Mock reminder log | Auto-escalation rules |
| HMIS Form 1 CSV export | Medical Council API |
| OTP-verified mobile (mock) | NPCBVI HMIS API push |

---

*Built for Smart India Hackathon 2026 — Team DRISHTI-LENS*
