/**
 * Next.js Middleware for route protection.
 *
 * Redirects unauthenticated users to login for protected routes.
 */
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Define public routes that don't require authentication
const publicRoutes = ['/auth/login', '/auth/register', '/pricing', '/landing', '/sentry-example-page'];

// Define auth routes (redirect to / if already logged in)
const authRoutes = ['/auth/login', '/auth/register'];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Check if user has access token
  const accessToken = request.cookies.get('access_token');
  const isAuthenticated = !!accessToken;

  // Check if route is public (doesn't require authentication)
  const isPublicRoute = publicRoutes.some((route) =>
    pathname.startsWith(route)
  );

  // Check if route is an auth route
  const isAuthRoute = authRoutes.some((route) => pathname.startsWith(route));

  // Redirect authenticated users away from landing page to the tool (/)
  if (pathname === '/landing' && isAuthenticated) {
    return NextResponse.redirect(new URL('/', request.url));
  }

  // Redirect unauthenticated users to /landing for ALL non-public routes
  // This protects the homepage (/) and all tool routes by default
  if (!isPublicRoute && !isAuthenticated) {
    // Redirect to landing page instead of login
    const landingUrl = new URL('/landing', request.url);
    return NextResponse.redirect(landingUrl);
  }

  // Redirect authenticated users away from auth pages to the tool (/)
  if (isAuthRoute && isAuthenticated) {
    return NextResponse.redirect(new URL('/', request.url));
  }

  return NextResponse.next();
}

// Configure which routes to run middleware on
export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public files (public folder)
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
};
