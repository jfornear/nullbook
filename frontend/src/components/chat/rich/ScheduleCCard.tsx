import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText } from "lucide-react";

interface ExpenseCategory {
  category: string;
  amount: string;
}

interface ScheduleCData {
  tax_year: number;
  business_name: string;
  gross_income: string;
  expenses: ExpenseCategory[];
  total_expenses: string;
  net_profit: string;
  se_tax_estimate: string;
}

export function ScheduleCCard({ data }: { data: unknown }) {
  const d = data as ScheduleCData;

  const fmt = (v: string) =>
    "$" +
    parseFloat(v).toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });

  const netProfit = parseFloat(d.net_profit);
  const isLoss = netProfit < 0;

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-sm">
            <FileText className="h-4 w-4" />
            {d.tax_year} Schedule C
          </CardTitle>
          {d.business_name && (
            <Badge variant="outline" className="text-xs">
              {d.business_name}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        {/* Gross Income */}
        <div className="flex justify-between rounded-md bg-muted/50 px-3 py-2 font-semibold">
          <span>Gross Income</span>
          <span>{fmt(d.gross_income)}</span>
        </div>

        {/* Expenses by Category */}
        <div className="space-y-1">
          <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Business Expenses
          </div>
          {d.expenses.map((exp) => (
            <div key={exp.category} className="flex justify-between px-1">
              <span className="text-muted-foreground">{exp.category}</span>
              <span className="font-medium">{fmt(exp.amount)}</span>
            </div>
          ))}
          <div className="flex justify-between border-t pt-1 font-semibold">
            <span>Total Expenses</span>
            <span>{fmt(d.total_expenses)}</span>
          </div>
        </div>

        {/* Net Profit / Loss */}
        <div
          className={`rounded-lg p-3 text-center ${
            isLoss ? "bg-red-50 dark:bg-red-950" : "bg-green-50 dark:bg-green-950"
          }`}
        >
          <div className="text-xs text-muted-foreground mb-1">Net {isLoss ? "Loss" : "Profit"}</div>
          <div className={`text-xl font-bold ${isLoss ? "text-red-600" : "text-green-600"}`}>
            {fmt(d.net_profit)}
          </div>
        </div>

        {/* SE Tax Estimate */}
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>Estimated Self-Employment Tax</span>
          <span className="font-medium text-foreground">{fmt(d.se_tax_estimate)}</span>
        </div>

        <div className="text-[10px] text-muted-foreground italic">
          Draft Schedule C summary. Review with a tax professional before filing.
        </div>
      </CardContent>
    </Card>
  );
}
