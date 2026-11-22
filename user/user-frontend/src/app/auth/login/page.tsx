'use client';

import { FormEvent, useState } from 'react';
import { useRouter } from 'next/navigation';
import axiosWithAuth from '@/lib/axiosWithAuth';
import { useAuth } from '@/lib/AuthContext';

export default function LoginPage() {
  const router = useRouter();
  const { refreshSession } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await axiosWithAuth.post('/auth/login', { username, password });
      const authenticated = await refreshSession();
      if (!authenticated) {
        throw new Error('نشست ایجاد شد اما تأیید آن ناموفق بود. دوباره وارد شوید.');
      }
      router.replace('/');
    } catch (cause) {
      const message =
        typeof cause === 'object' && cause !== null && 'response' in cause
          ? ((cause as { response?: { data?: { message?: string } } }).response?.data?.message ?? 'ورود ناموفق بود.')
          : cause instanceof Error ? cause.message : 'ورود ناموفق بود.';
      setError(message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4 text-text" dir="rtl">
      <section className="w-full max-w-md rounded-2xl border border-border bg-surface p-8 shadow-lg">
        <h1 className="text-2xl font-bold">ورود به MarketSage</h1>
        <p className="mt-2 text-sm text-text-secondary">
          دسترسی به فضای تحقیقاتی فقط برای حساب مجاز فعال است.
        </p>
        <form className="mt-6 space-y-4" onSubmit={submit}>
          <label className="block text-sm">
            نام کاربری
            <input
              autoComplete="username"
              required
              maxLength={128}
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-3"
            />
          </label>
          <label className="block text-sm">
            گذرواژه
            <input
              type="password"
              autoComplete="current-password"
              required
              maxLength={1024}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-3"
            />
          </label>
          {error ? <p role="alert" className="rounded-lg border border-red-500/40 p-3 text-sm text-red-500">{error}</p> : null}
          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-lg bg-primary px-4 py-3 font-semibold text-white disabled:opacity-60"
          >
            {submitting ? 'در حال ورود...' : 'ورود'}
          </button>
        </form>
      </section>
    </main>
  );
}
