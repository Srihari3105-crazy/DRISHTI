'use client';

import { useState, useEffect } from 'react';
import { patientsAPI } from '@/lib/api';
import type { Patient } from '@/lib/types';

export default function PatientsPage() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPatients();
  }, [search]);

  const loadPatients = async () => {
    setLoading(true);
    try {
      const params: Record<string, any> = { page: 1, size: 50 };
      if (search) params.search = search;
      const res = await patientsAPI.list(params);
      setPatients(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {/* Search */}
      <div style={{ marginBottom: 20 }}>
        <input
          className="input"
          style={{ maxWidth: 400 }}
          placeholder="🔍 Search by name or mobile..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>

      {/* Table */}
      <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Age</th>
                <th>Gender</th>
                <th>Mobile</th>
                <th>Verified</th>
                <th>District</th>
                <th>Block</th>
                <th>Diabetes</th>
                <th>HbA1c</th>
                <th>Registered</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 10 }).map((_, i) => (
                  <tr key={i}>{Array.from({ length: 10 }).map((_, j) => <td key={j}><div className="skeleton" style={{ height: 18, width: '70%' }} /></td>)}</tr>
                ))
              ) : patients.length > 0 ? patients.map(p => (
                <tr key={p.id}>
                  <td style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{p.name}</td>
                  <td>{p.age}</td>
                  <td>{p.gender}</td>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>{p.mobile}</td>
                  <td>
                    <span className={`badge ${p.mobile_verified ? 'badge-visited' : 'badge-queued'}`}>
                      {p.mobile_verified ? '✓ Verified' : 'Pending'}
                    </span>
                  </td>
                  <td>{p.district_id}</td>
                  <td>{p.block_id}</td>
                  <td style={{ color: 'var(--text-secondary)' }}>{p.diabetes_type || '—'}</td>
                  <td style={{ fontVariantNumeric: 'tabular-nums' }}>{p.hba1c?.toFixed(1) || '—'}</td>
                  <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{new Date(p.created_at).toLocaleDateString('en-IN')}</td>
                </tr>
              )) : (
                <tr><td colSpan={10} style={{ textAlign: 'center', padding: 48, color: 'var(--text-muted)' }}>No patients found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
