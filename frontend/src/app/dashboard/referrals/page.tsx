'use client';

import { useState, useEffect } from 'react';
import { referralsAPI } from '@/lib/api';
import type { Referral } from '@/lib/types';
import { SEVERITY_LABELS, STATE_LABELS } from '@/lib/types';
import Link from 'next/link';

export default function ReferralQueuePage() {
  const [referrals, setReferrals] = useState<Referral[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [stateFilter, setStateFilter] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadReferrals();
  }, [page, stateFilter]);

  const loadReferrals = async () => {
    setLoading(true);
    try {
      const params: Record<string, any> = { page, size: 20 };
      if (stateFilter) params.state = stateFilter;
      const res = await referralsAPI.list(params);
      setReferrals(res.data.items);
      setTotal(res.data.total);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const totalPages = Math.ceil(total / 20);

  return (
    <div>
      {/* Filters */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}>
        {['', 'queued', 'assigned', 'scheduled', 'reminders_active', 'visited', 'closed'].map(state => (
          <button
            key={state}
            className={`btn btn-sm ${stateFilter === state ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => { setStateFilter(state); setPage(1); }}
          >
            {state ? (STATE_LABELS[state as keyof typeof STATE_LABELS] || state) : 'All'}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
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
                <th>Doctor</th>
                <th>Hospital</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 10 }).map((_, i) => (
                  <tr key={i}>
                    {Array.from({ length: 11 }).map((_, j) => (
                      <td key={j}><div className="skeleton" style={{ height: 18, width: '80%' }} /></td>
                    ))}
                  </tr>
                ))
              ) : referrals.length > 0 ? referrals.map(ref => (
                <tr key={ref.id}>
                  <td style={{ fontWeight: 600, color: 'var(--primary-400)', fontFamily: 'monospace', fontSize: '0.85rem' }}>
                    {ref.referral_code}
                  </td>
                  <td style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{ref.patient_name}</td>
                  <td>{ref.patient_age}</td>
                  <td>{ref.eye}</td>
                  <td><span className={`badge severity-${ref.severity_level}`}>{SEVERITY_LABELS[ref.severity_level ?? 0]}</span></td>
                  <td>
                    <span className={`efs-badge ${(ref.efs_score ?? 0) >= 0.8 ? 'efs-high' : (ref.efs_score ?? 0) >= 0.6 ? 'efs-medium' : 'efs-low'}`}>
                      {(ref.efs_score ?? 0).toFixed(2)}
                    </span>
                  </td>
                  <td><span className={`badge badge-${ref.state}`}>{STATE_LABELS[ref.state as keyof typeof STATE_LABELS]}</span></td>
                  <td style={{ color: 'var(--text-secondary)' }}>{ref.doctor_name || '—'}</td>
                  <td style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{ref.hospital_name || '—'}</td>
                  <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {new Date(ref.created_at).toLocaleDateString('en-IN')}
                  </td>
                  <td>
                    <Link href={`/dashboard/referrals/${ref.id}`} className="btn btn-ghost btn-sm">View</Link>
                  </td>
                </tr>
              )) : (
                <tr>
                  <td colSpan={11} style={{ textAlign: 'center', padding: 48, color: 'var(--text-muted)' }}>
                    No referrals found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginTop: 20 }}>
          <button className="btn btn-ghost btn-sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>← Previous</button>
          <span style={{ padding: '6px 14px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Page {page} of {totalPages}
          </span>
          <button className="btn btn-ghost btn-sm" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>Next →</button>
        </div>
      )}
    </div>
  );
}
