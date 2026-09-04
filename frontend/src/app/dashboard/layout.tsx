'use client';

import { useAuth, type UserRole } from '@/lib/auth';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { useEffect } from 'react';

const NAV_ITEMS: Array<{
  label: string;
  href: string;
  icon: string;
  roles: UserRole[];
}> = [
  { label: 'Officer Dashboard', href: '/dashboard/officer', icon: '📊', roles: ['officer', 'admin'] },
  { label: 'Doctor Dashboard', href: '/dashboard/doctor', icon: '🩺', roles: ['doctor', 'admin'] },
  { label: 'Referral Queue', href: '/dashboard/referrals', icon: '📋', roles: ['officer', 'doctor', 'admin'] },
  { label: 'Auto-Assign', href: '/dashboard/auto-assign', icon: '⚡', roles: ['officer', 'admin'] },
  { label: 'Patients', href: '/dashboard/patients', icon: '👥', roles: ['operator', 'doctor', 'officer', 'admin'] },
  { label: 'Export HMIS', href: '/dashboard/exports', icon: '📥', roles: ['officer', 'admin'] },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, isAuthenticated, isLoading, logout, hasRole } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
        <div style={{ width: 40, height: 40, border: '3px solid var(--primary-500)', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  if (!isAuthenticated || !user) return null;

  const visibleNavItems = NAV_ITEMS.filter((item) =>
    item.roles.some((role) => hasRole(role))
  );

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      {/* Sidebar */}
      <aside className="gradient-sidebar" style={{
        width: 260, flexShrink: 0, borderRight: '1px solid var(--surface-border)',
        display: 'flex', flexDirection: 'column', position: 'fixed', height: '100vh',
        zIndex: 20,
      }}>
        {/* Logo */}
        <div style={{ padding: '20px 20px 16px', borderBottom: '1px solid var(--surface-border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{
              width: 36, height: 36, borderRadius: 10,
              background: 'linear-gradient(135deg, #3b5bdb, #12b886)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '1.1rem',
            }}>👁️</div>
            <div>
              <div style={{ fontWeight: 800, fontSize: '0.95rem', color: '#212529' }}>DRISHTI-LENS</div>
              <div style={{ fontSize: '0.7rem', color: '#868e96', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                DR Screening MVP
              </div>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav style={{ flex: 1, padding: '12px 10px', overflowY: 'auto' }}>
          {visibleNavItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`sidebar-link ${pathname === item.href ? 'active' : ''}`}
            >
              <span style={{ fontSize: '1.1rem' }}>{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>

        {/* User Info + Logout */}
        <div style={{
          padding: '16px 16px', borderTop: '1px solid #dee2e6',
          background: '#f8f9fa',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
            <div style={{
              width: 32, height: 32, borderRadius: 8,
              background: 'linear-gradient(135deg, #3b5bdb, #12b886)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '0.8rem', fontWeight: 700, color: 'white',
            }}>
              {user.name.charAt(0).toUpperCase()}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#212529', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {user.name}
              </div>
              <div style={{ fontSize: '0.7rem', color: '#868e96', textTransform: 'capitalize' }}>
                {user.role}{user.district_id ? ` · ${user.district_id}` : ''}
              </div>
            </div>
          </div>
          <button
            onClick={logout}
            className="btn btn-ghost btn-sm"
            style={{ width: '100%', fontSize: '0.8rem' }}
          >
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main style={{ flex: 1, marginLeft: 260, minHeight: '100vh' }}>
        {/* Header */}
        <header style={{
          padding: '16px 28px',
          background: 'rgba(255, 255, 255, 0.9)',
          backdropFilter: 'blur(12px)',
          borderBottom: '1px solid #dee2e6',
          position: 'sticky', top: 0, zIndex: 10,
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <div>
            <h1 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#212529' }}>
              {visibleNavItems.find(n => n.href === pathname)?.label || 'Dashboard'}
            </h1>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{
              padding: '4px 10px', borderRadius: 20, fontSize: '0.7rem', fontWeight: 600,
              background: '#ebfbee', color: '#2b8a3e',
            }}>
              ● Online
            </span>
          </div>
        </header>

        {/* Page Content */}
        <div style={{ padding: '24px 28px' }}>
          {children}
        </div>
      </main>
    </div>
  );
}
