// src/context/ThemeContext.tsx
'use client';
import { createContext, useContext, useEffect, useState } from 'react';

export interface AppTheme {
  name: string;
  colors: {
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    green: string;
    red: string;
    primary: string;
    border: string;
  };
  fonts: { primary: string };
}

const defaultTheme: AppTheme = {
  name: 'dark',
  colors: {
    background: '#0A0A0A',
    surface: '#141414',
    text: '#F5F5F5',
    textSecondary: '#A0A0A0',
    green: '#22C55E',
    red: '#EF4444',
    primary: '#3B82F6',
    border: '#2A2A2A',
  },
  fonts: { primary: 'Vazirmatn, sans-serif' },
};

const ThemeContext = createContext<{
  theme: AppTheme;
  setTheme: (theme: AppTheme) => void;
}>({
  theme: defaultTheme,
  setTheme: () => {},
});

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<AppTheme>(defaultTheme);

  useEffect(() => {
    // اعمال متغیرهای CSS
    const root = document.documentElement;
    root.style.setProperty('--color-background', theme.colors.background);
    root.style.setProperty('--color-surface', theme.colors.surface);
    root.style.setProperty('--color-text', theme.colors.text);
    root.style.setProperty(
      '--color-text-secondary',
      theme.colors.textSecondary,
    );
    root.style.setProperty('--color-green', theme.colors.green);
    root.style.setProperty('--color-red', theme.colors.red);
    root.style.setProperty('--color-primary', theme.colors.primary);
    root.style.setProperty('--color-border', theme.colors.border);
    document.body.style.fontFamily = theme.fonts.primary;
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export const useAppTheme = () => useContext(ThemeContext);
