import { Card, CardContent } from "@/components/ui/card";
import { DollarSign, Wallet, ArrowLeftRight, TrendingUp } from "lucide-react";
import { formatCurrency } from "@/lib/utils";

interface DashboardData {
  total_accounts: number;
  net_worth: string;
  recent_transactions: number;
  portfolio_value: string;
}

const stats = [
  { key: "net_worth", label: "Net Worth", icon: DollarSign, isCurrency: true },
  { key: "total_accounts", label: "Accounts", icon: Wallet, isCurrency: false },
  { key: "recent_transactions", label: "Recent Txns", icon: ArrowLeftRight, isCurrency: false },
  { key: "portfolio_value", label: "Portfolio", icon: TrendingUp, isCurrency: true },
] as const;

export function DashboardSummaryCard({ data }: { data: unknown }) {
  const d = data as DashboardData;

  return (
    <div className="grid grid-cols-2 gap-2">
      {stats.map((stat) => {
        const value = d[stat.key];
        return (
          <Card key={stat.key}>
            <CardContent className="flex items-center gap-3 p-3">
              <stat.icon className="h-4 w-4 text-muted-foreground shrink-0" />
              <div>
                <div className="text-xs text-muted-foreground">{stat.label}</div>
                <div className="text-sm font-semibold">
                  {stat.isCurrency ? formatCurrency(String(value)) : String(value)}
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
