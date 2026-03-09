import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Calculator, AlertTriangle } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

interface BracketDetail {
  bracket: string;
  rate: string;
  tax: string;
}

interface TaxEstimateData {
  tax_year: number;
  filing_status: string;
  gross_income: string;
  agi: string;
  taxable_income: string;
  standard_deduction: string;
  itemized_deduction: string;
  deduction_used: string;
  bracket_details: BracketDetail[];
  ordinary_tax: string;
  ltcg_tax: string;
  self_employment_tax: string;
  qbi_deduction: string;
  amt_estimate: string;
  total_tax: string;
  total_withheld: string;
  amount_owed: string;
  effective_rate: string;
  marginal_rate: string;
}

const BRACKET_COLORS = [
  "#22c55e",
  "#84cc16",
  "#eab308",
  "#f97316",
  "#ef4444",
  "#dc2626",
  "#991b1b",
];

export function TaxEstimateCard({ data }: { data: unknown }) {
  const d = data as TaxEstimateData;
  const amountOwed = parseFloat(d.amount_owed);
  const isRefund = amountOwed < 0;
  const seTax = parseFloat(d.self_employment_tax);
  const qbi = parseFloat(d.qbi_deduction);
  const amt = parseFloat(d.amt_estimate);

  const bracketData = d.bracket_details.map((b) => ({
    name: `${(parseFloat(b.rate) * 100).toFixed(0)}%`,
    income: parseFloat(b.bracket),
    tax: parseFloat(b.tax),
  }));

  const fmt = (v: string) =>
    "$" +
    parseFloat(v).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-sm">
            <Calculator className="h-4 w-4" />
            {d.tax_year} Federal Tax Estimate
          </CardTitle>
          <Badge variant="outline" className="text-xs capitalize">
            {d.filing_status.replace("_", " ")}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        {/* Bottom line */}
        <div
          className={`rounded-lg p-3 text-center ${isRefund ? "bg-green-50 dark:bg-green-950" : "bg-red-50 dark:bg-red-950"}`}
        >
          <div className="text-xs text-muted-foreground mb-1">
            {isRefund ? "Estimated Refund" : "Estimated Amount Owed"}
          </div>
          <div className={`text-2xl font-bold ${isRefund ? "text-green-600" : "text-red-600"}`}>
            {isRefund ? "+" : ""}
            {fmt(d.amount_owed)}
          </div>
        </div>

        {/* Income summary */}
        <div className="space-y-1">
          <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Income
          </div>
          <div className="flex justify-between">
            <span>Gross Income</span>
            <span className="font-medium">{fmt(d.gross_income)}</span>
          </div>
          <div className="flex justify-between">
            <span>AGI</span>
            <span className="font-medium">{fmt(d.agi)}</span>
          </div>
          <div className="flex justify-between">
            <span>Taxable Income</span>
            <span className="font-medium">{fmt(d.taxable_income)}</span>
          </div>
        </div>

        {/* Deduction comparison */}
        <div className="space-y-1">
          <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Deductions
          </div>
          <div className="flex justify-between">
            <span>Standard Deduction</span>
            <span
              className={
                d.deduction_used === "standard"
                  ? "font-semibold text-green-600"
                  : "text-muted-foreground"
              }
            >
              {fmt(d.standard_deduction)} {d.deduction_used === "standard" && "✓"}
            </span>
          </div>
          <div className="flex justify-between">
            <span>Itemized Deductions</span>
            <span
              className={
                d.deduction_used === "itemized"
                  ? "font-semibold text-green-600"
                  : "text-muted-foreground"
              }
            >
              {fmt(d.itemized_deduction)} {d.deduction_used === "itemized" && "✓"}
            </span>
          </div>
          {qbi > 0 && (
            <div className="flex justify-between">
              <span>QBI Deduction (Sec. 199A)</span>
              <span className="font-medium text-green-600">-{fmt(d.qbi_deduction)}</span>
            </div>
          )}
        </div>

        {/* Bracket chart */}
        {bracketData.length > 0 && (
          <div>
            <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
              Tax Brackets
            </div>
            <div className="h-32">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={bracketData}>
                  <XAxis dataKey="name" className="text-[10px]" />
                  <YAxis
                    tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
                    className="text-[10px]"
                  />
                  <Tooltip
                    formatter={(v: number, name: string) => [
                      `$${v.toLocaleString("en-US", { minimumFractionDigits: 2 })}`,
                      name === "tax" ? "Tax" : "Income",
                    ]}
                  />
                  <Bar dataKey="tax" radius={[4, 4, 0, 0]}>
                    {bracketData.map((_, i) => (
                      <Cell key={i} fill={BRACKET_COLORS[i % BRACKET_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Tax breakdown */}
        <div className="space-y-1">
          <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Tax Breakdown
          </div>
          <div className="flex justify-between">
            <span>Ordinary Income Tax</span>
            <span>{fmt(d.ordinary_tax)}</span>
          </div>
          {parseFloat(d.ltcg_tax) > 0 && (
            <div className="flex justify-between">
              <span>LTCG / Qualified Dividends Tax</span>
              <span>{fmt(d.ltcg_tax)}</span>
            </div>
          )}
          {seTax > 0 && (
            <div className="flex justify-between">
              <span>Self-Employment Tax</span>
              <span>{fmt(d.self_employment_tax)}</span>
            </div>
          )}
          {amt > 0 && (
            <div className="flex justify-between text-amber-600">
              <span className="flex items-center gap-1">
                <AlertTriangle className="h-3 w-3" /> AMT
              </span>
              <span>{fmt(d.amt_estimate)}</span>
            </div>
          )}
          <div className="flex justify-between border-t pt-1 font-semibold">
            <span>Total Federal Tax</span>
            <span>{fmt(d.total_tax)}</span>
          </div>
          <div className="flex justify-between">
            <span>Total Withheld</span>
            <span className="text-green-600">-{fmt(d.total_withheld)}</span>
          </div>
        </div>

        {/* Rates */}
        <div className="flex gap-4 text-xs text-muted-foreground">
          <span>
            Effective Rate:{" "}
            <strong className="text-foreground">{parseFloat(d.effective_rate).toFixed(1)}%</strong>
          </span>
          <span>
            Marginal Rate:{" "}
            <strong className="text-foreground">{parseFloat(d.marginal_rate).toFixed(0)}%</strong>
          </span>
        </div>

        <div className="text-[10px] text-muted-foreground italic">
          This is an estimate only. Consult a tax professional for official filing.
        </div>
      </CardContent>
    </Card>
  );
}
