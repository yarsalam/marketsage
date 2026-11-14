"use client";

const event = {
  symbol: "وغدیر",
  fiscalYear: "منتهی به ۱۴۰۴/۰۹/۳۰",
  meetingDate: "۱۴۰۴/۱۲/۱۰",
  dividendPerShare: "۱٬۵۰۰ ریال",
  referenceDate: "2026-04-18",
  priceBefore: "۱۵٬۰۷۰ ریال",
  priceAfter: "۱۳٬۵۷۰ ریال",
  dividendDifference: "۱٬۵۰۰ ریال",
  factor: "0.900464499004645",
  firstObservedTradingSession: "2026-06-09",
  firstSessionClose: "۱۵٬۴۶۰ ریال",
  juneSignal: "۱۱٫۰۵۲۸٪",
} as const;

function EvidenceRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1 border-t border-border/60 py-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
      <dt className="text-xs text-text-secondary">{label}</dt>
      <dd className="text-sm font-medium sm:text-left" dir="auto">{value}</dd>
    </div>
  );
}

export function CorporateActionEvidence() {
  return (
    <section className="space-y-4 rounded-2xl border border-border bg-surface p-4 md:p-5" dir="rtl">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs text-text-secondary">دفتر شواهد · بازار سهام ایران</p>
          <h2 className="mt-1 text-xl font-bold">رویداد شرکتی تأییدشده: سود نقدی وغدیر</h2>
          <p className="mt-1 text-xs text-text-secondary">
            {event.fiscalYear} · جلسه مجمع: {event.meetingDate}
          </p>
        </div>
        <span className="rounded-full border border-emerald-500/40 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-700">
          تأیید در سطح رویداد
        </span>
      </header>

      <div className="grid gap-3 sm:grid-cols-3">
        <article className="rounded-xl border border-border/70 p-3">
          <p className="text-xs text-text-secondary">سود نقدی مصوب هر سهم</p>
          <p className="mt-2 text-xl font-bold tabular-nums">{event.dividendPerShare}</p>
          <p className="mt-1 text-xs text-text-secondary">مصوبه مجمع عمومی عادی سالیانه</p>
        </article>
        <article className="rounded-xl border border-border/70 p-3">
          <p className="text-xs text-text-secondary">تغییر قیمت مرجع TSETMC</p>
          <p className="mt-2 text-xl font-bold tabular-nums">{event.dividendDifference}</p>
          <p className="mt-1 text-xs text-text-secondary">۱۵٬۰۷۰ ← ۱۳٬۵۷۰ ریال</p>
        </article>
        <article className="rounded-xl border border-border/70 p-3">
          <p className="text-xs text-text-secondary">ضریب قیمت بازسازی‌شده</p>
          <p className="mt-2 break-all text-lg font-bold tabular-nums" dir="ltr">{event.factor}</p>
          <p className="mt-1 text-xs text-text-secondary">ضریب رویداد؛ هنوز روی سری تاریخی اعمال نشده</p>
        </article>
      </div>

      <dl>
        <EvidenceRow label="تاریخ رکورد Price Adjust در TSETMC" value={event.referenceDate} />
        <EvidenceRow label="قیمت مرجع پیش از رویداد" value={event.priceBefore} />
        <EvidenceRow label="قیمت مرجع پس از رویداد" value={event.priceAfter} />
        <EvidenceRow label="اولین جلسه دارای معامله پس از توقف طولانی بازار در داده موجود" value={event.firstObservedTradingSession} />
        <EvidenceRow label="قیمت پایانی آن جلسه" value={event.firstSessionClose} />
      </dl>

      <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-3">
        <p className="text-sm font-semibold">مواردی که هنوز تأیید نشده‌اند</p>
        <ul className="mt-2 list-disc space-y-1 pr-5 text-xs leading-6 text-text-secondary">
          <li>تاریخ دقیق اثر معاملاتی/Ex-date از تاریخ ثبت رکورد TSETMC به‌تنهایی استنتاج نمی‌شود.</li>
          <li>سیگنال {event.juneSignal} در ۱۰ ژوئن ۲۰۲۶ هنوز به‌طور دقیق به این رویداد منتسب نشده و رویداد شرکتی مستقل هم محسوب نمی‌شود.</li>
          <li>تأیید این رویداد به معنی پذیرش کل تاریخچه تعدیل‌شده وغدیر یا کل منبع TSETMC نیست.</li>
        </ul>
      </div>

      <div className="rounded-xl border border-border/70 p-3 text-xs leading-6">
        <p className="font-semibold">حکم استفاده در MarketSage</p>
        <p className="mt-1 text-text-secondary">
          قابل ثبت و استفاده به‌عنوان شواهد رویداد شرکتی در پژوهش. ضریب فقط یک عامل قیمتِ مبتنی بر سود نقدی است؛
          نه ضریب بازده کل. این رکورد به‌تنهایی سری تعدیل‌شده را تأیید نمی‌کند و مجوز ورود به امتیازدهی یا تولید را نمی‌دهد.
        </p>
        <p className="mt-2 font-semibold text-amber-700">وضعیت اعمال: اعمال‌نشده · امتیازدهی: مسدود</p>
      </div>

      <p className="text-[11px] leading-5 text-text-secondary">
        منشأ شواهد: متن تصمیمات مجمع ارسالی مالک پروژه؛ رکورد خام TSETMC شامل dEven=20260418،
        pClosingNotAdjusted=15070 و pClosing=13570؛ داده روزانه معاملاتی TSETMC برای 2026-06-09.
        این کارت دفتر شواهد بازبینی‌شده است و به‌روزرسانی زنده از API انجام نمی‌دهد.
      </p>
    </section>
  );
}
