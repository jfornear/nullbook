import { useQuery } from "@tanstack/react-query";
import { FileText, FileSpreadsheet, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { QueryError } from "@/components/shared/QueryError";
import type { ImportBatch, PaginatedResponse } from "@/types";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatDate } from "@/lib/utils";
import ImportUploadFlow from "@/components/imports/ImportUploadFlow";

const instructions = [
  { step: "1", text: "Log into your bank or credit card website" },
  { step: "2", text: 'Find the "Download" or "Export" option in your transaction history' },
  { step: "3", text: "Select CSV, OFX/QFX, or QIF format and your desired date range" },
  { step: "4", text: "Upload the file here and nullbook will auto-detect the column layout" },
];

export default function ImportPage() {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["import-batches"],
    queryFn: () => api.get<PaginatedResponse<ImportBatch>>("/imports/batches/"),
  });

  const batches = data?.results || [];

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (isError) {
    return <QueryError message={error?.message} onRetry={refetch} />;
  }

  return (
    <div className="space-y-6">
      <ImportUploadFlow />

      {batches.length === 0 && (
        <Card>
          <CardHeader>
            <CardTitle>How to export from your bank</CardTitle>
            <CardDescription>
              Most banks and credit cards let you download your transactions as a CSV file.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {instructions.map((item) => (
                <div key={item.step} className="flex items-start gap-3">
                  <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-medium text-primary-foreground">
                    {item.step}
                  </div>
                  <p className="text-sm pt-0.5">{item.text}</p>
                </div>
              ))}
            </div>
            <div className="mt-6 flex items-start gap-3 rounded-lg bg-muted/50 p-4">
              <FileSpreadsheet className="mt-0.5 h-5 w-5 shrink-0 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">Supported formats</p>
                <p className="text-sm text-muted-foreground">
                  CSV, OFX/QFX, and QIF files. nullbook auto-detects column layouts from Chase, Bank
                  of America, Amex, Capital One, Wells Fargo, and most other institutions.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {batches.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Import History</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {batches.map((batch) => (
                <div
                  key={batch.id}
                  className="flex items-center justify-between rounded-lg border p-3"
                >
                  <div className="flex items-center gap-3">
                    <FileText className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="text-sm font-medium">{batch.file_name}</p>
                      <p className="text-xs text-muted-foreground">
                        {batch.imported_count} of {batch.row_count} rows imported
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-muted-foreground">
                      {formatDate(batch.created_at)}
                    </span>
                    <Badge variant={batch.status === "completed" ? "default" : "secondary"}>
                      {batch.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
