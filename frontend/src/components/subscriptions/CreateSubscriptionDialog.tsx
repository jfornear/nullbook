import { useState, useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";

interface Subscription {
  id: number;
  merchant: string;
  amount: string;
  frequency: string;
  status: string;
  cancellation_url: string;
  notes?: string;
}

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  editSubscription?: Subscription | null;
}

const FREQUENCIES = [
  { value: "weekly", label: "Weekly" },
  { value: "biweekly", label: "Biweekly" },
  { value: "monthly", label: "Monthly" },
  { value: "quarterly", label: "Quarterly" },
  { value: "semi_annual", label: "Semi-Annual" },
  { value: "annual", label: "Annual" },
];

const STATUSES = [
  { value: "active", label: "Active" },
  { value: "cancelled", label: "Cancelled" },
  { value: "cancellation_pending", label: "Cancellation Pending" },
];

export function CreateSubscriptionDialog({ open, onOpenChange, editSubscription }: Props) {
  const queryClient = useQueryClient();
  const isEdit = !!editSubscription;

  const [form, setForm] = useState({
    merchant: "",
    amount: "",
    frequency: "monthly",
    status: "active",
    cancellation_url: "",
    notes: "",
  });

  useEffect(() => {
    if (editSubscription) {
      setForm({
        merchant: editSubscription.merchant,
        amount: editSubscription.amount,
        frequency: editSubscription.frequency,
        status: editSubscription.status,
        cancellation_url: editSubscription.cancellation_url || "",
        notes: editSubscription.notes || "",
      });
    } else {
      setForm({
        merchant: "",
        amount: "",
        frequency: "monthly",
        status: "active",
        cancellation_url: "",
        notes: "",
      });
    }
  }, [editSubscription, open]);

  const mutation = useMutation({
    mutationFn: (data: typeof form) =>
      isEdit
        ? api.patch(`/transactions/subscriptions/${editSubscription!.id}/`, data)
        : api.post("/transactions/subscriptions/", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["subscriptions"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success(isEdit ? "Subscription updated" : "Subscription created");
      onOpenChange(false);
    },
    onError: (err: Error) => toast.error(err.message),
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit Subscription" : "Add Subscription"}</DialogTitle>
          <DialogDescription>
            Track a recurring charge to monitor your subscriptions.
          </DialogDescription>
        </DialogHeader>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            mutation.mutate(form);
          }}
          className="space-y-3 pt-2"
        >
          <div className="space-y-2">
            <Label htmlFor="merchant">Merchant</Label>
            <Input
              id="merchant"
              placeholder="Netflix, Spotify, etc."
              value={form.merchant}
              onChange={(e) => setForm((f) => ({ ...f, merchant: e.target.value }))}
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label htmlFor="amount">Amount</Label>
              <Input
                id="amount"
                type="number"
                step="0.01"
                placeholder="9.99"
                value={form.amount}
                onChange={(e) => setForm((f) => ({ ...f, amount: e.target.value }))}
                required
              />
            </div>
            <div className="space-y-2">
              <Label>Frequency</Label>
              <Select
                value={form.frequency}
                onValueChange={(v) => setForm((f) => ({ ...f, frequency: v }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {FREQUENCIES.map((f) => (
                    <SelectItem key={f.value} value={f.value}>
                      {f.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="space-y-2">
            <Label>Status</Label>
            <Select
              value={form.status}
              onValueChange={(v) => setForm((f) => ({ ...f, status: v }))}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {STATUSES.map((s) => (
                  <SelectItem key={s.value} value={s.value}>
                    {s.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="cancellation_url">Cancellation URL (optional)</Label>
            <Input
              id="cancellation_url"
              placeholder="https://..."
              value={form.cancellation_url}
              onChange={(e) => setForm((f) => ({ ...f, cancellation_url: e.target.value }))}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="notes">Notes (optional)</Label>
            <Textarea
              id="notes"
              placeholder="Any notes..."
              value={form.notes}
              onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
              rows={2}
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {isEdit ? "Save" : "Add"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
