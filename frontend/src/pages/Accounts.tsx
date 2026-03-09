import { useState, useCallback, useEffect, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Plus, Wallet, CreditCard, Landmark, PiggyBank, Building2, RefreshCw } from "lucide-react";
import { usePlaidLink } from "react-plaid-link";
import { api, plaidApi } from "@/lib/api";
import type { Account, PaginatedResponse } from "@/types";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatCurrency } from "@/lib/utils";
import { CardSkeleton } from "@/components/shared/CardSkeleton";
import { QueryError } from "@/components/shared/QueryError";
import { RowActions } from "@/components/shared/RowActions";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { AccountDetailSheet } from "@/components/accounts/AccountDetailSheet";
import AddAccountDialog from "@/components/accounts/AddAccountDialog";

const accountExamples = [
  {
    icon: Landmark,
    label: "Checking & Savings",
    description: "Chase, BofA, Wells Fargo, local banks and credit unions",
  },
  {
    icon: CreditCard,
    label: "Credit Cards",
    description: "Track balances and spending across Amex, Visa, Mastercard, and more",
  },
  {
    icon: PiggyBank,
    label: "Investment Accounts",
    description: "Brokerage, 401k, IRA, Roth, and other investment accounts",
  },
  {
    icon: Wallet,
    label: "Other",
    description: "Cash, loans, mortgages, crypto wallets, anything with a balance",
  },
];

function PlaidLinkButton() {
  const queryClient = useQueryClient();
  const [linkToken, setLinkToken] = useState<string | null>(null);

  const createLinkToken = useMutation({
    mutationFn: () => plaidApi.createLinkToken(),
    onSuccess: (data) => setLinkToken(data.link_token),
    onError: (err: Error) => toast.error(`Plaid: ${err.message}`),
  });

  const exchangeToken = useMutation({
    mutationFn: (args: { publicToken: string; institutionId?: string; institutionName?: string }) =>
      plaidApi.exchangePublicToken(args.publicToken, args.institutionId, args.institutionName),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["plaid-items"] });
      if (data.already_connected) {
        toast.info(`${data.item.institution_name} is already connected`);
      } else {
        toast.success(
          `Connected ${data.item.institution_name} — ${data.accounts_synced} account(s) synced`
        );
      }
      setLinkToken(null);
    },
    onError: (err: Error) => {
      toast.error(`Connection failed: ${err.message}`);
      setLinkToken(null);
    },
  });

  const exchangeTokenRef = useRef(exchangeToken);
  exchangeTokenRef.current = exchangeToken;

  const onSuccess = useCallback(
    (
      publicToken: string,
      metadata: { institution?: { institution_id?: string; name?: string } | null }
    ) => {
      exchangeTokenRef.current.mutate({
        publicToken,
        institutionId: metadata.institution?.institution_id,
        institutionName: metadata.institution?.name,
      });
    },
    []
  );

  const { open, ready } = usePlaidLink({
    token: linkToken,
    onSuccess,
    onExit: () => setLinkToken(null),
  });

  // Auto-open Plaid Link when token is ready
  useEffect(() => {
    if (linkToken && ready) {
      open();
    }
  }, [linkToken, ready, open]);

  const handleClick = () => {
    if (!linkToken) {
      createLinkToken.mutate();
    }
  };

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={handleClick}
      disabled={createLinkToken.isPending || exchangeToken.isPending}
    >
      <Building2 className="mr-2 h-4 w-4" />
      {createLinkToken.isPending
        ? "Connecting..."
        : exchangeToken.isPending
          ? "Linking..."
          : "Connect Bank"}
    </Button>
  );
}

