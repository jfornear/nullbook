import { useCallback, useSyncExternalStore } from "react";

type Theme = "light" | "dark";

function getTheme(): Theme {
  const stored = localStorage.getItem("theme");
  if (stored === "dark" || stored === "light") return stored;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

// Simple external store so all useTheme() consumers stay in sync
const listeners = new Set<() => void>();
let currentTheme: Theme = getTheme();

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function getSnapshot(): Theme {
  return currentTheme;
}

function setTheme(theme: Theme) {
  currentTheme = theme;
  localStorage.setItem("theme", theme);
  const root = document.documentElement;
  if (theme === "dark") {
    root.classList.add("dark");
  } else {
    root.classList.remove("dark");
  }
  listeners.forEach((l) => l());
}

// Apply initial theme on load
setTheme(currentTheme);

export function useTheme() {
  const theme = useSyncExternalStore(subscribe, getSnapshot);

  const toggleTheme = useCallback(() => {
    setTheme(currentTheme === "dark" ? "light" : "dark");
  }, []);

  return { theme, toggleTheme };
}
