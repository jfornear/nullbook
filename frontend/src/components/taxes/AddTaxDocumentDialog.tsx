import { useState, useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type { TaxDocument } from "@/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const DOCUMENT_TYPES = [
  { value: "w2", label: "W-2" },
  { value: "1099_int", label: "1099-INT" },
  { value: "1099_div", label: "1099-DIV" },
  { value: "1099_b", label: "1099-B" },
  { value: "1099_misc", label: "1099-MISC" },
  { value: "1099_nec", label: "1099-NEC" },
  { value: "1098", label: "1098" },
  { value: "k1", label: "K-1" },
  { value: "other", label: "Other" },
];

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  taxYearId: number;
  editDocument?: TaxDocument | null;
}

export default function AddTaxDocumentDialog({
  open,
  onOpenChange,
  taxYearId,
  editDocument,
}: Props) {
  const queryClient = useQueryClient();
  const [documentType, setDocumentType] = useState("w2");
  const [issuer, setIssuer] = useState("");
  const [amount, setAmount] = useState("");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState("");

  const isEditing = !!editDocument;

  useEffect(() => {
    if (editDocument) {
      setDocumentType(editDocument.document_type);
      setIssuer(editDocument.issuer);
      setAmount(editDocument.amount);
      setNotes(editDocument.notes);
    }
  }, [editDocument]);

  const mutation = useMutation({
    mutationFn: (data: {
      tax_year: number;
      document_type: string;
      issuer: string;
      amount: string;
      notes: string;
    }) =>
      isEditing
        ? api.put<TaxDocument>(`/taxes/documents/${editDocument!.id}/`, data)
        : api.post<TaxDocument>("/taxes/documents/", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tax-year-detail", taxYearId] });
      toast.success(isEditing ? "Document updated" : "Document added");
      handleClose();
    },
    onError: (err: Error) => setError(err.message),
  });

  function handleClose() {
    setDocumentType("w2");
    setIssuer("");
    setAmount("");
    setNotes("");
    setError("");
    onOpenChange(false);
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    mutation.mutate({
      tax_year: taxYearId,
      document_type: documentType,
      issuer,
      amount,
      notes,
    });
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent>
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>{isEditing ? "Edit Document" : "Add Document"}</DialogTitle>
            <DialogDescription>
              {isEditing ? "Update document details." : "Add a tax document for this year."}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>Document Type</Label>
              <Select value={documentType} onValueChange={setDocumentType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {DOCUMENT_TYPES.map((t) => (
                    <SelectItem key={t.value} value={t.value}>
                      {t.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              <Label>Issuer</Label>
              <Input
                placeholder="e.g. Fidelity Investments"
                value={issuer}
                onChange={(e) => setIssuer(e.target.value)}
                required
              />
            </div>
            <div className="grid gap-2">
              <Label>Amount</Label>
              <Input
                type="number"
                step="0.01"
                placeholder="0.00"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                required
              />
            </div>
            <div className="grid gap-2">
              <Label>Notes</Label>
              <Input
                placeholder="Optional notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? "Saving..." : isEditing ? "Save Changes" : "Add Document"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
