import { Menu } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ChatHeaderProps {
  title?: string;
  onMenuClick: () => void;
}

export function ChatHeader({ title, onMenuClick }: ChatHeaderProps) {
  return (
    <header className="flex h-12 shrink-0 items-center gap-3 border-b bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/60 md:hidden">
      <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onMenuClick}>
        <Menu className="h-4 w-4" />
        <span className="sr-only">Menu</span>
      </Button>
      <span className="text-base font-semibold truncate tracking-tight">{title || "nullbook"}</span>
    </header>
  );
}
