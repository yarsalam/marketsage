import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MarketSage Admin Operations",
  description: "Read-only internal operations workspace",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="fa" dir="rtl" className="h-full antialiased">
      <body className="min-h-full">{children}</body>
    </html>
  );
}
