// components/IndexCard.tsx
import { Sparkline } from './ui/Sparkline';

interface IndexCardProps {
  title: string;
  value: string;
  unit: string;
  changePercent: string;
  changeValue: string;
  time: string;
  data: { time: string; value: number }[];
  isPositive: boolean;
}

export const IndexCard = ({
  title,
  value,
  unit,
  changePercent,
  changeValue,
  time,
  data,
  isPositive,
}: IndexCardProps) => {
  return (
    <div className="bg-surface border border-border rounded-2xl p-4 flex flex-col">
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-sm font-medium text-text-secondary">{title}</h3>
        <span
          className={`text-xs font-bold px-1.5 py-0.5 rounded ${isPositive ? 'text-green bg-green/10' : 'text-red bg-red/10'}`}
        >
          {changePercent}
        </span>
      </div>
      <div className="flex items-baseline gap-2 mb-1">
        <span className="text-2xl font-bold text-text tracking-tight">
          {value}
        </span>
        <span className="text-xs text-text-secondary">{unit}</span>
      </div>
      <div className="flex justify-between items-center text-xs text-text-secondary mb-3">
        <span>{changeValue}</span>
        <span>{time}</span>
      </div>
      <Sparkline
        data={data}
        color={isPositive ? '#22C55E' : '#EF4444'}
        height={40}
      />
    </div>
  );
};
