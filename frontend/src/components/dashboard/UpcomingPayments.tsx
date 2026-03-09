import { useQuery } from "@tanstack/react-query";
import { CalendarDays } from "lucide-react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCurrency } from "@/lib/utils";

interface Subscription {
  id: number;
  merchant: string;
  amount: string;
  frequency: string;
  next_expected: string | null;
}

export function UpcomingPayments() {
  const { data } = useQuery({
    queryKey: ["subscriptions", "upcoming"],
    queryFn: () => api.get<Subscription[]>("/transactions/subscriptions/upcoming/"),
  });

  if (!data || data.length === 0) return null;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <CalendarDays className="h-4 w-4" />
          Upcoming Payments
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-1.5">
        {data.slice(0, 5).map((sub) => (
          <div
            key={sub.id}
            className="flex items-center justify-between rounded-md border px-2.5 py-2"
          >
            <div className="min-w-0">
              <div className="text-xs font-medium truncate">{sub.merchant}</div>
              {sub.next_expected && (
                <div className="text-[10px] text-muted-foreground">
                  {new Date(sub.next_expected).toLocaleDateString()}
                </div>
              )}
            </div>
            <div className="text-xs font-medium shrink-0">{formatCurrency(sub.amount)}</div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
