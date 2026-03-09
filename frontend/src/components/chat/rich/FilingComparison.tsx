import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Scale, Check } from "lucide-react";

interface ComparisonEntry {
  filing_status: string;
  filing_status_display: string;
  total_tax: string;
  amount_owed: string;
  effective_rate: string;
  taxable_income: string;
  deduction_used: string;
  standard_deduction: string;
  itemized_deduction: string;
}

interface FilingComparisonData {
  tax_year: number;
  comparisons: ComparisonEntry[];
  optimal_status: string;
}

export function FilingComparison({ data }: { data: unknown }) {
  const d = data as FilingComparisonData;

  const fmt = (v: string) =>
    "$" +
    parseFloat(v).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-sm">
          <Scale className="h-4 w-4" />
          {d.tax_year} Filing Status Comparison
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          {d.comparisons.map((c) => {
            const isOptimal = c.filing_status === d.optimal_status;
            const amountOwed = parseFloat(c.amount_owed);
            const isRefund = amountOwed < 0;

            return (
              <div
                key={c.filing_status}
                className={`rounded-lg border p-3 text-sm ${
                  isOptimal ? "border-green-500 bg-green-50/50 dark:bg-green-950/30" : ""
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium">{c.filing_status_display}</span>
                  {isOptimal && (
                    <Badge variant="default" className="text-[10px] bg-green-600">
                      <Check className="h-2.5 w-2.5 mr-0.5" /> Best
                    </Badge>
                  )}
                </div>
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Total Tax</span>
                    <span className="font-medium">{fmt(c.total_tax)}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">{isRefund ? "Refund" : "Owed"}</span>
                    <span className={`font-medium ${isRefund ? "text-green-600" : "text-red-600"}`}>
                      {isRefund ? "+" : ""}
                      {fmt(c.amount_owed)}
                    </span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Effective Rate</span>
                    <span>{parseFloat(c.effective_rate).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Deduction</span>
                    <span className="capitalize">{c.deduction_used}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
        <div className="mt-2 text-[10px] text-muted-foreground italic">
          Estimate only. Your actual eligibility for each status depends on your household
          situation.
        </div>
      </CardContent>
    </Card>
  );
}
