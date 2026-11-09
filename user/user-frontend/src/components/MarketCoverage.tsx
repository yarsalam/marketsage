"use client";

import { useEffect, useMemo, useState } from "react";

type ScopeFilter = "all" | "iran" | "global";

type Source = {
  source_id: string;
  market_scope: string;
  asset_family: string;
  provider: string | null;
  status: string;
  used_by_research_engine: boolean;
  approved_for_production: boolean;
  data_kinds: string[];
  timestamp_quality: string;
  required_checks: string[];
  notes: string;
  scoring_gate?: {
    eligible_for_production_scoring: boolean;
    blocked_reasons: string[];
  };
};

type SourceCatalog = {
  registry_version: string;
  policy: string;
  summary: {
    total_sources: number;
    production_approved: number;
    research_wired: number;
    pending_or_unapproved: number;
  };
  sources: Source[];
};

type RuntimeSeries = {
  series_key: string;
  canonical_instrument_id?: string | null;
  identity_status?: string;
  data_kind?: string;
  expected_data_kind?: string | null;
  price_basis_status?: "consistent" | "legacy_mismatch" | "not_mapped";
  stored_versions: number;
  distinct_records: number;
  latest_observed_at: string | null;
  latest_retrieved_at: string | null;
  observed_age_days: number | null;
  freshness: "fresh" | "stale" | "unknown";
};

type RuntimeSource = Source & {
  runtime_status: string;
  runtime_series_count: number;
  runtime_series: RuntimeSeries[];
};

type DataQuality = {
  generated_at: string;
  registry_version: string;
  storage: {
    kind: string;
    store_exists: boolean;
    record_versions: number;
    series_count: number;
  };
  sources: RuntimeSource[];
  limitations: string[];
};

type IranProvider = {
  market: string;
  label: string;
  status: string;
  enabled_for_scoring: boolean;
  source: string | null;
  notes: string;
  candidate_endpoints: string[];
};

type IranProviderCatalog = {
  policy: string;
  markets: IranProvider[];
};

type Instrument = {
  instrument_id: string;
  display_name: string;
  market_universe: string;
  asset_family: string;
  instrument_type: string;
  research_role: string;
  source_id: string;
  provider_symbol: string;
  quote_currency: string;
  quote_unit: string;
  price_basis: string;
  venue: string | null;
  identity_status: string;
  tradability_status: string;
  production_approved: boolean;
  scoring_gate: { eligible: boolean; blocked_reasons: string[] };
};

type InstrumentCatalog = {
  registry_version: string;
  policy: string;
  summary: {
    instrument_count: number;
    global_proxy_count: number;
    production_approved_count: number;
    iran_instrument_count: number;
    quarantined_iran_universes: number;
  };
  instruments: Instrument[];
  empty_universes: Array<{ market_universe: string; status: string; reason: string }>;
};

type CoveragePayload = {
  catalog: SourceCatalog;
  quality: DataQuality;
  iran: IranProviderCatalog;
  instruments: InstrumentCatalog;
};

const API_BASE = (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/$/, "");

const statusLabels: Record<string, string> = {
  research_only_existing: "نمونه پژوهشی موجود",
  adapter_implemented_not_scheduled: "آداپتور موجود؛ زمان‌بندی نشده",
  candidate_requires_validation: "نامزد؛ نیازمند اعتبارسنجی",
  provider_not_selected: "ارائه‌دهنده انتخاب نشده",
  discovery_only_not_verified: "فقط کشف؛ تأییدنشده",
  production_approved: "تأییدشده برای تولید",
  data_present: "داده در مخزن ثبت شده",
  no_data_captured: "هنوز داده‌ای ثبت نشده",
  fresh: "تازه بر اساس قاعده فعلی",
  stale: "قدیمی بر اساس قاعده فعلی",
  unknown: "تازگی نامشخص",
};

function label(value: string | null | undefined) {
  if (!value) return "مشخص نشده";
  return statusLabels[value] ?? value.replaceAll("_", " ");
}

function scopeLabel(value: string) {
  if (value.includes("iran") && value.includes("global")) return "ایران و جهانی";
  if (value.includes("iran")) return "ایران";
  if (value.includes("global")) return "جهانی";
  return value;
}

function matchesScope(value: string, selected: ScopeFilter) {
  return selected === "all" || value.toLowerCase().includes(selected);
}

