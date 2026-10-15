const events = [
  {
    time: "۱۴:۰۰",
    title: "نرخ تورم ماهانه",
    country: "ایران",
    importance: "high",
  },
  {
    time: "۱۶:۳۰",
    title: "اعلام نرخ بهره فدرال رزرو",
    country: "آمریکا",
    importance: "high",
  },
  {
    time: "۱۸:۰۰",
    title: "ذخایر نفت خام",
    country: "آمریکا",
    importance: "medium",
  },
  {
    time: "۲۰:۰۰",
    title: "سخنرانی رئیس بانک مرکزی اروپا",
    country: "اروپا",
    importance: "medium",
  },
];

export const EconomicCalendar = () => (
  <div className="bg-surface border border-border rounded-2xl p-4">
    <div className="flex items-center justify-between mb-4">
      <h3 className="text-lg font-semibold">📅 تقویم اقتصادی امروز</h3>
      {/* Disclaimer: news is context only, not an allocation input */}
      <span className="text-xs bg-background border border-border px-2 py-1 rounded text-text-secondary">
        توضیحی — تأثیری در تخصیص ندارد
      </span>
    </div>

    <div className="space-y-2">
      {events.map((e, i) => (
        <div
          key={i}
          className="flex items-center justify-between py-2 border-b border-border last:border-0"
        >
          <div className="flex items-center gap-3">
            <span className="text-xs text-text-secondary">{e.time}</span>
            <span className="font-medium text-sm">{e.title}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs bg-surface border border-border px-2 py-0.5 rounded">
              {e.country}
            </span>
            <span
              className={`w-2 h-2 rounded-full ${
                e.importance === "high" ? "bg-red" : "bg-yellow-500"
              }`}
            />
          </div>
        </div>
      ))}
    </div>

    {/* Footer note */}
    <p className="text-xs text-text-secondary mt-3 pt-3 border-t border-border">
      اخبار و رویدادهای اقتصادی صرفاً برای آگاهی نمایش داده می‌شوند. الگوریتم
      تخصیص پرتفوی بر پایه مومنتوم قیمتی است و از این اطلاعات استفاده نمی‌کند.
    </p>
  </div>
);
