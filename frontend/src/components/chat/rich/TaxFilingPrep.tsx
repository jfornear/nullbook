import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileCheck, CheckCircle2, Circle, ArrowRight } from "lucide-react";

interface Document {
  name: string;
  status: string;
  source: string;
}

interface Deduction {
  type: string;
  amount: string;
  status: string;
}

interface TaxEstimate {
  total_income: string;
  total_deductions: string;
  estimated_tax: string;
  amount_owed: string;
}

interface NextStep {
  step: string;
  description: string;
}

interface TaxFilingPrepData {
  tax_year: number;
  filing_status: string;
  documents: Document[];
  deductions: Deduction[];
  tax_estimate: TaxEstimate;
  next_steps: NextStep[];
}

export function TaxFilingPrep({ data }: { data: unknown }) {
  const d = data as TaxFilingPrepData;

  const fmt = (v: string) =>
    "$" +
    parseFloat(v).toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });

  const amountOwed = parseFloat(d.tax_estimate.amount_owed);
  const isRefund = amountOwed < 0;

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-sm">
            <FileCheck className="h-4 w-4" />
            {d.tax_year} Tax Filing Prep
          </CardTitle>
          <Badge variant="outline" className="text-xs capitalize">
            {d.filing_status.replace(/_/g, " ")}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        {/* Documents */}
        {d.documents && d.documents.length > 0 && (
          <div className="space-y-1">
            <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Documents
            </div>
            {d.documents.map((doc, i) => {
              const isReady = doc.status === "received" || doc.status === "complete";
              return (
                <div key={i} className="flex items-center gap-2 rounded-md px-2 py-1.5">
                  {isReady ? (
                    <CheckCircle2 className="h-3.5 w-3.5 text-green-600 shrink-0" />
                  ) : (
                    <Circle className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                  )}
                  <div className="flex-1 min-w-0">
                    <span className="font-medium">{doc.name}</span>
                    <span className="ml-2 text-xs text-muted-foreground">{doc.source}</span>
                  </div>
                  <Badge
                    variant={isReady ? "default" : "secondary"}
                    className="text-[10px] capitalize"
                  >
                    {doc.status}
                  </Badge>
                </div>
              );
            })}
          </div>
        )}

        {/* Deductions */}
        {d.deductions && d.deductions.length > 0 && (
          <div className="space-y-1">
            <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Deductions
            </div>
            {d.deductions.map((ded, i) => (
              <div key={i} className="flex items-center justify-between px-2 py-1">
                <div className="flex items-center gap-2">
                  <span>{ded.type}</span>
                  <Badge
                    variant={ded.status === "verified" ? "default" : "outline"}
                    className="text-[10px] capitalize"
                  >
                    {ded.status}
                  </Badge>
                </div>
                <span className="font-medium">{fmt(ded.amount)}</span>
              </div>
            ))}
          </div>
        )}

        {/* Tax Estimate */}
        <div className="space-y-1">
          <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Tax Estimate
          </div>
          <div className="flex justify-between">
            <span>Total Income</span>
            <span className="font-medium">{fmt(d.tax_estimate.total_income)}</span>
          </div>
          <div className="flex justify-between">
            <span>Total Deductions</span>
            <span className="font-medium text-green-600">
              -{fmt(d.tax_estimate.total_deductions)}
            </span>
          </div>
          <div className="flex justify-between">
            <span>Estimated Tax</span>
            <span className="font-medium">{fmt(d.tax_estimate.estimated_tax)}</span>
          </div>
          <div
            className={`flex justify-between border-t pt-1 font-semibold ${
              isRefund ? "text-green-600" : "text-red-600"
            }`}
          >
            <span>{isRefund ? "Estimated Refund" : "Estimated Owed"}</span>
            <span>
              {isRefund ? "+" : ""}
              {fmt(d.tax_estimate.amount_owed)}
            </span>
          </div>
        </div>

        {/* Next Steps */}
        {d.next_steps && d.next_steps.length > 0 && (
          <div className="space-y-1.5">
            <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Next Steps
            </div>
            {d.next_steps.map((step, i) => (
              <div key={i} className="flex items-start gap-2 rounded-md bg-muted/50 px-3 py-2">
                <ArrowRight className="h-3.5 w-3.5 mt-0.5 shrink-0 text-muted-foreground" />
                <div>
                  <div className="font-medium text-xs">{step.step}</div>
                  <div className="text-xs text-muted-foreground">{step.description}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
