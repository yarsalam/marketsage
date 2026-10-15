import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "react-hot-toast";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "Market Sage - تحلیل بازار",
  description: "پلتفرم جامع تحلیل بازارهای مالی ایران",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fa" dir="rtl" className="dark">
      <body className="min-h-screen bg-background text-text font-sans">
        <Providers>
          {children}
          <Toaster
            position="bottom-center"
            toastOptions={{
              style: { background: "#141414", color: "#F5F5F5", border: "1px solid #2A2A2A" },
            }}
          />
        </Providers>
      </body>
    </html>
  );
}