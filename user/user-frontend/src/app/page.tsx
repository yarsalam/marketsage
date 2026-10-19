"use client";
import { useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { IranMarketDashboard } from "@/components/IranMarketDashboard";
import { AIChatbot } from "@/components/layout/AIChatbot";
import { InvestmentDecision } from "@/components/InvestmentDecision";
import { RiskAnalysis } from "@/components/RiskAnalysis";
import {
  MomentumMonitor, MarketRegime, NewsIntelligence, PortfolioAllocator,
  BacktestingLab, MacroView, AIAnalyst, DataSettings,
} from "@/components/ResearchTab";

type TabComponent = React.FC<{ onNavigate: (tab: string) => void }>;
const tabComponents: Record<string, TabComponent> = {
  iran: IranMarketDashboard as TabComponent,
  decision: InvestmentDecision,
  momentum: MomentumMonitor,
  regime: MarketRegime,
  news: NewsIntelligence,
  risk: RiskAnalysis,
  portfolio: PortfolioAllocator,
  backtest: BacktestingLab,
  macro: MacroView,
  analyst: AIAnalyst,
  settings: DataSettings,
};

export default function Home() {
  const [activeTab, setActiveTab] = useState("iran");
  const ActiveComponent = tabComponents[activeTab] ?? InvestmentDecision;
  return (
    <div className="flex h-screen bg-background text-text">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
      <main className="min-w-0 flex-1 overflow-y-auto p-2 md:p-6">
        <ActiveComponent onNavigate={setActiveTab} />
      </main>
      <AIChatbot />
    </div>
  );
}
