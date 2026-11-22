"use client";

export type MarketTabId =
  | "iran_equities"
  | "iran_gold_coin"
  | "iran_fx"
  | "iran_fixed_income"
  | "iran_crypto"
  | "global";

const tabs: Array<{ id: MarketTabId; label: string }> = [
  { id: "iran_equities", label: "بورس و فرابورس" },
  { id: "iran_gold_coin", label: "طلا و سکه" },
  { id: "iran_fx", label: "ارز ایران" },
  { id: "iran_fixed_income", label: "صندوق و درآمد ثابت" },
  { id: "iran_crypto", label: "رمزارز ایران" },
  { id: "global", label: "بازارهای جهانی" },
];

export function MarketTabs({
  activeTab,
  onChange,
}: {
  activeTab: MarketTabId;
  onChange: (tabId: MarketTabId) => void;
}) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-2" role="tablist" aria-label="خانواده‌های بازار">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          role="tab"
          aria-selected={activeTab === tab.id}
          onClick={() => onChange(tab.id)}
          className={`rounded-xl border px-4 py-2 text-sm font-medium whitespace-nowrap transition-colors ${
            activeTab === tab.id
              ? "border-primary bg-primary/15 text-primary"
              : "border-border bg-surface text-text-secondary hover:bg-background"
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
