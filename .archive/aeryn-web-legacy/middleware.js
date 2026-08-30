import { NextResponse } from 'next/server';

export function middleware(request) {
  const url = request.nextUrl.pathname;
  
  // API routes pass through
  if (url.startsWith('/api') || url.startsWith('/_next')) {
    return NextResponse.next();
  }
  
  // Rewrite all non-root routes to /
  if (url !== '/') {
    return NextResponse.rewrite(new URL('/', request.url));
  }
  
  return NextResponse.next();
}

export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};
