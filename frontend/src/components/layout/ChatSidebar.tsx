import { useNavigate } from "react-router-dom";
import {
  ChevronLeft,
  ChevronRight,
  Plus,
  Landmark,
  TrendingUp,
  FileText,
  ArrowLeftRight,
  Upload,
  Settings,
  LogOut,
  Sun,
  Moon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { useSession, useLogout } from "@/lib/auth";
import { useTheme } from "@/lib/theme";
import { cn } from "@/lib/utils";
import { ConversationList } from "@/components/chat/ConversationList";

const configItems = [
  { icon: Landmark, label: "Accounts", panel: "accounts" },
  { icon: TrendingUp, label: "Portfolio", panel: "portfolio" },
  { icon: FileText, label: "Taxes", panel: "taxes" },
  { icon: ArrowLeftRight, label: "Transactions", panel: "transactions" },
  { icon: Upload, label: "Import", panel: "import" },
] as const;

export type PanelName =
  | "accounts"
  | "portfolio"
  | "taxes"
  | "budgets"
  | "goals"
  | "subscriptions"
  | "email"
  | "news"
  | "transactions"
  | "import"
  | "settings"
  | null;

interface ChatSidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  activePanel: PanelName;
  onPanelChange: (panel: PanelName) => void;
}

function UserInitials({ username }: { username: string }) {
  const initials = username
    .split(/[\s._-]+/)
    .slice(0, 2)
    .map((s) => s[0]?.toUpperCase() ?? "")
    .join("");
  return (
    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary text-[11px] font-medium text-primary-foreground">
      {initials || "?"}
    </div>
  );
}

