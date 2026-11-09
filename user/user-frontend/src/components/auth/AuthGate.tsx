'use client';

import { useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/lib/AuthContext';

export function AuthGate({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isAuthLoading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const isLoginRoute = pathname === '/auth/login';

  useEffect(() => {
    if (isAuthLoading) return;
    if (!isAuthenticated && !isLoginRoute) router.replace('/auth/login');
    if (isAuthenticated && isLoginRoute) router.replace('/');
  }, [isAuthenticated, isAuthLoading, isLoginRoute, router]);

  if (isAuthLoading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background text-text" aria-live="polite">
        در حال بررسی نشست امن...
      </main>
    );
  }
  if ((!isAuthenticated && !isLoginRoute) || (isAuthenticated && isLoginRoute)) {
    return null;
  }
  return <>{children}</>;
}
