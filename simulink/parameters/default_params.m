%DEFAULT_PARAMS Simulation parameter definitions for DR Telemedicine Ecosystem.
%  Units, default values, and operational boundaries for rural screening hubs.

params = struct();

% --- Population & Arrival Rates (Annual Scale: 100,000+ patients/year) ---
% 100,000 patients / 300 operational days / 8 hours/day = ~41.67 patients/hour
params.annual_target_screenings     = 120000;
params.annual_work_days             = 300;
params.daily_operating_hours        = 8;
params.hourly_patient_arrival_rate  = params.annual_target_screenings / (params.annual_work_days * params.daily_operating_hours); % ~50/hr

% --- Field Quality Gate Subsystem ---
params.quality_gate_pass_rate       = 0.82;   % 82% pass immediately
params.quality_gate_borderline_rate = 0.12;   % 12% undergo adaptive enhancement
params.quality_gate_reject_rate     = 0.06;   % 6% ungradable (prompt for recapture)
params.recapture_penalty_minutes    = 4.5;    % Time lost during recapture

% --- Rural Bandwidth & Network Queue ---
params.image_file_size_mb           = 3.2;    % High-res fundus JPEG
params.rural_uplink_mbps            = 1.5;    % Variable cellular 2G/3G/4G uplink
params.network_intermittent_prob    = 0.15;   % 15% probability of link disconnection
params.local_sqlite_buffer_capacity = 10000;  % Maximum offline queue depth on tablet

% --- Edge AI vs Cloud Inference Latency ---
params.edge_tflite_inference_sec    = 2.8;    % On-device mobile inference (sec/image)
params.cloud_gpu_inference_sec      = 0.35;   % Server-side inference

% --- Clinical Disease Prevalence ---
params.dr_prevalence_rate           = 0.22;   % 22% of diabetic patients exhibit DR
params.referable_dr_rate            = 0.09;   % 9% require hospital ophthalmic referral (ICDR >= 2)

% --- Ophthalmologist Review Capacity ---
params.num_active_ophthalmologists  = 4;      % In district hospital pool
params.target_review_seconds        = 30.0;   % Target <30 sec review time with AI assist
params.manual_review_seconds        = 180.0;  % Baseline manual fundus review time (3 mins)

% --- Simulation Timeframe ---
params.simulation_duration_hours    = 8;      % 1 single work shift (or 2400 for annual)
