/** Shared TypeScript types for the frontend */

export type UserRole = 'operator' | 'doctor' | 'officer' | 'admin';

export type ReferralState =
  | 'queued'
  | 'assigned'
  | 'scheduled'
  | 'reminders_active'
  | 'visited'
  | 'closed';

export interface User {
  id: string;
  phone: string;
  name: string;
  role: UserRole;
  district_id?: string;
  block_id?: string;
  is_verified: boolean;
}

export interface Patient {
  id: string;
  abha_id?: string;
  local_id?: string;
  name: string;
  age: number;
  gender: string;
  mobile: string;
  mobile_verified: boolean;
  email?: string;
  district_id: string;
  block_id: string;
  phc_id?: string;
  diabetes_type?: string;
  diabetes_duration_years?: number;
  hba1c?: number;
  created_at: string;
}

export interface ScreeningEvent {
  id: string;
  patient_id: string;
  operator_id: string;
  eye: 'OD' | 'OS';
  image_hash: string;
  image_path?: string;
  quality_score: number;
  quality_defects?: string[];
  lesion_masks_rle?: Record<string, string>;
  severity_level: number;
  dme_risk?: number;
  rule_trace: RuleTraceItem[];
  efs_score: number;
  captured_at: string;
  synced_at?: string;
  adjudication_status: string;
  gradcam_url?: string;
  report_url?: string;
  quality_decision?: string;
  enhancement_applied?: boolean;
  calibrated_confidence?: number;
}

export interface RuleTraceItem {
  rule_id: string;
  met: boolean;
  description: string;
  zones: string[];
}

export interface Referral {
  id: string;
  referral_code: string;
  state: ReferralState;
  screening_event_id: string;
  assigned_doctor_id?: string;
  assigned_officer_id?: string;
  hospital_id?: string;
  scheduled_at?: string;
  appointment_token?: string;
  visit_notes?: string;
  retake_reason?: string;
  closure_reason?: string;
  created_at: string;
  closed_at?: string;
  // Joined fields
  patient_name?: string;
  patient_age?: number;
  patient_mobile?: string;
  doctor_name?: string;
  hospital_name?: string;
  severity_level?: number;
  efs_score?: number;
  eye?: string;
}

export interface Hospital {
  id: string;
  name: string;
  address: string;
  latitude?: number;
  longitude?: number;
  district_id: string;
  phone?: string;
  facility_type: string;
}

export interface OfficerDashboard {
  total_referred: number;
  assigned: number;
  scheduled: number;
  visited: number;
  closed: number;
  closure_rate: number;
  avg_days_to_close: number;
  by_block: Record<string, Record<string, number>>;
  by_severity: Record<number, number>;
}

export interface NotificationLogEntry {
  id: string;
  channel: string;
  template_key: string;
  status: string;
  scheduled_for?: string;
  sent_at?: string;
  delivered_at?: string;
  message: string;
}

export interface Doctor {
  id: string;
  name: string;
  phone: string;
  reg_no: string;
  hospital_name: string;
  hospital_id: string;
  specialization: string;
}

// Severity helpers
export const SEVERITY_LABELS: Record<number, string> = {
  0: 'No DR',
  1: 'Mild NPDR',
  2: 'Moderate NPDR',
  3: 'Severe NPDR',
  4: 'PDR',
};

export const SEVERITY_COLORS: Record<number, string> = {
  0: '#22c55e',  // green
  1: '#eab308',  // yellow
  2: '#f97316',  // orange
  3: '#ef4444',  // red
  4: '#dc2626',  // dark red
};

export const STATE_COLORS: Record<ReferralState, string> = {
  queued: '#94a3b8',
  assigned: '#3b82f6',
  scheduled: '#8b5cf6',
  reminders_active: '#f59e0b',
  visited: '#22c55e',
  closed: '#6b7280',
};

export const STATE_LABELS: Record<ReferralState, string> = {
  queued: 'Queued',
  assigned: 'Assigned',
  scheduled: 'Scheduled',
  reminders_active: 'Reminders Active',
  visited: 'Visited',
  closed: 'Closed',
};
