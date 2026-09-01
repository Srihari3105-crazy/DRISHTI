'use client';

import { useState } from 'react';
import { referralsAPI } from '@/lib/api';
import { useAuth } from '@/lib/auth';

export default function AutoAssignPage() {
  const { hasRole } = useAuth();
  const [result, setResult] = useState<{ assigned: number; skipped: number; details: Array<{ referral_code: string; doctor_name: string }> } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleAutoAssign = async () => {
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const res = await referralsAPI.autoAssign();
      setResult(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Auto-assign failed.');
    } finally {
      setLoading(false);
    }
  };

  if (!hasRole('officer', 'admin')) {
    return <div style={{ padding: 48, textAlign: 'center', color: 'var(--text-muted)' }}>Access denied. Officers only.</div>;
  }

  return (
    <div style={{ maxWidth: 700, margin: '0 auto' }}>
      {/* Header */}
      <div className="glass-card animate-fadeIn" style={{ padding: 32, textAlign: 'center', marginBottom: 24 }}>
        <div style={{ fontSize: '3rem', marginBottom: 12 }}>⚡</div>
        <h2 style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>
          Auto-Assign Referrals
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', maxWidth: 500, margin: '0 auto 24px' }}>
          Automatically assigns all <strong style={{ color: 'var(--primary-400)' }}>QUEUED</strong> referrals to the nearest government ophthalmologist with fewer than 10 pending cases. Round-robin distribution ensures fair load balancing.
        </p>
        <button
          className="btn btn-primary pulse-glow"
          style={{ padding: '14px 32px', fontSize: '1rem' }}
          onClick={handleAutoAssign}
          disabled={loading}
        >
          {loading ? (
            <>
              <span style={{ width: 18, height: 18, border: '2px solid rgba(255,255,255,0.3)', borderTopColor: 'white', borderRadius: '50%', animation: 'spin 0.7s linear infinite', display: 'inline-block' }} />
              Assigning...
            </>
          ) : (
            '⚡ Run Auto-Assign'
          )}
        </button>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>

      {/* Error */}
      {error && (
        <div style={{ padding: '12px 16px', borderRadius: 12, background: '#fff5f5', border: '1px solid #ffc9c9', color: '#c92a2a', marginBottom: 20, fontSize: '0.9rem' }}>
          {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="glass-card animate-fadeIn" style={{ padding: 28 }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: 20 }}>
            Assignment Results
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 24 }}>
            <div className="stat-card" style={{ textAlign: 'center' }}>
              <div className="stat-value" style={{ color: '#2b8a3e' }}>{result.assigned}</div>
              <div className="stat-label">Assigned</div>
            </div>
            <div className="stat-card" style={{ textAlign: 'center' }}>
              <div className="stat-value" style={{ color: result.skipped > 0 ? '#e67700' : '#868e96' }}>{result.skipped}</div>
              <div className="stat-label">Skipped</div>
            </div>
          </div>

          {result.details.length > 0 && (
            <div>
              <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 12 }}>Assignment Details</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {result.details.map((d, idx) => (
                  <div key={idx} style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '10px 16px', borderRadius: 10, background: 'var(--surface-elevated)',
                    border: '1px solid var(--surface-border)',
                  }}>
                    <span style={{ fontFamily: 'monospace', fontWeight: 600, color: 'var(--primary-400)', fontSize: '0.85rem' }}>
                      {d.referral_code}
                    </span>
                    <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                      → Dr. {d.doctor_name}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {result.assigned === 0 && result.skipped === 0 && (
            <p style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 20 }}>
              No queued referrals to assign. All clear! ✅
            </p>
          )}
        </div>
      )}
    </div>
  );
}
