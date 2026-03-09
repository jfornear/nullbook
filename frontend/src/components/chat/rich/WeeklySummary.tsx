import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatCurrency } from "@/lib/utils";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface WeeklySummaryData {
  week_ending: string;
  spending: {
    this_week: string;
    last_week: string;
    change_pct: string;
  };
  top_categories: { name: string; amount: string }[];
  notable_transactions: { description: string; amount: string; date: string }[];
  net_worth: string;
  subscription_monthly: string;
}

export function WeeklySummary({ data }: { data: WeeklySummaryData }) {
  const changePct = parseFloat(data.spending?.change_pct || "0");
  const TrendIcon = changePct > 5 ? TrendingUp : changePct < -5 ? TrendingDown : Minus;
  const trendColor =
    changePct > 5 ? "text-red-500" : changePct < -5 ? "text-green-500" : "text-muted-foreground";

  return (
    <Card className="w-full">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Weekly Summary — {data.week_ending}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Spending comparison */}
        {data.spending && (
          <div className="grid grid-cols-3 gap-3">
            <div>
              <div className="text-xs text-muted-foreground">This Week</div>
              <div className="text-lg font-bold">{formatCurrency(data.spending.this_week)}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Last Week</div>
              <div className="text-lg font-bold">{formatCurrency(data.spending.last_week)}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Change</div>
              <div className={`flex items-center gap-1 text-lg font-bold ${trendColor}`}>
                <TrendIcon className="h-4 w-4" />
                {Math.abs(changePct)}%
              </div>
            </div>
          </div>
        )}

        {/* Top categories */}
        {data.top_categories && data.top_categories.length > 0 && (
          <div>
            <div className="text-xs font-medium text-muted-foreground mb-1">Top Categories</div>
            <div className="space-y-1">
              {data.top_categories.map((cat, i) => (
                <div key={i} className="flex items-center justify-between text-sm">
                  <span>{cat.name}</span>
                  <span className="tabular-nums font-medium">{formatCurrency(cat.amount)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Notable transactions */}
        {data.notable_transactions && data.notable_transactions.length > 0 && (
          <div>
            <div className="text-xs font-medium text-muted-foreground mb-1">
              Notable Transactions
            </div>
            <div className="space-y-1">
              {data.notable_transactions.map((txn, i) => (
                <div key={i} className="flex items-center justify-between text-sm">
                  <span className="truncate max-w-[60%]">{txn.description}</span>
                  <span className="tabular-nums font-medium">{formatCurrency(txn.amount)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Bottom stats */}
        <div className="flex items-center gap-3 pt-1">
          <Badge variant="outline" className="text-[10px]">
            Net Worth: {formatCurrency(data.net_worth)}
          </Badge>
          {parseFloat(data.subscription_monthly) > 0 && (
            <Badge variant="outline" className="text-[10px]">
              Subscriptions: {formatCurrency(data.subscription_monthly)}/mo
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
