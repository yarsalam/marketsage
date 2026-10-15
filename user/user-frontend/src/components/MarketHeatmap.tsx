const allSectors: Record<string, { name: string; value: number; color: string }[]> = {
  bourse: [
    { name: "پتروشیمی", value: 85, color: "#22C55E" },
    { name: "فلزات", value: 55, color: "#F59E0B" },
    { name: "بانکی", value: 70, color: "#22C55E" },
    { name: "خودرو", value: 90, color: "#22C55E" },
    { name: "فناوری", value: 40, color: "#EF4444" },
    { name: "غذایی", value: 60, color: "#F59E0B" },
  ],
  gold: [
    { name: "طلا ۱۸ عیار", value: 70, color: "#22C55E" },
    { name: "سکه", value: 80, color: "#22C55E" },
    { name: "انس جهانی", value: 50, color: "#F59E0B" },
    { name: "نقره", value: 35, color: "#EF4444" },
  ],
  crypto: [
    { name: "بیت‌کوین", value: 85, color: "#22C55E" },
    { name: "اتریوم", value: 70, color: "#22C55E" },
    { name: "سولانا", value: 60, color: "#F59E0B" },
    { name: "کاردانو", value: 30, color: "#EF4444" },
  ],
  oil: [
    { name: "نفت برنت", value: 65, color: "#F59E0B" },
    { name: "گازوئیل", value: 50, color: "#F59E0B" },
    { name: "بنزین", value: 45, color: "#EF4444" },
  ],
  forex: [
    { name: "EUR/USD", value: 55, color: "#F59E0B" },
    { name: "GBP/USD", value: 60, color: "#22C55E" },
    { name: "USD/JPY", value: 40, color: "#EF4444" },
  ],
};

export const MarketHeatmap = ({ market }: { market: string }) => {
  const sectors = allSectors[market] || allSectors.bourse;
  return (
    <div className="bg-surface border border-border rounded-2xl p-4">
      <h3 className="text-lg font-semibold mb-4">نقشه بازار</h3>
      <div className="grid grid-cols-2 gap-1" style={{ gridAutoRows: "minmax(40px, auto)" }}>
        {sectors.map((s, i) => (
          <div
            key={i}
            className="rounded flex items-center justify-center text-xs font-bold p-2"
            style={{ backgroundColor: s.color + "CC" }} // opacity via hex
          >
            {s.name}
          </div>
        ))}
      </div>
    </div>
  );
};