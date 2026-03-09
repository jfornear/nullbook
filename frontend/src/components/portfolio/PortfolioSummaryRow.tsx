import { useQuery } from "@tanstack/react-query";
import type { Holding } from "@/types";
import { Card, CardContent } from "@/components/ui/card";
import { formatCurrency } from "@/lib/utils";
import { api } from "@/lib/api";

interface Props {
  holdings: Holding[];
}

interface PerformanceData {
  total_market_value: string;
  total_unrealized_gain: string;
  total_unrealized_gain_pct: number;
}

export function PortfolioSummaryRow({ holdings }: Props) {
  const totalHoldings = holdings.length;
  const totalCostBasis = holdings.reduce((sum, h) => sum + parseFloat(h.cost_basis), 0);

  const { data: perf } = useQuery({
    queryKey: ["portfolio-performance"],
    queryFn: () => api.get<PerformanceData>("/portfolio/holdings/performance/"),
    refetchInterval: 5 * 60_000,
    staleTime: 5 * 60_000,
    placeholderData: (prev) => prev,
  });

  const marketValue = perf ? parseFloat(perf.total_market_value) : null;
  const gain = perf ? parseFloat(perf.total_unrealized_gain) : null;
  const gainPct = perf?.total_unrealized_gain_pct ?? null;

  return (
    <div className="grid gap-4 md:grid-cols-4">
      <Card>
        <CardContent className="pt-4 pb-4">
          <p className="text-sm text-muted-foreground">Total Holdings</p>
          <p className="text-2xl font-bold">{totalHoldings}</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-4 pb-4">
          <p className="text-sm text-muted-foreground">Cost Basis</p>
          <p className="text-2xl font-bold">{formatCurrency(totalCostBasis)}</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-4 pb-4">
          <p className="text-sm text-muted-foreground">Market Value</p>
          <p className="text-2xl font-bold">
            {marketValue !== null ? formatCurrency(marketValue) : formatCurrency(totalCostBasis)}
          </p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-4 pb-4">
          <p className="text-sm text-muted-foreground">Unrealized Gain</p>
          <div
            className={
              gain !== null && gain > 0
                ? "text-green-600"
                : gain !== null && gain < 0
                  ? "text-red-600"
                  : ""
            }
          >
            {gain !== null ? (
              <>
                <p className="text-2xl font-bold truncate">
                  {gain > 0 ? "+" : ""}
                  {formatCurrency(gain)}
                </p>
                {gainPct !== null && (
                  <p className="text-sm text-muted-foreground">
                    {gain > 0 ? "+" : ""}
                    {gainPct.toFixed(2)}%
                  </p>
                )}
              </>
            ) : (
              <p className="text-2xl font-bold">—</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
