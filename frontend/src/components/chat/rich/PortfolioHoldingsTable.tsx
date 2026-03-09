import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCurrency } from "@/lib/utils";

interface HoldingsData {
  holdings: {
    id: number;
    symbol: string;
    name: string;
    security_type: string;
    shares: string;
    cost_basis: string;
    account_name: string | null;
  }[];
  total: number;
}

export function PortfolioHoldingsTable({ data }: { data: unknown }) {
  const { holdings } = data as HoldingsData;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Holdings ({holdings.length})</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-1.5">
          {holdings.map((h) => (
            <div
              key={h.id}
              className="flex items-center justify-between rounded-md border px-3 py-1.5"
            >
              <div>
                <span className="text-sm font-medium">{h.symbol}</span>
                <span className="ml-2 text-xs text-muted-foreground">{h.name}</span>
              </div>
              <div className="text-right">
                <div className="text-sm">{parseFloat(h.shares).toLocaleString()} shares</div>
                <div className="text-xs text-muted-foreground">
                  {formatCurrency(h.cost_basis)} cost
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
