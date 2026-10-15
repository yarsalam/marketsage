"use client";
import { useEffect, useState } from "react";

/* ── Types ── */
interface AssetRanking {
  momentumRank: number;
  sharpeRank: number;
  volatilityRank: number;
  momentum4M: string;
  sharpe12M: string;
  volatilityMonthly: string;
}

interface Allocation {
  asset: string;
  weight: number;
  ranking?: AssetRanking;
}

interface DecisionResponse {
  horizon: string;
  allocation: Allocation[];
  capital_allocated: Record<string, number>;
  confidence: number;
  total_assets_analyzed?: number;
}

/* ── Mock rankings (until backend provides ranking data) ── */
const MOCK_RANKINGS: Record<string, AssetRanking> = {
  "Dollar Bullish": {
    momentumRank: 1,
    sharpeRank: 2,
    volatilityRank: 1,
    momentum4M: "+۶.۲٪",
    sharpe12M: "۱.۱۸",
    volatilityMonthly: "۴.۵٪",
  },
  "Nasdaq ETF": {
    momentumRank: 2,
    sharpeRank: 3,
    volatilityRank: 4,
    momentum4M: "+۵.۱٪",
    sharpe12M: "۱.۰۵",
    volatilityMonthly: "۸.۲٪",
  },
  "S&P500 ETF": {
    momentumRank: 3,
    sharpeRank: 4,
    volatilityRank: 3,
    momentum4M: "+۴.۳٪",
    sharpe12M: "۰.۹۸",
    volatilityMonthly: "۷.۱٪",
  },
};

/* ── Helpers ── */
function toConfidenceLabel(raw: number): { label: string; colorClass: string } {
  if (raw >= 75) return { label: "بالا", colorClass: "text-green" };
  if (raw >= 50) return { label: "متوسط", colorClass: "text-yellow-400" };
  return { label: "پایین", colorClass: "text-red" };
}

function RankRow({ label, rank }: { label: string; rank: number }) {
  const colorClass =
    rank === 1
      ? "text-green"
      : rank <= 3
      ? "text-primary"
      : "text-text-secondary";
  return (
    <div className="flex justify-between items-center text-xs">
      <span className="text-text-secondary">{label}</span>
      <span className={`font-bold ${colorClass}`}>رتبه #{rank}</span>
    </div>
  );
}

function NumericRow({
  label,
  value,
  valueClass = "text-text",
}: {
  label: string;
  value: string;
  valueClass?: string;
}) {
  return (
    <div className="flex justify-between items-center text-xs">
      <span className="text-text-secondary">{label}</span>
      <span className={`font-bold ${valueClass}`}>{value}</span>
    </div>
  );
}

