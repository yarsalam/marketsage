"use client";
import { useEffect, useRef } from "react";
import { createChart, ColorType, AreaSeries } from "lightweight-charts";

interface SparklineProps {
  data: { time: string; value: number }[];
  color?: string;
  height?: number;
}

export const Sparkline = ({ data, color = "#3B82F6", height = 40 }: SparklineProps) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const chart = createChart(containerRef.current, {
      height,
      layout: { background: { type: ColorType.Solid, color: "transparent" } },
      grid: { vertLines: { visible: false }, horzLines: { visible: false } },
      rightPriceScale: { visible: false },
      timeScale: { visible: false },
      handleScroll: false,
      handleScale: false,
      crosshair: { vertLine: { visible: false }, horzLine: { visible: false } },
    });

    const series = chart.addSeries(AreaSeries, {
      lineColor: color,
      topColor: `${color}30`,
      bottomColor: `${color}00`,
      lineWidth: 2,
    });
    series.setData(data);
    chart.timeScale().fitContent();

    return () => chart.remove();
  }, [data, color, height]);

  return <div ref={containerRef} style={{ width: "100%", height }} />;
};