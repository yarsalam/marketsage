"use client";

import { useCallback, useEffect, useState } from "react";

const API_BASE = (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/$/, "");

type SourceStatus = {
  source_id: string;
  provider: string;
  configured: boolean;
  refresh_enabled: boolean;
  public_display_enabled: boolean;
  network_tested: boolean;
  production_approved: boolean;
  eligible_for_scoring: boolean;
  stored_observation_count: number;
  refresh_attempt_count: number;
  latest_refresh: null | {
    retrieved_at: string;
    status: string;
    item_count: number;
    error_code?: string | null;
  };
  notes: string[];
};

type RatesResponse = {
  status: string;
  latest_refresh?: { retrieved_at: string; item_count: number } | null;
  rates: Array<{
    instrument_key: string;
    display_name: string;
    raw_rate: string;
    provider_decimals: number;
    unit: string | null;
    market_definition: string | null;
    retrieved_at: string;
  }>;
  notice?: string;
};

type Opportunities = {
  status: string;
  opportunities: Array<{ symbol: string; name: string; score: number }>;
  blocked_reasons: string[];
  message: string;
};

async function getJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { Accept: "application/json", ...(init?.headers ?? {}) },
    cache: "no-store",
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.message ?? body?.detail ?? `خطای سرور (${response.status})`);
  }
  return response.json() as Promise<T>;
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return <section className="rounded-2xl border border-border bg-surface p-5">
    <h2 className="mb-4 text-lg font-bold">{title}</h2>{children}
  </section>;
}

