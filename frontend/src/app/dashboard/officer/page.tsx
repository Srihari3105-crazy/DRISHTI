'use client';

import { useState, useEffect } from 'react';
import { officersAPI, referralsAPI } from '@/lib/api';
import type { OfficerDashboard, Referral } from '@/lib/types';
import { SEVERITY_LABELS, STATE_LABELS } from '@/lib/types';
import Link from 'next/link';

export default function OfficerDashboardPage() {
  const [dashboard, setDashboard] = useState<OfficerDashboard | null>(null);
  const [recentReferrals, setRecentReferrals] = useState<Referral[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const [dashRes, refRes] = await Promise.all([
        officersAPI.dashboard(),
        referralsAPI.list({ page: 1, size: 5 }),
      ]);
      setDashboard(dashRes.data);
      setRecentReferrals(refRes.data.items);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
          {[1, 2, 3, 4, 5, 6].map(i => (
            <div key={i} className="skeleton" style={{ height: 120 }} />
          ))}
        </div>
      </div>
    );
  }

  const stats = [
    { label: 'Total Referred', value: dashboard?.total_referred ?? 0, color: '#3b5bdb', icon: '📋' },
    { label: 'Assigned', value: dashboard?.assigned ?? 0, color: '#7950f2', icon: '👨‍⚕️' },
    { label: 'Scheduled', value: dashboard?.scheduled ?? 0, color: '#e67700', icon: '📅' },
    { label: 'Closed', value: dashboard?.closed ?? 0, color: '#2b8a3e', icon: '✅' },
    { label: 'Closure Rate', value: `${dashboard?.closure_rate ?? 0}%`, color: dashboard?.closure_rate && dashboard.closure_rate > 70 ? '#2b8a3e' : '#c92a2a', icon: '📈' },
    { label: 'Avg Days to Close', value: dashboard?.avg_days_to_close ?? 0, color: '#0c8599', icon: '⏱️' },
  ];

  return (
    <div>
      {/* Stats Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 32 }}>
        {stats.map((stat, idx) => (
          <div key={stat.label} className={`stat-card animate-fadeIn stagger-${idx + 1}`}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
              <span style={{ fontSize: '1.5rem' }}>{stat.icon}</span>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: stat.color }} />
            </div>
            <div className="stat-value" style={{ background: `linear-gradient(135deg, ${stat.color}, #212529)`, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>
              {stat.value}
            </div>
            <div className="stat-label">{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Severity Breakdown */}
      {dashboard?.by_severity && Object.keys(dashboard.by_severity).length > 0 && (
        <div className="glass-card animate-fadeIn" style={{ padding: 24, marginBottom: 24 }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: 16 }}>
            📊 Severity Distribution
          </h3>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            {Object.entries(dashboard.by_severity).map(([severity, count]) => (
              <div key={severity} style={{
                padding: '12px 20px', borderRadius: 12,
                background: 'var(--surface-elevated)', border: '1px solid var(--surface-border)',
                textAlign: 'center', minWidth: 100,
              }}>
                <div style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--text-primary)' }}>{count}</div>
                <div className={`badge severity-${severity}`} style={{ marginTop: 6 }}>
                  {SEVERITY_LABELS[Number(severity)] || `Grade ${severity}`}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Referrals */}
      <div className="glass-card animate-fadeIn" style={{ padding: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            📋 Recent Referrals
          </h3>
          <Link href="/dashboard/referrals" className="btn btn-ghost btn-sm">
            View All →
          </Link>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Code</th>
                <th>Patient</th>
                <th>Eye</th>
                <th>Severity</th>
                <th>EFS</th>
                <th>State</th>
                <th>Doctor</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {recentReferrals.map((ref) => (
                <tr key={ref.id}>
                  <td style={{ fontWeight: 600, color: 'var(--primary-400)', fontFamily: 'monospace' }}>
                    {ref.referral_code}
                  </td>
                  <td>
                    <div style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{ref.patient_name}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Age {ref.patient_age}</div>
                  </td>
                  <td>{ref.eye}</td>
                  <td>
                    <span className={`badge severity-${ref.severity_level}`}>
                      {SEVERITY_LABELS[ref.severity_level ?? 0]}
                    </span>
                  </td>
                  <td>
                    <span className={`efs-badge ${(ref.efs_score ?? 0) >= 0.8 ? 'efs-high' : (ref.efs_score ?? 0) >= 0.6 ? 'efs-medium' : 'efs-low'}`}>
                      {(ref.efs_score ?? 0).toFixed(2)}
                    </span>
                  </td>
                  <td>
                    <span className={`badge badge-${ref.state}`}>
                      {STATE_LABELS[ref.state as keyof typeof STATE_LABELS] || ref.state}
                    </span>
                  </td>
                  <td style={{ color: 'var(--text-secondary)' }}>{ref.doctor_name || '—'}</td>
                  <td>
                    <Link href={`/dashboard/referrals/${ref.id}`} className="btn btn-ghost btn-sm">
                      View
                    </Link>
                  </td>
                </tr>
              ))}
              {recentReferrals.length === 0 && (
                <tr>
                  <td colSpan={8} style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                    No referrals yet. Screenings with severity ≥ 2 will appear here.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
