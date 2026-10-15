'use client';
import { Sparkline } from '@/components/ui/Sparkline';

// داده‌های Mock (در نهایت از API گرفته می‌شود)
const mockPrediction = {
  current: 2548230,
  predicted: 2605000,
  lowerBound: 2480000,
  upperBound: 2720000,
  confidence: 72,
  history: [
    /* ... */
  ],
  forecast: [
    /* ... */
  ],
};

export const PricePrediction = () => {
  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold">پیش‌بینی قیمت (LSTM + VAR)</h2>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 bg-surface border border-border rounded-2xl p-4">
          <h3 className="font-bold mb-3">نمودار قیمت و پیش‌بینی ۷ روزه</h3>
          {/* در اینجا از یک کتابخانه نمودار بزرگ (مثلاً ECharts) استفاده می‌کنیم */}
          <div className="h-64 bg-background rounded flex items-center justify-center text-text-secondary">
            نمودار اصلی (در فاز بعد)
          </div>
        </div>
        <div className="bg-surface border border-border rounded-2xl p-4 space-y-3">
          <h3 className="font-bold">جزئیات پیش‌بینی</h3>
          <div className="flex justify-between">
            <span>قیمت فعلی</span>
            <span className="font-bold">
              {mockPrediction.current.toLocaleString()}
            </span>
          </div>
          <div className="flex justify-between">
            <span>پیش‌بینی ۷ روز</span>
            <span className="font-bold text-green">
              {mockPrediction.predicted.toLocaleString()} (+۲.۲٪)
            </span>
          </div>
          <div className="flex justify-between">
            <span>حد پایین (CI 95%)</span>
            <span>{mockPrediction.lowerBound.toLocaleString()}</span>
          </div>
          <div className="flex justify-between">
            <span>حد بالا (CI 95%)</span>
            <span>{mockPrediction.upperBound.toLocaleString()}</span>
          </div>
          <div className="text-sm text-text-secondary">
            دقت مدل: {mockPrediction.confidence}٪
          </div>
        </div>
      </div>
    </div>
  );
};
