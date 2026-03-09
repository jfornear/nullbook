import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp, TrendingDown, BarChart3 } from "lucide-react";
import { formatCurrency } from "@/lib/utils";

interface Holding {
  symbol: string;
  name: string;
  shares: string;
  cost_basis: string;
  market_value: string;
  unrealized_gain: string;
  unrealized_gain_pct: string;
  day_change: string;
  day_change_pct: string;
}

interface PortfolioPerformanceData {
  total_market_value: string;
  total_cost_basis: string;
  total_unrealized_gain: string;
  total_unrealized_gain_pct: string;
  total_day_change: string;
  total_day_change_pct: string;
  holdings: Holding[];
}

export function PortfolioPerformance({ data }: { data: unknown }) {
  const d = data as PortfolioPerformanceData;

  const totalGain = parseFloat(d.total_unrealized_gain);
  const totalDayChange = parseFloat(d.total_day_change);
  const isGain = totalGain >= 0;
  const isDayGain = totalDayChange >= 0;

  const fmt = (v: string) => formatCurrency(v);
  const pct = (v: string) => {
    const num = parseFloat(v);
    return (num >= 0 ? "+" : "") + num.toFixed(2) + "%";
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-sm">
          <BarChart3 className="h-4 w-4" />
          Portfolio Performance
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        {/* Summary Cards */}
        <div className="grid grid-cols-3 gap-2">
          <div className="rounded-md border p-2 text-center">
            <div className="text-[10px] text-muted-foreground uppercase">Market Value</div>
            <div className="text-sm font-semibold">{fmt(d.total_market_value)}</div>
          </div>
          <div
            className={`rounded-md border p-2 text-center ${
              isGain ? "bg-green-50/50 dark:bg-green-950/30" : "bg-red-50/50 dark:bg-red-950/30"
            }`}
          >
            <div className="text-[10px] text-muted-foreground uppercase">Unrealized</div>
            <div className={`text-sm font-semibold ${isGain ? "text-green-600" : "text-red-600"}`}>
              {fmt(d.total_unrealized_gain)}
            </div>
            <div className={`text-[10px] ${isGain ? "text-green-600" : "text-red-600"}`}>
              {pct(d.total_unrealized_gain_pct)}
            </div>
          </div>
          <div
            className={`rounded-md border p-2 text-center ${
              isDayGain ? "bg-green-50/50 dark:bg-green-950/30" : "bg-red-50/50 dark:bg-red-950/30"
            }`}
          >
            <div className="text-[10px] text-muted-foreground uppercase">Day Change</div>
            <div
              className={`text-sm font-semibold ${isDayGain ? "text-green-600" : "text-red-600"}`}
            >
              {fmt(d.total_day_change)}
            </div>
            <div className={`text-[10px] ${isDayGain ? "text-green-600" : "text-red-600"}`}>
              {pct(d.total_day_change_pct)}
            </div>
          </div>
        </div>

        {/* Holdings Table */}
        {d.holdings && d.holdings.length > 0 && (
          <div className="space-y-1">
            <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Holdings
            </div>
            {d.holdings.map((h) => {
              const gain = parseFloat(h.unrealized_gain);
              const holdingIsGain = gain >= 0;
              const GainIcon = holdingIsGain ? TrendingUp : TrendingDown;

              return (
                <div
                  key={h.symbol}
                  className="flex items-center justify-between rounded-md border px-3 py-2"
                >
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">{h.symbol}</span>
                      <span className="text-xs text-muted-foreground truncate">{h.name}</span>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {parseFloat(h.shares).toLocaleString()} shares
                    </div>
                  </div>
                  <div className="text-right ml-2">
                    <div className="text-sm font-medium">{fmt(h.market_value)}</div>
                    <div className="flex items-center justify-end gap-1">
                      <GainIcon
                        className={`h-3 w-3 ${holdingIsGain ? "text-green-600" : "text-red-600"}`}
                      />
                      <span
                        className={`text-xs font-medium ${
                          holdingIsGain ? "text-green-600" : "text-red-600"
                        }`}
                      >
                        {fmt(h.unrealized_gain)} ({pct(h.unrealized_gain_pct)})
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
