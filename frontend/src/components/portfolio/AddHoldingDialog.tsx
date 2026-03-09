import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import type { Holding, Account, PaginatedResponse, SecurityLookup } from "@/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
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
  editHolding?: Holding | null;
}

export default function AddHoldingDialog({ open, onOpenChange, editHolding }: Props) {
  const queryClient = useQueryClient();
  const [symbol, setSymbol] = useState("");
  const [lookedUp, setLookedUp] = useState<SecurityLookup | null>(null);
  const [lookupError, setLookupError] = useState("");
  const [isLooking, setIsLooking] = useState(false);
  const [accountId, setAccountId] = useState("");
  const [shares, setShares] = useState("");
  const [costBasis, setCostBasis] = useState("");
  const [costBasisTouched, setCostBasisTouched] = useState(false);
  const [error, setError] = useState("");
  const [showAddAccount, setShowAddAccount] = useState(false);

  const isEditing = !!editHolding;

  const { data: accountsData } = useQuery({
    queryKey: ["accounts", { account_type: "investment" }],
    queryFn: () =>
      api.get<PaginatedResponse<Account>>("/accounts/accounts/?account_type=investment"),
    enabled: open,
  });

  const accounts = accountsData?.results || [];

  useEffect(() => {
    if (editHolding) {
      setSymbol(editHolding.security_symbol);
      setShares(editHolding.shares);
      setCostBasis(editHolding.cost_basis);
      setCostBasisTouched(true);
      setAccountId(editHolding.account ? String(editHolding.account) : "none");
      // Create a fake lookup result so the form shows security info
      setLookedUp({
        id: editHolding.security,
        symbol: editHolding.security_symbol,
        name: editHolding.security_name,
        security_type: "",
        exchange: "",
        currency: "",
        current_price: null,
      });
    }
  }, [editHolding]);

  // Auto-calculate cost basis when shares or price changes (if user hasn't overridden)
  useEffect(() => {
    if (!costBasisTouched && lookedUp?.current_price && shares) {
      const calculated = (parseFloat(shares) * parseFloat(lookedUp.current_price)).toFixed(2);
      setCostBasis(calculated);
    }
  }, [shares, lookedUp, costBasisTouched]);

  async function handleLookup() {
    const trimmed = symbol.trim().toUpperCase();
    if (!trimmed) return;
    if (isEditing && trimmed === editHolding?.security_symbol) return;
    setLookupError("");
    setLookedUp(null);
    setIsLooking(true);
    try {
      const data = await api.get<SecurityLookup>(
        `/portfolio/securities/lookup/?symbol=${encodeURIComponent(trimmed)}`
      );
      setLookedUp(data);
      setSymbol(trimmed);
    } catch (err: unknown) {
      setLookupError(err instanceof Error ? err.message : "Lookup failed");
    } finally {
      setIsLooking(false);
    }
  }

  function handleSymbolKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter") {
      e.preventDefault();
      handleLookup();
    }
  }

  const mutation = useMutation({
    mutationFn: (data: {
      account: number | null;
      security: number;
      shares: string;
      cost_basis: string;
    }) =>
      isEditing
        ? api.put<Holding>(`/portfolio/holdings/${editHolding!.id}/`, data)
        : api.post<Holding>("/portfolio/holdings/", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["holdings"] });
      queryClient.invalidateQueries({ queryKey: ["allocation"] });
      queryClient.invalidateQueries({ queryKey: ["portfolio-performance"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success(isEditing ? "Holding updated" : "Holding added");
      handleClose();
    },
    onError: (err: Error) => setError(err.message),
  });

  function handleClose() {
    setSymbol("");
    setLookedUp(null);
    setLookupError("");
    setIsLooking(false);
    setAccountId("");
    setShares("");
    setCostBasis("");
    setCostBasisTouched(false);
    setError("");
    onOpenChange(false);
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!lookedUp) {
      setError("Please look up a symbol first.");
      return;
    }
    mutation.mutate({
      account: accountId && accountId !== "none" ? Number(accountId) : null,
      security: lookedUp.id,
      shares,
      cost_basis: costBasis,
    });
  }

  return (
    <>
      <Dialog open={open} onOpenChange={handleClose}>
        <DialogContent>
          <form onSubmit={handleSubmit}>
            <DialogHeader>
              <DialogTitle>{isEditing ? "Edit Holding" : "Add Holding"}</DialogTitle>
              <DialogDescription>
                {isEditing
                  ? "Update holding details."
                  : "Add a stock, ETF, or other security to your portfolio."}
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="symbol">Symbol</Label>
                <div className="flex gap-2">
                  <Input
                    id="symbol"
                    placeholder="e.g. AAPL"
                    value={symbol}
                    onChange={(e) => {
                      setSymbol(e.target.value.toUpperCase());
                      if (lookedUp && !isEditing) {
                        setLookedUp(null);
                        setCostBasis("");
                        setCostBasisTouched(false);
                      }
                    }}
                    onBlur={handleLookup}
                    onKeyDown={handleSymbolKeyDown}
                    disabled={isEditing}
                    required
                  />
                  {isLooking && (
                    <Loader2 className="h-5 w-5 animate-spin self-center text-muted-foreground" />
                  )}
                </div>
                {lookupError && <p className="text-sm text-destructive">{lookupError}</p>}
              </div>

              {lookedUp && (
                <div className="rounded-lg border bg-muted/50 p-3 space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{lookedUp.name}</span>
                    {lookedUp.security_type && (
                      <Badge variant="secondary">{lookedUp.security_type}</Badge>
                    )}
                  </div>
                  <div className="text-sm text-muted-foreground flex gap-4">
                    {lookedUp.exchange && <span>{lookedUp.exchange}</span>}
                    {lookedUp.current_price && (
                      <span>${parseFloat(lookedUp.current_price).toFixed(2)}</span>
                    )}
                  </div>
                </div>
              )}

              <div className="grid gap-2">
                <Label htmlFor="account">Account (optional)</Label>
                {accounts.length === 0 ? (
                  <div className="rounded-md border border-dashed p-3 text-sm text-muted-foreground">
                    No investment accounts yet.{" "}
                    <button
                      type="button"
                      className="text-primary underline underline-offset-4 hover:text-primary/80"
                      onClick={() => setShowAddAccount(true)}
                    >
                      Create one
                    </button>
                    , or leave blank.
                  </div>
                ) : (
                  <Select value={accountId} onValueChange={setAccountId}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select investment account" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">No account</SelectItem>
                      {accounts.map((a) => (
                        <SelectItem key={a.id} value={String(a.id)}>
                          {a.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="shares">Shares</Label>
                  <Input
                    id="shares"
                    type="number"
                    step="any"
                    placeholder="0"
                    value={shares}
                    onChange={(e) => setShares(e.target.value)}
                    required
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="costBasis">Cost Basis</Label>
                  <Input
                    id="costBasis"
                    type="number"
                    step="0.01"
                    placeholder="0.00"
                    value={costBasis}
                    onChange={(e) => {
                      setCostBasis(e.target.value);
                      setCostBasisTouched(true);
                    }}
                    required
                  />
                </div>
              </div>
              {error && <p className="text-sm text-destructive">{error}</p>}
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button type="submit" disabled={mutation.isPending || !lookedUp}>
                {mutation.isPending
                  ? isEditing
                    ? "Saving..."
                    : "Adding..."
                  : isEditing
                    ? "Save Changes"
                    : "Add Holding"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
      <AddAccountDialog open={showAddAccount} onOpenChange={setShowAddAccount} />
    </>
  );
}
