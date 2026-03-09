import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

const shortcuts = [
  { keys: ["Cmd", "K"], description: "Focus chat input" },
  { keys: ["Cmd", "N"], description: "New conversation" },
  { keys: ["Escape"], description: "Close panel or dialog" },
  { keys: ["?"], description: "Show keyboard shortcuts" },
];

function Kbd({ children }: { children: React.ReactNode }) {
  return (
    <kbd className="inline-flex h-5 min-w-[20px] items-center justify-center rounded border bg-muted px-1.5 font-mono text-[10px] font-medium">
      {children}
    </kbd>
  );
}

interface KeyboardShortcutsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function KeyboardShortcutsDialog({ open, onOpenChange }: KeyboardShortcutsDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Keyboard Shortcuts</DialogTitle>
          <DialogDescription>Available keyboard shortcuts for quick navigation.</DialogDescription>
        </DialogHeader>
        <div className="space-y-2">
          {shortcuts.map((s) => (
            <div key={s.description} className="flex items-center justify-between py-1">
              <span className="text-sm">{s.description}</span>
              <div className="flex items-center gap-1">
                {s.keys.map((k, i) => (
                  <span key={i} className="flex items-center gap-0.5">
                    {i > 0 && <span className="text-[10px] text-muted-foreground">+</span>}
                    <Kbd>{k === "Cmd" ? "\u2318" : k}</Kbd>
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}
