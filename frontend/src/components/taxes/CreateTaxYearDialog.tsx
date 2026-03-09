import { useState, useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type { TaxYear, PaginatedResponse } from "@/types";
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

const FILING_STATUSES = [
  { value: "single", label: "Single" },
  { value: "married_joint", label: "Married Filing Jointly" },
  { value: "married_separate", label: "Married Filing Separately" },
  { value: "head_of_household", label: "Head of Household" },
];

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  editTaxYear?: TaxYear | null;
}

export default function CreateTaxYearDialog({ open, onOpenChange, editTaxYear }: Props) {
  const queryClient = useQueryClient();
  const [year, setYear] = useState(() => String(new Date().getFullYear()));
  const [filingStatus, setFilingStatus] = useState("single");
  const [error, setError] = useState("");

  const isEditing = !!editTaxYear;

  const { data: existingYearsData } = useQuery({
    queryKey: ["tax-years"],
    queryFn: () => api.get<PaginatedResponse<TaxYear>>("/taxes/tax-years/"),
    enabled: open,
  });

  const existingYears = new Set((existingYearsData?.results || []).map((ty) => ty.year));
  const isDuplicate = !isEditing && existingYears.has(Number(year));

  useEffect(() => {
    if (editTaxYear) {
      setYear(String(editTaxYear.year));
      setFilingStatus(editTaxYear.filing_status);
    }
  }, [editTaxYear]);

  const mutation = useMutation({
    mutationFn: (data: { year: number; filing_status: string }) =>
      isEditing
        ? api.put<TaxYear>(`/taxes/tax-years/${editTaxYear!.id}/`, data)
        : api.post<TaxYear>("/taxes/tax-years/", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tax-years"] });
      toast.success(isEditing ? "Tax year updated" : "Tax year created");
      handleClose();
    },
    onError: (err: Error) => setError(err.message),
  });

  function handleClose() {
    setYear(String(new Date().getFullYear()));
    setFilingStatus("single");
    setError("");
    onOpenChange(false);
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    mutation.mutate({
      year: Number(year),
      filing_status: filingStatus,
    });
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent>
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>{isEditing ? "Edit Tax Year" : "Create Tax Year"}</DialogTitle>
            <DialogDescription>
              {isEditing
                ? "Update tax year details."
                : "Start tracking tax documents and deductions for a specific year."}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="year">Tax Year</Label>
              <Input
                id="year"
                type="number"
                min={2000}
                max={2099}
                value={year}
                onChange={(e) => setYear(e.target.value)}
                disabled={isEditing}
                required
              />
              {isDuplicate && (
                <p className="text-sm text-destructive">You already have a tax year for {year}.</p>
              )}
            </div>
            <div className="grid gap-2">
              <Label htmlFor="filingStatus">Filing Status</Label>
              <Select value={filingStatus} onValueChange={setFilingStatus}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {FILING_STATUSES.map((s) => (
                    <SelectItem key={s.value} value={s.value}>
                      {s.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={mutation.isPending || isDuplicate}>
              {mutation.isPending
                ? isEditing
                  ? "Saving..."
                  : "Creating..."
                : isEditing
                  ? "Save Changes"
                  : "Create Tax Year"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
