"use client";

import { useEffect, useState } from "react";

interface Allocation {
  asset: string;
  ticker: string;
  weight: number;
  capital_allocated: number;
}

interface DecisionResponse {
  horizon: string;
  market_scope: string;
  source: string;
  data_as_of: string;
  generated_at: string;
  allocation: Allocation[];
  capital: number;
  confidence: number | null;
  confidence_status: string;
  risk_level: string;
  annualized_volatility: number | null;
  total_assets_analyzed: number;
  warnings: string[];
}

const API_BASE = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:4500").replace(/\/$/, "");

export const InvestmentDecision = ({ onNavigate }: { onNavigate: (tab: string) => void }) => {
  const [decision, setDecision] = useState<DecisionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetch(`${API_BASE}/api/decision?horizon=1M&capital=500000000`, {
      headers: { Accept: "application/json" },
      signal: controller.signal,
      cache: "no-store",
    })
      .then(async (response) => {
        if (!response.ok) {
          const body = await response.json().catch(() => null);
          throw new Error(body?.message ?? body?.detail ?? `خطای سرور (${response.status})`);
        }
        return response.json() as Promise<DecisionResponse>;
      })
      .then(setDecision)
      .catch((cause: unknown) => {
        if (cause instanceof Error && cause.name === "AbortError") return;
        setError(cause instanceof Error ? cause.message : "دریافت اطلاعات بازار ناموفق بود.");
      });
    return () => controller.abort();
  }, []);

  if (error) {
    return (
      <section className="m-6 rounded-2xl border border-border bg-surface p-6" role="alert">
        <h2 className="text-xl font-bold">پیشنهاد سرمایه‌گذاری در دسترس نیست</h2>
        <p className="mt-2 text-sm text-text-secondary">{error}</p>
        <p className="mt-2 text-xs text-text-secondary">
          برای جلوگیری از نمایش پیشنهاد ساختگی، داده جایگزین نمایش داده نمی‌شود.
        </p>
      </section>
    );
  }

  if (!decision) {
    return <div className="animate-pulse p-6 text-text-secondary">در حال دریافت داده واقعی سرویس تحلیل...</div>;
  }

  return (
    <section className="space-y-6 p-6">
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <h2 className="text-2xl font-bold">🎯 رتبه‌بندی پژوهشی دارایی‌ها</h2>
        <span className="text-sm text-text-secondary">
          افق درخواستی: {decision.horizon} · دارایی معتبر: {decision.total_assets_analyzed}
        </span>
      </div>

      <div className="rounded-xl border border-border bg-surface p-4 text-sm">
        <div className="flex flex-wrap gap-x-6 gap-y-2">
          <span>محدوده داده: {decision.market_scope === "global_proxy" ? "نماینده‌های بازار جهانی" : decision.market_scope}</span>
          <span>آخرین داده: {decision.data_as_of}</span>
          <span>ریسک نوسانی: {decision.risk_level}</span>
          <span>
            نوسان سالانه‌شده: {decision.annualized_volatility == null
              ? "نامشخص"
              : `${(decision.annualized_volatility * 100).toFixed(1)}٪`}
          </span>
        </div>
        <p className="mt-2 text-xs text-text-secondary">
          اطمینان مدل: محاسبه نشده؛ احتمال‌ها هنوز خارج از نمونه کالیبره نشده‌اند.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {decision.allocation.map((item, index) => (
          <article key={item.ticker} className="flex flex-col gap-3 rounded-2xl border border-border bg-surface p-4">
            <div className="flex items-start justify-between gap-2">
              <span className="text-lg font-bold">{item.asset}</span>
              <span className="rounded border border-border px-2 py-0.5 text-xs text-text-secondary">#{index + 1}</span>
            </div>
            <div className="text-3xl font-bold text-primary">{(item.weight * 100).toFixed(1)}٪</div>
            <div className="text-sm text-text-secondary">
              {item.capital_allocated.toLocaleString("fa-IR")} واحد از سرمایه واردشده
            </div>
            <div className="text-xs text-text-secondary">نماد داده: {item.ticker}</div>
          </article>
        ))}
      </div>

      <div className="rounded-2xl border border-border bg-surface p-4">
        <h3 className="font-bold">محدودیت‌ها و هشدارها</h3>
        <ul className="mt-2 list-disc space-y-1 pr-5 text-sm text-text-secondary">
          {decision.warnings.map((warning) => <li key={warning}>{warning}</li>)}
        </ul>
        <p className="mt-3 text-xs text-text-secondary">منبع داده: {decision.source}</p>
        <button onClick={() => onNavigate("risk")} className="mt-3 text-sm text-primary hover:underline">
          مشاهده مرکز ریسک ←
        </button>
      </div>
    </section>
  );
};
