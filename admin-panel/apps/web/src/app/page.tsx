"use client";

import { useCallback, useEffect, useState } from "react";

type ProbeStatus = "healthy" | "unavailable" | "not_configured" | "disabled";
interface OpsStatus {
  enabled: boolean;
  checkedAt: string;
  access: "read_only";
  services: { userBackend: ProbeStatus; analysisEngine: ProbeStatus };
}

const API_BASE = (process.env.NEXT_PUBLIC_ADMIN_API_URL ?? "http://localhost:4000").replace(/\/$/, "");
const labels: Record<ProbeStatus, string> = {
  healthy: "سالم",
  unavailable: "در دسترس نیست",
  not_configured: "اتصال تنظیم نشده",
  disabled: "غیرفعال",
};

function StatusCard({ title, status }: { title: string; status: ProbeStatus }) {
  const positive = status === "healthy";
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <h2 className="font-semibold text-slate-800">{title}</h2>
        <span className={`rounded-full px-3 py-1 text-sm ${positive ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-600"}`}>
          {labels[status]}
        </span>
      </div>
      <p className="mt-3 text-sm text-slate-500">
        {positive
          ? "پاسخ سلامت سرویس تأیید شد."
          : status === "unavailable"
            ? "درخواست سلامت موفق نبود؛ علت داخلی نمایش داده نمی‌شود."
            : status === "not_configured"
              ? "نشانی این سرویس در محیط اجرایی تنظیم نشده است."
              : "پایش تا تکمیل راه‌اندازی داخلی غیرفعال است."}
      </p>
    </article>
  );
}

export default function Home() {
  const [data, setData] = useState<OpsStatus | null>(null);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      const response = await fetch(`${API_BASE}/ops/status`, {
        method: "GET",
        headers: { Accept: "application/json" },
        cache: "no-store",
        signal: AbortSignal.timeout(7000),
      });
      if (!response.ok) throw new Error("status unavailable");
      setData((await response.json()) as OpsStatus);
    } catch {
      setError(true);
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return (
    <main dir="rtl" className="min-h-screen bg-slate-50 px-4 py-8 text-slate-900 md:px-10">
      <div className="mx-auto max-w-5xl">
        <header className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-sky-700">MARKETSAGE / ADMIN</p>
            <h1 className="mt-2 text-3xl font-bold">مرکز عملیات</h1>
            <p className="mt-2 text-sm text-slate-500">پایش فقط‌خواندنی سلامت سرویس‌ها</p>
          </div>
          <button
            type="button"
            onClick={() => void refresh()}
            disabled={loading}
            className="rounded-xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white disabled:opacity-50"
          >
            {loading ? "در حال بررسی..." : "بررسی مجدد"}
          </button>
        </header>

        <section className="mt-8 rounded-2xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900">
          این فضای عملیاتی هنوز برای انتشار عمومی مجاز نیست. احراز هویت مدیر، نقش‌ها و ثبت رویدادهای ممیزی باید پیش از اتصال عمومی تکمیل شوند.
        </section>

        {error ? (
          <p role="alert" className="mt-6 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            دریافت وضعیت سرویس ممکن نشد؛ هیچ وضعیت فرضی نمایش داده نمی‌شود.
          </p>
        ) : null}

        {data ? (
          <>
            <section className="mt-8 grid gap-4 md:grid-cols-2">
              <StatusCard title="API کاربر" status={data.services.userBackend} />
              <StatusCard title="موتور تحلیل" status={data.services.analysisEngine} />
            </section>
            <p className="mt-4 text-xs text-slate-500">
              {data.enabled ? "پایش فعال" : "پایش غیرفعال"} · حالت فقط‌خواندنی · زمان بررسی: {new Date(data.checkedAt).toLocaleString("fa-IR")}
            </p>
            {!data.enabled ? (
              <p className="mt-4 rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-600">
                برای فعال‌سازی پایش در محیط داخلی، MARKETSAGE_ADMIN_OPS_ENABLED=true را تنظیم کنید. این تنظیم به‌تنهایی مجوز انتشار عمومی نیست.
              </p>
            ) : null}
          </>
        ) : !error ? (
          <p className="mt-8 text-sm text-slate-500">در حال دریافت وضعیت...</p>
        ) : null}
      </div>
    </main>
  );
}
