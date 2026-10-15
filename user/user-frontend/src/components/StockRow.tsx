// components/StockRow.tsx
import { Sparkline } from './ui/Sparkline';

interface StockRowProps {
  symbol: string;
  market: string;
  price: string;
  changePercent: string;
  isPositive: boolean;
  data: { time: string; value: number }[];
}

export const StockRow = ({
  symbol,
  market,
  price,
  changePercent,
  isPositive,
  data,
}: StockRowProps) => {
  return (
    <div className="flex items-center justify-between py-3 border-b border-border last:border-0">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-text truncate">{symbol}</span>
          <span className="text-xs text-text-secondary bg-surface border border-border px-2 py-0.5 rounded">
            {market}
          </span>
        </div>
        <div className="text-sm text-text mt-0.5">{price}</div>
      </div>
      <div className="flex items-center gap-3">
        <span
          className={`text-sm font-medium ${isPositive ? 'text-green' : 'text-red'}`}
        >
          {changePercent}
        </span>
        <div className="w-20 h-8">
          <Sparkline
            data={data}
            color={isPositive ? '#22C55E' : '#EF4444'}
            height={30}
          />
        </div>
      </div>
    </div>
  );
};
