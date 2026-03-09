import { Wallet } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Props {
  totalAccounts: number;
}

export function AccountsSummaryCard({ totalAccounts }: Props) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">Accounts</CardTitle>
        <Wallet className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{totalAccounts}</div>
        <p className="text-xs text-muted-foreground">Active accounts</p>
      </CardContent>
    </Card>
  );
}
