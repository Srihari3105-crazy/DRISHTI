'use client';

import { useState, useEffect } from 'react';
import { referralsAPI } from '@/lib/api';
import type { Referral } from '@/lib/types';
import { SEVERITY_LABELS, STATE_LABELS } from '@/lib/types';
import Link from 'next/link';

export default function DoctorDashboardPage() {
  const [referrals, setReferrals] = useState<Referral[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('');
  const [total, setTotal] = useState(0);

  useEffect(() => {
    loadReferrals();
  }, [filter]);

  const loadReferrals = async () => {
    setLoading(true);
    try {
      const params: Record<string, any> = { page: 1, size: 50 };
      if (filter) params.state = filter;
      const res = await referralsAPI.list(params);
      setReferrals(res.data.items);
      setTotal(res.data.total);
    } catch (err) {
      console.error('Failed to load referrals:', err);
    } finally {
      setLoading(false);
    }
  };

  const statCounts = {
    pending: referrals.filter(r => r.state === 'assigned').length,
    scheduled: referrals.filter(r => ['scheduled', 'reminders_active'].includes(r.state)).length,
    visited: referrals.filter(r => ['visited', 'closed'].includes(r.state)).length,
  };

  return (
    <div>
      {/* Quick Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 28 }}>
        <div className="stat-card animate-fadeIn stagger-1" onClick={() => setFilter('assigned')} style={{ cursor: 'pointer' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
            <span style={{ fontSize: '1.2rem' }}>⏳</span>
            <div className="stat-label">Pending Review</div>
          </div>
          <div className="stat-value">{statCounts.pending}</div>
        </div>
        <div className="stat-card animate-fadeIn stagger-2" onClick={() => setFilter('scheduled')} style={{ cursor: 'pointer' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
            <span style={{ fontSize: '1.2rem' }}>📅</span>
            <div className="stat-label">Scheduled</div>
          </div>
          <div className="stat-value">{statCounts.scheduled}</div>
        </div>
        <div className="stat-card animate-fadeIn stagger-3" onClick={() => setFilter('')} style={{ cursor: 'pointer' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
            <span style={{ fontSize: '1.2rem' }}>✅</span>
            <div className="stat-label">Completed</div>
          </div>
          <div className="stat-value">{statCounts.visited}</div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
        {[
          { label: 'All', value: '' },
          { label: 'Pending', value: 'assigned' },
          { label: 'Scheduled', value: 'scheduled' },
          { label: 'Visited', value: 'visited' },
          { label: 'Closed', value: 'closed' },
        ].map(tab => (
          <button
            key={tab.value}
            className={`btn btn-sm ${filter === tab.value ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setFilter(tab.value)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Referrals Table */}
      <div className="glass-card animate-fadeIn" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Code</th>
                <th>Patient</th>
                <th>Age</th>
                <th>Eye</th>
                <th>Severity</th>
                <th>EFS</th>
                <th>State</th>
                <th>Scheduled</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i}>
                    {Array.from({ length: 9 }).map((_, j) => (
                      <td key={j}><div className="skeleton" style={{ height: 20, width: '80%' }} /></td>
                    ))}
                  </tr>
                ))
              ) : referrals.length > 0 ? (
                referrals.map((ref) => (
                  <tr key={ref.id}>
                    <td style={{ fontWeight: 600, color: 'var(--primary-400)', fontFamily: 'monospace' }}>
                      {ref.referral_code}
                    </td>
                    <td style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{ref.patient_name}</td>
                    <td>{ref.patient_age}</td>
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
                    <td style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                      {ref.scheduled_at ? new Date(ref.scheduled_at).toLocaleDateString('en-IN') : '—'}
                    </td>
                    <td>
                      <Link href={`/dashboard/referrals/${ref.id}`} className="btn btn-primary btn-sm">
                        Open Case
                      </Link>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={9} style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                    No cases found for this filter.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {total > 0 && (
        <div style={{ marginTop: 12, textAlign: 'right', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
          Showing {referrals.length} of {total} referrals
        </div>
      )}
    </div>
  );
}