/* ── Component ── */
export const InvestmentDecision = ({
  onNavigate,
}: {
  onNavigate: (tab: string) => void;
}) => {
  const [decision, setDecision] = useState<DecisionResponse | null>(null);
  const [expandedAsset, setExpandedAsset] = useState<string | null>(null);

  useEffect(() => {
    fetch("http://localhost:4500/api/decision?horizon=1M")
      .then((res) => res.json())
      .then((data: DecisionResponse) => {
        // Cap raw confidence to a realistic ceiling — the model uses only
        // price momentum, so values above ~72 are not yet justified.
        setDecision({ ...data, confidence: Math.min(data.confidence, 72) });
      })
      .catch(() => {
        // Fallback for local development when Python engine is offline
        setDecision({
          horizon: "1M",
          allocation: [
            { asset: "Dollar Bullish", weight: 0.2 },
            { asset: "Nasdaq ETF", weight: 0.2 },
            { asset: "S&P500 ETF", weight: 0.2 },
          ],
          capital_allocated: {
            "Dollar Bullish": 100_000_000,
            "Nasdaq ETF": 100_000_000,
            "S&P500 ETF": 100_000_000,
          },
          confidence: 62,
          total_assets_analyzed: 9,
        });
      });
  }, []);

  if (!decision)
    return (
      <div className="p-6 text-text-secondary animate-pulse">
        در حال دریافت پیشنهاد...
      </div>
    );

  const { label: confLabel, colorClass: confColor } = toConfidenceLabel(
    decision.confidence
  );

  return (
    <div className="space-y-6 p-6">
      {/* ── Header ── */}
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <h2 className="text-2xl font-bold">🎯 پیشنهاد سرمایه‌گذاری این ماه</h2>
        <span className="text-sm text-text-secondary">
          بازه: {decision.horizon} — تحلیل{" "}
          {decision.total_assets_analyzed ?? "—"} دارایی
        </span>
      </div>

      {/* ── Allocation cards ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {decision.allocation.map((item, idx) => {
          const ranking = item.ranking ?? MOCK_RANKINGS[item.asset];
          const isExpanded = expandedAsset === item.asset;

          return (
            <div
              key={item.asset}
              className="bg-surface border border-border rounded-2xl p-4 flex flex-col gap-3"
            >
              {/* Asset name + rank badge */}
              <div className="flex justify-between items-start">
                <span className="text-lg font-bold">{item.asset}</span>
                <span className="text-xs bg-background border border-border px-2 py-0.5 rounded text-text-secondary">
                  #{idx + 1}
                </span>
              </div>

              {/* Weight */}
              <div className="text-3xl font-bold text-primary">
                {(item.weight * 100).toFixed(0)}٪
              </div>

              {/* Capital */}
              <div className="text-sm text-text-secondary">
                {decision.capital_allocated[item.asset]?.toLocaleString("fa-IR")}{" "}
                تومان
              </div>

              {/* Ranking summary */}
              {ranking && (
                <div className="space-y-1.5 pt-3 border-t border-border">
                  <p className="text-xs font-semibold text-text-secondary mb-2">
                    دلایل انتخاب:
                  </p>
                  <RankRow label="مومنتوم ۴ ماهه" rank={ranking.momentumRank} />
                  <RankRow label="نسبت Sharpe" rank={ranking.sharpeRank} />
                  <RankRow
                    label="نوسان (کمتر = بهتر)"
                    rank={ranking.volatilityRank}
                  />
                </div>
              )}

              {/* Expand toggle */}
              {ranking && (
                <>
                  <button
                    onClick={() =>
                      setExpandedAsset(isExpanded ? null : item.asset)
                    }
                    className="text-xs text-primary hover:underline self-start"
                  >
                    {isExpanded ? "بستن جزئیات ↑" : "جزئیات عددی ↓"}
                  </button>

                  {/* Expanded numeric detail */}
                  {isExpanded && (
                    <div className="bg-background rounded-xl border border-border p-3 space-y-2">
                      <NumericRow
                        label="مومنتوم ۴ ماهه"
                        value={ranking.momentum4M}
                        valueClass="text-green"
                      />
                      <NumericRow
                        label="Sharpe ۱۲ ماهه"
                        value={ranking.sharpe12M}
                      />
                      <NumericRow
                        label="نوسان ماهانه"
                        value={ranking.volatilityMonthly}
                      />
                    </div>
                  )}
                </>
              )}
            </div>
          );
        })}
      </div>

      {/* ── Footer: confidence + disclaimer ── */}
      <div className="flex flex-wrap items-center gap-x-6 gap-y-2 bg-surface border border-border rounded-2xl px-5 py-3 text-sm">
        <div className="flex items-center gap-2">
          <span className="text-text-secondary">سطح اطمینان مدل:</span>
          <span className={`font-bold ${confColor}`}>
            {confLabel} — {decision.confidence}/100
          </span>
        </div>
        <span className="text-xs text-text-secondary">
          پیشنهاد بر اساس مومنتوم قیمتی — توصیه مالی نیست
        </span>
        <button
          onClick={() => onNavigate("risk")}
          className="text-primary hover:underline text-xs mr-auto"
        >
          مشاهده تحلیل ریسک ←
        </button>
      </div>
    </div>
  );
};
