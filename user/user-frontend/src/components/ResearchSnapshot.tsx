"use client";

import { useState } from "react";

type Snapshot = {
  pipeline_version: string;
  as_of_date: string;
  news: {
    articles_analyzed: number;
    future_articles_excluded: number;
    articles: Array<{
      title: string;
      sentiment_label: string;
      event_categories: string[];
      eligible_for_scoring: boolean;
    }>;
  };
  markets: Array<{
    symbol: string;
    metrics: {
      status: string;
      observations_used: number;
      first_observation_date: string | null;
      last_observation_date: string | null;
      total_return: number | null;
      daily_volatility: number | null;
      max_drawdown: number | null;
    };
    eligible_for_scoring: boolean;
    exclusion_reasons: string[];
  }>;
  investment_ranking: null;
  investment_ranking_status: string;
  point_in_time_limitations: string[];
};

const API_BASE = (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/$/, "");

const demoPayload = {
  as_of_date: "2026-10-17",
  articles: [
    {
      source_id: "fixture.news",
      url: "https://example.test/markets/central-bank-demo",
      title: "بانک مرکزی از رشد و توافق خبر داد",
      first_seen_date: "2026-10-16",
    },
    {
      source_id: "fixture.news",
      url: "https://example.test/markets/future-demo",
      title: "Markets surge after agreement",
      first_seen_date: "2026-10-19",
    },
  ],
  market_series: [
    {
      symbol: "DEMO",
      source_id: "fixture.market",
      unit: "USD per unit",
      currency: "USD",
      unit_confirmed: true,
      currency_confirmed: true,
      observations: [
        { date: "2026-10-15", close: 100 },
        { date: "2026-10-16", close: 110 },
        { date: "2026-10-17", close: 105 },
        { date: "2026-10-18", close: 1000 },
      ],
    },
  ],
};

function percent(value: number | null) {
  return value == null || !Number.isFinite(value)
    ? "نامشخص"
    : `${(value * 100).toFixed(2)}٪`;
}

export function ResearchSnapshot() {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function runDemo() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/api/markets/research-snapshot`, {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json" },
        body: JSON.stringify(demoPayload),
        cache: "no-store",
      });
      const body = await response.json().catch(() => null);
      if (!response.ok) {
        throw new Error(body?.message ?? body?.detail ?? `خطای سرور (${response.status})`);
      }
      setSnapshot(body as Snapshot);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "اجرای نمونه ناموفق بود.");
    } finally {
      setLoading(false);
    }
  }

  const market = snapshot?.markets[0];
  return (
    <section className="space-y-5 p-4 md:p-6" dir="rtl">
      <header className="space-y-2">
        <h2 className="text-2xl font-bold">نمونهٔ انتهابه‌انتهای پژوهش</h2>
        <p className="text-sm text-text-secondary">
          این دمو دادهٔ ثابت و ساختگی را از API عبور می‌دهد تا مسیر نرمال‌سازی خبر،
          حذف دادهٔ آینده و محاسبهٔ معیارهای تاریخی را نشان دهد؛ دادهٔ زنده نیست.
        </p>
      </header>

      <div className="rounded-xl border border-border bg-surface p-4">
        <p className="font-semibold">آزمون قابل تکرار</p>
        <ul className="mt-2 list-disc space-y-1 pr-5 text-sm text-text-secondary">
          <li>دو خبر ورودی؛ خبر دارای تاریخ آینده باید کنار گذاشته شود.</li>
          <li>چهار قیمت ورودی؛ قیمت ۱۸ اکتبر نباید در snapshot مورخ ۱۷ اکتبر اثر بگذارد.</li>
          <li>رتبه‌بندی سرمایه‌گذاری باید خاموش بماند، حتی اگر معیارهای توصیفی محاسبه شوند.</li>
        </ul>
        <button
          type="button"
          onClick={runDemo}
          disabled={loading}
          className="mt-4 rounded-lg bg-primary px-4 py-2 font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? "در حال اجرای نمونه..." : "اجرای نمونه از طریق API"}
        </button>
        {error && <p className="mt-3 text-sm text-red-400" role="alert">{error}</p>}
      </div>

      {snapshot && (
        <div className="space-y-4">
          <div className="rounded-xl border border-border bg-surface p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="font-bold">نتیجهٔ API</h3>
              <span className="text-xs text-text-secondary">
                نسخه {snapshot.pipeline_version} · تا تاریخ {snapshot.as_of_date}
              </span>
            </div>
            <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-lg bg-background p-3">
                <p className="text-xs text-text-secondary">خبرهای تحلیل‌شده</p>
                <p className="mt-1 text-xl font-bold">{snapshot.news.articles_analyzed}</p>
              </div>
              <div className="rounded-lg bg-background p-3">
                <p className="text-xs text-text-secondary">خبرهای آیندهٔ حذف‌شده</p>
                <p className="mt-1 text-xl font-bold">{snapshot.news.future_articles_excluded}</p>
              </div>
              <div className="rounded-lg bg-background p-3">
                <p className="text-xs text-text-secondary">بازده توصیفی DEMO</p>
                <p className="mt-1 text-xl font-bold">{market ? percent(market.metrics.total_return) : "نامشخص"}</p>
              </div>
              <div className="rounded-lg bg-background p-3">
                <p className="text-xs text-text-secondary">آخرین قیمت استفاده‌شده</p>
                <p className="mt-1 text-xl font-bold">{market?.metrics.last_observation_date ?? "نامشخص"}</p>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-border bg-surface p-4">
            <h3 className="font-bold">تحلیل خبر</h3>
            {snapshot.news.articles.map((article, index) => (
              <div key={index} className="mt-3 border-t border-border pt-3">
                <p>{article.title}</p>
                <p className="mt-1 text-sm text-text-secondary">
                  احساس: {article.sentiment_label} · رویدادها: {article.event_categories.join("، ") || "تشخیص داده نشد"}
                </p>
              </div>
            ))}
          </div>

          <div className="rounded-xl border border-border bg-surface p-4">
            <h3 className="font-bold">محدودیت رتبه‌بندی</h3>
            <p className="mt-2 text-sm text-text-secondary">
              وضعیت: {snapshot.investment_ranking_status}
            </p>
            <p className="mt-1 text-sm">
              رتبهٔ سرمایه‌گذاری: {snapshot.investment_ranking === null ? "غیرفعال" : "موجود"}
            </p>
            <p className="mt-1 text-sm text-text-secondary">
              دلایل کنارگذاری سری قیمت: {market?.exclusion_reasons.join("، ") || "ندارد"}
            </p>
            <ul className="mt-3 list-disc space-y-1 pr-5 text-xs text-text-secondary">
              {snapshot.point_in_time_limitations.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </div>
        </div>
      )}
    </section>
  );
}
