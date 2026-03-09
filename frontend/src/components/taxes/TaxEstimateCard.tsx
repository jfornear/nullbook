import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

interface TaxBreakdown {
  gross_income: string;
  agi: string;
  taxable_income: string;
  standard_deduction: string;
  itemized_deduction: string;
  deduction_used: string;
  ordinary_tax: string;
  ltcg_tax: string;
  self_employment_tax: string;
  total_tax: string;
  total_withheld: string;
  amount_owed: string;
  effective_rate: string;
  marginal_rate: string;
}

interface TaxEstimate {
  tax_year: number;
  filing_status: string;
  total_income: string;
  total_deductions: string;
  tax_breakdown: TaxBreakdown;
  document_count: number;
  deduction_count: number;
}

interface Props {
  taxYearId: number;
}

export function TaxEstimateCard({ taxYearId }: Props) {
  const { data, isLoading } = useQuery({
    queryKey: ["tax-estimate", taxYearId],
    queryFn: () => api.get<TaxEstimate>(`/taxes/tax-years/${taxYearId}/estimate/`),
  });

  if (isLoading) {
    return <Skeleton className="h-48 w-full" />;
  }

  if (!data || data.document_count === 0) {
    return (
      <Card>
        <CardContent className="py-4 text-center text-sm text-muted-foreground">
          Add income documents to see your tax estimate.
        </CardContent>
      </Card>
    );
  }

  const tb = data.tax_breakdown;
  const amountOwed = parseFloat(tb.amount_owed);
  const isRefund = amountOwed < 0;

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm">Tax Estimate</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
          <Row label="Gross Income" value={formatCurrency(tb.gross_income)} />
          <Row label="AGI" value={formatCurrency(tb.agi)} />
          <Row
            label={`Deduction (${tb.deduction_used})`}
            value={formatCurrency(
              tb.deduction_used === "itemized" ? tb.itemized_deduction : tb.standard_deduction
            )}
          />
          <Row label="Taxable Income" value={formatCurrency(tb.taxable_income)} />
        </div>

        <div className="border-t pt-2 grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
          <Row label="Ordinary Tax" value={formatCurrency(tb.ordinary_tax)} />
          <Row label="LTCG Tax" value={formatCurrency(tb.ltcg_tax)} />
          <Row label="SE Tax" value={formatCurrency(tb.self_employment_tax)} />
          <Row label="Total Tax" value={formatCurrency(tb.total_tax)} bold />
        </div>

        <div className="border-t pt-2 grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
          <Row label="Withheld" value={formatCurrency(tb.total_withheld)} />
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground font-medium">
              {isRefund ? "Refund" : "Owed"}
            </span>
            <span className={`font-bold ${isRefund ? "text-green-600" : "text-red-600"}`}>
              {isRefund ? `+${formatCurrency(Math.abs(amountOwed))}` : formatCurrency(amountOwed)}
            </span>
          </div>
        </div>

        <div className="border-t pt-2 flex gap-4 text-xs text-muted-foreground">
          <span>Effective Rate: {tb.effective_rate}%</span>
          <span>Marginal Rate: {tb.marginal_rate}%</span>
        </div>
      </CardContent>
    </Card>
  );
}

function Row({ label, value, bold }: { label: string; value: string; bold?: boolean }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-muted-foreground">{label}</span>
      <span className={bold ? "font-bold" : ""}>{value}</span>
    </div>
  );
}
