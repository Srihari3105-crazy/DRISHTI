'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { authAPI, pincodeAPI } from '@/lib/api';

const ROLES = [
  { value: 'doctor',   label: 'Doctor',          desc: 'Ophthalmologist reviewing cases' },
  { value: 'officer',  label: 'District Officer', desc: 'Manages referrals & assignments' },
  { value: 'operator', label: 'Field Operator',   desc: 'Captures fundus images on-site' },
  { value: 'admin',    label: 'System Admin',     desc: 'Full access (single-admin locked)' },
];

export default function LoginPage() {
  const [tab, setTab] = useState<'signin' | 'signup'>('signin');

  // Sign-in state
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');

  // Sign-up state
  const [suName, setSuName] = useState('');
  const [suEmail, setSuEmail] = useState('');
  const [suPhone, setSuPhone] = useState('');
  const [suPassword, setSuPassword] = useState('');
  const [suConfirm, setSuConfirm] = useState('');
  const [suRole, setSuRole] = useState('');

  // PIN code & auto-filled location state
  const [suPincode, setSuPincode] = useState('');
  const [suDistrict, setSuDistrict] = useState('');
  const [suState, setSuState] = useState('');
  const [suArea, setSuArea] = useState('');
  const [areaOptions, setAreaOptions] = useState<string[]>([]);
  const [isPinLoading, setIsPinLoading] = useState(false);
  const [pinMessage, setPinMessage] = useState('');

  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const { login } = useAuth();
  const router = useRouter();

  // ── PIN Code Auto-Fill Effect ─────────────────────────────────
  useEffect(() => {
    const cleanPin = suPincode.replace(/\D/g, '').slice(0, 6);
    if (cleanPin.length === 6) {
      setIsPinLoading(true);
      setPinMessage('Looking up postal area...');
      pincodeAPI.lookup(cleanPin)
        .then((res) => {
          const data = res.data;
          if (data && data.district) {
            setSuDistrict(data.district);
            setSuState(data.state);
            const areas = data.areas || [];
            setAreaOptions(areas);
            setSuArea(areas[0] || '');
            setPinMessage(`✓ Located: ${data.district}, ${data.state}`);
          }
        })
        .catch(() => {
          setPinMessage('Location found from region prefix');
        })
        .finally(() => {
          setIsPinLoading(false);
        });
    } else {
      if (cleanPin.length > 0 && cleanPin.length < 6) {
        setPinMessage('Enter 6-digit postal PIN code');
      } else {
        setPinMessage('');
      }
    }
  }, [suPincode]);

  // ── Sign In ──────────────────────────────────────────────────
  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(''); setSuccess(''); setIsLoading(true);
    try {
      const formattedPhone = phone.startsWith('+91') ? phone : `+91${phone.replace(/\D/g, '').slice(0, 10)}`;
      await login(formattedPhone, password);
      router.push('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Incorrect phone or password.');
    } finally {
      setIsLoading(false);
    }
  };

  // ── Sign Up ──────────────────────────────────────────────────
  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(''); setSuccess('');

    if (!suRole) { setError('Please select your role.'); return; }
    if (suPassword !== suConfirm) { setError('Passwords do not match.'); return; }
    if (suPassword.length < 6) { setError('Password must be at least 6 characters.'); return; }

    setIsLoading(true);
    try {
      const formattedPhone = suPhone.startsWith('+91') ? suPhone : `+91${suPhone.replace(/\D/g, '').slice(0, 10)}`;
      const res = await authAPI.register({
        name: suName.trim(),
        email: suEmail.trim() || undefined,
        phone: formattedPhone,
        password: suPassword,
        role: suRole,
        district_id: suDistrict || undefined,
        pincode: suPincode || undefined,
        area: suArea || undefined,
        state: suState || undefined,
      });

      // Store tokens + auto-login
      const { access_token, refresh_token, user } = res.data;
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      localStorage.setItem('user', JSON.stringify(user));

      setSuccess(`Account created! Welcome, ${user.name}.`);
      setTimeout(() => router.push('/'), 800);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="lp-wrap">
      <div className="lp-card">

        {/* Header */}
        <div className="lp-header">
          <div className="lp-logo">
            <svg width="34" height="34" viewBox="0 0 36 36" fill="none">
              <circle cx="18" cy="18" r="16" stroke="#3b5bdb" strokeWidth="2.5" />
              <circle cx="18" cy="18" r="7" fill="#3b5bdb" opacity="0.25" />
              <circle cx="18" cy="18" r="3.5" fill="#3b5bdb" />
            </svg>
          </div>
          <div>
            <h1 className="lp-title">DRISHTI-LENS</h1>
            <p className="lp-subtitle">National Diabetic Retinopathy Screening</p>
          </div>
        </div>

        {/* Tab switcher */}
        <div className="lp-tabs">
          <button
            type="button"
            className={`lp-tab ${tab === 'signin' ? 'active' : ''}`}
            onClick={() => { setTab('signin'); setError(''); setSuccess(''); }}
          >
            Sign In
          </button>
          <button
            type="button"
            className={`lp-tab ${tab === 'signup' ? 'active' : ''}`}
            onClick={() => { setTab('signup'); setError(''); setSuccess(''); }}
          >
            Create Account
          </button>
        </div>

        {/* Alerts */}
        {error && <div className="lp-alert lp-alert-error">{error}</div>}
        {success && <div className="lp-alert lp-alert-success">{success}</div>}

        {/* ── SIGN IN FORM ── */}
        {tab === 'signin' && (
          <form onSubmit={handleSignIn} className="lp-form">
            <div className="lp-field">
              <label className="lp-label">Mobile Number</label>
              <div className="lp-input-wrap">
                <span className="lp-prefix">+91</span>
                <input
                  id="login-phone"
                  type="tel"
                  className="lp-input lp-input-prefix"
                  placeholder="9876543210"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value.replace(/\D/g, '').slice(0, 10))}
                  required autoFocus
                />
              </div>
            </div>
            <div className="lp-field">
              <label className="lp-label">Password</label>
              <input
                id="login-password"
                type="password"
                className="lp-input"
                placeholder="Your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <button id="login-submit" type="submit" className="lp-btn" disabled={isLoading}>
              {isLoading ? <span className="lp-spinner" /> : null}
              {isLoading ? 'Signing in…' : 'Sign In'}
            </button>

            {/* Demo quick-logins */}
            <div className="lp-divider"><span>Preconfigured Demo Logins</span></div>
            <div className="lp-demo-grid">
              {[
                { label: '🏛️ Officer', phone: '+919876540001', pass: 'drishti123' },
                { label: '🩺 Doctor',  phone: '+919876543001', pass: 'drishti123' },
                { label: '📱 Operator',phone: '+919999000001', pass: 'drishti123' },
                { label: '🔑 Admin',   phone: '+919999000000', pass: 'admin123'   },
              ].map((d) => (
                <button key={d.label} type="button" className="lp-demo-btn"
                  onClick={async () => {
                    setIsLoading(true); setError('');
                    try { await login(d.phone, d.pass); router.push('/'); }
                    catch { setError(`Quick login as ${d.label} failed.`); }
                    finally { setIsLoading(false); }
                  }}>
                  {d.label}
                </button>
              ))}
            </div>
          </form>
        )}

        {/* ── SIGN UP FORM ── */}
        {tab === 'signup' && (
          <form onSubmit={handleSignUp} className="lp-form">
            <div className="lp-field">
              <label className="lp-label">Full Name *</label>
              <input
                id="signup-name"
                className="lp-input"
                placeholder="Dr. Priya Sharma"
                value={suName}
                onChange={(e) => setSuName(e.target.value)}
                required
                minLength={2}
              />
            </div>

            <div className="lp-field">
              <label className="lp-label">Email Address *</label>
              <input
                id="signup-email"
                type="email"
                className="lp-input"
                placeholder="doctor.sharma@hospital.org"
                value={suEmail}
                onChange={(e) => setSuEmail(e.target.value)}
                required
              />
            </div>

            <div className="lp-field">
              <label className="lp-label">Mobile Number *</label>
              <div className="lp-input-wrap">
                <span className="lp-prefix">+91</span>
                <input
                  id="signup-phone"
                  type="tel"
                  className="lp-input lp-input-prefix"
                  placeholder="9876543210"
                  value={suPhone}
                  onChange={(e) => setSuPhone(e.target.value.replace(/\D/g, '').slice(0, 10))}
                  required
                />
              </div>
            </div>

            {/* Role selector */}
            <div className="lp-field">
              <label className="lp-label">Register As *</label>
              <div className="lp-roles">
                {ROLES.map((r) => (
                  <button
                    key={r.value}
                    type="button"
                    className={`lp-role-btn ${suRole === r.value ? 'selected' : ''}`}
                    onClick={() => setSuRole(r.value)}
                  >
                    <span className="lp-role-name">{r.label}</span>
                    <span className="lp-role-desc">{r.desc}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* PIN Code & Auto-filled Locations */}
            <div className="lp-location-box">
              <div className="lp-field">
                <label className="lp-label" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>Postal PIN Code *</span>
                  {isPinLoading && <span style={{ fontSize: '0.72rem', color: '#3b5bdb' }}>Fetching location...</span>}
                </label>
                <input
                  id="signup-pincode"
                  type="text"
                  className="lp-input"
                  placeholder="e.g. 302001, 110001, 600001"
                  maxLength={6}
                  value={suPincode}
                  onChange={(e) => setSuPincode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  required
                />
                {pinMessage && (
                  <span style={{ fontSize: '0.72rem', color: pinMessage.startsWith('✓') ? '#2b8a3e' : '#868e96', marginTop: 2 }}>
                    {pinMessage}
                  </span>
                )}
              </div>

              {/* Auto-filled District & State */}
              <div className="lp-row" style={{ marginTop: 8 }}>
                <div className="lp-field" style={{ flex: 1 }}>
                  <label className="lp-label">District (Auto-filled)</label>
                  <input
                    id="signup-district"
                    className="lp-input lp-input-readonly"
                    placeholder="Auto-filled via PIN"
                    value={suDistrict}
                    onChange={(e) => setSuDistrict(e.target.value)}
                  />
                </div>
                <div className="lp-field" style={{ flex: 1 }}>
                  <label className="lp-label">State (Auto-filled)</label>
                  <input
                    id="signup-state"
                    className="lp-input lp-input-readonly"
                    placeholder="Auto-filled via PIN"
                    value={suState}
                    onChange={(e) => setSuState(e.target.value)}
                  />
                </div>
              </div>

              {/* Area / Post Office Selection */}
              {areaOptions.length > 0 && (
                <div className="lp-field" style={{ marginTop: 8 }}>
                  <label className="lp-label">Area / Post Office</label>
                  <select
                    id="signup-area"
                    className="lp-input"
                    value={suArea}
                    onChange={(e) => setSuArea(e.target.value)}
                  >
                    {areaOptions.map((a, idx) => (
                      <option key={idx} value={a}>{a}</option>
                    ))}
                  </select>
                </div>
              )}
            </div>

            <div className="lp-row">
              <div className="lp-field" style={{ flex: 1 }}>
                <label className="lp-label">Password *</label>
                <input
                  id="signup-password"
                  type="password"
                  className="lp-input"
                  placeholder="Min. 6 chars"
                  value={suPassword}
                  onChange={(e) => setSuPassword(e.target.value)}
                  required
                  minLength={6}
                />
              </div>
              <div className="lp-field" style={{ flex: 1 }}>
                <label className="lp-label">Confirm Password *</label>
                <input
                  id="signup-confirm-password"
                  type="password"
                  className="lp-input"
                  placeholder="Re-enter password"
                  value={suConfirm}
                  onChange={(e) => setSuConfirm(e.target.value)}
                  required
                />
              </div>
            </div>

            <button type="submit" className="lp-btn" disabled={isLoading}>
              {isLoading ? <span className="lp-spinner" /> : null}
              {isLoading ? 'Creating Account…' : 'Create Account'}
            </button>

            <p className="lp-note">
              Patients register directly through the <strong>DRISHTI-LENS mobile app</strong> during on-field fundus screening.
            </p>
          </form>
        )}
      </div>

      <style jsx>{`
        .lp-wrap {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #f1f3f5;
          padding: 24px;
        }
        .lp-card {
          width: 100%;
          max-width: 480px;
          background: #ffffff;
          border-radius: 10px;
          border: 1px solid #ced4da;
          box-shadow: 0 4px 16px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.04);
          overflow: hidden;
        }
        .lp-header {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 20px 24px 16px;
          border-bottom: 1px solid #e9ecef;
          background: #fafbfc;
        }
        .lp-logo {
          flex-shrink: 0;
        }
        .lp-title {
          font-size: 1.15rem;
          font-weight: 700;
          color: #212529;
          letter-spacing: 0.02em;
          margin: 0;
        }
        .lp-subtitle {
          font-size: 0.76rem;
          color: #6c757d;
          margin: 2px 0 0;
        }
        .lp-tabs {
          display: flex;
          border-bottom: 1px solid #e9ecef;
          background: #f8f9fa;
        }
        .lp-tab {
          flex: 1;
          padding: 12px;
          background: none;
          border: none;
          font-size: 0.875rem;
          font-weight: 500;
          color: #6c757d;
          cursor: pointer;
          border-bottom: 2px solid transparent;
          transition: color 0.15s, border-color 0.15s, background 0.15s;
        }
        .lp-tab.active {
          color: #3b5bdb;
          border-bottom-color: #3b5bdb;
          background: #ffffff;
          font-weight: 600;
        }
        .lp-form {
          padding: 22px 24px;
          display: flex;
          flex-direction: column;
          gap: 14px;
        }
        .lp-field {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .lp-label {
          font-size: 0.78rem;
          font-weight: 600;
          color: #495057;
        }
        .lp-input-wrap {
          position: relative;
        }
        .lp-prefix {
          position: absolute;
          left: 10px;
          top: 50%;
          transform: translateY(-50%);
          font-size: 0.85rem;
          color: #868e96;
          pointer-events: none;
        }
        .lp-input {
          width: 100%;
          padding: 8px 11px;
          border: 1px solid #ced4da;
          border-radius: 6px;
          font-size: 0.85rem;
          color: #212529;
          background: #ffffff;
          transition: border-color 0.15s, box-shadow 0.15s;
          outline: none;
        }
        .lp-input:focus {
          border-color: #4c6ef5;
          box-shadow: 0 0 0 3px rgba(76,110,245,0.12);
        }
        .lp-input-prefix {
          padding-left: 36px;
        }
        .lp-input-readonly {
          background: #f8f9fa;
          color: #495057;
        }
        .lp-location-box {
          padding: 12px;
          border: 1px solid #e9ecef;
          border-radius: 8px;
          background: #fdfdfd;
        }
        .lp-roles {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 8px;
        }
        .lp-role-btn {
          display: flex;
          flex-direction: column;
          align-items: flex-start;
          padding: 9px 11px;
          border: 1px solid #ced4da;
          border-radius: 6px;
          background: #ffffff;
          cursor: pointer;
          text-align: left;
          transition: border-color 0.15s, background 0.15s;
        }
        .lp-role-btn:hover {
          border-color: #748ffc;
          background: #f8f9fa;
        }
        .lp-role-btn.selected {
          border-color: #3b5bdb;
          background: #edf2ff;
        }
        .lp-role-name {
          font-size: 0.8rem;
          font-weight: 600;
          color: #212529;
        }
        .lp-role-desc {
          font-size: 0.68rem;
          color: #868e96;
          margin-top: 2px;
          line-height: 1.25;
        }
        .lp-row {
          display: flex;
          gap: 10px;
        }
        .lp-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          width: 100%;
          padding: 10px 16px;
          background: #3b5bdb;
          color: #ffffff;
          border: none;
          border-radius: 6px;
          font-size: 0.88rem;
          font-weight: 600;
          cursor: pointer;
          transition: background 0.15s;
          margin-top: 4px;
        }
        .lp-btn:hover:not(:disabled) {
          background: #364fc7;
        }
        .lp-btn:disabled {
          opacity: 0.65;
          cursor: not-allowed;
        }
        .lp-spinner {
          width: 14px;
          height: 14px;
          border: 2px solid rgba(255,255,255,0.35);
          border-top-color: #ffffff;
          border-radius: 50%;
          animation: spin 0.7s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .lp-divider {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #adb5bd;
          font-size: 0.72rem;
          margin: 4px 0;
        }
        .lp-divider::before, .lp-divider::after {
          content: '';
          flex: 1;
          height: 1px;
          background: #e9ecef;
        }
        .lp-demo-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 6px;
        }
        .lp-demo-btn {
          padding: 7px 10px;
          background: #f8f9fa;
          border: 1px solid #dee2e6;
          border-radius: 6px;
          font-size: 0.76rem;
          font-weight: 500;
          color: #495057;
          cursor: pointer;
          transition: all 0.12s;
        }
        .lp-demo-btn:hover {
          background: #edf2ff;
          border-color: #748ffc;
          color: #3b5bdb;
        }
        .lp-alert {
          margin: 0 24px;
          padding: 8px 12px;
          border-radius: 6px;
          font-size: 0.8rem;
          line-height: 1.35;
        }
        .lp-alert-error {
          background: #fff5f5;
          border: 1px solid #ffc9c9;
          color: #c92a2a;
        }
        .lp-alert-success {
          background: #ebfbee;
          border: 1px solid #b2f2bb;
          color: #2b8a3e;
        }
        .lp-note {
          font-size: 0.72rem;
          color: #868e96;
          text-align: center;
          margin: 0;
        }
        .lp-note strong {
          color: #495057;
        }
      `}</style>
    </div>
  );
}
