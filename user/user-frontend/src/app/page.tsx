"use client";

import { useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { AIChatbot } from "@/components/layout/AIChatbot";
import { InvestmentDecision } from "@/components/InvestmentDecision";
import { MarketCoverage } from "@/components/MarketCoverage";
import { ResearchTab } from "@/components/ResearchTab";
import { useAuth } from "@/lib/AuthContext";

const researchTabs = new Set([
  "momentum", "regime", "news", "risk", "portfolio", "backtest", "macro", "analyst", "settings",
]);

export default function Home() {
  const [activeTab, setActiveTab] = useState("coverage");
  const { user, logout } = useAuth();

  async function handleLogout() {
    await logout();
  }

  return (
    <div className="flex h-screen bg-background text-text">
      <Sidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        userName={user?.nickname ?? "کاربر"}
        onLogout={() => void handleLogout()}
      />
      <main className="min-w-0 flex-1 overflow-y-auto p-2 md:p-6">
        {activeTab === "coverage" ? (
          <MarketCoverage onNavigate={setActiveTab} />
        ) : activeTab === "decision" ? (
          <InvestmentDecision onNavigate={setActiveTab} />
        ) : researchTabs.has(activeTab) ? (
          <ResearchTab activeTab={activeTab as never} onNavigate={setActiveTab} />
        ) : (
          <MarketCoverage onNavigate={setActiveTab} />
        )}
      </main>
      <AIChatbot onNavigate={setActiveTab} />
    </div>
  );
}
