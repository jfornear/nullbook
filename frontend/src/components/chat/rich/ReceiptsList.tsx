import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Receipt } from "lucide-react";

interface ReceiptItem {
  id: number;
  merchant: string;
  date: string | null;
  total_amount: string | null;
  category: string;
  status: string;
}

interface ReceiptsListData {
  receipts: ReceiptItem[];
  total: number;
}

const statusVariant: Record<string, "default" | "secondary" | "outline" | "destructive"> = {
  completed: "default",
  processing: "secondary",
  pending: "outline",
  failed: "destructive",
};

export function ReceiptsList({ data }: { data: unknown }) {
  const d = data as ReceiptsListData;

  if (!d.receipts || d.receipts.length === 0) {
    return (
      <Card>
        <CardContent className="py-4 text-center text-sm text-muted-foreground">
          No receipts found.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-sm">
          <Receipt className="h-4 w-4" />
          Receipts ({d.total})
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-1">
        {d.receipts.map((r) => (
          <div
            key={r.id}
            className="flex items-center justify-between rounded-md border px-3 py-2 text-sm"
          >
            <div className="flex-1 min-w-0">
              <div className="font-medium truncate">{r.merchant}</div>
              <div className="text-xs text-muted-foreground">
                {r.date || "No date"}
                {r.category ? ` · ${r.category}` : ""}
              </div>
            </div>
            <div className="flex items-center gap-2 ml-2">
              {r.total_amount && (
                <span className="text-sm font-medium">
                  ${parseFloat(r.total_amount).toFixed(2)}
                </span>
              )}
              <Badge variant={statusVariant[r.status] || "outline"} className="text-[10px]">
                {r.status}
              </Badge>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
