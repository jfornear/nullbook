import { TrendingUp } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCurrency } from "@/lib/utils";

interface Props {
  portfolioValue: string;
}

export function PortfolioSummaryCard({ portfolioValue }: Props) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">Portfolio Value</CardTitle>
        <TrendingUp className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{formatCurrency(portfolioValue)}</div>
        <p className="text-xs text-muted-foreground">Total investments</p>
      </CardContent>
    </Card>
  );
}
