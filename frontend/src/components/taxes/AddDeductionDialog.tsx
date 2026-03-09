import { useState, useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type { DeductibleExpense } from "@/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
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

const DEDUCTION_TYPES = [
  { value: "standard", label: "Standard" },
  { value: "mortgage_interest", label: "Mortgage Interest" },
  { value: "state_local_tax", label: "State & Local Tax" },
  { value: "charitable", label: "Charitable" },
  { value: "medical", label: "Medical" },
  { value: "business", label: "Business" },
  { value: "education", label: "Education" },
  { value: "other", label: "Other" },
];

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  taxYearId: number;
  editDeduction?: DeductibleExpense | null;
}

export default function AddDeductionDialog({
  open,
  onOpenChange,
  taxYearId,
  editDeduction,
}: Props) {
  const queryClient = useQueryClient();
  const [deductionType, setDeductionType] = useState("other");
  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");
  const [isVerified, setIsVerified] = useState(false);
  const [error, setError] = useState("");

  const isEditing = !!editDeduction;

  useEffect(() => {
    if (editDeduction) {
      setDeductionType(editDeduction.deduction_type);
      setDescription(editDeduction.description);
      setAmount(editDeduction.amount);
      setIsVerified(editDeduction.is_verified);
    }
  }, [editDeduction]);

  const mutation = useMutation({
    mutationFn: (data: {
      tax_year: number;
      deduction_type: string;
      description: string;
      amount: string;
      is_verified: boolean;
    }) =>
      isEditing
        ? api.put<DeductibleExpense>(`/taxes/deductions/${editDeduction!.id}/`, data)
        : api.post<DeductibleExpense>("/taxes/deductions/", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tax-year-detail", taxYearId] });
      toast.success(isEditing ? "Deduction updated" : "Deduction added");
      handleClose();
    },
    onError: (err: Error) => setError(err.message),
  });

  function handleClose() {
    setDeductionType("other");
    setDescription("");
    setAmount("");
    setIsVerified(false);
    setError("");
    onOpenChange(false);
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    mutation.mutate({
      tax_year: taxYearId,
      deduction_type: deductionType,
      description,
      amount,
      is_verified: isVerified,
    });
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent>
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>{isEditing ? "Edit Deduction" : "Add Deduction"}</DialogTitle>
            <DialogDescription>
              {isEditing ? "Update deduction details." : "Add a deductible expense for this year."}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>Deduction Type</Label>
              <Select value={deductionType} onValueChange={setDeductionType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {DEDUCTION_TYPES.map((t) => (
                    <SelectItem key={t.value} value={t.value}>
                      {t.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              <Label>Description</Label>
              <Input
                placeholder="e.g. Home office expenses"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
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
            <div className="flex items-center gap-2">
              <Checkbox
                id="verified"
                checked={isVerified}
                onCheckedChange={(checked) => setIsVerified(checked === true)}
              />
              <Label htmlFor="verified" className="text-sm font-normal">
                Verified with documentation
              </Label>
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? "Saving..." : isEditing ? "Save Changes" : "Add Deduction"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
