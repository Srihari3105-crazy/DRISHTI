'use client';

import { useState } from 'react';
import { exportsAPI } from '@/lib/api';
import { useAuth } from '@/lib/auth';

export default function ExportsPage() {
  const { hasRole } = useAuth();
  const [month, setMonth] = useState(new Date().toISOString().slice(0, 7)); // YYYY-MM
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleExport = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await exportsAPI.hmisForm1(month);
      // Download blob as CSV
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `NPCBVI_Form1_${month}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Export failed.');
    } finally {
      setLoading(false);
    }
  };

  if (!hasRole('officer', 'admin')) {
    return <div style={{ padding: 48, textAlign: 'center', color: 'var(--text-muted)' }}>Access denied. Officers only.</div>;
  }

  return (
    <div style={{ maxWidth: 600, margin: '0 auto' }}>
      <div className="glass-card animate-fadeIn" style={{ padding: 36, textAlign: 'center' }}>
        <div style={{ fontSize: '3rem', marginBottom: 16 }}>📥</div>
        <h2 style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>
          NPCBVI HMIS Form 1
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: 28 }}>
          Export monthly screening and referral data as CSV for NPCBVI HMIS reporting.
        </p>

        <div style={{ display: 'flex', gap: 12, justifyContent: 'center', alignItems: 'flex-end' }}>
          <div style={{ textAlign: 'left' }}>
            <label className="label">Select Month</label>
            <input
              type="month"
              className="input"
              style={{ width: 200 }}
              value={month}
              onChange={e => setMonth(e.target.value)}
            />
          </div>
          <button className="btn btn-primary" onClick={handleExport} disabled={loading} style={{ height: 42 }}>
            {loading ? 'Exporting...' : '📥 Download CSV'}
          </button>
        </div>

        {error && (
          <div style={{ marginTop: 16, padding: '10px 14px', borderRadius: 10, background: '#fff5f5', border: '1px solid #ffc9c9', color: '#c92a2a', fontSize: '0.85rem' }}>
            {error}
          </div>
        )}

        <div style={{ marginTop: 28, paddingTop: 20, borderTop: '1px solid var(--surface-border)', textAlign: 'left' }}>
          <h4 style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 10 }}>CSV Columns</h4>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.8 }}>
            S.No · Patient Name · Age · Gender · District · Block · Mobile · Screening Date · Eye · DR Grade (ICDR) · DME Risk · Referred To Hospital · Referral Code · Doctor Name · Appointment Date · Visit Status · Visit Date · Days to Closure · EFS Score
          </div>
        </div>
      </div>
    </div>
  );
}
