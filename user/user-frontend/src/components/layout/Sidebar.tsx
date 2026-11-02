"use client";
const tabs = [
  { id: "iran", label: "🇮🇷 داده‌های بازار ایران" },
  { id: "decision", label: "🎯 تصمیم سرمایه‌گذاری" },
  { id: "momentum", label: "📈 مانیتور مومنتوم" },
  { id: "regime", label: "🌍 رژیم بازار" },
  { id: "news", label: "📰 اخبار" },
  { id: "risk", label: "🛡️ مرکز ریسک" },
  { id: "portfolio", label: "💰 پرتفوی" },
  { id: "backtest", label: "🧪 آزمایشگاه بک‌تست" },
  { id: "macro", label: "📊 دید کلان" },
  { id: "analyst", label: "🤖 تحلیلگر AI" },
  { id: "settings", label: "⚙️ تنظیمات" },
];

interface SidebarProps {
  activeTab: string;
  onTabChange: (id: string) => void;
}

export const Sidebar = ({ activeTab, onTabChange }: SidebarProps) => (
  <aside className="w-64 bg-surface border-l border-border h-screen overflow-y-auto p-3 flex-shrink-0">
    <h2 className="text-lg font-bold mb-4 text-primary">MarketSage AI</h2>
    <nav className="space-y-1">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          className={`w-full text-right p-3 rounded-xl transition-colors ${
            activeTab === tab.id
              ? "bg-primary/20 text-primary border border-primary/30"
              : "hover:bg-background text-text-secondary"
          }`}
        >
          {tab.label}
        </button>
      ))}
    </nav>
  </aside>
);