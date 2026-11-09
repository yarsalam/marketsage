"use client";

export const InvestmentDecision = ({ onNavigate }: { onNavigate: (tab: string) => void }) => (
  <section className="m-6 space-y-4 rounded-2xl border border-border bg-surface p-6">
    <div>
      <p className="text-xs text-text-secondary">MarketSage · پژوهش، نه دستور سرمایه‌گذاری</p>
      <h2 className="mt-1 text-2xl font-bold">خروجی تصمیم سرمایه‌گذاری فعلاً غیرفعال است</h2>
    </div>
    <p className="text-sm leading-7 text-text-secondary">
      موتور فعلی فقط یک نمونهٔ محدود از پروکسی‌های جهانی دارد. هویت و قابلیت معاملهٔ ابزارهای ایرانی،
      مجوز و کیفیت منابع، پوشش تاریخی، هزینه‌ها و اعتبار روش شش‌ماهه هنوز کامل تأیید نشده‌اند.
      بنابراین این صفحه رتبه‌بندی، وزن پرتفوی یا مبلغ تخصیص‌یافته نمایش نمی‌دهد و هیچ درخواست محاسبهٔ
      تصمیم یا سرمایه‌ای به API ارسال نمی‌کند.
    </p>
    <div className="rounded-xl border border-border/70 p-4 text-sm">
      <strong>شرایط بازگشایی</strong>
      <ul className="mt-2 list-disc space-y-1 pr-5 text-text-secondary">
        <li>تأیید هویت و کیفیت داده برای هر بازار و ابزار به‌صورت مستقل</li>
        <li>پوشش تاریخی و بازپخش point-in-time بدون look-ahead</li>
        <li>اعتبارسنجی زمانی خارج از نمونه، هزینه‌ها، نقدشوندگی و ریسک</li>
        <li>تأیید صریح مالک پروژه برای فعال‌سازی خروجی‌های تصمیم</li>
      </ul>
    </div>
    <button
      type="button"
      onClick={() => onNavigate("coverage")}
      className="rounded-lg border border-border px-4 py-2 text-sm hover:bg-background"
    >
      مشاهده پوشش بازار و کیفیت منابع
    </button>
  </section>
);
