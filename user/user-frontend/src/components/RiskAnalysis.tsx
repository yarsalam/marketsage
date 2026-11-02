"use client";
import { RiskCenter } from "@/components/ResearchTab";

export const RiskAnalysis = ({ onNavigate }: { onNavigate?: (tab: string) => void }) => (
  <RiskCenter onNavigate={onNavigate ?? (() => undefined)} />
);
