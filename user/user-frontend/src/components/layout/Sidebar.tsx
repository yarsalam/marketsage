"use client";

const tabs = [
  { id: "coverage", label: "🧭 پوشش بازار و کیفیت داده" },
  { id: "decision", label: "🎯 تصمیم پژوهشی · غیرفعال" },
  { id: "momentum", label: "📈 مومنتوم · غیرفعال" },
  { id: "regime", label: "🌍 رژیم بازار · غیرفعال" },
  { id: "news", label: "📰 اخبار · غیرفعال" },
  { id: "risk", label: "🛡️ ریسک · غیرفعال" },
  { id: "portfolio", label: "💰 تخصیص پرتفوی · غیرفعال" },
  { id: "backtest", label: "🧪 بک‌تست · متوقف تا تأیید داده" },
  { id: "macro", label: "📊 دید کلان · غیرفعال" },
  { id: "analyst", label: "🤖 تحلیلگر AI · متصل نیست" },
  { id: "settings", label: "⚙️ وضعیت داده" },
];

interface SidebarProps {
  activeTab: string;
  onTabChange: (id: string) => void;
  userName: string;
  onLogout: () => void;
}

export const Sidebar = ({ activeTab, onTabChange, userName, onLogout }: SidebarProps) => (
  <aside className="flex h-screen w-64 flex-shrink-0 flex-col overflow-y-auto border-l border-border bg-surface p-3">
    <h2 className="mb-1 text-lg font-bold text-primary">MarketSage</h2>
    <p className="mb-4 truncate text-xs text-text-secondary">{userName}</p>
    <nav className="flex-1 space-y-1" aria-label="بخش‌های MarketSage">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          onClick={() => onTabChange(tab.id)}
          aria-current={activeTab === tab.id ? "page" : undefined}
          className={`w-full rounded-xl p-3 text-right transition-colors ${
            activeTab === tab.id
              ? "border border-primary/30 bg-primary/20 text-primary"
              : "text-text-secondary hover:bg-background"
          }`}
        >
          {tab.label}
        </button>
      ))}
    </nav>
    <button
      type="button"
      onClick={onLogout}
      className="mt-4 w-full rounded-xl border border-border p-3 text-right text-sm text-text-secondary hover:bg-background"
    >
      خروج از حساب
    </button>
  </aside>
);
