export const SentimentAnalysis = () => (
  <div className="space-y-4">
    <h2 className="text-xl font-bold">تحلیل احساسات بازار</h2>
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div className="bg-surface border border-border rounded-2xl p-4 text-center">
        <div className="text-4xl mb-2">😐</div>
        <div className="text-3xl font-bold text-yellow-400">۵۸</div>
        <div className="text-sm text-text-secondary">شاخص ترس و طمع</div>
      </div>
      <div className="bg-surface border border-border rounded-2xl p-4">
        <h3 className="font-bold mb-3">توزیع احساسات</h3>
        <div className="space-y-2">
          <div className="flex justify-between">
            <span>🟢 مثبت</span>
            <span>۶۲٪</span>
          </div>
          <div className="h-2 bg-border rounded-full">
            <div
              className="h-full bg-green rounded-full"
              style={{ width: '62%' }}
            />
          </div>
          {/* ... */}
        </div>
      </div>
      <div className="bg-surface border border-border rounded-2xl p-4">
        <h3 className="font-bold mb-3">منابع تحلیل</h3>
        <div className="text-xs space-y-1">
          <div>Contify News: ۱۲۴ مقاله</div>
          <div>Apify Sentiment Score: ۰.۶۵</div>
          <div>Permutable AI: ۸ شاخص کلان</div>
        </div>
      </div>
    </div>
  </div>
);
