import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatCurrency } from "@/lib/utils";

interface SecurityData {
  symbol: string;
  name: string;
  security_type: string;
  exchange: string;
  current_price: string | null;
  market_cap: number | null;
  pe_ratio: number | null;
  dividend_yield: number | null;
}

export function SecurityLookupCard({ data }: { data: unknown }) {
  const s = data as SecurityData;

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm">
            {s.symbol} - {s.name}
          </CardTitle>
          <Badge variant="secondary">{s.security_type}</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-3 text-sm">
          {s.current_price && (
            <div>
              <div className="text-xs text-muted-foreground">Price</div>
              <div className="font-semibold">{formatCurrency(s.current_price)}</div>
            </div>
          )}
          {s.exchange && (
            <div>
              <div className="text-xs text-muted-foreground">Exchange</div>
              <div>{s.exchange}</div>
            </div>
          )}
          {s.market_cap != null && (
            <div>
              <div className="text-xs text-muted-foreground">Market Cap</div>
              <div>
                {s.market_cap >= 1e12
                  ? `$${(s.market_cap / 1e12).toFixed(2)}T`
                  : s.market_cap >= 1e9
                    ? `$${(s.market_cap / 1e9).toFixed(2)}B`
                    : `$${(s.market_cap / 1e6).toFixed(2)}M`}
              </div>
            </div>
          )}
          {s.pe_ratio != null && (
            <div>
              <div className="text-xs text-muted-foreground">P/E Ratio</div>
              <div>{s.pe_ratio.toFixed(2)}</div>
            </div>
          )}
          {s.dividend_yield != null && (
            <div>
              <div className="text-xs text-muted-foreground">Dividend Yield</div>
              <div>{(s.dividend_yield * 100).toFixed(2)}%</div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
