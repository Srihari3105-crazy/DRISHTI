# DRISHTI-LENS — Simulink Telemedicine Queuing & Workflow Model

**SIH 2026 Problem Statement Compliance Document**

---

## 1. Executive Summary & Modeling Rationale
The primary operational failure in rural tele-ophthalmology is **queue saturation and lost-to-follow-up**:
1. Field operators take ungradable photos without on-site feedback.
2. Huge backlogs of normal cases overload tertiary hospital ophthalmologists.
3. Patient waiting times stretch into weeks, leading to non-compliance and preventable blindness.

The DRISHTI-LENS Simulink model (`simulink/`) validates how combining **automated on-device Quality Gates**, **edge-AI referable triage**, and **structured explainability review (<30-second target)** resolves systemic bottlenecks at an annual scale of **100,000+ to 120,000 patients**.

---

## 2. Queuing Subsystems & Parameter Formulation

### 2.1 Arrival Process ($M$)
- Poisson distributed arrival rate:
  $$\lambda = \frac{N_{\text{annual}}}{D_{\text{days}} \times H_{\text{hours}}} = \frac{120,000}{300 \times 8} = 50 \text{ patients/hour} \approx 0.833 \text{ patients/minute}$$

### 2.2 Quality Gate Subsystem
- Immediate Pass Rate: $82\%$
- Borderline Rate (repaired on-site via CLAHE/normalization): $12\%$
- Rejected / Recapture Required on-site: $6\%$

### 2.3 Network & Storage Delay Buffer
- Local SQLite queue depth on mobile tablet: up to 10,000 screening records.
- 15% intermittent cellular link dropout model with exponential reconnection delay.

### 2.4 Doctor Service Facility ($M/M/c$)
- Pool of active district ophthalmologists: $c = 4$.
- Target review duration with DRISHTI-LENS structured UI: $\mu_{\text{target}} = 30 \text{ seconds/case}$.
- Baseline manual review duration without AI: $\mu_{\text{manual}} = 180 \text{ seconds/case}$.

---

## 3. Scenario Comparison & Empirical Results

| Metric | Scenario A: Cloud + Manual Review | Scenario B: Edge AI (No Quality Gate) | Scenario C: DRISHTI-LENS Ecosystem |
|---|---|---|---|
| **Shift Patient Load** | ~400 patients / shift | ~400 patients / shift | ~400 patients / shift |
| **Referrals Reaching Doctor** | 400 cases (100%) | 84 cases (21%) | 36 cases (9%) |
| **Doctor Time / Patient** | 180 seconds | 60 seconds | **<30 seconds** |
| **Peak Queue Backlog** | **>120 cases** (Severe saturation) | ~25 cases | **<4 cases** |
| **End-of-Shift Backlog** | **Unreviewed cases roll over** | Minor backlog | **Zero pending cases** |
| **Bandwidth Demand** | 1.28 GB continuous uplink | 268 MB uplink | **115 MB filtered sync** |

---

## 4. Execution & Artifacts
- Parameter dictionary: `simulink/parameters/default_params.m`
- Comparative simulation script: `simulink/scripts/run_simulation.m`
- Generated charts: `simulink/results/simulation_queue_comparison.png`
- Exported metrics: `simulink/results/simulation_metrics_comparison.csv`
- Programmatic block diagram builder: `simulink/scripts/build_simulink_model.m`
