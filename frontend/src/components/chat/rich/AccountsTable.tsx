import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatCurrency } from "@/lib/utils";

interface AccountData {
  accounts: {
    id: number;
    name: string;
    account_type: string;
    balance: string;
    currency: string;
    institution_name: string | null;
  }[];
  total: number;
}

export function AccountsTable({ data }: { data: unknown }) {
  const { accounts } = data as AccountData;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Accounts ({accounts.length})</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {accounts.map((a) => (
            <div
              key={a.id}
              className="flex items-center justify-between rounded-md border px-3 py-2"
            >
              <div>
                <div className="text-sm font-medium">{a.name}</div>
                {a.institution_name && (
                  <div className="text-xs text-muted-foreground">{a.institution_name}</div>
                )}
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="secondary" className="text-xs">
                  {a.account_type}
                </Badge>
                <span className="text-sm font-medium">{formatCurrency(a.balance, a.currency)}</span>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
