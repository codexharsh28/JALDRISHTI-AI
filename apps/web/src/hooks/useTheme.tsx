import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

export type ThemeMode = 'dark' | 'light' | 'system';

interface ThemeContextType {
  theme: ThemeMode;
  effectiveTheme: 'dark' | 'light';
  setTheme: (mode: ThemeMode) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const STORAGE_KEY = 'jaldrishti_theme';

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setThemeState] = useState<ThemeMode>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved === 'light' || saved === 'dark' || saved === 'system') {
        return saved;
      }
    } catch {
      // Storage unavailable fallback
    }
    return 'dark';
  });

  const getSystemTheme = (): 'dark' | 'light' => {
    if (typeof window !== 'undefined' && window.matchMedia) {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    return 'dark';
  };

  const [effectiveTheme, setEffectiveTheme] = useState<'dark' | 'light'>(() => {
    return theme === 'system' ? getSystemTheme() : theme;
  });

  const applyTheme = useCallback((mode: ThemeMode) => {
    const root = document.documentElement;
    const computed = mode === 'system' ? getSystemTheme() : mode;
    setEffectiveTheme(computed);

    root.classList.remove('dark', 'light');
    root.classList.add(computed);
    root.setAttribute('data-theme', computed);

    try {
      localStorage.setItem(STORAGE_KEY, mode);
    } catch {
      // Ignore storage errors
    }
  }, []);

  const setTheme = useCallback((mode: ThemeMode) => {
    setThemeState(mode);
    applyTheme(mode);
  }, [applyTheme]);

  const toggleTheme = useCallback(() => {
    setThemeState(prev => {
      let next: ThemeMode = 'dark';
      if (prev === 'dark') next = 'light';
      else if (prev === 'light') next = 'system';
      else next = 'dark';
      applyTheme(next);
      return next;
    });
  }, [applyTheme]);

  // Handle system preference changes
  useEffect(() => {
    applyTheme(theme);

    if (typeof window !== 'undefined' && window.matchMedia) {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      const handleChange = () => {
        if (theme === 'system') {
          applyTheme('system');
        }
      };
      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    }
  }, [theme, applyTheme]);

  return (
    <ThemeContext.Provider value={{ theme, effectiveTheme, setTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
