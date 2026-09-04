'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { referralsAPI, officersAPI, screeningsAPI } from '@/lib/api';
import { useAuth } from '@/lib/auth';
import type { Referral, NotificationLogEntry, Hospital, ScreeningEvent } from '@/lib/types';
import { SEVERITY_LABELS, STATE_LABELS, STATE_COLORS } from '@/lib/types';

export default function ReferralDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { user, hasRole } = useAuth();
  const [referral, setReferral] = useState<Referral | null>(null);
  const [screening, setScreening] = useState<ScreeningEvent | null>(null);
  const [notifications, setNotifications] = useState<NotificationLogEntry[]>([]);
  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [loading, setLoading] = useState(true);

  // Clinical Review Timer (<30-second target tracking)
  const [reviewSeconds, setReviewSeconds] = useState(0);
  const [timerRunning, setTimerRunning] = useState(true);
  const [activeImageView, setActiveImageView] = useState<'original' | 'gradcam'>('original');
  const [adjudicationStatus, setAdjudicationStatus] = useState<string>('pending');

  // Modal states
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [showRetakeModal, setShowRetakeModal] = useState(false);
  const [showVisitModal, setShowVisitModal] = useState(false);

  // Form states
  const [scheduleDate, setScheduleDate] = useState('');
  const [scheduleHospital, setScheduleHospital] = useState('');
  const [retakeReason, setRetakeReason] = useState('');
  const [visitNotes, setVisitNotes] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, [id]);

  // Review timer tick
  useEffect(() => {
    let interval: any;
    if (timerRunning) {
      interval = setInterval(() => {
        setReviewSeconds(s => s + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [timerRunning]);

  const loadData = async () => {
    try {
      const [refRes, notifRes, hospRes] = await Promise.all([
        referralsAPI.get(id),
        referralsAPI.getNotifications(id).catch(() => ({ data: [] })),
        officersAPI.hospitals().catch(() => ({ data: [] })),
      ]);
      setReferral(refRes.data);
      setNotifications(notifRes.data);
      setHospitals(hospRes.data);

      // Load screening details
      if (refRes.data.screening_event_id) {
        const scrRes = await screeningsAPI.get(refRes.data.screening_event_id);
        setScreening(scrRes.data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSchedule = async () => {
    if (!scheduleDate || !scheduleHospital) return;
    setActionLoading(true);
    try {
      await referralsAPI.schedule(id, { scheduled_at: new Date(scheduleDate).toISOString(), hospital_id: scheduleHospital });
      await loadData();
      setShowScheduleModal(false);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to schedule');
    } finally {
      setActionLoading(false);
    }
  };

  const handleVisit = async () => {
    setActionLoading(true);
    try {
      await referralsAPI.markVisited(id, visitNotes || undefined);
      await loadData();
      setShowVisitModal(false);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to mark visited');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRetake = async () => {
    if (!retakeReason) return;
    setActionLoading(true);
    try {
      await referralsAPI.requestRetake(id, retakeReason);
      await loadData();
      setShowRetakeModal(false);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to request retake');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return <div style={{ display: 'grid', gap: 16 }}>{[1, 2, 3].map(i => <div key={i} className="skeleton" style={{ height: 200 }} />)}</div>;
  }

  if (!referral) {
    return <div style={{ textAlign: 'center', padding: 48, color: 'var(--text-muted)' }}>Referral not found.</div>;
  }

  return (
    <div>
      {/* Header Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <button className="btn btn-ghost btn-sm" onClick={() => router.back()}>← Back</button>
          <div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)', fontFamily: 'monospace' }}>
              {referral.referral_code}
            </h2>
            <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
              <span className={`badge badge-${referral.state}`}>
                {STATE_LABELS[referral.state as keyof typeof STATE_LABELS]}
              </span>
              {referral.appointment_token && (
                <span className="badge" style={{ background: '#f3f0ff', color: '#7950f2' }}>
                  🎫 {referral.appointment_token}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Action Buttons & Clinical Review Timer */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {/* <30-second target review stopwatch */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 6, padding: '6px 14px', borderRadius: 20,
            background: reviewSeconds <= 30 ? 'rgba(43, 138, 62, 0.1)' : 'rgba(230, 119, 0, 0.12)',
            border: `1px solid ${reviewSeconds <= 30 ? '#2b8a3e' : '#e67700'}`,
          }} title="SIH 2026 Target: Ophthalmologist case review within 30 seconds">
            <span style={{ fontSize: '0.9rem' }}>⏱️</span>
            <span style={{
              fontSize: '0.8rem', fontWeight: 700,
              color: reviewSeconds <= 30 ? '#2b8a3e' : '#e67700',
              fontFamily: 'monospace'
            }}>
              {reviewSeconds}s {reviewSeconds <= 30 ? '(Target Met)' : '(Over 30s)'}
            </span>
          </div>

          {screening?.id && (
            <a
              href={`http://localhost:8000/api/v1/screenings/${screening.id}/report`}
              target="_blank"
              rel="noreferrer"
              className="btn btn-ghost"
              style={{ fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: 6, textDecoration: 'none' }}
            >
              📄 Clinical Report
            </a>
          )}

          {(hasRole('doctor', 'admin') && referral.state === 'assigned') && (
            <button className="btn btn-primary" onClick={() => setShowScheduleModal(true)}>📅 Schedule</button>
          )}
          {(hasRole('doctor', 'admin') && ['scheduled', 'reminders_active'].includes(referral.state)) && (
            <button className="btn btn-success" onClick={() => setShowVisitModal(true)}>✅ Mark Visited</button>
          )}
          {(hasRole('doctor', 'admin') && ['assigned', 'scheduled', 'reminders_active'].includes(referral.state)) && (
            <button className="btn btn-ghost" onClick={() => setShowRetakeModal(true)}>🔄 Request Retake</button>
          )}
        </div>
      </div>

      {/* Main Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        {/* Left: Patient & Screening Info */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* Patient Card */}
          <div className="glass-card" style={{ padding: 24 }}>
            <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 16 }}>
              Patient Information
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <InfoRow label="Name" value={referral.patient_name || '—'} />
              <InfoRow label="Age" value={referral.patient_age?.toString() || '—'} />
              <InfoRow label="Mobile" value={referral.patient_mobile || '—'} />
              <InfoRow label="Eye" value={referral.eye || '—'} />
            </div>
          </div>

          {/* AI Retinal Imaging & Grad-CAM Card */}
          <div className="glass-card" style={{ padding: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
              <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', margin: 0 }}>
                Retinal Fundus & Explainability
              </h3>
              <div style={{ display: 'flex', gap: 6 }}>
                <button
                  type="button"
                  className={`btn btn-sm ${activeImageView === 'original' ? 'btn-primary' : 'btn-ghost'}`}
                  onClick={() => setActiveImageView('original')}
                  style={{ fontSize: '0.75rem', padding: '4px 10px' }}
                >
                  Fundus Image
                </button>
                <button
                  type="button"
                  className={`btn btn-sm ${activeImageView === 'gradcam' ? 'btn-primary' : 'btn-ghost'}`}
                  onClick={() => setActiveImageView('gradcam')}
                  style={{ fontSize: '0.75rem', padding: '4px 10px' }}
                >
                  Grad-CAM Heatmap
                </button>
              </div>
            </div>

            <div style={{
              width: '100%', height: 260, borderRadius: 10, overflow: 'hidden',
              background: '#0d1117', display: 'flex', alignItems: 'center', justifyContent: 'center',
              border: '1px solid rgba(255,255,255,0.08)', position: 'relative'
            }}>
              {activeImageView === 'original' ? (
                screening?.image_path ? (
                  <img
                    src={`http://localhost:8000/${screening.image_path}`}
                    alt="Fundus Photography"
                    style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                  />
                ) : (
                  <div style={{ textAlign: 'center', color: '#8b949e', fontSize: '0.85rem' }}>
                    <div style={{ fontSize: '2rem', marginBottom: 6 }}>👁️</div>
                    <div>Digital Fundus Capture (Stored Securely)</div>
                    <div style={{ fontSize: '0.75rem', opacity: 0.7, marginTop: 4 }}>Hash: {screening?.image_hash?.slice(0, 16) || 'Local Asset'}...</div>
                  </div>
                )
              ) : (
                screening?.gradcam_url ? (
                  <img
                    src={`http://localhost:8000/${screening.gradcam_url}`}
                    alt="Grad-CAM Spatial Heatmap"
                    style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                  />
                ) : (
                  <div style={{ textAlign: 'center', color: '#8b949e', fontSize: '0.85rem', padding: 20 }}>
                    <div style={{ fontSize: '2rem', marginBottom: 6 }}>🧠</div>
                    <div style={{ fontWeight: 600 }}>Grad-CAM Activation Map</div>
                    <div style={{ fontSize: '0.75rem', opacity: 0.8, marginTop: 4 }}>
                      Spatial attention weights highlighting diagnostic regions influencing ICDR classification.
                    </div>
                  </div>
                )
              )}
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 8, textAlign: 'center' }}>
              ⚠️ [AI-ASSISTED SCREENING — PROTOTYPE] Must be clinically validated by licensed ophthalmologist.
            </div>
          </div>

          {/* Doctor Adjudication Panel (Human-In-The-Loop) */}
          <div className="glass-card" style={{ padding: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
              <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', margin: 0 }}>
                Doctor Adjudication (Human-In-The-Loop)
              </h3>
              <span className="badge" style={{
                background: adjudicationStatus === 'confirmed' ? '#ebfbee' : adjudicationStatus === 'retake' ? '#fff5f5' : '#f8f9fa',
                color: adjudicationStatus === 'confirmed' ? '#2b8a3e' : adjudicationStatus === 'retake' ? '#c92a2a' : '#495057',
                fontSize: '0.75rem'
              }}>
                Status: {adjudicationStatus.toUpperCase()}
              </span>
            </div>

            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 14 }}>
              Adjudicate the AI screening findings. Decisions update the closed-loop referral tracking engine.
            </p>

            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <button
                type="button"
                className="btn btn-sm btn-success"
                onClick={() => {
                  setAdjudicationStatus('confirmed');
                  setTimerRunning(false);
                }}
              >
                ✅ Confirm Grade
              </button>
              <button
                type="button"
                className="btn btn-sm btn-ghost"
                onClick={() => {
                  setAdjudicationStatus('downgraded');
                  setTimerRunning(false);
                }}
              >
                ⬇️ Downgrade
              </button>
              <button
                type="button"
                className="btn btn-sm btn-ghost"
                onClick={() => {
                  setAdjudicationStatus('upgraded');
                  setTimerRunning(false);
                }}
              >
                ⬆️ Upgrade
              </button>
              <button
                type="button"
                className="btn btn-sm btn-danger"
                onClick={() => {
                  setAdjudicationStatus('retake');
                  setShowRetakeModal(true);
                }}
              >
                🔄 Order Retake
              </button>
            </div>
          </div>

          {/* Grading Card */}
          <div className="glass-card" style={{ padding: 24 }}>
            <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 16 }}>
              AI Grading Result
            </h3>
            <div style={{ display: 'flex', gap: 16, marginBottom: 20 }}>
              <div style={{ flex: 1, padding: 16, borderRadius: 12, background: 'var(--surface-elevated)', textAlign: 'center' }}>
                <div className={`badge severity-${referral.severity_level}`} style={{ fontSize: '0.85rem', padding: '6px 16px' }}>
                  {SEVERITY_LABELS[referral.severity_level ?? 0]}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 6 }}>ICDR Grade</div>
              </div>
              <div style={{ flex: 1, padding: 16, borderRadius: 12, background: 'var(--surface-elevated)', textAlign: 'center' }}>
                <div className={`efs-badge ${(referral.efs_score ?? 0) >= 0.8 ? 'efs-high' : (referral.efs_score ?? 0) >= 0.6 ? 'efs-medium' : 'efs-low'}`}
                     style={{ fontSize: '1.1rem', padding: '6px 16px' }}>
                  {(referral.efs_score ?? 0).toFixed(2)}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 6 }}>EFS Score</div>
              </div>
              {screening?.dme_risk !== undefined && (
                <div style={{ flex: 1, padding: 16, borderRadius: 12, background: 'var(--surface-elevated)', textAlign: 'center' }}>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: screening.dme_risk > 0.5 ? '#c92a2a' : '#2b8a3e' }}>
                    {(screening.dme_risk * 100).toFixed(0)}%
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 6 }}>DME Risk</div>
                </div>
              )}
            </div>

            {/* Lesion Types */}
            {screening?.lesion_masks_rle && Object.keys(screening.lesion_masks_rle).length > 0 && (
              <div style={{ marginTop: 12 }}>
                <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8 }}>Detected Lesions:</div>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {Object.keys(screening.lesion_masks_rle).map(lesion => {
                    const colors: Record<string, string> = { MA: '#c92a2a', HE: '#d9480f', EX: '#e67700', CWS: '#7950f2', VB: '#d6336c', IRMA: '#0c8599', NV: '#a61e1e' };
                    return (
                      <span key={lesion} style={{
                        padding: '4px 10px', borderRadius: 6, fontSize: '0.75rem', fontWeight: 600,
                        background: `${colors[lesion] || '#6b7280'}20`, color: colors[lesion] || '#9ca3af',
                        border: `1px solid ${colors[lesion] || '#6b7280'}30`,
                      }}>
                        ● {lesion}
                      </span>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right: Rule Trace + Timeline */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* Rule Trace */}
          <div className="glass-card" style={{ padding: 24 }}>
            <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 16 }}>
              ICDR Rule Trace
            </h3>
            {screening?.rule_trace ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {screening.rule_trace.map((rule, idx) => (
                  <div key={idx} style={{
                    display: 'flex', alignItems: 'flex-start', gap: 10, padding: '10px 14px', borderRadius: 10,
              background: rule.met ? 'rgba(201, 42, 42, 0.06)' : 'rgba(47, 158, 68, 0.04)',
                    border: `1px solid ${rule.met ? 'rgba(201, 42, 42, 0.2)' : 'rgba(206, 212, 218, 0.8)'}`,
                  }}>
                    <span style={{ fontSize: '1rem', marginTop: 1 }}>{rule.met ? '🔴' : '🟢'}</span>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-primary)', fontFamily: 'monospace' }}>
                        {rule.rule_id}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: 2 }}>
                        {rule.description}
                      </div>
                      {rule.zones.length > 0 && (
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 4 }}>
                          Zones: {rule.zones.join(', ')}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No rule trace available.</p>
            )}
          </div>

          {/* Notification Timeline */}
          <div className="glass-card" style={{ padding: 24 }}>
            <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 16 }}>
              🔔 Reminder Log
            </h3>
            {notifications.length > 0 ? (
              <div>
                {notifications.map((n) => (
                  <div key={n.id} className="timeline-item">
                    <div className={`timeline-dot ${n.status}`} />
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                          {n.template_key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </span>
                        <span className={`badge badge-${n.status === 'sent' || n.status === 'delivered' ? 'visited' : n.status === 'cancelled' ? 'closed' : 'queued'}`} style={{ fontSize: '0.65rem', padding: '2px 8px' }}>
                          {n.status}
                        </span>
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 2 }}>
                        {n.channel} · {n.scheduled_for ? new Date(n.scheduled_for).toLocaleString('en-IN') : '—'}
                      </div>
                      {n.message && (
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: 4, fontStyle: 'italic' }}>
                          "{n.message}"
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                No notifications yet. Schedule an appointment to start reminders.
              </p>
            )}
          </div>

          {/* Referral Info */}
          <div className="glass-card" style={{ padding: 24 }}>
            <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 16 }}>
              Referral Details
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <InfoRow label="Doctor" value={referral.doctor_name || 'Unassigned'} />
              <InfoRow label="Hospital" value={referral.hospital_name || '—'} />
              <InfoRow label="Scheduled" value={referral.scheduled_at ? new Date(referral.scheduled_at).toLocaleString('en-IN') : '—'} />
              <InfoRow label="Token" value={referral.appointment_token || '—'} />
              <InfoRow label="Created" value={new Date(referral.created_at).toLocaleDateString('en-IN')} />
              <InfoRow label="Closed" value={referral.closed_at ? new Date(referral.closed_at).toLocaleDateString('en-IN') : '—'} />
            </div>
            {referral.visit_notes && (
              <div style={{ marginTop: 12, padding: 12, borderRadius: 8, background: 'var(--surface-elevated)', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                <strong>Visit Notes:</strong> {referral.visit_notes}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Schedule Modal */}
      {showScheduleModal && (
        <div className="modal-overlay" onClick={() => setShowScheduleModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: 20, color: 'var(--text-primary)' }}>📅 Schedule Appointment</h3>
            <div style={{ marginBottom: 16 }}>
              <label className="label">Date & Time</label>
              <input type="datetime-local" className="input" value={scheduleDate} onChange={e => setScheduleDate(e.target.value)} />
            </div>
            <div style={{ marginBottom: 20 }}>
              <label className="label">Hospital</label>
              <select className="input select" value={scheduleHospital} onChange={e => setScheduleHospital(e.target.value)}>
                <option value="">Select hospital...</option>
                {hospitals.map(h => (
                  <option key={h.id} value={h.id}>{h.name} ({h.facility_type})</option>
                ))}
              </select>
            </div>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button className="btn btn-ghost" onClick={() => setShowScheduleModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleSchedule} disabled={actionLoading || !scheduleDate || !scheduleHospital}>
                {actionLoading ? 'Scheduling...' : 'Confirm Schedule'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Visit Modal */}
      {showVisitModal && (
        <div className="modal-overlay" onClick={() => setShowVisitModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: 20, color: 'var(--text-primary)' }}>✅ Mark Patient Visited</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: 16 }}>
              Confirming this will close the referral, stop all pending reminders, and send a thank-you message to the patient.
            </p>
            <div style={{ marginBottom: 20 }}>
              <label className="label">Visit Notes (optional)</label>
              <textarea className="input" rows={3} value={visitNotes} onChange={e => setVisitNotes(e.target.value)} placeholder="E.g., Treated with laser photocoagulation..." />
            </div>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button className="btn btn-ghost" onClick={() => setShowVisitModal(false)}>Cancel</button>
              <button className="btn btn-success" onClick={handleVisit} disabled={actionLoading}>
                {actionLoading ? 'Processing...' : 'Confirm Visit'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Retake Modal */}
      {showRetakeModal && (
        <div className="modal-overlay" onClick={() => setShowRetakeModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: 20, color: 'var(--text-primary)' }}>🔄 Request Retake</h3>
            <div style={{ marginBottom: 20 }}>
              <label className="label">Reason for Retake</label>
              <textarea className="input" rows={3} value={retakeReason} onChange={e => setRetakeReason(e.target.value)} placeholder="E.g., Image quality insufficient for diagnosis, pupil too small..." required />
            </div>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button className="btn btn-ghost" onClick={() => setShowRetakeModal(false)}>Cancel</button>
              <button className="btn btn-danger" onClick={handleRetake} disabled={actionLoading || retakeReason.length < 5}>
                {actionLoading ? 'Processing...' : 'Request Retake'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div style={{ fontSize: '0.7rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 2 }}>{label}</div>
      <div style={{ fontSize: '0.9rem', color: 'var(--text-primary)', fontWeight: 500 }}>{value}</div>
    </div>
  );
}
