import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Account, Transaction, PaginatedResponse } from "@/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Pencil, Trash2 } from "lucide-react";
import { formatCurrency, formatDate } from "@/lib/utils";

interface Props {
  account: Account | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onEdit: (account: Account) => void;
  onDelete: (account: Account) => void;
}

export function AccountDetailSheet({ account, open, onOpenChange, onEdit, onDelete }: Props) {
  const { data: txnData } = useQuery({
    queryKey: ["transactions", { account: account?.id }],
    queryFn: () =>
      api.get<PaginatedResponse<Transaction>>(`/transactions/transactions/?account=${account!.id}`),
    enabled: !!account,
  });

  const transactions = txnData?.results?.slice(0, 10) || [];

  if (!account) return null;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:w-[480px] overflow-y-auto">
        <SheetHeader>
          <div className="flex items-center justify-between">
            <SheetTitle className="flex items-center gap-2">
              {account.institution_logo_url && (
                <img
                  src={account.institution_logo_url}
                  alt={`${account.institution_name || account.name} logo`}
                  className="h-5 w-5 rounded-sm object-contain"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = "none";
                  }}
                />
              )}
              {account.name}
            </SheetTitle>
            <div className="flex gap-1">
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => onEdit(account)}
              >
                <Pencil className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-destructive"
                onClick={() => onDelete(account)}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </SheetHeader>

        <div className="mt-6 space-y-4">
          <div>
            <div className="text-3xl font-bold">
              {formatCurrency(account.balance, account.currency)}
            </div>
            <div className="mt-1 flex items-center gap-2">
              <Badge variant="secondary">{account.account_type}</Badge>
              {account.institution_name && (
                <span className="text-sm text-muted-foreground">{account.institution_name}</span>
              )}
            </div>
          </div>

          {account.notes && <p className="text-sm text-muted-foreground">{account.notes}</p>}

          <Separator />

          <div>
            <h3 className="mb-3 text-sm font-medium">Recent Transactions</h3>
            {transactions.length === 0 ? (
              <p className="text-sm text-muted-foreground">No transactions for this account.</p>
            ) : (
              <div className="space-y-2">
                {transactions.map((txn) => (
                  <div key={txn.id} className="flex items-center justify-between py-1">
                    <div>
                      <p className="text-sm">{txn.description}</p>
                      <p className="text-xs text-muted-foreground">{formatDate(txn.date)}</p>
                    </div>
                    <span
                      className={`text-sm font-medium ${txn.transaction_type === "income" ? "text-green-600" : "text-red-600"}`}
                    >
                      {txn.transaction_type === "income" ? "+" : "-"}
                      {formatCurrency(txn.amount)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
