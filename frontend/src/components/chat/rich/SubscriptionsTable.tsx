import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CreditCard } from "lucide-react";
import { formatCurrency } from "@/lib/utils";

interface Subscription {
  id: number;
  merchant: string;
  amount: string;
  frequency: string;
  status: string;
  last_charged: string | null;
  next_expected: string | null;
  annual_cost: number;
  cancellation_url: string;
}

interface SubscriptionsTableData {
  subscriptions: Subscription[];
  total_monthly: string;
  total_annual: string;
  total: number;
}

const statusColor: Record<string, string> = {
  active: "bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-400",
  cancelled: "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-400",
  cancellation_pending: "bg-yellow-100 text-yellow-700 dark:bg-yellow-950 dark:text-yellow-400",
  possibly_cancelled: "bg-orange-100 text-orange-700 dark:bg-orange-950 dark:text-orange-400",
};

function statusLabel(status: string): string {
  return status.replace(/_/g, " ");
}

export function SubscriptionsTable({ data }: { data: unknown }) {
  const d = data as SubscriptionsTableData;

  if (!d.subscriptions || d.subscriptions.length === 0) {
    return (
      <Card>
        <CardContent className="py-4 text-center text-sm text-muted-foreground">
          No subscriptions detected.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-sm">
            <CreditCard className="h-4 w-4" />
            Subscriptions ({d.total})
          </CardTitle>
          <Badge variant="secondary" className="text-xs">
            {formatCurrency(d.total_monthly)}/mo
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-1">
        {/* Table header */}
        <div className="grid grid-cols-[1fr_auto_auto_auto_auto] gap-2 px-3 py-1 text-[10px] font-medium text-muted-foreground uppercase tracking-wide">
          <span>Merchant</span>
          <span className="w-16 text-right">Amount</span>
          <span className="w-16 text-center">Frequency</span>
          <span className="w-20 text-center">Status</span>
          <span className="w-20 text-right">Annual Cost</span>
        </div>

        {d.subscriptions.map((sub) => (
          <div
            key={sub.id}
            className="grid grid-cols-[1fr_auto_auto_auto_auto] gap-2 items-center rounded-md border px-3 py-2 text-sm"
          >
            <span className="font-medium truncate">{sub.merchant}</span>
            <span className="w-16 text-right">{formatCurrency(sub.amount)}</span>
            <span className="w-16 text-center text-xs text-muted-foreground capitalize">
              {sub.frequency}
            </span>
            <span className="w-20 flex justify-center">
              <span
                className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-medium capitalize ${
                  statusColor[sub.status] || "bg-muted text-muted-foreground"
                }`}
              >
                {statusLabel(sub.status)}
              </span>
            </span>
            <span className="w-20 text-right font-medium">{formatCurrency(sub.annual_cost)}</span>
          </div>
        ))}

        {/* Totals */}
        <div className="flex items-center justify-between rounded-md bg-muted/50 px-3 py-2 mt-2 text-sm font-semibold">
          <span>Total</span>
          <div className="flex gap-4 text-xs">
            <span>{formatCurrency(d.total_monthly)}/mo</span>
            <span>{formatCurrency(d.total_annual)}/yr</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
