import { Sparkline } from "./ui/Sparkline";

const reasons: Record<
  string,
  { reason: string; chartData: { time: string; value: number }[] }
> = {
  bourse: {
    reason:
      'رشد ۲٪ شاخص کل عمدتاً به دلیل افزایش قیمت جهانی نفت و گزارش مثبت پتروشیمی‌ها بود. همچنین ورود نقدینگی جدید از صندوق‌های ETF حمایت کرد.',
    chartData: [
      { time: '2024-01-01', value: 100 },
      { time: '2024-01-02', value: 102 },
      { time: '2024-01-03', value: 101 },
      { time: '2024-01-04', value: 104 },
      { time: '2024-01-05', value: 102 },
    ],
  },
  gold: {
    reason:
      'افزایش ۱.۵٪ قیمت طلا ناشی از تنش‌های ژئوپلیتیک جدید و کاهش ارزش دلار آمریکا بود. سرمایه‌گذاران به سمت دارایی‌های امن حرکت کردند.',
    chartData: [
      { time: '2024-01-01', value: 1900 },
      { time: '2024-01-02', value: 1925 },
      { time: '2024-01-03', value: 1910 },
      { time: '2024-01-04', value: 1935 },
      { time: '2024-01-05', value: 1930 },
    ],
  },
  crypto: {
    reason:
      'بیت‌کوین با رشد ۴٪ به دلیل تایید ETFهای جدید و افزایش پذیرش نهادی روبه‌رو شد. حجم معاملات ۳۰٪ افزایش یافت.',
    chartData: [
      { time: '2024-01-01', value: 64000 },
      { time: '2024-01-02', value: 66500 },
      { time: '2024-01-03', value: 65800 },
      { time: '2024-01-04', value: 68200 },
      { time: '2024-01-05', value: 67200 },
    ],
  },
  oil: {
    reason:
      'کاهش ۱.۱٪ قیمت نفت به دلیل افزایش ذخایر نفت خام آمریکا و کاهش نگرانی‌های عرضه در خاورمیانه بود.',
    chartData: [
      { time: '2024-01-01', value: 86 },
      { time: '2024-01-02', value: 85 },
      { time: '2024-01-03', value: 84.5 },
      { time: '2024-01-04', value: 85.4 },
      { time: '2024-01-05', value: 85.0 },
    ],
  },
  forex: {
    reason:
      'دلار آمریکا در برابر یورو ۰.۳٪ تضعیف شد، زیرا آمار اشتغال کمتر از حد انتظار بود و احتمال کاهش نرخ بهره افزایش یافت.',
    chartData: [
      { time: '2024-01-01', value: 1.08 },
      { time: '2024-01-02', value: 1.082 },
      { time: '2024-01-03', value: 1.079 },
      { time: '2024-01-04', value: 1.083 },
      { time: '2024-01-05', value: 1.085 },
    ],
  },
};

export const WhyToday = ({ market }: { market: string }) => {
  const data = reasons[market] || reasons.bourse;
  return (
    <div className="bg-surface border border-border rounded-2xl p-4">
      <h3 className="text-lg font-semibold mb-3">چرا امروز؟</h3>
      <p className="text-text-secondary mb-4 leading-relaxed">{data.reason}</p>
      <div className="h-20 w-full">
        <Sparkline data={data.chartData} color="#3B82F6" height={80} />
      </div>
    </div>
  );
};
