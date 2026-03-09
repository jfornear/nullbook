import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileDown } from "lucide-react";

interface IncomeSummary {
  wages: string;
  self_employment: string;
  investment: string;
  other: string;
  total: string;
}

interface DeductionsSummary {
  standard_deduction: string;
  itemized_total: string;
  deduction_used: string;
  deduction_amount: string;
}

interface TaxCalculation {
  taxable_income: string;
  total_tax: string;
  total_withheld: string;
  amount_owed: string;
  effective_rate: string;
}

interface TaxSummaryExportData {
  tax_year: number;
  format: string;
  income_summary: IncomeSummary;
  deductions_summary: DeductionsSummary;
  tax_calculation: TaxCalculation;
  csv_data?: string;
}

export function TaxSummaryExport({ data }: { data: unknown }) {
  const d = data as TaxSummaryExportData;

  const fmt = (v: string) =>
    "$" +
    parseFloat(v).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  const amountOwed = parseFloat(d.tax_calculation.amount_owed);
  const isRefund = amountOwed < 0;

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-sm">
            <FileDown className="h-4 w-4" />
            {d.tax_year} Tax Summary
          </CardTitle>
          <Badge variant="outline" className="text-xs uppercase">
            {d.format}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        {/* Income Summary */}
        <div className="space-y-1">
          <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Income
          </div>
          <div className="flex justify-between">
            <span>Wages</span>
            <span className="font-medium">{fmt(d.income_summary.wages)}</span>
          </div>
          <div className="flex justify-between">
            <span>Self-Employment</span>
            <span className="font-medium">{fmt(d.income_summary.self_employment)}</span>
          </div>
          <div className="flex justify-between">
            <span>Investment</span>
            <span className="font-medium">{fmt(d.income_summary.investment)}</span>
          </div>
          {parseFloat(d.income_summary.other) > 0 && (
            <div className="flex justify-between">
              <span>Other</span>
              <span className="font-medium">{fmt(d.income_summary.other)}</span>
            </div>
          )}
          <div className="flex justify-between border-t pt-1 font-semibold">
            <span>Total Income</span>
            <span>{fmt(d.income_summary.total)}</span>
          </div>
        </div>

        {/* Deductions Summary */}
        <div className="space-y-1">
          <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Deductions
          </div>
          <div className="flex justify-between">
            <span>Standard Deduction</span>
            <span
              className={
                d.deductions_summary.deduction_used === "standard"
                  ? "font-semibold text-green-600"
                  : "text-muted-foreground"
              }
            >
              {fmt(d.deductions_summary.standard_deduction)}
            </span>
          </div>
          <div className="flex justify-between">
            <span>Itemized Deductions</span>
            <span
              className={
                d.deductions_summary.deduction_used === "itemized"
                  ? "font-semibold text-green-600"
                  : "text-muted-foreground"
              }
            >
              {fmt(d.deductions_summary.itemized_total)}
            </span>
          </div>
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>Using</span>
            <span className="capitalize">{d.deductions_summary.deduction_used}</span>
          </div>
        </div>

        {/* Tax Calculation */}
        <div className="space-y-1">
          <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Tax Calculation
          </div>
          <div className="flex justify-between">
            <span>Taxable Income</span>
            <span className="font-medium">{fmt(d.tax_calculation.taxable_income)}</span>
          </div>
          <div className="flex justify-between">
            <span>Total Tax</span>
            <span className="font-medium">{fmt(d.tax_calculation.total_tax)}</span>
          </div>
          <div className="flex justify-between">
            <span>Total Withheld</span>
            <span className="font-medium text-green-600">
              -{fmt(d.tax_calculation.total_withheld)}
            </span>
          </div>
          <div
            className={`flex justify-between border-t pt-1 font-semibold ${
              isRefund ? "text-green-600" : "text-red-600"
            }`}
          >
            <span>{isRefund ? "Estimated Refund" : "Estimated Owed"}</span>
            <span>
              {isRefund ? "+" : ""}
              {fmt(d.tax_calculation.amount_owed)}
            </span>
          </div>
          <div className="text-xs text-muted-foreground">
            Effective Rate: {parseFloat(d.tax_calculation.effective_rate).toFixed(1)}%
          </div>
        </div>

        {/* CSV Preview */}
        {d.format === "csv" && d.csv_data && (
          <div>
            <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
              CSV Data
            </div>
            <pre className="rounded-md bg-muted p-3 text-xs overflow-x-auto max-h-48 overflow-y-auto">
              <code>{d.csv_data}</code>
            </pre>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