export function ChatSidebar({ collapsed, onToggle, activePanel, onPanelChange }: ChatSidebarProps) {
  const navigate = useNavigate();
  const { data: user } = useSession();
  const logout = useLogout();
  const { theme, toggleTheme } = useTheme();

  return (
    <aside
      className={cn(
        "flex h-full flex-col border-r bg-muted/30 transition-[width] duration-200",
        collapsed ? "w-12" : "w-72"
      )}
    >
      {/* Logo + collapse toggle */}
      <div
        className={cn(
          "flex h-12 shrink-0 items-center",
          collapsed ? "justify-center px-1" : "justify-between pl-4 pr-3"
        )}
      >
        {!collapsed && (
          <svg width="72" height="12" viewBox="1.27 5.7 39.2 6.3" fill="none">
            <g transform="translate(0.5, 3.5) scale(0.6)">
              <path
                d="M2.55 14L1.29 14L1.29 6.30L2.55 6.30L2.55 7.77L2.81 7.77L2.55 8.06Q2.55 7.15 3.09 6.66Q3.64 6.16 4.61 6.16L4.61 6.16Q5.77 6.16 6.45 6.87Q7.14 7.59 7.14 8.82L7.14 8.82L7.14 14L5.88 14L5.88 8.96Q5.88 8.13 5.44 7.69Q5.00 7.25 4.24 7.25L4.24 7.25Q3.46 7.25 3.00 7.73Q2.55 8.20 2.55 9.10L2.55 9.10L2.55 14ZM12.59 14.14L12.59 14.14Q11.26 14.14 10.46 13.35Q9.66 12.56 9.66 11.20L9.66 11.20L9.66 6.30L10.92 6.30L10.92 11.20Q10.92 12.07 11.37 12.55Q11.82 13.03 12.59 13.03L12.59 13.03Q13.37 13.03 13.82 12.55Q14.28 12.07 14.28 11.20L14.28 11.20L14.28 6.30L15.54 6.30L15.54 11.20Q15.54 12.56 14.73 13.35Q13.92 14.14 12.59 14.14ZM24.50 14L22.05 14Q21.38 14 20.87 13.73Q20.37 13.47 20.09 12.98Q19.81 12.49 19.81 11.83L19.81 11.83L19.81 4.93L17.22 4.93L17.22 3.78L21.07 3.78L21.07 11.83Q21.07 12.31 21.34 12.58Q21.60 12.85 22.05 12.85L22.05 12.85L24.50 12.85L24.50 14ZM32.90 14L30.45 14Q29.78 14 29.27 13.73Q28.77 13.47 28.49 12.98Q28.21 12.49 28.21 11.83L28.21 11.83L28.21 4.93L25.62 4.93L25.62 3.78L29.47 3.78L29.47 11.83Q29.47 12.31 29.74 12.58Q30.00 12.85 30.45 12.85L30.45 12.85L32.90 12.85L32.90 14ZM38.25 14.14L38.25 14.14Q37.30 14.14 36.72 13.63Q36.15 13.12 36.15 12.24L36.15 12.24L36.40 12.53L36.15 12.53L36.15 14L34.89 14L34.89 3.78L36.15 3.78L36.15 6.02L36.12 7.77L36.40 7.77L36.15 8.06Q36.15 7.20 36.73 6.68Q37.31 6.16 38.25 6.16L38.25 6.16Q39.41 6.16 40.11 6.93Q40.81 7.70 40.81 9.03L40.81 9.03L40.81 11.28Q40.81 12.60 40.11 13.37Q39.41 14.14 38.25 14.14ZM37.83 13.05L37.83 13.05Q38.63 13.05 39.09 12.57Q39.55 12.10 39.55 11.20L39.55 11.20L39.55 9.10Q39.55 8.20 39.09 7.73Q38.63 7.25 37.83 7.25L37.83 7.25Q37.06 7.25 36.60 7.74Q36.15 8.23 36.15 9.10L36.15 9.10L36.15 11.20Q36.15 12.07 36.60 12.56Q37.06 13.05 37.83 13.05ZM46.20 14.11L46.20 14.11Q45.28 14.11 44.60 13.76Q43.93 13.41 43.56 12.75Q43.19 12.08 43.19 11.17L43.19 11.17L43.19 9.13Q43.19 8.20 43.56 7.55Q43.93 6.89 44.60 6.54Q45.28 6.19 46.20 6.19L46.20 6.19Q47.12 6.19 47.80 6.54Q48.47 6.89 48.84 7.55Q49.21 8.20 49.21 9.11L49.21 9.11L49.21 11.17Q49.21 12.08 48.84 12.75Q48.47 13.41 47.80 13.76Q47.12 14.11 46.20 14.11ZM46.20 12.99L46.20 12.99Q47.03 12.99 47.49 12.53Q47.95 12.07 47.95 11.17L47.95 11.17L47.95 9.13Q47.95 8.23 47.49 7.77Q47.03 7.31 46.20 7.31L46.20 7.31Q45.39 7.31 44.92 7.77Q44.45 8.23 44.45 9.13L44.45 9.13L44.45 11.17Q44.45 12.07 44.92 12.53Q45.39 12.99 46.20 12.99ZM54.60 14.11L54.60 14.11Q53.68 14.11 53.00 13.76Q52.33 13.41 51.96 12.75Q51.59 12.08 51.59 11.17L51.59 11.17L51.59 9.13Q51.59 8.20 51.96 7.55Q52.33 6.89 53.00 6.54Q53.68 6.19 54.60 6.19L54.60 6.19Q55.52 6.19 56.20 6.54Q56.87 6.89 57.24 7.55Q57.61 8.20 57.61 9.11L57.61 9.11L57.61 11.17Q57.61 12.08 57.24 12.75Q56.87 13.41 56.20 13.76Q55.52 14.11 54.60 14.11ZM54.60 12.99L54.60 12.99Q55.43 12.99 55.89 12.53Q56.35 12.07 56.35 11.17L56.35 11.17L56.35 9.13Q56.35 8.23 55.89 7.77Q55.43 7.31 54.60 7.31L54.60 7.31Q53.79 7.31 53.32 7.77Q52.85 8.23 52.85 9.13L52.85 9.13L52.85 11.17Q52.85 12.07 53.32 12.53Q53.79 12.99 54.60 12.99ZM61.39 14L60.13 14L60.13 3.78L61.39 3.78L61.39 9.48L62.87 9.48L65.11 6.30L66.56 6.30L63.97 9.97L66.60 14L65.13 14L62.89 10.57L61.39 10.57L61.39 14Z"
                fill="hsl(var(--foreground))"
              />
            </g>
          </svg>
        )}
        <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onToggle}>
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </Button>
      </div>

      {/* New Chat */}
      <div className={cn("shrink-0 p-2", collapsed && "px-1")}>
        <Button
          variant="ghost"
          className={cn("w-full justify-start gap-2", collapsed && "justify-center px-0")}
          size="sm"
          onClick={() => navigate("/")}
        >
          <Plus className="h-4 w-4" />
          {!collapsed && <span>New Chat</span>}
        </Button>
      </div>

      {/* Conversation list */}
      <div className="flex-1 overflow-hidden">
        <ConversationList collapsed={collapsed} />
      </div>

      <Separator />

      {/* Config nav */}
      <div className={cn("space-y-0.5 p-2", collapsed && "px-1")}>
        {configItems.map((item) => (
          <Button
            key={item.panel}
            variant={activePanel === item.panel ? "secondary" : "ghost"}
            className={cn(
              "w-full justify-start gap-2 h-8 text-xs",
              collapsed && "justify-center px-0"
            )}
            size="sm"
            onClick={() => onPanelChange(activePanel === item.panel ? null : item.panel)}
          >
            <item.icon className="h-3.5 w-3.5 shrink-0" />
            {!collapsed && <span>{item.label}</span>}
          </Button>
        ))}
      </div>

      <Separator />

      {/* User menu */}
      <div className={cn("shrink-0 p-2", collapsed && "px-1")}>
        <Popover>
          <PopoverTrigger asChild>
            <button
              type="button"
              className={cn(
                "flex w-full items-center gap-2.5 rounded-md px-2 py-1.5 text-sm hover:bg-accent cursor-pointer",
                collapsed && "justify-center px-0"
              )}
            >
              <UserInitials username={user?.username ?? ""} />
              {!collapsed && (
                <span className="min-w-0 truncate text-xs font-medium">{user?.username}</span>
              )}
            </button>
          </PopoverTrigger>
          <PopoverContent side="top" align="start" className="w-56 p-1">
            <div className="flex items-center gap-2.5 px-2 py-2">
              <UserInitials username={user?.username ?? ""} />
              <div className="min-w-0">
                <div className="truncate text-sm font-medium">{user?.username}</div>
                <div className="truncate text-xs text-muted-foreground">{user?.email}</div>
              </div>
            </div>
            <Separator className="my-1" />
            <button
              type="button"
              className="flex w-full cursor-pointer items-center gap-2 rounded-sm px-2 py-1.5 text-sm hover:bg-accent"
              onClick={() => onPanelChange(activePanel === "settings" ? null : "settings")}
            >
              <Settings className="h-4 w-4" />
              Settings
            </button>
            <button
              type="button"
              className="flex w-full cursor-pointer items-center gap-2 rounded-sm px-2 py-1.5 text-sm hover:bg-accent"
              onClick={toggleTheme}
            >
              {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
              {theme === "dark" ? "Light mode" : "Dark mode"}
            </button>
            <Separator className="my-1" />
            <button
              type="button"
              className="flex w-full cursor-pointer items-center gap-2 rounded-sm px-2 py-1.5 text-sm hover:bg-accent"
              onClick={() => logout.mutate()}
            >
              <LogOut className="h-4 w-4" />
              Log out
            </button>
          </PopoverContent>
        </Popover>
      </div>
    </aside>
  );
}
