"use client";
import { useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { AIChatbot } from "@/components/layout/AIChatbot";
import { PricePrediction } from "@/components/PricePrediction";
import { RiskAnalysis } from "@/components/RiskAnalysis";
import { InvestmentDecision } from "@/components/InvestmentDecision";

// سایر importها...
type TabComponent = React.FC<{ onNavigate: (tab: string) => void }>;
const tabComponents: Record<string, TabComponent> = {
  decision: InvestmentDecision,
  risk: RiskAnalysis,
  // ... بقیه
};

export default function Home() {
  const [activeTab, setActiveTab] = useState("decision");
  const ActiveComponent = tabComponents[activeTab] || InvestmentDecision;

  return (
    <div className="flex h-screen bg-background text-text">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
      <main className="flex-1 overflow-y-auto p-6">
        <ActiveComponent onNavigate={setActiveTab} />
      </main>
      <AIChatbot />
    </div>
  );
}
