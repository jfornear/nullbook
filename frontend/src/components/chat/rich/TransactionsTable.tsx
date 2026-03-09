import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCurrency, formatDate } from "@/lib/utils";
import { cn } from "@/lib/utils";

interface TransactionData {
  transactions: {
    id: number;
    date: string;
    description: string;
    amount: string;
    transaction_type: string;
    category_name: string;
    account_name: string | null;
  }[];
  total: number;
}

export function TransactionsTable({ data }: { data: unknown }) {
  const { transactions } = data as TransactionData;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Transactions ({transactions.length})</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-1.5">
          {transactions.map((t) => (
            <div
              key={t.id}
              className="flex items-center justify-between rounded-md border px-3 py-1.5"
            >
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm">{t.description}</div>
                <div className="flex gap-2 text-xs text-muted-foreground">
                  <span>{formatDate(t.date)}</span>
                  <span>{t.category_name}</span>
                </div>
              </div>
              <span
                className={cn(
                  "ml-2 shrink-0 text-sm font-medium",
                  t.transaction_type === "income"
                    ? "text-green-600 dark:text-green-400"
                    : t.transaction_type === "expense"
                      ? "text-red-600 dark:text-red-400"
                      : ""
                )}
              >
                {t.transaction_type === "income"
                  ? "+"
                  : t.transaction_type === "expense"
                    ? "-"
                    : ""}
                {formatCurrency(t.amount)}
              </span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
