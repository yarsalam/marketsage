import { Sparkline } from "@/components/ui/Sparkline";

const allOpps: Record<string, { symbol: string; risk: number; return: number }[]> = {
  bourse: [
    { symbol: "فولاد", risk: 15, return: 8 },
    { symbol: "شپنا", risk: 20, return: 12 },
    { symbol: "وغدیر", risk: 10, return: 6 },
  ],
  gold: [
    { symbol: "طلا ۱۸ عیار", risk: 8, return: 5 },
    { symbol: "سکه امامی", risk: 10, return: 7 },
    { symbol: "ربع سکه", risk: 12, return: 9 },
  ],
  crypto: [
    { symbol: "BTC", risk: 25, return: 18 },
    { symbol: "ETH", risk: 22, return: 15 },
    { symbol: "SOL", risk: 30, return: 22 },
  ],
  oil: [
    { symbol: "نفت برنت", risk: 18, return: 10 },
    { symbol: "نفت WTI", risk: 17, return: 9 },
    { symbol: "گاز طبیعی", risk: 22, return: 14 },
  ],
  forex: [
    { symbol: "EUR/USD", risk: 5, return: 3 },
    { symbol: "USD/TRY", risk: 15, return: 12 },
    { symbol: "GBP/JPY", risk: 12, return: 8 },
  ],
};

export const TopOpportunities = ({ market }: { market: string }) => {
  const list = allOpps[market] || allOpps.bourse;
  return (
    <div className="bg-surface border border-border rounded-2xl p-4">
      <h3 className="text-lg font-semibold mb-4">📈 برترین فرصت‌ها</h3>
      <div className="space-y-3">
        {list.map((item, i) => (
          <div key={i} className="flex justify-between items-center p-3 rounded-xl bg-background border border-border">
            <div>
              <div className="font-bold">{item.symbol}</div>
              <div className="text-sm text-text-secondary">ریسک: {item.risk}٪ | بازده: {item.return}٪</div>
            </div>
            <div className="w-16 h-8">
              <Sparkline data={[
                { time: "2024-01-01", value: 10 },
                { time: "2024-01-02", value: 10 + item.return },
              ]} color="#22C55E" height={30} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};