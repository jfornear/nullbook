import { useState, useRef, useCallback } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Upload, CheckCircle2, AlertCircle, Loader2, BadgeCheck } from "lucide-react";
import { api } from "@/lib/api";
import type { Account, PaginatedResponse, UploadPreview, ImportExecuteResult } from "@/types";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import AddAccountDialog from "@/components/accounts/AddAccountDialog";

type Step = "select" | "preview" | "result";

const COLUMN_OPTIONS = [
  { value: "", label: "Skip" },
  { value: "date", label: "Date" },
  { value: "amount", label: "Amount" },
  { value: "description", label: "Description" },
  { value: "category", label: "Category" },
  { value: "notes", label: "Notes" },
];

function splitCSVLine(line: string): string[] {
  const fields: string[] = [];
  let current = "";
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (inQuotes) {
      if (ch === '"') {
        if (i + 1 < line.length && line[i + 1] === '"') {
          current += '"';
          i++; // skip escaped quote
        } else {
          inQuotes = false;
        }
      } else {
        current += ch;
      }
    } else if (ch === '"') {
      inQuotes = true;
    } else if (ch === ",") {
      fields.push(current.trim());
      current = "";
    } else {
      current += ch;
    }
  }
  fields.push(current.trim());
  return fields;
}

function parseCSV(text: string): { headers: string[]; rows: Record<string, string>[] } {
  const lines = text.split("\n").filter((l) => l.trim());
  if (lines.length === 0) return { headers: [], rows: [] };
  const headers = splitCSVLine(lines[0]);
  const rows = lines.slice(1).map((line) => {
    const values = splitCSVLine(line);
    const row: Record<string, string> = {};
    headers.forEach((h, i) => {
      row[h] = values[i] || "";
    });
    return row;
  });
  return { headers, rows };
}

