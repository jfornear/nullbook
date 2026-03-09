import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Receipt, DollarSign, Calendar } from "lucide-react";

interface ReceiptCardData {
  receipt_id: number;
  merchant: string;
  date: string | null;
  total_amount: string | null;
  deduction_type: string;
  tax_year: number;
  line_items?: { description: string; total_price: string }[];
}

export function ReceiptCard({ data }: { data: unknown }) {
  const d = data as ReceiptCardData;

  return (
    <Card className="border-green-200 dark:border-green-900">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-sm">
            <Receipt className="h-4 w-4 text-green-600" />
            Expense Created from Receipt
          </CardTitle>
          <Badge variant="outline" className="text-xs">
            {d.deduction_type}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        <div className="flex items-center justify-between">
          <span className="font-medium">{d.merchant}</span>
          {d.total_amount && (
            <span className="flex items-center gap-1 font-semibold text-green-600">
              <DollarSign className="h-3 w-3" />
              {parseFloat(d.total_amount).toLocaleString("en-US", {
                minimumFractionDigits: 2,
              })}
            </span>
          )}
        </div>
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          {d.date && (
            <span className="flex items-center gap-1">
              <Calendar className="h-3 w-3" /> {d.date}
            </span>
          )}
          <span>Tax Year {d.tax_year}</span>
        </div>
        {d.line_items && d.line_items.length > 0 && (
          <div className="mt-2 rounded-md border p-2">
            <div className="text-xs font-medium text-muted-foreground mb-1">Line Items</div>
            {d.line_items.map((item, i) => (
              <div key={i} className="flex justify-between text-xs">
                <span>{item.description}</span>
                <span>${parseFloat(item.total_price).toFixed(2)}</span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
