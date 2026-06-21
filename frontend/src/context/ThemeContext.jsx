import { createContext, useContext, useEffect, useState } from 'react';

const ThemeContext = createContext();

export const ThemeProvider = ({ children }) => {
  // Check local storage or system preference
  const [isDarkMode, setIsDarkMode] = useState(() => {
    if (typeof window !== 'undefined') {
      const savedTheme = localStorage.getItem('fluenttech-theme');
      if (savedTheme) {
        return savedTheme === 'dark';
      }
      // If no saved theme, check system preference. But default to light mode to show off both.
      // Or default to dark if that was the original. Let's default to dark to preserve original behavior safely.
      return true;
    }
    return true;
  });

  useEffect(() => {
    const root = window.document.documentElement;
    if (isDarkMode) {
      root.classList.add('dark');
      localStorage.setItem('fluenttech-theme', 'dark');
    } else {
      root.classList.remove('dark');
      localStorage.setItem('fluenttech-theme', 'light');
    }
  }, [isDarkMode]);

  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode);
  };

  return (
    <ThemeContext.Provider value={{ isDarkMode, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => useContext(ThemeContext);