export default function ImportUploadFlow() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [step, setStep] = useState<Step>("select");
  const [file, setFile] = useState<File | null>(null);
  const [accountId, setAccountId] = useState("");
  const [preview, setPreview] = useState<UploadPreview | null>(null);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [parsedRows, setParsedRows] = useState<Record<string, string>[]>([]);
  const [result, setResult] = useState<ImportExecuteResult | null>(null);
  const [error, setError] = useState("");
  const [showAddAccount, setShowAddAccount] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);

  const { data: accountsData } = useQuery({
    queryKey: ["accounts"],
    queryFn: () => api.get<PaginatedResponse<Account>>("/accounts/accounts/"),
  });

  const IMPORTABLE_TYPES = ["checking", "savings", "credit_card"];
  const accounts = (accountsData?.results || []).filter((a) =>
    IMPORTABLE_TYPES.includes(a.account_type)
  );

  const uploadMutation = useMutation({
    mutationFn: async (formData: FormData) => {
      return api.upload<UploadPreview>("/imports/batches/upload/", formData);
    },
    onSuccess: (data) => {
      setPreview(data);
      setMapping(data.detected_mapping || {});
      // For non-CSV formats, the backend returns all rows; use those
      if (data.rows) {
        setParsedRows(data.rows);
      }
      setStep("preview");
      toast.success("File uploaded");
    },
    onError: (err: Error) => setError(err.message),
  });

  const executeMutation = useMutation({
    mutationFn: async () => {
      if (!preview) throw new Error("No preview data");
      return api.post<ImportExecuteResult>(`/imports/batches/${preview.batch_id}/execute/`, {
        mapping,
        rows: parsedRows,
      });
    },
    onSuccess: (data) => {
      setResult(data);
      setStep("result");
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["import-batches"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success(`${data.imported_count} transactions imported`);
    },
    onError: (err: Error) => setError(err.message),
  });

  function processFile(selected: File) {
    setFile(selected);
    setError("");
    const reader = new FileReader();
    reader.onload = (evt) => {
      const text = evt.target?.result as string;
      const { rows } = parseCSV(text);
      setParsedRows(rows);
    };
    reader.readAsText(selected);
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const selected = e.target.files?.[0];
    if (selected) processFile(selected);
  }

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const dropped = e.dataTransfer.files[0];
    const ext = dropped?.name.split(".").pop()?.toLowerCase();
    if (dropped && ext && ["csv", "ofx", "qfx", "qif"].includes(ext)) {
      processFile(dropped);
    }
  }, []);

  function handleUpload() {
    if (!file || !accountId) return;
    setError("");
    const formData = new FormData();
    formData.append("file", file);
    formData.append("account", accountId);
    uploadMutation.mutate(formData);
  }

  function getInternalFieldForHeader(csvHeader: string): string {
    for (const [internal, csv] of Object.entries(mapping)) {
      if (csv === csvHeader) return internal;
    }
    return "";
  }

  function handleMappingChange(csvHeader: string, newInternalField: string) {
    setMapping((prev) => {
      const next = { ...prev };
      for (const [key, val] of Object.entries(next)) {
        if (val === csvHeader) {
          delete next[key];
          break;
        }
      }
      if (newInternalField) {
        delete next[newInternalField];
        next[newInternalField] = csvHeader;
      }
      return next;
    });
  }

  // Validation: check if date and amount are mapped
  const mappedFields = new Set(Object.keys(mapping));
  const hasMissingRequired = !mappedFields.has("date") || !mappedFields.has("amount");

  function handleReset() {
    setStep("select");
    setFile(null);
    setAccountId("");
    setPreview(null);
    setMapping({});
    setParsedRows([]);
    setResult(null);
    setError("");
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  const isProcessing = uploadMutation.isPending || executeMutation.isPending;

  if (step === "result" && result) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col items-center text-center py-6">
            {result.error_count === 0 ? (
              <CheckCircle2 className="mb-4 h-10 w-10 text-green-600" />
            ) : (
              <AlertCircle className="mb-4 h-10 w-10 text-yellow-600" />
            )}
            <p className="text-lg font-medium">Import Complete</p>
            <p className="mt-1 text-sm text-muted-foreground">
              {result.imported_count} transactions imported
              {result.error_count > 0 && `, ${result.error_count} errors`}
            </p>
            {result.errors.length > 0 && (
              <div className="mt-4 w-full max-w-md rounded-lg bg-destructive/10 p-3 text-left">
                {result.errors.slice(0, 5).map((err, i) => (
                  <p key={i} className="text-sm text-destructive">
                    {err}
                  </p>
                ))}
              </div>
            )}
            <Button className="mt-6" onClick={handleReset}>
              Import Another File
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (step === "preview" && preview) {
    return (
      <Card>
        <CardContent className="relative pt-6 space-y-4">
          {isProcessing && (
            <div className="absolute inset-0 z-10 flex items-center justify-center rounded-lg bg-background/80">
              <div className="flex items-center gap-2">
                <Loader2 className="h-5 w-5 animate-spin" />
                <span className="text-sm font-medium">Importing...</span>
              </div>
            </div>
          )}
          <div>
            <div className="flex items-center gap-2">
              <p className="font-medium">{preview.file_name}</p>
              {preview.bank_profile_name && (
                <Badge variant="default" className="bg-green-600 hover:bg-green-700">
                  <BadgeCheck className="mr-1 h-3 w-3" />
                  Detected: {preview.bank_profile_name}
                </Badge>
              )}
            </div>
            <p className="text-sm text-muted-foreground">
              {preview.row_count} rows detected.{" "}
              {preview.bank_profile
                ? "Column mapping auto-configured. Review and import."
                : "Map columns below, then import."}
            </p>
          </div>

          {!preview.bank_profile && (
            <div className="grid gap-3 sm:grid-cols-3">
              {preview.headers.map((header) => (
                <div key={header} className="grid gap-1.5">
                  <Label className="text-xs">{header}</Label>
                  <Select
                    value={getInternalFieldForHeader(header)}
                    onValueChange={(v) => handleMappingChange(header, v)}
                  >
                    <SelectTrigger className="h-8 text-xs">
                      <SelectValue placeholder="Skip" />
                    </SelectTrigger>
                    <SelectContent>
                      {COLUMN_OPTIONS.map((opt) => (
                        <SelectItem key={opt.value} value={opt.value}>
                          {opt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              ))}
            </div>
          )}

          {hasMissingRequired && (
            <div className="rounded-lg border border-yellow-500/50 bg-yellow-50 p-3 text-sm text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-200">
              Both "Date" and "Amount" columns must be mapped before importing.
            </div>
          )}

          <div className="overflow-x-auto rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  {preview.headers.map((h) => (
                    <TableHead key={h} className="text-xs whitespace-nowrap">
                      {h}
                    </TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {preview.preview.slice(0, 5).map((row, i) => (
                  <TableRow key={i}>
                    {preview.headers.map((h) => (
                      <TableCell key={h} className="text-xs whitespace-nowrap">
                        {row[h]}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}

          <div className="flex gap-3">
            <Button variant="outline" onClick={handleReset}>
              Back
            </Button>
            <Button
              onClick={() => executeMutation.mutate()}
              disabled={executeMutation.isPending || hasMissingRequired}
            >
              {executeMutation.isPending ? "Importing..." : `Import ${preview.row_count} Rows`}
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Step: select
  return (
    <>
      <Card>
        <CardContent className="relative pt-6 space-y-4">
          {isProcessing && (
            <div className="absolute inset-0 z-10 flex items-center justify-center rounded-lg bg-background/80">
              <div className="flex items-center gap-2">
                <Loader2 className="h-5 w-5 animate-spin" />
                <span className="text-sm font-medium">Uploading...</span>
              </div>
            </div>
          )}
          <div
            onClick={() => fileInputRef.current?.click()}
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragOver(true);
            }}
            onDragEnter={(e) => {
              e.preventDefault();
              setIsDragOver(true);
            }}
            onDragLeave={() => setIsDragOver(false)}
            onDrop={handleDrop}
            className={cn(
              "flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-12 text-center transition-colors",
              isDragOver
                ? "border-primary bg-primary/5"
                : "border-muted-foreground/25 hover:border-muted-foreground/50"
            )}
          >
            <Upload className="mb-4 h-10 w-10 text-muted-foreground" />
            {file ? (
              <>
                <p className="text-lg font-medium">{file.name}</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  Click to choose a different file
                </p>
              </>
            ) : (
              <>
                <p className="text-lg font-medium">Drop a file here or click to browse</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  Supports CSV, OFX, QFX, and QIF formats from banks and brokerages
                </p>
              </>
            )}
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.ofx,.qfx,.qif"
              className="hidden"
              onChange={handleFileChange}
            />
          </div>

          {file && (
            <div className="space-y-3">
              <div className="grid gap-2">
                <Label htmlFor="importAccount">Target Account</Label>
                {accounts.length === 0 ? (
                  <div className="rounded-md border border-dashed p-3 text-sm text-muted-foreground">
                    No checking, savings, or credit card accounts to import into.{" "}
                    <button
                      type="button"
                      className="text-primary underline underline-offset-4 hover:text-primary/80"
                      onClick={() => setShowAddAccount(true)}
                    >
                      Add one first
                    </button>
                    .
                  </div>
                ) : (
                  <Select value={accountId} onValueChange={setAccountId}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select account to import into" />
                    </SelectTrigger>
                    <SelectContent>
                      {accounts.map((a) => (
                        <SelectItem key={a.id} value={String(a.id)}>
                          {a.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              </div>
              {error && <p className="text-sm text-destructive">{error}</p>}
              <Button onClick={handleUpload} disabled={!accountId || uploadMutation.isPending}>
                {uploadMutation.isPending ? "Uploading..." : "Upload & Preview"}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
      <AddAccountDialog open={showAddAccount} onOpenChange={setShowAddAccount} />
    </>
  );
}
