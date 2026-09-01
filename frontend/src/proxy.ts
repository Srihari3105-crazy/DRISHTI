import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Paths that don't need authentication
const PUBLIC_PATHS = ['/login', '/api'];

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow public paths
  if (PUBLIC_PATHS.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  // Allow root — client-side layout handles role-based redirect
  if (pathname === '/') {
    return NextResponse.next();
  }

  // MVP uses client-side localStorage auth.
  // All routes pass through here; protected pages redirect via AuthProvider.
  // Production upgrade: read httpOnly JWT cookie here and return 401/redirect.
  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|.*\\.png$).*)'],
};

