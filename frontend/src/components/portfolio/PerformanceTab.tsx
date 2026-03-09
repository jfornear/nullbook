import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface HoldingPerformance {
  id: number;
  symbol: string;
  name: string;
  shares: string;
  cost_basis: string;
  current_price: string | null;
  market_value: string;
  unrealized_gain: string;
  unrealized_gain_pct: number;
  day_change: string;
  day_change_pct: number;
}

interface PerformanceData {
  total_market_value: string;
  total_cost_basis: string;
  total_unrealized_gain: string;
  total_unrealized_gain_pct: number;
  day_change: string;
  day_change_pct: number;
  holdings: HoldingPerformance[];
}

function GainText({ value, pct }: { value: string; pct?: number }) {
  const num = parseFloat(value);
  const color = num > 0 ? "text-green-600" : num < 0 ? "text-red-600" : "text-muted-foreground";
  const sign = num > 0 ? "+" : "";
  return (
    <span className={color}>
      {sign}
      {formatCurrency(value)}
      {pct !== undefined && (
        <span className="text-xs ml-1">
          ({sign}
          {pct.toFixed(2)}%)
        </span>
      )}
    </span>
  );
}

export function PerformanceTab() {
  const { data, isLoading, isPlaceholderData, dataUpdatedAt } = useQuery({
    queryKey: ["portfolio-performance"],
    queryFn: () => api.get<PerformanceData>("/portfolio/holdings/performance/"),
    refetchInterval: 5 * 60_000,
    staleTime: 5 * 60_000,
    placeholderData: (prev) => prev,
  });

  if (isLoading && !data) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  if (!data || data.holdings.length === 0) {
    return (
      <div className="py-8 text-center text-sm text-muted-foreground">
        No performance data available. Add holdings with price history to see gains and losses.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Summary bar */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="pt-4 pb-4">
            <p className="text-sm text-muted-foreground">Market Value</p>
            <p className="text-2xl font-bold">{formatCurrency(data.total_market_value)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 pb-4">
            <p className="text-sm text-muted-foreground">Total Gain/Loss</p>
            <p className="text-2xl font-bold">
              <GainText value={data.total_unrealized_gain} pct={data.total_unrealized_gain_pct} />
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 pb-4">
            <p className="text-sm text-muted-foreground">Day Change</p>
            <p className="text-2xl font-bold">
              <GainText value={data.day_change} pct={data.day_change_pct} />
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Last updated indicator */}
      {dataUpdatedAt > 0 && (
        <p className="text-xs text-muted-foreground text-right">
          {isPlaceholderData
            ? "Refreshing..."
            : `Updated ${new Date(dataUpdatedAt).toLocaleTimeString()}`}
        </p>
      )}

      {/* Holdings table */}
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Symbol</TableHead>
              <TableHead className="hidden md:table-cell">Shares</TableHead>
              <TableHead className="text-right">Price</TableHead>
              <TableHead className="text-right">Market Value</TableHead>
              <TableHead className="text-right">Gain/Loss</TableHead>
              <TableHead className="text-right hidden md:table-cell">Day Change</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.holdings.map((h) => (
              <TableRow key={h.id}>
                <TableCell>
                  <div className="font-medium">{h.symbol}</div>
                  <div className="text-xs text-muted-foreground hidden sm:block">{h.name}</div>
                </TableCell>
                <TableCell className="hidden md:table-cell">
                  {parseFloat(h.shares).toLocaleString()}
                </TableCell>
                <TableCell className="text-right">
                  {h.current_price ? formatCurrency(h.current_price) : "—"}
                </TableCell>
                <TableCell className="text-right">{formatCurrency(h.market_value)}</TableCell>
                <TableCell className="text-right">
                  <GainText value={h.unrealized_gain} pct={h.unrealized_gain_pct} />
                </TableCell>
                <TableCell className="text-right hidden md:table-cell">
                  <GainText value={h.day_change} pct={h.day_change_pct} />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
