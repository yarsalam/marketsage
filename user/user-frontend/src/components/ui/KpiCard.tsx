import React from 'react';

interface KpiCardProps {
  title: string;
  value: string;
  change?: { value: string; isPositive: boolean };
  chart?: React.ReactNode;
  className?: string;
}

export const KpiCard = ({
  title,
  value,
  change,
  chart,
  className = '',
}: KpiCardProps) => (
  <div
    className={`bg-surface border border-border rounded-2xl p-4 flex flex-col justify-between ${className}`}
  >
    <div className="flex justify-between items-start mb-2">
      <span className="text-sm text-text-secondary">{title}</span>
      {change && (
        <span
          className={`text-xs font-bold px-2 py-0.5 rounded ${change.isPositive ? 'text-green bg-green/10' : 'text-red bg-red/10'}`}
        >
          {change.value}
        </span>
      )}
    </div>
    <div className="text-2xl font-bold text-text mb-3 tracking-tight">
      {value}
    </div>
    <div className="h-8 w-full">{chart}</div>
  </div>
);
