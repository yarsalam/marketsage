"use client";

import { useEffect, useMemo, useState } from "react";

type FooladPreview = {
  instrument: { symbol: string; name: string; ins_code: string; currency: string; unit: string };
  dataset: {
    status: string;
    daily_rows: number;
    daily_start: string;
    daily_end: string;
    display_sampling: string;
    display_points: number;
    adjusted_close_candidate_sha256: string;
    source_archive_sha256: string;
    event_count: number;
    price_adjust_records: number;
    share_change_events: number;
    arithmetic_mismatches: number;
    ohlc_violations: number;
    zero_volume_rows: number;
    corporate_action_completeness: string;
    scoring_eligible: boolean;
    backtest_approved: boolean;
  };
  points: [string, number][];
  warnings: string[];
};

const API_BASE = (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/$/, "");

function faNumber(value: number) {
  return value.toLocaleString("fa-IR", { maximumFractionDigits: 2 });
}

export function FooladMarketPanel() {
  const [payload, setPayload] = useState<FooladPreview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    fetch(`${API_BASE}/api/markets/iran-equities/foolad/preview`, {
      cache: "no-store",
      credentials: "include",
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) throw new Error(`دریافت داده فولاد ناموفق بود (HTTP ${response.status}).`);
        return response.json() as Promise<FooladPreview>;
      })
      .then((data) => setPayload(data))
      .catch((cause: unknown) => {
        if (cause instanceof Error && cause.name === "AbortError") return;
        setError(cause instanceof Error ? cause.message : "دریافت داده فولاد ناموفق بود.");
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [retry]);

  const chart = useMemo(() => {
    const points = payload?.points ?? [];
    if (points.length < 2) return "";
    const values = points.map((point) => point[1]);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const span = Math.max(1, max - min);
    return points.map((point, index) => {
      const x = 36 + (index / (points.length - 1)) * 888;
      const y = 218 - ((point[1] - min) / span) * 184;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(" ");
  }, [payload]);

  if (loading) {
    return <section className="rounded-2xl border border-border bg-surface p-5"><p className="animate-pulse text-sm text-text-secondary">در حال بارگذاری سری پژوهشی فولاد...</p></section>;
  }
  if (error || !payload) {
    return (
      <section className="space-y-3 rounded-2xl border border-border bg-surface p-5" role="alert">
        <h2 className="text-lg font-bold">داده فولاد در دسترس نیست</h2>
        <p className="text-sm text-text-secondary">{error ?? "پاسخ معتبری از سرویس دریافت نشد."}</p>
        <button type="button" onClick={() => setRetry((value) => value + 1)} className="text-sm text-primary underline">تلاش مجدد</button>
      </section>
    );
  }

  const { dataset, points, instrument } = payload;
  const latest = points[points.length - 1];

  return (
    <section className="space-y-4 rounded-2xl border border-border bg-surface p-4 md:p-5" dir="rtl">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs text-text-secondary">بورس و فرابورس ایران · سری تاریخی پژوهشی</p>
          <h2 className="mt-1 text-xl font-bold">{instrument.name} ({instrument.symbol})</h2>
          <p className="mt-1 text-xs text-text-secondary">شناسه ابزار: <span dir="ltr">{instrument.ins_code}</span></p>
        </div>
        <span className="rounded-full border border-amber-500/40 bg-amber-500/10 px-3 py-1 text-xs font-semibold text-amber-700">
          کاندیدای اصلاح‌شده · نیازمند بررسی
        </span>
      </header>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <article className="rounded-xl border border-border/70 p-3">
          <p className="text-xs text-text-secondary">آخرین نقطه نمایشی</p>
          <p className="mt-1 text-lg font-bold tabular-nums">{faNumber(latest[1])} ریال</p>
          <p className="text-xs text-text-secondary" dir="ltr">{latest[0]}</p>
        </article>
        <article className="rounded-xl border border-border/70 p-3">
          <p className="text-xs text-text-secondary">تاریخچه روزانه در candidate</p>
          <p className="mt-1 text-lg font-bold tabular-nums">{faNumber(dataset.daily_rows)} ردیف</p>
          <p className="text-xs text-text-secondary" dir="ltr">{dataset.daily_start} تا {dataset.daily_end}</p>
        </article>
        <article className="rounded-xl border border-border/70 p-3">
          <p className="text-xs text-text-secondary">رویدادهای تعدیل ثبت‌شده</p>
          <p className="mt-1 text-lg font-bold tabular-nums">{faNumber(dataset.event_count)}</p>
          <p className="text-xs text-text-secondary">{faNumber(dataset.price_adjust_records)} PriceAdjust · {faNumber(dataset.share_change_events)} تغییر سهام</p>
        </article>
        <article className="rounded-xl border border-border/70 p-3">
          <p className="text-xs text-text-secondary">نقض OHLC منتقل‌شده از خام</p>
          <p className="mt-1 text-lg font-bold tabular-nums">{faNumber(dataset.ohlc_violations)}</p>
          <p className="text-xs text-text-secondary">حجم صفر: {faNumber(dataset.zero_volume_rows)} ردیف</p>
        </article>
      </div>

      <div className="rounded-xl border border-border/70 p-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h3 className="font-semibold">روند قیمت تعدیل‌شده نامزد</h3>
            <p className="mt-1 text-xs text-text-secondary">نمونه‌برداری فصلی از سری روزانه · ریال به‌ازای هر سهم · {faNumber(dataset.display_points)} نقطه نمایشی</p>
          </div>
          <span className="text-xs text-text-secondary">آخرین مشاهده: <span dir="ltr">{latest[0]}</span></span>
        </div>
        <svg viewBox="0 0 960 250" className="mt-3 h-56 w-full" role="img" aria-label="نمودار فصلی قیمت تعدیل‌شده نامزد فولاد">
          <line x1="36" y1="34" x2="924" y2="34" stroke="currentColor" opacity=".12" />
          <line x1="36" y1="126" x2="924" y2="126" stroke="currentColor" opacity=".12" />
          <line x1="36" y1="218" x2="924" y2="218" stroke="currentColor" opacity=".12" />
          <polyline points={chart} fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />
        </svg>
        <div className="flex justify-between text-[11px] text-text-secondary" dir="ltr">
          <span>{points[0][0]}</span><span>{latest[0]}</span>
        </div>
      </div>

      <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-3 text-sm leading-6">
        <p className="font-semibold">محدودیت استفاده</p>
        <ul className="mt-1 list-disc space-y-1 pr-5 text-xs text-text-secondary">
          {payload.warnings.map((warning) => <li key={warning}>{warning}</li>)}
        </ul>
        <p className="mt-2 text-xs font-semibold text-amber-700">
          امتیازدهی: {dataset.scoring_eligible ? "مجاز" : "مسدود"} · بک‌تست: {dataset.backtest_approved ? "مجاز" : "مسدود"}
        </p>
      </div>

      <details className="rounded-xl border border-border/70 p-3 text-xs">
        <summary className="cursor-pointer font-semibold">منشأ و هش نسخه داده</summary>
        <p className="mt-2 text-text-secondary">SHA-256 خروجی candidate</p>
        <p className="break-all font-mono" dir="ltr">{dataset.adjusted_close_candidate_sha256}</p>
        <p className="mt-2 text-text-secondary">SHA-256 آرشیو ورودی</p>
        <p className="break-all font-mono" dir="ltr">{dataset.source_archive_sha256}</p>
        <p className="mt-2 text-text-secondary">تطبیق حسابی close × factor: {dataset.arithmetic_mismatches} مغایرت · کامل‌بودن اقدامات شرکتی: {dataset.corporate_action_completeness}</p>
      </details>
    </section>
  );
}
