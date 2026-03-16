import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { FileText, FileSpreadsheet, Loader2, ChevronDown, Search } from "lucide-react";
import { api } from "@/lib/api";
import { QueryError } from "@/components/shared/QueryError";
import type { ImportBatch, PaginatedResponse } from "@/types";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { formatDate } from "@/lib/utils";
import ImportUploadFlow from "@/components/imports/ImportUploadFlow";
import { downloadGuides, type DownloadGuide } from "@/data/download-guides";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";

function BankGuideItem({ guide }: { guide: DownloadGuide }) {
  return (
    <Collapsible>
      <CollapsibleTrigger className="flex w-full items-center justify-between rounded-lg border p-3 text-left hover:bg-muted/50 transition-colors">
        <div>
          <span className="text-sm font-medium">{guide.institution}</span>
          <span className="ml-2 text-xs text-muted-foreground">{guide.accountType}</span>
        </div>
        <ChevronDown className="h-4 w-4 text-muted-foreground transition-transform [[data-state=open]_&]:rotate-180" />
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="border border-t-0 rounded-b-lg p-4 space-y-3">
          <div className="space-y-2">
            {guide.steps.map((step, i) => (
              <div key={i} className="flex items-start gap-2">
                <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary text-[10px] font-medium text-primary-foreground mt-0.5">
                  {i + 1}
                </div>
                <p className="text-sm">{step}</p>
              </div>
            ))}
          </div>
          {guide.tips.length > 0 && (
            <div className="rounded-lg bg-muted/50 p-3 space-y-1">
              {guide.tips.map((tip, i) => (
                <p key={i} className="text-xs text-muted-foreground">
                  {tip}
                </p>
              ))}
            </div>
          )}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}

export default function ImportPage() {
  const [guideSearch, setGuideSearch] = useState("");

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["import-batches"],
    queryFn: () => api.get<PaginatedResponse<ImportBatch>>("/imports/batches/"),
  });

  const batches = data?.results || [];

  const filteredGuides = useMemo(() => {
    if (!guideSearch) return downloadGuides;
    const q = guideSearch.toLowerCase();
    return downloadGuides.filter(
      (g) => g.institution.toLowerCase().includes(q) || g.accountType.toLowerCase().includes(q)
    );
  }, [guideSearch]);

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

      <Card>
        <CardHeader>
          <CardTitle>How to export from your bank</CardTitle>
          <CardDescription>
            Step-by-step instructions for downloading transaction data from your institution.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search banks (Chase, Amex, Coinbase...)"
                value={guideSearch}
                onChange={(e) => setGuideSearch(e.target.value)}
                className="pl-9"
              />
            </div>

            {filteredGuides.map((guide) => (
              <BankGuideItem key={guide.id} guide={guide} />
            ))}

            {filteredGuides.length === 0 && (
              <div className="text-center py-4">
                <p className="text-sm text-muted-foreground">
                  No guides found for "{guideSearch}".
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  Most banks support CSV export — look for a "Download" or "Export" button in your
                  transaction history. nullbook auto-detects most column layouts.
                </p>
              </div>
            )}

            <div className="flex items-start gap-3 rounded-lg bg-muted/50 p-4">
              <FileSpreadsheet className="mt-0.5 h-5 w-5 shrink-0 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">Supported formats</p>
                <p className="text-sm text-muted-foreground">
                  CSV, OFX/QFX, and QIF files. nullbook auto-detects column layouts from Chase, Bank
                  of America, Amex, Capital One, Wells Fargo, and most other institutions.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

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
