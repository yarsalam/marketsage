export interface FinanceTheme {
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
  fonts: {
    primary: string;
  };
}

export const financialTheme: FinanceTheme = {
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
  fonts: {
    primary: 'var(--font-vazirmatn)',
  },
};
