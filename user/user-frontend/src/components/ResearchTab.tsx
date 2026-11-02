"use client";

import { useEffect, useState } from "react";

type TabId = "momentum" | "regime" | "news" | "risk" | "portfolio" | "backtest" | "macro" | "analyst" | "settings";
type Allocation = { asset: string; ticker: string; weight: number; capital_allocated: number };
type Decision = { allocation: Allocation[]; data_as_of: string; source: string; warnings: string[]; confidence_status: string };
type Backtest = {
  start: string; end: string; periods: number; data_as_of: string;
  metrics: Record<string, number | null>;
  benchmarks: Record<string, Record<string, number | null>>;
  holdout?: {
    method: string; start: string; end: string; periods: number;
    metrics: Record<string, number | null>;
    benchmarks: Record<string, Record<string, number | null>>;
  };
  monthly: Array<Record<string, string | number>>;
  warnings: string[];
  confidence_status: string;
};
type Scores = { signal_as_of: string; provider_data_as_of: string; scores: Record<string, number>; stale: boolean; confidence_status: string };
type DataStatus = Record<string, unknown>;

const API_BASE = (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/$/, "");
const unavailable: Record<string, { title: string; description: string; next: string }> = {
  regime: { title: "تشخیص رژیم بازار", description: "مدل رژیم بازار هنوز به داده‌های زمان‌دار و آزمون خارج از نمونه متصل نشده است؛ در این بخش عدد یا برچسب ساختگی نمایش داده نمی‌شود.", next: "پس از تعریف ویژگی‌ها، برچسب‌ها و آزمون walk-forward، این تب به سرویس تحلیل متصل می‌شود." },
  news: { title: "هوش اخبار", description: "گردآورنده خبر، منبع معتبر و زمان انتشار قابل ممیزی هنوز پیکربندی نشده‌اند.", next: "نیازمند ارائه‌دهنده خبر، ثبت timestamp و سیاست deduplication است." },
  macro: { title: "داده‌های کلان", description: "سری‌های کلان با زمان انتشار و نسخه‌های تاریخی در حال حاضر در این سرویس در دسترس نیستند.", next: "داده‌های کلان باید با زمان انتشار واقعی منتشرکننده نگهداری شوند تا look-ahead ایجاد نشود." },
  analyst: { title: "تحلیلگر AI", description: "خلاصه‌سازی هوشمند هنوز به شواهد واقعی و قابل استناد بازار متصل نشده است.", next: "پس از اتصال منابع معتبر و ثبت ارجاعات، این بخش فعال می‌شود." },
};

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return <section className="space-y-4 p-6"><h2 className="text-2xl font-bold">{title}</h2>{children}</section>;
}
function Notice({ children }: { children: React.ReactNode }) {
  return <div className="rounded-xl border border-border bg-surface p-4 text-sm text-text-secondary">{children}</div>;
}
function formatPercent(value: number | null | undefined) {
  return value == null || !Number.isFinite(value) ? "نامشخص" : `${(value * 100).toFixed(2)}٪`;
}
function formatMetric(value: number | null | undefined) {
  return value == null || !Number.isFinite(value) ? "نامشخص" : value.toFixed(3);
}

