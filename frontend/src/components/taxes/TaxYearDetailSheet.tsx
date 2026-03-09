import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Plus, Pencil, Trash2, CheckCircle2, Circle, Download } from "lucide-react";
import { api, getCsrfToken } from "@/lib/api";
import type { TaxYear, TaxDocument, DeductibleExpense } from "@/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { formatCurrency } from "@/lib/utils";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import AddTaxDocumentDialog from "./AddTaxDocumentDialog";
import AddDeductionDialog from "./AddDeductionDialog";
import { TaxEstimateCard } from "./TaxEstimateCard";

interface Props {
  taxYear: TaxYear | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onEdit: (ty: TaxYear) => void;
  onDelete: (ty: TaxYear) => void;
}

interface TaxYearDetail extends TaxYear {
  documents: TaxDocument[];
  deductions: DeductibleExpense[];
}

export function TaxYearDetailSheet({ taxYear, open, onOpenChange, onEdit, onDelete }: Props) {
  const queryClient = useQueryClient();
  const [docDialogOpen, setDocDialogOpen] = useState(false);
  const [editDoc, setEditDoc] = useState<TaxDocument | null>(null);
  const [deleteDoc, setDeleteDoc] = useState<TaxDocument | null>(null);
  const [dedDialogOpen, setDedDialogOpen] = useState(false);
  const [editDed, setEditDed] = useState<DeductibleExpense | null>(null);
  const [deleteDed, setDeleteDed] = useState<DeductibleExpense | null>(null);

  const { data: detail } = useQuery({
    queryKey: ["tax-year-detail", taxYear?.id],
    queryFn: () => api.get<TaxYearDetail>(`/taxes/tax-years/${taxYear!.id}/`),
    enabled: !!taxYear,
  });

  const deleteDocMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/taxes/documents/${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tax-year-detail", taxYear?.id] });
      queryClient.invalidateQueries({ queryKey: ["tax-estimate", taxYear?.id] });
      toast.success("Document deleted");
      setDeleteDoc(null);
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const deleteDedMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/taxes/deductions/${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tax-year-detail", taxYear?.id] });
      queryClient.invalidateQueries({ queryKey: ["tax-estimate", taxYear?.id] });
      toast.success("Deduction deleted");
      setDeleteDed(null);
    },
    onError: (err: Error) => toast.error(err.message),
  });

  async function handleExportCSV() {
    if (!taxYear) return;
    try {
      const csrfToken = getCsrfToken();
      const headers: Record<string, string> = {};
      if (csrfToken) headers["X-CSRFToken"] = csrfToken;
      const res = await fetch(
        `${import.meta.env.VITE_API_URL || ""}/api/taxes/tax-years/${taxYear.id}/export/`,
        { credentials: "include", headers }
      );
      if (!res.ok) throw new Error("Export failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `tax_summary_${taxYear.year}.csv`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success("CSV exported");
    } catch {
      toast.error("Failed to export CSV");
    }
  }

  if (!taxYear) return null;

  const documents = detail?.documents || [];
  const deductions = detail?.deductions || [];

  return (
    <>
      <Sheet open={open} onOpenChange={onOpenChange}>
        <SheetContent className="w-full sm:w-[480px] overflow-y-auto">
          <SheetHeader>
            <div className="flex items-center justify-between">
              <SheetTitle>{taxYear.year} Tax Year</SheetTitle>
              <div className="flex gap-1">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={handleExportCSV}
                  title="Export CSV"
                >
                  <Download className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => onEdit(taxYear)}
                >
                  <Pencil className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-destructive"
                  onClick={() => onDelete(taxYear)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </SheetHeader>

          <div className="mt-6 space-y-4">
            <div>
              <Badge variant="secondary">{taxYear.filing_status.replace(/_/g, " ")}</Badge>
            </div>

            {/* Tax Estimate */}
            <TaxEstimateCard taxYearId={taxYear.id} />

            <Separator />

            <div>
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-sm font-medium">Documents ({documents.length})</h3>
                <Button variant="outline" size="sm" onClick={() => setDocDialogOpen(true)}>
                  <Plus className="mr-1 h-3 w-3" />
                  Add
                </Button>
              </div>
              {documents.length === 0 ? (
                <p className="text-sm text-muted-foreground">No documents yet.</p>
              ) : (
                <div className="space-y-2">
                  {documents.map((doc) => (
                    <div
                      key={doc.id}
                      className="flex items-center justify-between rounded-lg border p-3"
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="text-xs">
                            {doc.document_type.toUpperCase()}
                          </Badge>
                          <span className="text-sm font-medium">{doc.issuer}</span>
                        </div>
                        <p className="mt-0.5 text-xs text-muted-foreground">
                          {formatCurrency(doc.amount)}
                        </p>
                      </div>
                      <div className="flex gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7"
                          onClick={() => setEditDoc(doc)}
                        >
                          <Pencil className="h-3 w-3" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 text-destructive"
                          onClick={() => setDeleteDoc(doc)}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <Separator />

            <div>
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-sm font-medium">Deductions ({deductions.length})</h3>
                <Button variant="outline" size="sm" onClick={() => setDedDialogOpen(true)}>
                  <Plus className="mr-1 h-3 w-3" />
                  Add
                </Button>
              </div>
              {deductions.length === 0 ? (
                <p className="text-sm text-muted-foreground">No deductions yet.</p>
              ) : (
                <div className="space-y-2">
                  {deductions.map((ded) => (
                    <div
                      key={ded.id}
                      className="flex items-center justify-between rounded-lg border p-3"
                    >
                      <div className="flex items-start gap-2">
                        {ded.is_verified ? (
                          <CheckCircle2 className="mt-0.5 h-4 w-4 text-green-600 shrink-0" />
                        ) : (
                          <Circle className="mt-0.5 h-4 w-4 text-muted-foreground shrink-0" />
                        )}
                        <div>
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className="text-xs">
                              {ded.deduction_type.replace(/_/g, " ")}
                            </Badge>
                            <span className="text-sm">{ded.description}</span>
                          </div>
                          <p className="mt-0.5 text-xs text-muted-foreground">
                            {formatCurrency(ded.amount)}
                          </p>
                        </div>
                      </div>
                      <div className="flex gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7"
                          onClick={() => setEditDed(ded)}
                        >
                          <Pencil className="h-3 w-3" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 text-destructive"
                          onClick={() => setDeleteDed(ded)}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </SheetContent>
      </Sheet>

      <AddTaxDocumentDialog
        open={docDialogOpen || !!editDoc}
        onOpenChange={(open) => {
          if (!open) {
            setDocDialogOpen(false);
            setEditDoc(null);
          }
        }}
        taxYearId={taxYear.id}
        editDocument={editDoc}
      />

      <AddDeductionDialog
        open={dedDialogOpen || !!editDed}
        onOpenChange={(open) => {
          if (!open) {
            setDedDialogOpen(false);
            setEditDed(null);
          }
        }}
        taxYearId={taxYear.id}
        editDeduction={editDed}
      />

      <ConfirmDialog
        open={!!deleteDoc}
        onOpenChange={(open) => !open && setDeleteDoc(null)}
        title="Delete Document"
        description={`Delete ${deleteDoc?.document_type.toUpperCase()} from ${deleteDoc?.issuer}?`}
        onConfirm={() => deleteDoc && deleteDocMutation.mutate(deleteDoc.id)}
        destructive
        loading={deleteDocMutation.isPending}
      />

      <ConfirmDialog
        open={!!deleteDed}
        onOpenChange={(open) => !open && setDeleteDed(null)}
        title="Delete Deduction"
        description={`Delete "${deleteDed?.description}"?`}
        onConfirm={() => deleteDed && deleteDedMutation.mutate(deleteDed.id)}
        destructive
        loading={deleteDedMutation.isPending}
      />
    </>
  );
}
