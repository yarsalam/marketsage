'use client';
import { useState } from 'react';

const tabs = [
  { id: 'bourse', label: 'بورس' },
  { id: 'gold', label: 'طلا' },
  { id: 'crypto', label: 'رمز ارز' },
  { id: 'oil', label: 'نفت' },
  { id: 'forex', label: 'فارکس' },
];

interface MarketTabsProps {
  onChange: (tabId: string) => void;
}

export const MarketTabs = ({ onChange }: MarketTabsProps) => {
  const [active, setActive] = useState('bourse');

  const handleClick = (id: string) => {
    setActive(id);
    onChange(id);
  };

  return (
    <div className="flex gap-2 overflow-x-auto pb-2">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => handleClick(tab.id)}
          className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-colors
            ${active === tab.id ? 'bg-primary text-white' : 'bg-surface text-text-secondary hover:bg-border'}`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
};
