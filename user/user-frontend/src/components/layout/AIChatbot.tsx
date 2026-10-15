"use client";
import { useState, useRef, useEffect } from "react";

type Message = { role: "user" | "assistant"; content: string };

/* ─────────────────────────────────────────────────────────────────
   Knowledge base — all answers are traceable to ranking numbers.
   When the backend starts returning ranking data, pull these values
   from the API response instead of hardcoding them here.
───────────────────────────────────────────────────────────────── */
const KB = {
  dollar: `Dollar Bullish به دلایل زیر در رتبه اول قرار گرفته:

• مومنتوم ۴ ماهه: +۶.۲٪ — رتبه ۱ از ۹ دارایی
• نسبت Sharpe ۱۲ ماهه: ۱.۱۸ — رتبه ۲
• نوسان ماهانه: ۴.۵٪ — رتبه ۱ (کمترین نوسان)

در ۴ ماه اخیر بالاترین بازده تعدیل‌شده به ریسک را داشته است.`,

  nasdaq: `Nasdaq ETF به دلایل زیر انتخاب شده:

• مومنتوم ۴ ماهه: +۵.۱٪ — رتبه ۲ از ۹ دارایی
• نسبت Sharpe ۱۲ ماهه: ۱.۰۵ — رتبه ۳
• نوسان ماهانه: ۸.۲٪ — رتبه ۴

بازده خوبی داشته اما نوسان آن بیشتر از دلار است.`,

  spx: `S&P 500 ETF به دلایل زیر انتخاب شده:

• مومنتوم ۴ ماهه: +۴.۳٪ — رتبه ۳ از ۹ دارایی
• نسبت Sharpe ۱۲ ماهه: ۰.۹۸ — رتبه ۴
• نوسان ماهانه: ۷.۱٪ — رتبه ۳

پایه‌ای محافظه‌کارانه برای تنوع‌بخشی به پرتفوی.`,

  risk: `ریسک پرتفوی فعلی:

• VaR 95٪ = ۳.۲٪
  در ۹۵٪ مواقع افت هفتگی کمتر از این خواهد بود.

• Max Drawdown = ۵.۱٪
  بیشترین افت تاریخی ثبت‌شده.

• Sharpe = ۱.۴
  به ازای هر واحد ریسک، ۱.۴ واحد بازده اضافی.

پرتفوی در مجموع محافظه‌کارانه طراحی شده (بتا = ۰.۸۵).`,

  confidence: `سطح اطمینان مدل «متوسط» (۶۲/۱۰۰) است.

مدل فعلی فقط از مومنتوم قیمتی استفاده می‌کند.
عواملی که هنوز در مدل لحاظ نشده‌اند:
• اخبار و احساسات بازار
• داده‌های کلان اقتصادی واقعی
• Walk-Forward Validation کامل

این پیشنهاد نقطه شروع است، نه توصیه قطعی.`,

  algo: `مدل بر اساس سه معیار رتبه‌بندی می‌کند:

۱. مومنتوم — بازده قیمتی ۴ ماه گذشته
۲. Sharpe — بازده تعدیل‌شده به نوسان (۱۲ ماهه)
۳. نوسان — پایداری قیمت ماهانه (کمتر بهتر)

دارایی‌هایی که در هر سه معیار رتبه بالاتری دارند
وزن بیشتری در پرتفوی می‌گیرند.`,

  default: `می‌توانم در این موارد کمک کنم:

• «چرا دلار انتخاب شد؟»
• «چرا ناسداک انتخاب شد؟»
• «چرا S&P 500 انتخاب شد؟»
• «ریسک پرتفوی چقدر است؟»
• «سطح اطمینان مدل چیست؟»
• «الگوریتم چطور کار می‌کند؟»`,
} as const;

/* ── Keyword router ── */
function getAnswer(q: string): string {
  const t = q.toLowerCase();
  if (t.includes("دلار") || t.includes("dollar")) return KB.dollar;
  if (t.includes("ناسداک") || t.includes("nasdaq")) return KB.nasdaq;
  if (
    t.includes("s&p") ||
    t.includes("spx") ||
    t.includes("اس اند") ||
    t.includes("اس‌اند")
  )
    return KB.spx;
  if (
    t.includes("ریسک") ||
    t.includes("var") ||
    t.includes("drawdown") ||
    t.includes("sharpe") ||
    t.includes("بتا")
  )
    return KB.risk;
  if (
    t.includes("اطمینان") ||
    t.includes("confidence") ||
    t.includes("دقت مدل")
  )
    return KB.confidence;
  if (
    t.includes("الگوریتم") ||
    t.includes("معیار") ||
    t.includes("چطور") ||
    t.includes("چرا") ||
    t.includes("مومنتوم")
  )
    return KB.algo;
  return KB.default;
}

/* ── Component ── */
export const AIChatbot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "سلام! می‌توانم دلایل عددی هر پیشنهاد را توضیح دهم.\n\nمثلاً بپرسید:\n• «چرا دلار انتخاب شد؟»\n• «ریسک پرتفوی چقدر است؟»\n• «سطح اطمینان مدل چیست؟»",
    },
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const handleSend = () => {
    const text = input.trim();
    if (!text) return;
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setInput("");
    setIsTyping(true);
    setTimeout(() => {
      setIsTyping(false);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: getAnswer(text) },
      ]);
    }, 420);
  };

  return (
    <>
      {/* Floating button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-4 left-4 bg-primary text-white p-4 rounded-full shadow-lg z-50 hover:bg-primary/80 transition-colors"
          title="تحلیلگر AI"
        >
          🤖
        </button>
      )}

      {/* Chat panel */}
      {isOpen && (
        <div className="fixed bottom-4 left-4 w-96 h-[530px] bg-surface border border-border rounded-2xl shadow-2xl z-50 flex flex-col">
          {/* Header */}
          <div className="flex justify-between items-start p-3 border-b border-border">
            <div>
              <p className="font-bold">🤖 تحلیلگر MarketSage</p>
              <p className="text-xs text-text-secondary">
                پاسخ‌ها بر اساس داده‌های مومنتوم
              </p>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="text-text-secondary hover:text-text mt-0.5"
              aria-label="بستن"
            >
              ✕
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            {messages.map((m, i) => (
              <div
                key={i}
                className={`flex ${
                  m.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[85%] p-3 rounded-xl text-sm whitespace-pre-line leading-relaxed ${
                    m.role === "user"
                      ? "bg-primary text-white"
                      : "bg-background border border-border"
                  }`}
                >
                  {m.content}
                </div>
              </div>
            ))}

            {/* Typing indicator */}
            {isTyping && (
              <div className="flex justify-start">
                <div className="bg-background border border-border px-4 py-3 rounded-xl text-sm text-text-secondary">
                  در حال تایپ...
                </div>
              </div>
            )}
            <div ref={endRef} />
          </div>

          {/* Input */}
          <div className="p-3 border-t border-border flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) =>
                e.key === "Enter" && !e.shiftKey && handleSend()
              }
              placeholder="چرا این دارایی انتخاب شد؟"
              className="flex-1 bg-background border border-border rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-primary transition-colors"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim()}
              className="bg-primary text-white px-4 rounded-xl disabled:opacity-40 transition-opacity"
            >
              ➤
            </button>
          </div>
        </div>
      )}
    </>
  );
};