export function ResearchTab({ activeTab, onNavigate }: { activeTab: TabId; onNavigate: (tab: string) => void }) {
  const [data, setData] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    let endpoint: string | null = null;
    if (activeTab === "momentum") endpoint = "/api/markets/scores";
    if (activeTab === "risk" || activeTab === "backtest") endpoint = "/api/markets/backtest";
    if (activeTab === "portfolio") endpoint = "/api/decision?horizon=1M&capital=500000000";
    if (activeTab === "settings") endpoint = "/api/markets/data-status";
    if (!endpoint) { setData(null); setError(null); setLoading(false); return () => controller.abort(); }

    setLoading(true); setData(null); setError(null);
    fetch(`${API_BASE}${endpoint}`, { headers: { Accept: "application/json" }, cache: "no-store", signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) {
          const body = await response.json().catch(() => null);
          throw new Error(body?.message ?? body?.detail ?? `خطای سرور (${response.status})`);
        }
        return response.json();
      })
      .then(setData)
      .catch((cause: unknown) => {
        if (cause instanceof Error && cause.name === "AbortError") return;
        setError(cause instanceof Error ? cause.message : "دریافت داده ناموفق بود.");
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [activeTab]);

  if (unavailable[activeTab]) {
    const item = unavailable[activeTab];
    return <Panel title={item.title}><Notice>{item.description}<p className="mt-3">{item.next}</p></Notice></Panel>;
  }
  if (loading) return <Panel title="در حال دریافت داده"><p className="animate-pulse text-text-secondary">در حال دریافت اطلاعات از API...</p></Panel>;
  if (error) return <Panel title="داده در دسترس نیست"><Notice><p role="alert">{error}</p><p className="mt-2">برای جلوگیری از نمایش اعداد ساختگی، داده نمونه جایگزین نشده است.</p><button className="mt-3 text-primary underline" onClick={() => onNavigate("decision")}>بازگشت به تصمیم پژوهشی</button></Notice></Panel>;
  if (!data) {
    return <Panel title="تنظیمات داده"><Notice>هنوز داده‌ای در حافظه سرویس بارگذاری نشده است. برای دریافت نخستین snapshot، ابتدا تب «تصمیم سرمایه‌گذاری» را باز کن.</Notice></Panel>;
  }

  if (activeTab === "momentum") {
    const result = data as Scores;
    return <Panel title="مانیتور مومنتوم">
      <Notice>امتیازها رتبه‌بندی نسبی هستند، نه احتمال سود یا پیش‌بینی بازده. تاریخ سیگنال: {result.signal_as_of ?? "نامشخص"} · آخرین داده دریافت‌شده: {result.provider_data_as_of ?? "نامشخص"}{result.stale ? " · هشدار: داده cache ممکن است قدیمی باشد." : ""}</Notice>
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">{Object.entries(result.scores ?? {}).map(([name, score], i) => <article key={name} className="rounded-xl border border-border bg-surface p-4"><div className="flex justify-between"><strong>{name}</strong><span className="text-xs text-text-secondary">رتبه {i + 1}</span></div><p className="mt-3 text-2xl font-bold text-primary">{score.toFixed(4)}</p><div className="mt-2 h-2 rounded bg-background"><div className="h-2 rounded bg-primary" style={{ width: `${Math.max(0, Math.min(1, score)) * 100}%` }} /></div></article>)}</div>
    </Panel>;
  }

  if (activeTab === "portfolio") {
    const result = data as Decision;
    return <Panel title="تخصیص پرتفوی پژوهشی"><Notice>این تخصیص برابر‌وزن از رتبه‌بندی تاریخی به‌دست آمده و توصیه شخصی یا پرتفوی کم‌ریسک تضمین‌شده نیست. آخرین داده: {result.data_as_of}</Notice><div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">{result.allocation?.map((item) => <article key={item.ticker} className="rounded-xl border border-border bg-surface p-4"><strong>{item.asset}</strong><p className="mt-2 text-2xl font-bold">{formatPercent(item.weight)}</p><p className="text-sm text-text-secondary">{item.capital_allocated.toLocaleString("fa-IR")} واحد سرمایه</p><p className="text-xs text-text-secondary">{item.ticker}</p></article>)}</div><ul className="list-disc space-y-1 pr-5 text-sm text-text-secondary">{result.warnings?.map((warning) => <li key={warning}>{warning}</li>)}</ul></Panel>;
  }

  if (activeTab === "settings") {
    const status = data as DataStatus;
    return <Panel title="وضعیت سرویس داده"><Notice>این صفحه وضعیت cache درون حافظه سرویس را نشان می‌دهد؛ پس از restart ممکن است تا دریافت درخواست تحلیل، بارگذاری نشده باشد.</Notice><pre className="overflow-x-auto rounded-xl border border-border bg-surface p-4 text-xs" dir="ltr">{JSON.stringify(status, null, 2)}</pre><button className="text-primary underline" onClick={() => onNavigate("decision")}>دریافت داده و مشاهده تحلیل</button></Panel>;
  }

  const result = data as Backtest;
  const m = result.holdout?.metrics ?? result.metrics ?? {};
  const shownBenchmarks = result.holdout?.benchmarks ?? result.benchmarks ?? {};
  const metricCards: Array<[string, number | null | undefined, boolean]> = [
    ["بازده کل خالص", m.total_return, true],
    ["CAGR", m.cagr, true],
    ["نوسان سالانه", m.annualized_volatility, true],
    ["Sharpe (بدون نرخ بدون ریسک)", m.sharpe, false],
    ["حداکثر افت سرمایه", m.max_drawdown, true],
    ["VaR تاریخی ۹۵٪ ماهانه", m.historical_var_95_monthly, true],
    ["بتا نسبت به SPY", m.beta_vs_spy, false],
    ["میانگین گردش ماهانه", m.average_monthly_turnover, false],
  ];
  return <Panel title={activeTab === "risk" ? "مرکز ریسک — بک‌تست تاریخی" : "آزمایشگاه بک‌تست"}>
    <Notice>کل تاریخچه: {result.start} تا {result.end} · {result.periods} ماه بازده · داده تا {result.data_as_of ?? "نامشخص"}<br />{result.holdout ? `دوره آزمون زمانی جداگانه (۳۰٪ انتهایی): ${result.holdout.start} تا ${result.holdout.end} · ${result.holdout.periods} ماه` : "دوره آزمون جداگانه در دسترس نیست."}<br />اعداد کارت‌ها و جدول معیارها مربوط به دوره آزمون جداگانه‌اند. این شبیه‌سازی پژوهشی است؛ هزینه‌ها تخمینی‌اند و این آزمون جایگزین اعتبارسنجی مستقل در بازار واقعی نیست.</Notice>
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{metricCards.map(([label, value, percent]) => <article key={label} className="rounded-xl border border-border bg-surface p-4"><p className="text-xs text-text-secondary">{label}</p><p className="mt-2 text-xl font-bold">{percent ? formatPercent(value) : formatMetric(value)}</p></article>)}</div>
    <h3 className="font-bold">مقایسه با معیارها (قبل از هزینه معاملات معیار)</h3>
    <div className="overflow-x-auto rounded-xl border border-border"><table className="w-full text-right text-sm"><thead className="bg-surface"><tr><th className="p-3">معیار</th><th className="p-3">بازده کل</th><th className="p-3">CAGR</th><th className="p-3">افت حداکثر</th><th className="p-3">نوسان</th></tr></thead><tbody>{Object.entries(shownBenchmarks).map(([name, metrics]) => <tr key={name} className="border-t border-border"><td className="p-3">{name.replaceAll("_", " ")}</td><td className="p-3">{formatPercent(metrics.total_return)}</td><td className="p-3">{formatPercent(metrics.cagr)}</td><td className="p-3">{formatPercent(metrics.max_drawdown)}</td><td className="p-3">{formatPercent(metrics.annualized_volatility)}</td></tr>)}</tbody></table></div>
    {activeTab === "backtest" && <><h3 className="font-bold">۳۶ دوره اخیر</h3><div className="max-h-96 overflow-auto rounded-xl border border-border"><table className="w-full text-right text-xs"><thead className="sticky top-0 bg-surface"><tr><th className="p-2">تاریخ</th><th className="p-2">بازده خالص</th><th className="p-2">افت سرمایه</th><th className="p-2">گردش</th><th className="p-2">دارایی‌های منتخب</th></tr></thead><tbody>{result.monthly?.map((row) => <tr key={String(row.date)} className="border-t border-border"><td className="p-2">{row.date}</td><td className="p-2">{formatPercent(Number(row.net_return))}</td><td className="p-2">{formatPercent(Number(row.drawdown))}</td><td className="p-2">{formatMetric(Number(row.turnover))}</td><td className="p-2">{row.selected_assets}</td></tr>)}</tbody></table></div></>}
    {result.holdout?.method && <p className="text-xs text-text-secondary">روش آزمون: {result.holdout.method}</p>}
    <ul className="list-disc space-y-1 pr-5 text-xs text-text-secondary">{result.warnings?.map((warning) => <li key={warning}>{warning}</li>)}</ul>
  </Panel>;
}

export const MomentumMonitor = (props: { onNavigate: (tab: string) => void }) => <ResearchTab activeTab="momentum" {...props} />;
export const MarketRegime = (props: { onNavigate: (tab: string) => void }) => <ResearchTab activeTab="regime" {...props} />;
export const NewsIntelligence = (props: { onNavigate: (tab: string) => void }) => <ResearchTab activeTab="news" {...props} />;
export const RiskCenter = (props: { onNavigate: (tab: string) => void }) => <ResearchTab activeTab="risk" {...props} />;
export const PortfolioAllocator = (props: { onNavigate: (tab: string) => void }) => <ResearchTab activeTab="portfolio" {...props} />;
export const BacktestingLab = (props: { onNavigate: (tab: string) => void }) => <ResearchTab activeTab="backtest" {...props} />;
export const MacroView = (props: { onNavigate: (tab: string) => void }) => <ResearchTab activeTab="macro" {...props} />;
export const AIAnalyst = (props: { onNavigate: (tab: string) => void }) => <ResearchTab activeTab="analyst" {...props} />;
export const DataSettings = (props: { onNavigate: (tab: string) => void }) => <ResearchTab activeTab="settings" {...props} />;
