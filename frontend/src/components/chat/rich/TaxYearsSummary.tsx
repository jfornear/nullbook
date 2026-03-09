import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatCurrency } from "@/lib/utils";

interface TaxData {
  tax_years: {
    id: number;
    year: number;
    filing_status: string;
    document_count: number;
    total_document_income: string;
    deduction_count: number;
    total_deductions: string;
  }[];
  total: number;
}

export function TaxYearsSummary({ data }: { data: unknown }) {
  const { tax_years } = data as TaxData;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Tax Years ({tax_years.length})</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {tax_years.map((ty) => (
            <div
              key={ty.id}
              className="flex items-center justify-between rounded-md border px-3 py-2"
            >
              <div>
                <div className="text-sm font-medium">{ty.year}</div>
                <div className="flex gap-2 text-xs text-muted-foreground">
                  <span>{ty.document_count} docs</span>
                  <span>{ty.deduction_count} deductions</span>
                </div>
              </div>
              <div className="text-right">
                <Badge variant="secondary" className="text-xs">
                  {ty.filing_status.replace(/_/g, " ")}
                </Badge>
                {parseFloat(ty.total_deductions) > 0 && (
                  <div className="text-xs text-muted-foreground mt-0.5">
                    {formatCurrency(ty.total_deductions)} deducted
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