export function IranMarketDashboard() {
  const [status, setStatus] = useState<SourceStatus | null>(null);
  const [rates, setRates] = useState<RatesResponse | null>(null);
  const [opportunities, setOpportunities] = useState<Opportunities | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshResult, setRefreshResult] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState("");

  const load = useCallback(async () => {
    setError(null);
    try {
      const [s, r, o] = await Promise.all([
        getJson<SourceStatus>("/api/markets/iran/data-status"),
        getJson<RatesResponse>("/api/markets/iran/currency-rates"),
        getJson<Opportunities>("/api/markets/iran/opportunities"),
      ]);
      setStatus(s);
      setRates(r);
      setOpportunities(o);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "دریافت وضعیت داده ناموفق بود.");
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const refresh = async () => {
    setRefreshing(true);
    setRefreshResult(null);
    setError(null);
    try {
      const result = await getJson<{ status: string; item_count: number; message: string }>(
        "/api/markets/iran/refresh",
        { method: "POST", headers: { "X-Iran-Refresh-Token": refreshToken } },
      );
      setRefreshResult(`دریافت موفق: ${result.item_count} رکورد ذخیره شد.`);
      await load();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "به‌روزرسانی منبع ناموفق بود.");
    } finally {
      setRefreshing(false);
    }
  };

  return <div className="space-y-5 p-4 md:p-6" dir="rtl">
    <header className="flex flex-wrap items-start justify-between gap-4">
      <div>
        <h1 className="text-2xl font-bold">مرکز داده بازار ایران</h1>
        <p className="mt-2 max-w-3xl text-sm text-text-secondary">
          اتصال منبع، ذخیره‌سازی داده خام و نرمال‌شده و نمایش وضعیت پوشش بازار.
          به‌روزرسانی فقط دستی و با توکن سروری انجام می‌شود تا سهمیه API مصرف بی‌دلیل نداشته باشد. توکن در مرورگر ذخیره نمی‌شود.
        </p>
      </div>
      <div className="flex w-full flex-col gap-2 sm:w-auto">
        <label className="text-xs text-text-secondary" htmlFor="iran-refresh-token">توکن مجاز به‌روزرسانی (فقط برای همین درخواست)</label>
        <input id="iran-refresh-token" type="password" autoComplete="off" value={refreshToken}
          onChange={(event) => setRefreshToken(event.target.value)}
          placeholder="توکن تنظیم‌شده روی سرور"
          className="rounded-xl border border-border bg-background px-3 py-2 text-sm" />
        <button onClick={refresh} disabled={refreshing || !status?.configured || !status?.refresh_enabled || !refreshToken}
          className="rounded-xl bg-primary px-4 py-2 font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50">
          {refreshing ? "در حال دریافت..." : "دریافت آخرین داده از Tindex"}
        </button>
      </div>
    </header>

    {error && <div role="alert" className="rounded-xl border border-red-500/40 p-4 text-sm">{error}</div>}
    {refreshResult && <div role="status" className="rounded-xl border border-border p-4 text-sm">{refreshResult}</div>}

    <div className="grid gap-4 md:grid-cols-3">
      <Panel title="وضعیت اتصال">
        <p className="text-sm">{status?.configured ? "تنظیمات اتصال کامل است" : "توکن یا API origin تنظیم نشده"}</p>
        <p className="mt-2 text-xs text-text-secondary">شناسه: iran.tindex.public_api</p>
        <p className="mt-1 text-xs text-text-secondary">درخواست شبکه: {status?.network_tested ? "قبلاً موفق بوده" : "هنوز تأیید نشده"}</p>
      </Panel>
      <Panel title="داده ذخیره‌شده">
        <p className="text-2xl font-bold">{(status?.stored_observation_count ?? 0).toLocaleString("fa-IR")}</p>
        <p className="mt-1 text-sm text-text-secondary">مشاهده نرمال‌شده</p>
        <p className="mt-2 text-xs text-text-secondary">تلاش‌های دریافت: {(status?.refresh_attempt_count ?? 0).toLocaleString("fa-IR")}</p>
      </Panel>
      <Panel title="وضعیت استفاده تجاری">
        <p className="font-semibold">امتیازدهی غیرفعال</p>
        <p className="mt-2 text-sm text-text-secondary">تأیید مجوز، تعریف واحدها و زمان مشاهده هنوز کامل نیست.</p>
        <p className="mt-1 text-xs text-text-secondary">نمایش عمومی داده: {status?.public_display_enabled ? "فعال" : "غیرفعال تا تأیید مجوز"}</p>
      </Panel>
    </div>

    <Panel title="نرخ‌های دریافتی از منبع">
      {!rates?.rates?.length ? (
        <p className="text-sm text-text-secondary">{rates?.notice ?? "هنوز دریافت موفقی ثبت نشده است. پس از تنظیم متغیرهای اتصال، دکمه دریافت را بزن."}</p>
      ) : <>
        <p className="mb-3 text-xs text-text-secondary">
          آخرین دریافت: {rates.latest_refresh?.retrieved_at ?? "نامشخص"} · اعداد خام منبع هستند و واحدشان تأیید نشده است.
        </p>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[520px] text-right text-sm">
            <thead><tr className="border-b border-border text-text-secondary">
              <th className="p-2">شناسه</th><th className="p-2">نام منبع</th><th className="p-2">مقدار خام</th><th className="p-2">واحد</th>
            </tr></thead>
            <tbody>{rates.rates.map((row) => <tr key={row.instrument_key} className="border-b border-border/60">
              <td className="p-2 font-mono">{row.instrument_key}</td>
              <td className="p-2">{row.display_name}</td>
              <td className="p-2 font-mono">{Number(row.raw_rate).toLocaleString("fa-IR", { maximumFractionDigits: row.provider_decimals })}</td>
              <td className="p-2">{row.unit ?? "تأیید نشده"}</td>
            </tr>)}</tbody>
          </table>
        </div>
        <p className="mt-3 text-xs text-text-secondary">{rates.notice}</p>
      </>}
    </Panel>

    <Panel title="رتبه‌بندی فرصت‌های سرمایه‌گذاری ایران">
      <p className="font-semibold">فعلاً رتبه‌ای منتشر نمی‌شود</p>
      <p className="mt-2 text-sm text-text-secondary">{opportunities?.message ?? "در انتظار دریافت وضعیت API..."}</p>
      <ul className="mt-3 list-disc space-y-1 pr-5 text-sm text-text-secondary">
        {(opportunities?.blocked_reasons ?? [
          "منبع دارای مجوز تولیدی هنوز تأیید نشده است.",
          "برای رتبه‌بندی، تاریخچه قابل مقایسه و واحدهای تأییدشده لازم است.",
        ]).map((reason) => <li key={reason}>{reason}</li>)}
      </ul>
    </Panel>

    <Panel title="گام‌های لازم برای فعال‌سازی رتبه‌بندی">
      <ol className="list-decimal space-y-2 pr-5 text-sm text-text-secondary">
        <li>تأیید کتبی مجوز استفاده تجاری و بازنشر Tindex.</li>
        <li>تأیید واحد، تعریف بازار و زمان مشاهده هر نرخ با ارائه‌دهنده.</li>
        <li>اتصال تاریخچه قیمت مجاز برای دارایی‌های قابل مقایسه و ذخیره منظم آن.</li>
        <li>تأیید کیفیت، تازگی، پوشش تاریخی و سپس فعال‌سازی جداگانه هر منبع برای امتیازدهی.</li>
      </ol>
    </Panel>
  </div>;
}
