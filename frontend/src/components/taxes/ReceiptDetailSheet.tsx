import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Pencil, Save, X, Search, Link, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import type { PaginatedResponse, Transaction } from "@/types";

interface ReceiptLineItem {
  id: number;
  description: string;
  quantity: string;
  unit_price: string;
  total_price: string;
  category: string;
}

interface ReceiptDetail {
  id: number;
  image_url: string | null;
  status: string;
  merchant: string;
  date: string | null;
  total_amount: string | null;
  subtotal: string | null;
  tax_amount: string | null;
  tip_amount: string | null;
  currency: string;
  payment_method: string;
  category: string;
  transaction: number | null;
  line_items: ReceiptLineItem[];
  created_at: string;
}

interface Props {
  receiptId: number | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ReceiptDetailSheet({ receiptId, open, onOpenChange }: Props) {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({
    merchant: "",
    date: "",
    total_amount: "",
    subtotal: "",
    tax_amount: "",
    tip_amount: "",
    category: "",
    payment_method: "",
  });
  const [txnSearch, setTxnSearch] = useState("");
  const [debouncedTxnSearch, setDebouncedTxnSearch] = useState("");
  const [showTxnSearch, setShowTxnSearch] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedTxnSearch(txnSearch), 300);
    return () => clearTimeout(timer);
  }, [txnSearch]);

  const { data: receipt } = useQuery({
    queryKey: ["receipt-detail", receiptId],
    queryFn: () => api.get<ReceiptDetail>(`/taxes/receipts/${receiptId}/`),
    enabled: !!receiptId,
  });

  const { data: txnResults } = useQuery({
    queryKey: ["txn-search", debouncedTxnSearch],
    queryFn: () =>
      api.get<PaginatedResponse<Transaction>>(
        `/transactions/transactions/?search=${encodeURIComponent(debouncedTxnSearch)}`
      ),
    enabled: debouncedTxnSearch.length >= 2,
  });

  useEffect(() => {
    if (receipt) {
      setForm({
        merchant: receipt.merchant || "",
        date: receipt.date || "",
        total_amount: receipt.total_amount || "",
        subtotal: receipt.subtotal || "",
        tax_amount: receipt.tax_amount || "",
        tip_amount: receipt.tip_amount || "",
        category: receipt.category || "",
        payment_method: receipt.payment_method || "",
      });
    }
  }, [receipt]);

  const saveMutation = useMutation({
    mutationFn: (data: typeof form) => api.patch(`/taxes/receipts/${receiptId}/`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["receipt-detail", receiptId] });
      queryClient.invalidateQueries({ queryKey: ["receipts"] });
      toast.success("Receipt updated");
      setEditing(false);
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const linkMutation = useMutation({
    mutationFn: (transactionId: number) =>
      api.patch(`/taxes/receipts/${receiptId}/`, { transaction: transactionId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["receipt-detail", receiptId] });
      queryClient.invalidateQueries({ queryKey: ["receipts"] });
      toast.success("Transaction linked");
      setShowTxnSearch(false);
      setTxnSearch("");
    },
    onError: (err: Error) => toast.error(err.message),
  });

  if (!receiptId) return null;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:w-[520px] overflow-y-auto">
        <SheetHeader>
          <div className="flex items-center justify-between">
            <SheetTitle>Receipt Details</SheetTitle>
            {receipt && !editing && (
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => setEditing(true)}
              >
                <Pencil className="h-4 w-4" />
              </Button>
            )}
            {editing && (
              <div className="flex gap-1">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => setEditing(false)}
                >
                  <X className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => saveMutation.mutate(form)}
                  disabled={saveMutation.isPending}
                >
                  {saveMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="h-4 w-4" />
                  )}
                </Button>
              </div>
            )}
          </div>
        </SheetHeader>

        {receipt && (
          <div className="mt-4 space-y-4">
            {/* Receipt image */}
            {receipt.image_url && (
              <div className="rounded-lg border overflow-hidden">
                <img
                  src={receipt.image_url}
                  alt="Receipt"
                  className="w-full object-contain max-h-64"
                />
              </div>
            )}

            {/* Status badge */}
            <Badge variant={receipt.status === "completed" ? "default" : "secondary"}>
              {receipt.status}
            </Badge>

            <Separator />

            {/* Extracted data */}
            <div className="grid gap-3">
              <Field
                label="Merchant"
                value={form.merchant}
                editing={editing}
                onChange={(v) => setForm((f) => ({ ...f, merchant: v }))}
              />
              <Field
                label="Date"
                value={form.date}
                editing={editing}
                onChange={(v) => setForm((f) => ({ ...f, date: v }))}
                type="date"
              />
              <div className="grid grid-cols-2 gap-3">
                <Field
                  label="Total"
                  value={form.total_amount}
                  editing={editing}
                  onChange={(v) => setForm((f) => ({ ...f, total_amount: v }))}
                  type="number"
                />
                <Field
                  label="Subtotal"
                  value={form.subtotal}
                  editing={editing}
                  onChange={(v) => setForm((f) => ({ ...f, subtotal: v }))}
                  type="number"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <Field
                  label="Tax"
                  value={form.tax_amount}
                  editing={editing}
                  onChange={(v) => setForm((f) => ({ ...f, tax_amount: v }))}
                  type="number"
                />
                <Field
                  label="Tip"
                  value={form.tip_amount}
                  editing={editing}
                  onChange={(v) => setForm((f) => ({ ...f, tip_amount: v }))}
                  type="number"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <Field
                  label="Category"
                  value={form.category}
                  editing={editing}
                  onChange={(v) => setForm((f) => ({ ...f, category: v }))}
                />
                <Field
                  label="Payment Method"
                  value={form.payment_method}
                  editing={editing}
                  onChange={(v) => setForm((f) => ({ ...f, payment_method: v }))}
                />
              </div>
            </div>

            {/* Line items */}
            {receipt.line_items.length > 0 && (
              <>
                <Separator />
                <div>
                  <h3 className="text-sm font-medium mb-2">Line Items</h3>
                  <div className="space-y-1">
                    {receipt.line_items.map((item) => (
                      <div
                        key={item.id}
                        className="flex items-center justify-between rounded-md border px-3 py-1.5 text-sm"
                      >
                        <span>{item.description}</span>
                        <span className="text-muted-foreground">
                          {item.quantity && `${item.quantity} × `}
                          {formatCurrency(item.total_price)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}

            {/* Transaction link */}
            <Separator />
            <div>
              <h3 className="text-sm font-medium mb-2">Linked Transaction</h3>
              {receipt.transaction ? (
                <div className="rounded-md border px-3 py-2 text-sm flex items-center gap-2">
                  <Link className="h-3.5 w-3.5 text-muted-foreground" />
                  <span>Transaction #{receipt.transaction}</span>
                </div>
              ) : (
                <>
                  {!showTxnSearch ? (
                    <Button variant="outline" size="sm" onClick={() => setShowTxnSearch(true)}>
                      <Search className="mr-2 h-3.5 w-3.5" />
                      Link to Transaction
                    </Button>
                  ) : (
                    <div className="space-y-2">
                      <Input
                        placeholder="Search transactions..."
                        value={txnSearch}
                        onChange={(e) => setTxnSearch(e.target.value)}
                        autoFocus
                      />
                      {txnResults?.results && txnResults.results.length > 0 && (
                        <div className="max-h-40 overflow-y-auto space-y-1">
                          {txnResults.results.slice(0, 5).map((txn) => (
                            <button
                              key={txn.id}
                              className="flex w-full items-center justify-between rounded-md border px-3 py-1.5 text-sm hover:bg-accent"
                              onClick={() => linkMutation.mutate(txn.id)}
                              disabled={linkMutation.isPending}
                            >
                              <span>{txn.description}</span>
                              <span className="text-muted-foreground">
                                {formatCurrency(txn.amount)} · {txn.date}
                              </span>
                            </button>
                          ))}
                        </div>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-xs"
                        onClick={() => {
                          setShowTxnSearch(false);
                          setTxnSearch("");
                        }}
                      >
                        Cancel
                      </Button>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}

function Field({
  label,
  value,
  editing,
  onChange,
  type = "text",
}: {
  label: string;
  value: string;
  editing: boolean;
  onChange: (v: string) => void;
  type?: string;
}) {
  if (editing) {
    return (
      <div className="space-y-1">
        <Label className="text-xs">{label}</Label>
        <Input
          type={type}
          step={type === "number" ? "0.01" : undefined}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="h-8 text-sm"
        />
      </div>
    );
  }

  return (
    <div>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-sm">{value || "—"}</p>
    </div>
  );
}
