# DRISHTI-LENS — Telemedicine Queuing & Workflow Simulation (Simulink)

This directory models and simulates the end-to-end operational dynamics of a large-scale rural Diabetic Retinopathy screening network for Smart India Hackathon (SIH) 2026.

---

## 1. Simulation Objectives
- Model an operational throughput of **100,000+ to 120,000 screenings per year** across district PHC networks.
- Evaluate the impact of intermittent 2G/3G connectivity on local SQLite buffer capacity.
- Quantify the reduction in ophthalmologist backlog achieved by:
  1. The automated field **Quality Gate** (rejecting ungradables on-site before referral).
  2. The **<30-second target review UI** with AI explainability overlays vs. traditional 3-minute manual grading.

---

## 2. Directory Layout
```
simulink/
├── dr_screening_workflow.slx      # Simulink system model
├── parameters/
│   └── default_params.m           # Screening arrival rates, doctor capacity, bandwidth parameters
├── scripts/
│   ├── run_simulation.m           # Multi-scenario Monte Carlo queuing runner (A/B/C)
│   └── build_simulink_model.m     # Programmatic Simulink block diagram generator
└── results/
    ├── simulation_queue_comparison.png
    └── simulation_metrics_comparison.csv
```

---

## 3. Scenarios Evaluated
- **Scenario A (Traditional Telemedicine):** Centralized cloud upload without on-device edge AI. All images reviewed manually (mean review time: 180 seconds). Result: Immediate queue saturation and high doctor fatigue.
- **Scenario B (Edge AI without Quality Gate):** High ungradable rate (18%) causes diagnostic friction and unnecessary specialist queries.
- **Scenario C (DRISHTI-LENS Closed Loop):** Edge AI + Quality Gate triage. Only true referable cases (ICDR $\ge 2$, ~9%) reach ophthalmologists, and structured AI evidence reduces review time to $<30$ seconds. Result: Zero persistent backlog at end of shift.

---

## 4. How to Run
```matlab
% In MATLAB:
cd('c:/Users/dell/Downloads/DRISHTI-main/simulink/scripts');
run_simulation;
```
Outputs are written to `simulink/results/`.