function formatDate(value: string | null | undefined) {
  if (!value) return "نامشخص";
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime())
    ? value
    : parsed.toLocaleString("fa-IR", { dateStyle: "medium", timeStyle: "short" });
}

function SummaryCard({ title, value, detail }: { title: string; value: string | number; detail: string }) {
  return (
    <article className="rounded-2xl border border-border bg-surface p-4">
      <p className="text-xs text-text-secondary">{title}</p>
      <p className="mt-2 text-2xl font-bold tabular-nums">{value}</p>
      <p className="mt-1 text-xs text-text-secondary">{detail}</p>
    </article>
  );
}

function SourceCard({ source, runtime }: { source: Source; runtime?: RuntimeSource }) {
  const gate = source.scoring_gate;
  const series = runtime?.runtime_series ?? [];
  const freshCount = series.filter((item) => item.freshness === "fresh").length;
  const staleCount = series.filter((item) => item.freshness === "stale").length;

  return (
    <article className="space-y-4 rounded-2xl border border-border bg-surface p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="font-bold">{source.provider ?? "ارائه‌دهنده انتخاب نشده"}</h3>
          <p className="mt-1 break-all text-xs text-text-secondary" dir="ltr">{source.source_id}</p>
        </div>
        <span className="rounded-full border border-border px-3 py-1 text-xs">
          {label(source.status)}
        </span>
      </div>

      <div className="grid gap-3 text-sm sm:grid-cols-2">
        <div>
          <p className="text-xs text-text-secondary">بازار</p>
          <p className="mt-1">{scopeLabel(source.market_scope)}</p>
        </div>
        <div>
          <p className="text-xs text-text-secondary">خانواده دارایی</p>
          <p className="mt-1">{source.asset_family.replaceAll("_", " ")}</p>
        </div>
        <div>
          <p className="text-xs text-text-secondary">اتصال به موتور پژوهش</p>
          <p className="mt-1">{source.used_by_research_engine ? "متصل است" : "متصل نیست"}</p>
        </div>
        <div>
          <p className="text-xs text-text-secondary">مجوز استفاده در تولید</p>
          <p className="mt-1 font-semibold">{source.approved_for_production ? "تأیید شده" : "تأیید نشده"}</p>
        </div>
        <div className="sm:col-span-2">
          <p className="text-xs text-text-secondary">کیفیت زمان انتشار</p>
          <p className="mt-1">{source.timestamp_quality}</p>
        </div>
      </div>

      <div className="rounded-xl border border-border/70 p-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <strong className="text-sm">وضعیت دادهٔ ثبت‌شده</strong>
          <span className="text-xs text-text-secondary">
            {label(runtime?.runtime_status ?? "unknown")}
          </span>
        </div>
        <p className="mt-2 text-sm text-text-secondary">
          {runtime
            ? `تعداد سری‌ها: ${runtime.runtime_series_count} · نسخه‌های رکورد: ${series.reduce((sum, item) => sum + item.stored_versions, 0)}`
            : "گزارش کیفیت برای این منبع در دسترس نیست."}
        </p>
        {series.length > 0 && (
          <p className="mt-1 text-xs text-text-secondary">
            تازگی ثبت‌شده: {freshCount} تازه، {staleCount} قدیمی، {series.length - freshCount - staleCount} نامشخص · ناسازگاری مبنای قیمت: {series.filter((item) => item.price_basis_status === "legacy_mismatch").length}
          </p>
        )}
        {series.length > 0 && (
          <div className="mt-3 space-y-2">
            {series.slice(0, 4).map((item) => (
              <div key={`${item.series_key}:${item.data_kind ?? "unknown"}`} className="flex flex-wrap items-center justify-between gap-2 border-t border-border/60 pt-2 text-xs">
                <span className="flex flex-col" dir="ltr">
                  <span>{item.series_key}</span>
                  {item.canonical_instrument_id && (
                    <span className="mt-1 text-[10px] text-text-secondary">{item.canonical_instrument_id}</span>
                  )}
                </span>
                <span className="flex flex-col items-end gap-1 text-text-secondary">
                  <span>{label(item.freshness)} · {item.distinct_records.toLocaleString("fa-IR")} رکورد · آخرین مشاهده: {formatDate(item.latest_observed_at)}</span>
                  <span>{label(item.price_basis_status ?? "not_mapped")}</span>
                  {item.price_basis_status === "legacy_mismatch" && (
                    <span dir="ltr">stored: {item.data_kind} · expected: {item.expected_data_kind}</span>
                  )}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div>
        <p className="text-xs text-text-secondary">انواع داده</p>
        <div className="mt-2 flex flex-wrap gap-2">
          {source.data_kinds.map((kind) => (
            <span key={kind} className="rounded-lg bg-background px-2 py-1 text-xs">{kind.replaceAll("_", " ")}</span>
          ))}
        </div>
      </div>

      <div>
        <p className="text-xs text-text-secondary">مدارک و کنترل‌های لازم</p>
        <ul className="mt-2 list-disc space-y-1 pr-5 text-xs text-text-secondary">
          {source.required_checks.map((check) => <li key={check}>{check.replaceAll("_", " ")}</li>)}
        </ul>
      </div>

      {gate && gate.blocked_reasons.length > 0 && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-3">
          <p className="text-xs font-semibold">دلایل مسدود بودن استفاده در امتیازدهی تولیدی</p>
          <ul className="mt-2 list-disc space-y-1 pr-5 text-xs text-text-secondary">
            {gate.blocked_reasons.map((reason) => <li key={reason}>{reason.replaceAll("_", " ")}</li>)}
          </ul>
        </div>
      )}

      <p className="text-xs leading-6 text-text-secondary">{source.notes}</p>
    </article>
  );
}

export function MarketCoverage({ onNavigate }: { onNavigate: (tab: string) => void }) {
  const [payload, setPayload] = useState<CoveragePayload | null>(null);
  const [scope, setScope] = useState<ScopeFilter>("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);

    const load = async () => {
      const [catalogResponse, qualityResponse, iranResponse, instrumentsResponse] = await Promise.all([
        fetch(`${API_BASE}/api/markets/sources`, { cache: "no-store", credentials: "include", signal: controller.signal }),
        fetch(`${API_BASE}/api/markets/data-quality`, { cache: "no-store", credentials: "include", signal: controller.signal }),
        fetch(`${API_BASE}/api/markets/iran-providers`, { cache: "no-store", credentials: "include", signal: controller.signal }),
        fetch(`${API_BASE}/api/markets/instruments`, { cache: "no-store", credentials: "include", signal: controller.signal }),
      ]);
      const responses = [catalogResponse, qualityResponse, iranResponse, instrumentsResponse];
      const failed = responses.find((response) => !response.ok);
      if (failed) throw new Error(`دریافت پوشش داده ناموفق بود (HTTP ${failed.status}).`);
      const [catalog, quality, iran, instruments] = await Promise.all(
        responses.map((response) => response.json()),
      );
      setPayload({ catalog, quality, iran, instruments });
    };

    load()
      .catch((cause: unknown) => {
        if (cause instanceof Error && cause.name === "AbortError") return;
        setError(cause instanceof Error ? cause.message : "دریافت وضعیت منابع ناموفق بود.");
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [refreshToken]);

  const runtimeBySource = useMemo(
    () => new Map((payload?.quality.sources ?? []).map((source) => [source.source_id, source])),
    [payload],
  );
  const filteredSources = useMemo(
    () => (payload?.catalog.sources ?? []).filter((source) => matchesScope(source.market_scope, scope)),
    [payload, scope],
  );
  const filteredIranProviders = useMemo(
    () => (payload?.iran.markets ?? []).filter((provider) =>
      scope === "all" ||
      (scope === "iran" && provider.market !== "crypto_global") ||
      (scope === "global" && provider.market === "crypto_global")
    ),
    [payload, scope],
  );

  if (loading) {
    return <section className="space-y-4 p-6"><h1 className="text-2xl font-bold">پوشش بازار و کیفیت داده</h1><p className="animate-pulse text-text-secondary">در حال دریافت رجیستری منابع و وضعیت مخزن...</p></section>;
  }

  if (error || !payload) {
    return (
      <section className="m-6 space-y-3 rounded-2xl border border-border bg-surface p-6" role="alert">
        <h1 className="text-2xl font-bold">پوشش بازار در دسترس نیست</h1>
        <p className="text-sm text-text-secondary">{error ?? "پاسخ معتبری از سرویس دریافت نشد."}</p>
        <p className="text-xs text-text-secondary">برای جلوگیری از نمایش دادهٔ ساختگی، از اطلاعات نمونه استفاده نشده است.</p>
        <div className="flex flex-wrap gap-4">
          <button
            type="button"
            className="text-sm text-primary underline disabled:opacity-50"
            onClick={() => setRefreshToken((current) => current + 1)}
            disabled={loading}
          >
            تلاش مجدد
          </button>
          <button
            type="button"
            className="text-sm text-primary underline"
            onClick={() => onNavigate("settings")}
          >
            مشاهده وضعیت خام سرویس
          </button>
        </div>
      </section>
    );
  }

  const summary = payload.catalog.summary;
  return (
    <section className="space-y-6 p-4 md:p-6">
      <header className="space-y-2">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="text-xs text-text-secondary">MarketSage · لایه شفافیت داده</p>
            <h1 className="mt-1 text-2xl font-bold md:text-3xl">پوشش بازار و کیفیت داده</h1>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <p className="text-xs text-text-secondary">آخرین ارزیابی: {formatDate(payload.quality.generated_at)}</p>
            <button
              type="button"
              onClick={() => setRefreshToken((current) => current + 1)}
              disabled={loading}
              className="rounded-lg border border-border px-3 py-2 text-xs disabled:opacity-50"
            >
              {loading ? "در حال به‌روزرسانی..." : "به‌روزرسانی وضعیت"}
            </button>
          </div>
        </div>
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-4 text-sm leading-7">
          {payload.catalog.policy}
          <p className="mt-1 text-xs text-text-secondary">ثبت‌شدن منبع یا وجود داده در مخزن، به معنی مجوز استفاده در تحلیل سرمایه‌گذاری یا تأیید دقت آن نیست.</p>
        </div>
      </header>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <SummaryCard title="منابع ثبت‌شده" value={summary.total_sources} detail={`نسخه رجیستری ${payload.catalog.registry_version}`} />
        <SummaryCard title="متصل به پژوهش" value={summary.research_wired} detail="اتصال فنی؛ نه تأیید حقوقی یا کیفیت" />
        <SummaryCard title="تأییدشده برای تولید" value={summary.production_approved} detail="فقط تأیید صریح رجیستری" />
        <SummaryCard title="نسخه رکوردهای ذخیره‌شده" value={payload.quality.storage.record_versions.toLocaleString("fa-IR")} detail={`تعداد سری‌ها: ${payload.quality.storage.series_count}`} />
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <span className="ml-2 text-sm text-text-secondary">نمایش بازار:</span>
        {([
          ["all", "همه"],
          ["iran", "ایران"],
          ["global", "جهانی"],
        ] as const).map(([value, title]) => (
          <button
            key={value}
            type="button"
            onClick={() => setScope(value)}
            aria-pressed={scope === value}
            className={`rounded-xl border px-4 py-2 text-sm transition-colors ${scope === value ? "border-primary bg-primary/15 text-primary" : "border-border text-text-secondary hover:bg-surface"}`}
          >
            {title}
          </button>
        ))}
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        {filteredSources.map((source) => (
          <SourceCard key={source.source_id} source={source} runtime={runtimeBySource.get(source.source_id)} />
        ))}
      </div>

      {filteredSources.length === 0 && (
        <div className="rounded-xl border border-border bg-surface p-4 text-sm text-text-secondary">برای این فیلتر منبعی در رجیستری ثبت نشده است.</div>
      )}

      {(scope === "all" || scope === "iran") && (
        <section className="space-y-4">
          <div>
            <h2 className="text-xl font-bold">آمادگی ارائه‌دهندگان بازار ایران</h2>
            <p className="mt-1 text-xs text-text-secondary">این فهرست کاتالوگ نامزدهاست؛ هیچ ردیف آن به‌تنهایی مجوز دریافت یا امتیازدهی ایجاد نمی‌کند.</p>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            {filteredIranProviders.map((provider) => (
              <article key={provider.market} className="space-y-2 rounded-2xl border border-border bg-surface p-4">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <strong>{provider.label}</strong>
                  <span className="rounded-full border border-border px-2 py-1 text-xs">{label(provider.status)}</span>
                </div>
                <p className="text-xs text-text-secondary">{provider.source ?? "ارائه‌دهنده انتخاب نشده"}</p>
                <p className="text-sm leading-6 text-text-secondary">{provider.notes}</p>
                <p className="text-xs">فعال برای امتیازدهی: {provider.enabled_for_scoring ? "بله" : "خیر"}</p>
              </article>
            ))}
          </div>
        </section>
      )}

      {scope !== "iran" && (
      <section className="space-y-4">
        <div>
          <h2 className="text-xl font-bold">رجیستری هویت ابزارها</h2>
          <p className="mt-1 text-xs leading-6 text-text-secondary">
            شناسه داخلی هر ابزار از نماد ارائه‌دهنده جداست. موارد زیر فقط ابزارهای پروکسی پژوهشی موجودند؛
            این فهرست نه تأیید قابلیت معامله است و نه مجوز استفاده تولیدی.
          </p>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <SummaryCard title="ابزارهای ثبت‌شده" value={payload.instruments.summary.instrument_count} detail={`نسخه رجیستری ${payload.instruments.registry_version}`} />
          <SummaryCard title="پروکسی‌های جهانی" value={payload.instruments.summary.global_proxy_count} detail="برای پژوهش؛ نه دارایی تأییدشده در ایران" />
          <SummaryCard title="ابزار تأییدشده تولیدی" value={payload.instruments.summary.production_approved_count} detail="فقط با تأیید صریح" />
          <SummaryCard title="ابزارهای ایران" value={payload.instruments.summary.iran_instrument_count} detail={`${payload.instruments.summary.quarantined_iran_universes} خانواده بازار قرنطینه`} />
        </div>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {payload.instruments.instruments.map((instrument) => (
            <article key={instrument.instrument_id} className="space-y-2 rounded-2xl border border-border bg-surface p-4">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <strong>{instrument.display_name}</strong>
                <span className="rounded-full border border-border px-2 py-1 text-xs">پروکسی پژوهشی</span>
              </div>
              <p className="break-all text-xs text-text-secondary" dir="ltr">{instrument.instrument_id}</p>
              <p className="text-sm" dir="ltr">{instrument.provider_symbol}</p>
              <dl className="grid grid-cols-2 gap-2 text-xs">
                <div><dt className="text-text-secondary">خانواده دارایی</dt><dd className="mt-1">{instrument.asset_family.replaceAll("_", " ")}</dd></div>
                <div><dt className="text-text-secondary">واحد مظنه</dt><dd className="mt-1" dir="ltr">{instrument.quote_currency} · {instrument.quote_unit}</dd></div>
                <div><dt className="text-text-secondary">مبنای قیمت</dt><dd className="mt-1">{instrument.price_basis.replaceAll("_", " ")}</dd></div>
                <div><dt className="text-text-secondary">بازار/محل معامله</dt><dd className="mt-1">{instrument.venue ?? "نامشخص"}</dd></div>
              </dl>
              <p className="text-xs text-text-secondary">قابلیت معامله: ارزیابی نشده · مجوز تولید: ندارد</p>
              {instrument.scoring_gate.blocked_reasons.length > 0 && (
                <p className="text-xs text-text-secondary">محدودیت: {instrument.scoring_gate.blocked_reasons.join("، ")}</p>
              )}
            </article>
          ))}
        </div>
      </section>
      )}

      {(scope === "all" || scope === "iran") && (
        <section className="space-y-3 rounded-2xl border border-border bg-surface p-4">
          <div>
            <h2 className="font-semibold">خانواده‌های بازار ایران — بدون ابزار پذیرفته‌شده</h2>
            <p className="mt-1 text-xs text-text-secondary">تا زمان تأیید هویت، منبع، واحد و شواهد مستقل، این خانواده‌ها وارد رجیستری ابزارهای قابل استفاده نمی‌شوند.</p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {payload.instruments.empty_universes.map((universe) => (
              <div key={universe.market_universe} className="rounded-xl border border-border/70 p-3">
                <p className="text-sm font-medium">{universe.market_universe.replaceAll("_", " ")}</p>
                <p className="mt-1 text-xs text-text-secondary">{universe.reason}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="rounded-2xl border border-border bg-surface p-4">
        <h2 className="font-bold">محدودیت‌های گزارش کیفیت</h2>
        <ul className="mt-2 list-disc space-y-1 pr-5 text-xs leading-6 text-text-secondary">
          {payload.quality.limitations.map((item) => <li key={item}>{item}</li>)}
        </ul>
      </section>
    </section>
  );
}
