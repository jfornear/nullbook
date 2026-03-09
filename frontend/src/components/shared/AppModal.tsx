import { lazy, Suspense } from "react";
import { Dialog, DialogClose, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Landmark,
  TrendingUp,
  FileText,
  ArrowLeftRight,
  Upload,
  PiggyBank,
  Target,
  Repeat,
  Mail,
  Newspaper,
  Settings,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";

export type SectionId =
  | "accounts"
  | "portfolio"
  | "transactions"
  | "taxes"
  | "budgets"
  | "goals"
  | "subscriptions"
  | "import"
  | "email"
  | "news"
  | "settings";

const AccountsPage = lazy(() => import("@/pages/Accounts"));
const PortfolioPage = lazy(() => import("@/pages/Portfolio"));
const TransactionsPage = lazy(() => import("@/pages/Transactions"));
const TaxesPage = lazy(() => import("@/pages/Taxes"));
const ImportPage = lazy(() => import("@/pages/Import"));
const ReceiptsPage = lazy(() => import("@/pages/Receipts"));
const NewsPage = lazy(() => import("@/pages/News"));

const BudgetsContent = lazy(() =>
  import("@/components/panels/BudgetsPanel").then((m) => ({
    default: m.BudgetsContent,
  }))
);
const GoalsContent = lazy(() =>
  import("@/components/panels/GoalsPanel").then((m) => ({
    default: m.GoalsContent,
  }))
);
const SubscriptionsContent = lazy(() =>
  import("@/components/panels/SubscriptionsPanel").then((m) => ({
    default: m.SubscriptionsContent,
  }))
);
const EmailContent = lazy(() =>
  import("@/components/panels/EmailPanel").then((m) => ({
    default: m.EmailContent,
  }))
);

const SettingsPage = lazy(() =>
  import("@/components/settings/SettingsDialog").then((m) => ({
    default: m.SettingsPage,
  }))
);

interface NavItem {
  id: SectionId;
  label: string;
  icon: typeof Settings;
}

const sectionGroups: { items: NavItem[] }[] = [
  {
    items: [
      { id: "accounts", label: "Accounts", icon: Landmark },
      { id: "portfolio", label: "Portfolio", icon: TrendingUp },
      { id: "transactions", label: "Transactions", icon: ArrowLeftRight },
      { id: "taxes", label: "Taxes", icon: FileText },
    ],
  },
  {
    items: [
      { id: "budgets", label: "Budgets", icon: PiggyBank },
      { id: "goals", label: "Goals", icon: Target },
      { id: "subscriptions", label: "Subscriptions", icon: Repeat },
    ],
  },
  {
    items: [
      { id: "import", label: "Import", icon: Upload },
      { id: "email", label: "Email", icon: Mail },
      { id: "news", label: "News", icon: Newspaper },
    ],
  },
  {
    items: [{ id: "settings", label: "Settings", icon: Settings }],
  },
];

const allItems = sectionGroups.flatMap((g) => g.items);

function SectionFallback() {
  return (
    <div className="space-y-3">
      <Skeleton className="h-6 w-32" />
      <Skeleton className="h-20 w-full" />
      <Skeleton className="h-20 w-full" />
    </div>
  );
}

function ImportSection() {
  return (
    <Tabs defaultValue="files">
      <TabsList>
        <TabsTrigger value="files">Files</TabsTrigger>
        <TabsTrigger value="receipts">Receipts</TabsTrigger>
      </TabsList>
      <TabsContent value="files">
        <Suspense fallback={<SectionFallback />}>
          <ImportPage />
        </Suspense>
      </TabsContent>
      <TabsContent value="receipts">
        <Suspense fallback={<SectionFallback />}>
          <ReceiptsPage />
        </Suspense>
      </TabsContent>
    </Tabs>
  );
}

interface AppModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  section: SectionId;
  onSectionChange: (section: SectionId) => void;
}

export function AppModal({ open, onOpenChange, section, onSectionChange }: AppModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="max-w-5xl h-[min(85vh,720px)] p-0 gap-0 flex overflow-hidden sm:rounded-2xl"
        aria-describedby={undefined}
        hideClose
      >
        <DialogTitle className="sr-only">
          {allItems.find((i) => i.id === section)?.label ?? "Settings"}
        </DialogTitle>

        {/* Left nav */}
        <nav className="w-[210px] shrink-0 border-r bg-muted/30 p-2 overflow-y-auto flex flex-col">
          <div className="flex py-2 px-1">
            <DialogClose className="rounded-lg p-2 opacity-60 hover:opacity-100 hover:bg-accent transition-all">
              <X className="h-4 w-4" />
              <span className="sr-only">Close</span>
            </DialogClose>
          </div>
          {sectionGroups.map((group, gi) => (
            <div key={gi} className={gi > 0 ? "mt-3" : ""}>
              <div className="space-y-0.5">
                {group.items.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    className={cn(
                      "flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm cursor-pointer hover:bg-accent transition-colors",
                      section === item.id && "bg-accent font-medium"
                    )}
                    onClick={() => onSectionChange(item.id)}
                  >
                    <item.icon className="h-[18px] w-[18px] shrink-0" />
                    {item.label}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </nav>

        {/* Right content */}
        <div className="flex-1 overflow-y-auto px-5">
          <div className="flex min-h-[60px] items-center border-b py-3 sticky top-0 bg-background z-10">
            <h2 className="text-lg">{allItems.find((i) => i.id === section)?.label}</h2>
          </div>
          <div className="pt-4">
            <Suspense fallback={<SectionFallback />}>
              {section === "accounts" && <AccountsPage />}
              {section === "portfolio" && <PortfolioPage />}
              {section === "transactions" && <TransactionsPage />}
              {section === "taxes" && <TaxesPage />}
              {section === "budgets" && <BudgetsContent />}
              {section === "goals" && <GoalsContent />}
              {section === "subscriptions" && <SubscriptionsContent />}
              {section === "import" && <ImportSection />}
              {section === "email" && <EmailContent />}
              {section === "news" && <NewsPage />}
              {section === "settings" && <SettingsPage />}
            </Suspense>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
