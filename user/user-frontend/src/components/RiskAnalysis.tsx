/* ── Types ── */
interface RiskMetrics {
  var95Weekly: number; // weekly VaR at 95% confidence
  maxDrawdown: number; // historical max drawdown
  sharpe: number;
  beta: number;
}

/* ── Data (replace with API call when backend is ready) ── */
const riskMetrics: RiskMetrics = {
  var95Weekly: 3.2,
  maxDrawdown: 5.1,
  sharpe: 1.4,
  beta: 0.85,
};

/* ── Sub-components ── */
function MetricCard({
  title,
  value,
  valueColorClass = "text-text",
  explanation,
}: {
  title: string;
  value: string;
  valueColorClass?: string;
  explanation: string;
}) {
  return (
    <div className="bg-surface border border-border rounded-2xl p-5 flex flex-col gap-2">
      <span className="text-xs text-text-secondary">{title}</span>
      <span className={`text-2xl font-bold ${valueColorClass}`}>{value}</span>
      <p className="text-sm text-text-secondary leading-relaxed">
        {explanation}
      </p>
    </div>
  );
}

function ScenarioRow({
  label,
  probability,
  range,
  colorClass,
}: {
  label: string;
  probability: string;
  range: string;
  colorClass: string;
}) {
  return (
    <div className="flex justify-between items-center py-3">
      <div>
        <span className="text-sm font-medium">{label}</span>
        <span className="text-xs text-text-secondary mr-2">
          (احتمال: {probability})
        </span>
      </div>
      <span className={`text-sm font-bold ${colorClass}`}>{range}</span>
    </div>
  );
}

/* ── Main component ── */
export const RiskAnalysis = ({
  onNavigate,
}: {
  onNavigate?: (tab: string) => void;
}) => {
  const { var95Weekly, maxDrawdown, sharpe, beta } = riskMetrics;

  return (
    <div className="space-y-6 p-6">
      <h2 className="text-xl font-bold">🛡️ تحلیل ریسک پرتفوی</h2>

      {/* ── Human-readable metric cards ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <MetricCard
          title="ارزش در معرض ریسک (VaR 95٪)"
          value={`${var95Weekly}٪`}
          valueColorClass="text-yellow-400"
          explanation={`در شرایط نرمال، ۹۵٪ مواقع زیان هفتگی پرتفوی بیشتر از ${var95Weekly}٪ نخواهد بود.`}
        />

        <MetricCard
          title="بیشترین افت تاریخی (Max Drawdown)"
          value={`${maxDrawdown}٪−`}
          valueColorClass="text-red"
          explanation={`در بدترین دوره ثبت‌شده، ارزش پرتفوی حداکثر ${maxDrawdown}٪ کاهش یافته است.`}
        />

        <MetricCard
          title="نسبت Sharpe (بازده به‌ازای ریسک)"
          value={String(sharpe)}
          valueColorClass={sharpe >= 1 ? "text-green" : "text-yellow-400"}
          explanation={`به ازای هر واحد ریسک، ${sharpe} واحد بازده اضافی تولید شده.${
            sharpe >= 1 ? " (مطلوب)" : " (نیاز به بهبود)"
          }`}
        />

        <MetricCard
          title="بتا (حساسیت به بازار)"
          value={String(beta)}
          explanation={`اگر بازار ۱٪ تغییر کند، پرتفوی شما حدود ${beta}٪ تغییر می‌کند.${
            beta < 1 ? " (محافظه‌کارانه)" : " (تهاجمی)"
          }`}
        />
      </div>

      {/* ── Scenario analysis ── */}
      <div className="bg-surface border border-border rounded-2xl p-4">
        <h3 className="font-bold mb-4">📊 تحلیل سناریو ماهانه</h3>
        <div className="divide-y divide-border">
          <ScenarioRow
            label="سناریو نرمال"
            probability="۷۰٪"
            range="۰ تا +۵٪"
            colorClass="text-green"
          />
          <ScenarioRow
            label="سناریو نزولی"
            probability="۲۰٪"
            range={`−${var95Weekly}٪ تا ۰`}
            colorClass="text-yellow-400"
          />
          <ScenarioRow
            label="سناریو بحرانی"
            probability="۱۰٪"
            range={`بیش از −${maxDrawdown}٪`}
            colorClass="text-red"
          />
        </div>

        {/* ── Honest disclaimer — no unsupported macro claims ── */}
        <p className="text-xs text-text-secondary mt-3 pt-3 border-t border-border">
          * این سناریوها از داده‌های تاریخی مومنتوم استخراج شده‌اند. عوامل
          ژئوپلیتیک، GPR و کلان اقتصادی در مدل فعلی لحاظ نشده‌اند و تأثیری در
          این اعداد ندارند.
        </p>
      </div>
    </div>
  );
};
