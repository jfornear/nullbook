import { useState, useMemo, useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type { Account, Institution, PaginatedResponse } from "@/types";
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
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const ACCOUNT_TYPES = [
  { value: "checking", label: "Checking" },
  { value: "savings", label: "Savings" },
  { value: "credit_card", label: "Credit Card" },
  { value: "investment", label: "Investment" },
  { value: "loan", label: "Loan" },
  { value: "mortgage", label: "Mortgage" },
  { value: "cash", label: "Cash" },
  { value: "other", label: "Other" },
];

const TYPE_LABELS: Record<string, string> = {
  bank: "Banks",
  credit_union: "Credit Unions",
  brokerage: "Brokerages",
  crypto: "Crypto Exchanges",
};

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  editAccount?: Account | null;
}

export default function AddAccountDialog({ open, onOpenChange, editAccount }: Props) {
  const queryClient = useQueryClient();
  const [institutionId, setInstitutionId] = useState("");
  const [name, setName] = useState("");
  const [accountType, setAccountType] = useState("checking");
  const [balance, setBalance] = useState("0.00");
  const [currency, setCurrency] = useState("USD");
  const [error, setError] = useState("");

  const isEditing = !!editAccount;

  const { data: institutionsData } = useQuery({
    queryKey: ["institutions"],
    queryFn: () => api.get<PaginatedResponse<Institution>>("/accounts/institutions/"),
    enabled: open,
  });

  const institutions = useMemo(() => institutionsData?.results || [], [institutionsData]);

  const grouped = useMemo(() => {
    const groups: Record<string, Institution[]> = {};
    for (const inst of institutions) {
      const type = inst.institution_type;
      if (!groups[type]) groups[type] = [];
      groups[type].push(inst);
    }
    return groups;
  }, [institutions]);

  useEffect(() => {
    if (editAccount) {
      setInstitutionId(editAccount.institution ? String(editAccount.institution) : "none");
      setName(editAccount.name);
      setAccountType(editAccount.account_type);
      setBalance(editAccount.balance);
      setCurrency(editAccount.currency);
    }
  }, [editAccount]);

  const mutation = useMutation({
    mutationFn: (data: Partial<Account>) =>
      isEditing
        ? api.put<Account>(`/accounts/accounts/${editAccount!.id}/`, data)
        : api.post<Account>("/accounts/accounts/", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success(isEditing ? "Account updated" : "Account created");
      handleClose();
    },
    onError: (err: Error) => setError(err.message),
  });

  function handleClose() {
    setInstitutionId("");
    setName("");
    setAccountType("checking");
    setBalance("0.00");
    setCurrency("USD");
    setError("");
    onOpenChange(false);
  }

  function handleInstitutionChange(value: string) {
    setInstitutionId(value);
    if (value && value !== "none") {
      const inst = institutions.find((i) => String(i.id) === value);
      if (inst && !name) {
        setName(inst.name);
      }
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    mutation.mutate({
      name,
      account_type: accountType,
      balance,
      currency,
      institution: institutionId && institutionId !== "none" ? Number(institutionId) : null,
    } as Partial<Account>);
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent>
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>{isEditing ? "Edit Account" : "Add Account"}</DialogTitle>
            <DialogDescription>
              {isEditing
                ? "Update account details."
                : "Add a bank account, credit card, or investment account to track."}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="institution">Institution</Label>
              <Select value={institutionId} onValueChange={handleInstitutionChange}>
                <SelectTrigger>
                  <SelectValue placeholder="Select institution" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">Other / Not listed</SelectItem>
                  {Object.entries(grouped).map(([type, insts]) => (
                    <SelectGroup key={type}>
                      <SelectLabel>{TYPE_LABELS[type] || type}</SelectLabel>
                      {insts.map((inst) => (
                        <SelectItem key={inst.id} value={String(inst.id)}>
                          <span className="flex items-center gap-2">
                            {inst.logo_url && (
                              <img
                                src={inst.logo_url}
                                alt={`${inst.name} logo`}
                                className="h-4 w-4 rounded-sm object-contain"
                                onError={(e) => {
                                  (e.target as HTMLImageElement).style.display = "none";
                                }}
                              />
                            )}
                            {inst.name}
                          </span>
                        </SelectItem>
                      ))}
                    </SelectGroup>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="name">Account Name</Label>
              <Input
                id="name"
                placeholder="e.g. Chase Checking"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="type">Account Type</Label>
              <Select value={accountType} onValueChange={setAccountType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {ACCOUNT_TYPES.map((t) => (
                    <SelectItem key={t.value} value={t.value}>
                      {t.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="balance">Balance</Label>
                <Input
                  id="balance"
                  type="number"
                  step="0.01"
                  value={balance}
                  onChange={(e) => setBalance(e.target.value)}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="currency">Currency</Label>
                <Input
                  id="currency"
                  value={currency}
                  onChange={(e) => setCurrency(e.target.value)}
                  maxLength={3}
                />
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
                  : "Add Account"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
