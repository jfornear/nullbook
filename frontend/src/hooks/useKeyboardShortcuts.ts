import { useEffect, useState, useCallback } from "react";

export interface Shortcut {
  key: string;
  meta?: boolean;
  description: string;
  action: () => void;
}

export function useKeyboardShortcuts(shortcuts: Shortcut[]) {
  useEffect(() => {
    function handler(e: KeyboardEvent) {
      // Don't trigger in input/textarea unless it's Escape
      const tag = (e.target as HTMLElement)?.tagName;
      const isInput =
        tag === "INPUT" || tag === "TEXTAREA" || (e.target as HTMLElement)?.isContentEditable;

      for (const s of shortcuts) {
        const metaMatch = s.meta ? e.metaKey || e.ctrlKey : !e.metaKey && !e.ctrlKey;
        if (e.key === s.key && metaMatch) {
          if (isInput && e.key !== "Escape") continue;
          e.preventDefault();
          s.action();
          return;
        }
      }
    }

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [shortcuts]);
}

export function useShortcutsDialog() {
  const [open, setOpen] = useState(false);
  const toggle = useCallback(() => setOpen((v) => !v), []);
  return { open, setOpen, toggle };
}
