# DRISHTI-LENS — Production Deployment & Field Setup Guide

---

## 1. System Architecture
DRISHTI-LENS is partitioned into three operational tiers:
1. **Edge Client (Mobile / Tablet):** Offline-first Flutter app with local SQLite (Drift) queue, camera quality feedback, and AES-256 encrypted storage.
2. **Rural Gateway / Backend:** FastAPI microservice powering asynchronous batch ingestion, real-time AI inference, Grad-CAM generation, and NPCBVI HMIS Form 1 reporting.
3. **Clinical Web Portal:** Next.js dashboard providing ophthalmologist triage queues, <30-second review stopwatch, and interactive Grad-CAM adjudication.

---

## 2. Environment Setup & Bootstrapping

### 2.1 Backend Server (Local / Docker)
```bash
cd backend

# Option A: Local Dev Server (SQLite + Python 3.13)
py -3.13 dev_start.py

# Option B: Docker Production Cluster
docker compose -f ../docker/docker-compose.yml up -d --build
```
API endpoints are served at `http://localhost:8000`. Interactive OpenAPI documentation is accessible at `http://localhost:8000/docs`.

### 2.2 Database Initialization & Seeding
To populate clinical referral queues, mock patients, and doctor directories:
```bash
cd backend
py -3.13 scripts/seed.py
```

### 2.3 Frontend Clinical Web Portal
```bash
cd frontend
npm install
npm run dev
```
Dashboard is served at `http://localhost:3000`.

---

## 3. MATLAB & Simulink Runtime Deployment

### 3.1 Headless MATLAB Execution
To run the automated DR screening pipeline on fundus batches without GUI overhead:
```bash
matlab -batch "cd('matlab/pipeline'); dr_screening_pipeline('sample.jpg', './out'); exit;"
```

### 3.2 Running the Telemedicine Queuing Simulation
```bash
matlab -batch "cd('simulink/scripts'); run_simulation; exit;"
```
Results and comparative workload plots will be saved to `simulink/results/`.
