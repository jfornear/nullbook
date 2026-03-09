import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
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
import { api } from "@/lib/api";
import type { Category, PaginatedResponse } from "@/types";

interface CreateBudgetDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CreateBudgetDialog({ open, onOpenChange }: CreateBudgetDialogProps) {
  const queryClient = useQueryClient();
  const [categoryId, setCategoryId] = useState<string>("");
  const [amount, setAmount] = useState("");
  const [period, setPeriod] = useState("monthly");

  const { data: categoriesData } = useQuery({
    queryKey: ["categories"],
    queryFn: () => api.get<PaginatedResponse<Category>>("/transactions/categories/"),
  });

  const mutation = useMutation({
    mutationFn: (data: { category: number | null; amount: string; period: string }) =>
      api.post("/transactions/budgets/", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["budgets"] });
      toast.success("Budget created");
      onOpenChange(false);
      setCategoryId("");
      setAmount("");
      setPeriod("monthly");
    },
    onError: (err: Error) => toast.error(err.message),
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    mutation.mutate({
      category: categoryId && categoryId !== "__total__" ? Number(categoryId) : null,
      amount,
      period,
    });
  }

  const categories = categoriesData?.results || [];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create Budget</DialogTitle>
          <DialogDescription>Set a spending limit for a category.</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label>Category</Label>
            <Select value={categoryId} onValueChange={setCategoryId}>
              <SelectTrigger>
                <SelectValue placeholder="Total (all spending)" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__total__">Total (all spending)</SelectItem>
                {categories.map((cat) => (
                  <SelectItem key={cat.id} value={String(cat.id)}>
                    {cat.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Amount</Label>
            <Input
              type="number"
              step="0.01"
              min="0"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="500.00"
              required
            />
          </div>
          <div className="space-y-2">
            <Label>Period</Label>
            <Select value={period} onValueChange={setPeriod}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="weekly">Weekly</SelectItem>
                <SelectItem value="monthly">Monthly</SelectItem>
                <SelectItem value="annual">Annual</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <Button type="submit" className="w-full" disabled={mutation.isPending}>
            {mutation.isPending ? "Creating..." : "Create Budget"}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
