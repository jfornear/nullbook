import { ArrowLeftRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Props {
  recentTransactions: number;
}

export function RecentTransactionsCard({ recentTransactions }: Props) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">Recent Transactions</CardTitle>
        <ArrowLeftRight className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{recentTransactions}</div>
        <p className="text-xs text-muted-foreground">In the last 30 days</p>
      </CardContent>
    </Card>
  );
}