export default function AccountsPage() {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editAccount, setEditAccount] = useState<Account | null>(null);
  const [deleteAccount, setDeleteAccount] = useState<Account | null>(null);
  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["accounts"],
    queryFn: () => api.get<PaginatedResponse<Account>>("/accounts/accounts/"),
  });

  const { data: plaidItems, isLoading: plaidLoading } = useQuery({
    queryKey: ["plaid-items"],
    queryFn: () => plaidApi.listItems(),
  });

  const syncMutation = useMutation({
    mutationFn: (plaidItemId: number) => plaidApi.syncItem(plaidItemId),
    onSuccess: () => toast.success("Sync started — new transactions will appear shortly"),
    onError: (err: Error) => toast.error(err.message),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/accounts/accounts/${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Account deleted");
      setDeleteAccount(null);
      setSelectedAccount(null);
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const accounts = data?.results || [];

  if (isError) {
    return <QueryError message={error?.message} onRetry={refetch} />;
  }

  function handleEditFromSheet(account: Account) {
    setSelectedAccount(null);
    setEditAccount(account);
  }

  function handleDeleteFromSheet(account: Account) {
    setSelectedAccount(null);
    setDeleteAccount(account);
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-muted-foreground">
          {accounts.length} account{accounts.length !== 1 ? "s" : ""}
        </p>
        <div className="flex items-center gap-2">
          <PlaidLinkButton />
          <Button size="sm" onClick={() => setDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Add Manual
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      ) : accounts.length === 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Your accounts, all in one place</CardTitle>
            <CardDescription>
              Add bank accounts, credit cards, and investment accounts to get a complete picture of
              your finances. Everything stays on your machine.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 sm:grid-cols-2">
              {accountExamples.map((example) => (
                <div key={example.label} className="flex items-start gap-3 rounded-lg border p-4">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-secondary">
                    <example.icon className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="font-medium">{example.label}</p>
                    <p className="text-sm text-muted-foreground">{example.description}</p>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-6">
              <Button onClick={() => setDialogOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Add your first account
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {accounts.map((account) => (
            <Card
              key={account.id}
              className="cursor-pointer transition-colors hover:bg-accent/50"
              onClick={() => setSelectedAccount(account)}
            >
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-base font-medium flex items-center gap-2">
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
                </CardTitle>
                <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                  <Badge variant="secondary">{account.account_type}</Badge>
                  <RowActions
                    onEdit={() => setEditAccount(account)}
                    onDelete={() => setDeleteAccount(account)}
                  />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {formatCurrency(account.balance, account.currency)}
                </div>
                {account.institution_name && (
                  <p className="mt-1 text-xs text-muted-foreground">{account.institution_name}</p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Connected Banks (Plaid) */}
      {plaidLoading && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-muted-foreground">Connected Banks</h3>
          <div className="text-sm text-muted-foreground">Loading...</div>
        </div>
      )}
      {plaidItems && plaidItems.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-muted-foreground">Connected Banks</h3>
          <div className="space-y-1">
            {plaidItems.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between rounded-md border px-3 py-2"
              >
                <div className="flex items-center gap-2">
                  <Building2 className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <div className="text-sm font-medium">{item.institution_name}</div>
                    <div className="text-xs text-muted-foreground">
                      {item.last_synced_at
                        ? `Last synced: ${new Date(item.last_synced_at).toLocaleString()}`
                        : "Never synced"}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge
                    variant={item.status === "active" ? "default" : "destructive"}
                    className="text-[10px]"
                  >
                    {item.status}
                  </Badge>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0"
                    onClick={() => syncMutation.mutate(item.id)}
                    disabled={syncMutation.isPending || item.status !== "active"}
                    aria-label={`Sync ${item.institution_name}`}
                  >
                    <RefreshCw
                      className={`h-3.5 w-3.5 ${syncMutation.isPending ? "animate-spin" : ""}`}
                    />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <AddAccountDialog
        open={dialogOpen || !!editAccount}
        onOpenChange={(open) => {
          if (!open) {
            setDialogOpen(false);
            setEditAccount(null);
          }
        }}
        editAccount={editAccount}
      />

      <AccountDetailSheet
        account={selectedAccount}
        open={!!selectedAccount}
        onOpenChange={(open) => !open && setSelectedAccount(null)}
        onEdit={handleEditFromSheet}
        onDelete={handleDeleteFromSheet}
      />

      <ConfirmDialog
        open={!!deleteAccount}
        onOpenChange={(open) => !open && setDeleteAccount(null)}
        title="Delete Account"
        description={`Are you sure you want to delete "${deleteAccount?.name}"? This action cannot be undone.`}
        onConfirm={() => deleteAccount && deleteMutation.mutate(deleteAccount.id)}
        destructive
        loading={deleteMutation.isPending}
      />
    </div>
  );
}
