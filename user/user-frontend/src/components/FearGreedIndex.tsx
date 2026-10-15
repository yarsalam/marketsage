"use client";
const values: Record<string, number> = { bourse: 65, gold: 45, crypto: 80, oil: 30, forex: 55 };

export const FearGreedIndex = ({ market }: { market: string }) => {
  const value = values[market] ?? 50;
  const angle = (value / 100) * 180 - 90;
  const color = value > 50 ? "#22C55E" : value < 30 ? "#EF4444" : "#F59E0B";
  const label = value > 70 ? "طمع" : value > 50 ? "خوش‌بینی" : value > 30 ? "تردید" : "ترس";

  return (
    <div className="bg-surface border border-border rounded-2xl p-4">
      <h3 className="text-lg font-semibold mb-4">شاخص ترس و طمع</h3>
      <div className="flex flex-col items-center">
        <svg width="160" height="100" viewBox="0 0 160 100">
          <path d="M10 90 A70 70 0 0 1 150 90" fill="none" stroke="#2A2A2A" strokeWidth="10" />
          <line x1="80" y1="90" x2={80 + 70 * Math.cos((angle * Math.PI) / 180)} y2={90 - 70 * Math.sin((angle * Math.PI) / 180)} stroke={color} strokeWidth="3" strokeLinecap="round" />
          <circle cx="80" cy="90" r="6" fill={color} />
        </svg>
        <div className="text-2xl font-bold mt-2" style={{ color }}>{value}</div>
        <div className="text-sm text-text-secondary mt-1">{label}</div>
      </div>
    </div>
  );
};