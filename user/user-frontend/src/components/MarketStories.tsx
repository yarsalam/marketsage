const stories = [
  {
    title: 'اگر برجام احیا شود؟',
    description: 'تحلیل اثر رفع تحریم‌ها بر صنایع بانکی و خودرویی',
    icon: '🕊️',
  },
  {
    title: 'نفت ۱۲۰ دلاری',
    description: 'سناریوی صعودی نفت و تأثیر بر پتروشیمی‌ها',
    icon: '🛢️',
  },
  {
    title: 'سقوط بیت‌کوین',
    description: 'اگر بازار رمزارزها وارد فاز اصلاحی شود',
    icon: '📉',
  },
  {
    title: 'جنگ تجاری جدید',
    description: 'تأثیر تعرفه‌های آمریکا و چین بر کامودیتی‌ها',
    icon: '🌍',
  },
];

export const MarketStories = ({ market }: { market: string }) => (
  <div className="bg-surface border border-border rounded-2xl p-4">
    <h3 className="text-lg font-semibold mb-4">📰 داستان‌های بازار</h3>
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      {stories.map((s, i) => (
        <div
          key={i}
          className="flex items-start gap-3 p-3 bg-background rounded-xl border border-border hover:border-primary cursor-pointer transition-colors"
        >
          <div className="text-2xl">{s.icon}</div>
          <div>
            <div className="font-bold text-sm">{s.title}</div>
            <div className="text-xs text-text-secondary mt-1">
              {s.description}
            </div>
          </div>
        </div>
      ))}
    </div>
  </div>
);
