"use client";

import { useEffect, useRef, useState } from "react";

type Message = { role: "user" | "assistant"; content: string };
type GuideAnswer = { content: string; destination?: string };

function getGuideAnswer(question: string): GuideAnswer {
  const text = question.trim().toLowerCase();

  if (/قیمت|خرید|فروش|پیشنهاد|رتبه|دلار|طلا|بورس|ناسداک|سود|بازده/.test(text)) {
    return {
      content: "در این نسخه، خروجی رتبه‌بندی و تخصیص سرمایه تا زمان تأیید منابع و روش پژوهشی غیرفعال است. من هم به قیمت زنده یا یک مدل زبانی متصل نیستم؛ بنابراین عدد یا پیشنهاد خرید و فروش تولید نمی‌کنم. برای دیدن وضعیت منابع و داده‌های ثبت‌شده، بخش «وضعیت داده» را باز کن.",
      destination: "settings",
    };
  }

  if (/ریسک|افت|ضرر|var|شارپ|نوسان|پرتفوی|سرمایه/.test(text)) {
    return {
      content: "نمایش معیارهای ریسک و وزن پرتفوی فعلاً بسته است؛ اعداد تاریخی نمونه نباید به‌عنوان ریسک فعلی یا پیشنهاد تخصیص تلقی شوند. بازگشایی به دادهٔ زمان‌مند، هزینه و نقدشوندگی معتبر و ارزیابی خارج از نمونه نیاز دارد.",
      destination: "decision",
    };
  }

  if (/خبر|سیاسی|احساسات|سنتیمنت|کلان|تورم|نرخ بهره|رژیم بازار/.test(text)) {
    return {
      content: "خط لولهٔ عملیاتی و قابل ممیزی برای خبر، رویداد سیاسی، احساسات و دادهٔ کلان هنوز در نسخهٔ اجرایی متصل نشده است. این بخش‌ها تا زمان داشتن منبع، زمان انتشار و تاریخچهٔ قابل بازپخش، خروجی تحلیلی ارائه نمی‌کنند.",
    };
  }

  if (/منبع|داده|کیفیت|تازگی|اتصال|ایران|tsetmc|codal|fred/.test(text)) {
    return {
      content: "موتور فعلی فقط یک نمونهٔ محدود از پروکسی‌های جهانی را به جریان پژوهش متصل کرده است. منابع ایران، از جمله بورس، طلا و ارز، هنوز تأیید و وارد محاسبات نشده‌اند. وضعیت واقعی ثبت داده، اتصال منابع و محدودیت‌ها را از بخش «وضعیت داده» بررسی کن.",
      destination: "settings",
    };
  }

  if (/ادمین|مدیریت|کاربر|ورود|حساب/.test(text)) {
    return {
      content: "پنل ادمین هنوز سرویس عملیاتی کامل نیست؛ احراز هویت، سطح دسترسی، ثبت ممیزی، ذخیره‌سازی و عملیات واقعی مدیریت باید تکمیل و امن‌سازی شوند. فعلاً نباید از آن برای مدیریت کاربران یا منابع استفاده کرد.",
    };
  }

  if (/هوش مصنوعی|چت.?بات|مدل زبانی|ai/.test(text)) {
    return {
      content: "این پنجره در حال حاضر فقط راهنمای ثابت محصول است، نه دستیار هوش مصنوعی متصل به مدل زبانی. برای تبدیل آن به تحلیلگر واقعی باید API مدل، بازیابی شواهد از داده‌های تأییدشده، ارجاع هر ادعا و کنترل پاسخ بدون مدرک ساخته شود.",
    };
  }

  return {
    content: "می‌توانم وضعیت فعلی قابلیت‌ها و محدودیت‌های MarketSage را توضیح بدهم، اما قیمت، رتبه، ریسک یا توصیهٔ سرمایه‌گذاری تولید نمی‌کنم. موضوعت را دربارهٔ منابع داده، کیفیت داده، موتور تحلیل، اخبار، ریسک یا پنل ادمین مشخص کن.",
  };
}

export const AIChatbot = ({ onNavigate }: { onNavigate: (tab: string) => void }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "سلام. من فعلاً راهنمای ثابت MarketSage هستم، نه مدل هوش مصنوعی یا تحلیلگر متصل به دادهٔ زنده. می‌توانم قابلیت‌های موجود و بخش‌های تکمیل‌نشده را توضیح بدهم.",
    },
  ]);
  const [input, setInput] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isOpen]);

  const handleSend = () => {
    const question = input.trim();
    if (!question) return;
    const answer = getGuideAnswer(question);
    setMessages((current) => [
      ...current,
      { role: "user", content: question },
      { role: "assistant", content: answer.content },
    ]);
    setInput("");
    if (answer.destination) onNavigate(answer.destination);
  };

  return (
    <>
      {!isOpen && (
        <button
          type="button"
          onClick={() => setIsOpen(true)}
          className="fixed bottom-4 left-4 z-50 rounded-full bg-primary p-4 text-white shadow-lg transition-colors hover:bg-primary/80"
          title="راهنمای MarketSage"
          aria-label="باز کردن راهنمای MarketSage"
        >
          ?
        </button>
      )}

      {isOpen && (
        <section
          className="fixed bottom-4 left-4 z-50 flex h-[530px] w-[min(24rem,calc(100vw-2rem))] flex-col rounded-2xl border border-border bg-surface shadow-2xl"
          aria-label="راهنمای MarketSage"
        >
          <header className="flex items-start justify-between border-b border-border p-3">
            <div>
              <p className="font-bold">راهنمای MarketSage</p>
              <p className="text-xs text-text-secondary">راهنمای ثابت محصول · بدون مدل زبانی یا دادهٔ زنده</p>
            </div>
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="mt-0.5 text-text-secondary hover:text-text"
              aria-label="بستن"
            >
              ✕
            </button>
          </header>

          <div className="flex-1 space-y-3 overflow-y-auto p-3">
            {messages.map((message, index) => (
              <div
                key={message.role + "-" + index}
                className={"flex " + (message.role === "user" ? "justify-end" : "justify-start")}
              >
                <p
                  className={
                    "max-w-[88%] whitespace-pre-line rounded-xl p-3 text-sm leading-relaxed " +
                    (message.role === "user" ? "bg-primary text-white" : "border border-border bg-background")
                  }
                >
                  {message.content}
                </p>
              </div>
            ))}
            <div ref={endRef} />
          </div>

          <form
            className="flex gap-2 border-t border-border p-3"
            onSubmit={(event) => {
              event.preventDefault();
              handleSend();
            }}
          >
            <input
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="دربارهٔ وضعیت واقعی محصول بپرس..."
              className="min-w-0 flex-1 rounded-xl border border-border bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none"
            />
            <button
              type="submit"
              disabled={!input.trim()}
              className="rounded-xl bg-primary px-4 text-white transition-opacity disabled:opacity-40"
            >
              ارسال
            </button>
          </form>
        </section>
      )}
    </>
  );
};
