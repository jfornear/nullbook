import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type { Transaction, Account, Category, PaginatedResponse } from "@/types";
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
import AddAccountDialog from "@/components/accounts/AddAccountDialog";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  editTransaction?: Transaction | null;
}

export default function AddTransactionDialog({ open, onOpenChange, editTransaction }: Props) {
  const queryClient = useQueryClient();
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [amount, setAmount] = useState("");
  const [transactionType, setTransactionType] = useState<"expense" | "income" | "transfer">(
    "expense"
  );
  const [description, setDescription] = useState("");
  const [accountId, setAccountId] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [error, setError] = useState("");
  const [showAddAccount, setShowAddAccount] = useState(false);

  const isEditing = !!editTransaction;

  const { data: accountsData } = useQuery({
    queryKey: ["accounts"],
    queryFn: () => api.get<PaginatedResponse<Account>>("/accounts/accounts/"),
    enabled: open,
  });

  const { data: categoriesData } = useQuery({
    queryKey: ["categories"],
    queryFn: () => api.get<PaginatedResponse<Category>>("/transactions/categories/"),
    enabled: open,
  });

  useEffect(() => {
    if (editTransaction) {
      setDate(editTransaction.date);
      setAmount(editTransaction.amount);
      setTransactionType(editTransaction.transaction_type);
      setDescription(editTransaction.description);
      setAccountId(String(editTransaction.account));
      setCategoryId(editTransaction.category ? String(editTransaction.category) : "");
    }
  }, [editTransaction]);

  // Reset account selection when transaction type changes (filtered list may differ)
  // But skip this if we're pre-filling from edit
  useEffect(() => {
    if (!editTransaction) {
      setAccountId("");
    }
  }, [transactionType, editTransaction]);

  const allAccounts = accountsData?.results || [];
  const accounts =
    transactionType === "transfer"
      ? allAccounts
      : allAccounts.filter((a) => a.account_type !== "investment");
  const categories = categoriesData?.results || [];

  const mutation = useMutation({
    mutationFn: (data: Partial<Transaction>) =>
      isEditing
        ? api.put<Transaction>(`/transactions/transactions/${editTransaction!.id}/`, data)
        : api.post<Transaction>("/transactions/transactions/", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success(isEditing ? "Transaction updated" : "Transaction created");
      handleClose();
    },
    onError: (err: Error) => setError(err.message),
  });

  function handleClose() {
    setDate(new Date().toISOString().slice(0, 10));
    setAmount("");
    setTransactionType("expense");
    setDescription("");
    setAccountId("");
    setCategoryId("");
    setError("");
    onOpenChange(false);
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!accountId) {
      setError("Please select an account.");
      return;
    }
    mutation.mutate({
      date,
      amount,
      transaction_type: transactionType,
      description,
      account: Number(accountId),
      category: categoryId ? Number(categoryId) : null,
    });
  }

  return (
    <>
      <Dialog open={open} onOpenChange={handleClose}>
        <DialogContent>
          <form onSubmit={handleSubmit}>
            <DialogHeader>
              <DialogTitle>{isEditing ? "Edit Transaction" : "Add Transaction"}</DialogTitle>
              <DialogDescription>
                {isEditing
                  ? "Update transaction details."
                  : "Record an income, expense, or transfer manually."}
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="date">Date</Label>
                  <Input
                    id="date"
                    type="date"
                    value={date}
                    onChange={(e) => setDate(e.target.value)}
                    required
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="amount">Amount</Label>
                  <Input
                    id="amount"
                    type="number"
                    step="0.01"
                    placeholder="0.00"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    required
                  />
                </div>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="type">Type</Label>
                <Select
                  value={transactionType}
                  onValueChange={(v) => setTransactionType(v as "expense" | "income" | "transfer")}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="expense">Expense</SelectItem>
                    <SelectItem value="income">Income</SelectItem>
                    <SelectItem value="transfer">Transfer</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="description">Description</Label>
                <Input
                  id="description"
                  placeholder="e.g. Grocery store"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="account">Account</Label>
                  {accounts.length === 0 ? (
                    <div className="rounded-md border border-dashed p-3 text-sm text-muted-foreground">
                      No accounts yet.{" "}
                      <button
                        type="button"
                        className="text-primary underline underline-offset-4 hover:text-primary/80"
                        onClick={() => setShowAddAccount(true)}
                      >
                        Add an account first
                      </button>
                      .
                    </div>
                  ) : (
                    <Select value={accountId} onValueChange={setAccountId}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select account" />
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
                <div className="grid gap-2">
                  <Label htmlFor="category">Category</Label>
                  <Select value={categoryId} onValueChange={setCategoryId}>
                    <SelectTrigger>
                      <SelectValue placeholder="None" />
                    </SelectTrigger>
                    <SelectContent>
                      {categories.map((c) => (
                        <SelectItem key={c.id} value={String(c.id)}>
                          {c.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              {error && <p className="text-sm text-destructive">{error}</p>}
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button type="submit" disabled={mutation.isPending}>
                {mutation.isPending
                  ? isEditing
                    ? "Saving..."
                    : "Adding..."
                  : isEditing
                    ? "Save Changes"
                    : "Add Transaction"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
      <AddAccountDialog open={showAddAccount} onOpenChange={setShowAddAccount} />
    </>
  );
}
