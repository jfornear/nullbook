import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Search,
  Upload,
  ArrowRight,
  Plus,
  ChevronLeft,
  ChevronRight,
  Download,
  Copy,
  Trash2,
} from "lucide-react";
import { api } from "@/lib/api";
import type { Transaction, PaginatedResponse } from "@/types";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatCurrency, formatDate } from "@/lib/utils";
import { TableSkeleton } from "@/components/shared/TableSkeleton";
import { QueryError } from "@/components/shared/QueryError";
import { RowActions } from "@/components/shared/RowActions";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { TransactionFilters } from "@/components/transactions/TransactionFilters";
import { DuplicateReview } from "@/components/transactions/DuplicateReview";
import AddTransactionDialog from "@/components/transactions/AddTransactionDialog";

interface Filters {
  dateFrom?: string;
  dateTo?: string;
  account?: string;
  category?: string;
  type?: string;
}

export default function TransactionsPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState<Filters>({});
  const [page, setPage] = useState(1);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editTxn, setEditTxn] = useState<Transaction | null>(null);
  const [deleteTxn, setDeleteTxn] = useState<Transaction | null>(null);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [dupOpen, setDupOpen] = useState(false);
  const [debouncedSearch, setDebouncedSearch] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search), 300);
    return () => clearTimeout(timer);
  }, [search]);

  // Clear selection when filters or page change
  useEffect(() => {
    setSelected(new Set());
  }, [debouncedSearch, filters, page]);

  function buildQueryString() {
    const params = new URLSearchParams();
    if (debouncedSearch) params.set("search", debouncedSearch);
    if (filters.dateFrom) params.set("date_from", filters.dateFrom);
    if (filters.dateTo) params.set("date_to", filters.dateTo);
    if (filters.account) params.set("account", filters.account);
    if (filters.category) params.set("category", filters.category);
    if (filters.type) params.set("transaction_type", filters.type);
    if (page > 1) params.set("page", String(page));
    const qs = params.toString();
    return qs ? `?${qs}` : "";
  }

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["transactions", debouncedSearch, filters, page],
    queryFn: () =>
      api.get<PaginatedResponse<Transaction>>(`/transactions/transactions/${buildQueryString()}`),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/transactions/transactions/${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Transaction deleted");
      setDeleteTxn(null);
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const bulkDeleteMutation = useMutation({
    mutationFn: (ids: number[]) => api.post("/transactions/transactions/bulk_delete/", { ids }),
    onSuccess: (_, ids) => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success(`Deleted ${ids.length} transactions`);
      setSelected(new Set());
    },
    onError: (err: Error) => toast.error(err.message),
  });

  async function handleExport() {
    const qs = buildQueryString();
    try {
      const res = await fetch(
        `${import.meta.env.VITE_API_URL || ""}/api/transactions/transactions/export/${qs}`,
        { credentials: "include" }
      );
      if (!res.ok) {
        toast.error("Export failed");
        return;
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "transactions.csv";
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      toast.error("Export failed");
    }
  }

  const transactions = data?.results || [];
  const totalCount = data?.count || 0;

  function toggleSelect(id: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function toggleSelectAll() {
    if (selected.size === transactions.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(transactions.map((t) => t.id)));
    }
  }

  if (isError) {
    return <QueryError message={error?.message} onRetry={refetch} />;
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search transactions..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="pl-9"
          />
        </div>
        <div className="flex items-center gap-2">
          <Button size="sm" variant="outline" onClick={() => setDupOpen(true)}>
            <Copy className="mr-2 h-4 w-4" />
            Duplicates
          </Button>
          <Button size="sm" variant="outline" onClick={handleExport}>
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
          <Button size="sm" onClick={() => setDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Add Transaction
          </Button>
        </div>
      </div>

      <TransactionFilters
        filters={filters}
        onChange={(f) => {
          setFilters(f);
          setPage(1);
        }}
      />

      {isLoading ? (
        <TableSkeleton rows={8} cols={5} />
      ) : transactions.length === 0 &&
        !search &&
        !filters.dateFrom &&
        !filters.account &&
        !filters.category &&
        !filters.type ? (
        <Card>
          <CardHeader>
            <CardTitle>See where your money goes</CardTitle>
            <CardDescription>
              Import bank and credit card statements to build your complete transaction history.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-start gap-3 rounded-lg border p-4">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-secondary">
                  <Upload className="h-4 w-4" />
                </div>
                <div className="flex-1">
                  <p className="font-medium">Import from CSV</p>
                  <p className="text-sm text-muted-foreground">
                    Most banks let you download transactions as CSV. Go to your bank's website,
                    export your recent transactions, and upload the file here.
                  </p>
                  <Button variant="outline" size="sm" className="mt-3" asChild>
                    <Link to="/import">
                      Go to Import
                      <ArrowRight className="ml-2 h-3 w-3" />
                    </Link>
                  </Button>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setDialogOpen(true)}
                className="flex w-full cursor-pointer items-start gap-3 rounded-lg border p-4 text-left transition-colors hover:bg-accent"
              >
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-secondary">
                  <Plus className="h-4 w-4" />
                </div>
                <div className="flex-1">
                  <p className="font-medium">Add manually</p>
                  <p className="text-sm text-muted-foreground">
                    Useful for cash purchases or one-off entries that don't appear on statements.
                  </p>
                </div>
              </button>
            </div>
          </CardContent>
        </Card>
      ) : transactions.length === 0 ? (
        <div className="py-12 text-center text-muted-foreground">No transactions found</div>
      ) : (
        <>
          {/* Bulk action bar */}
          {selected.size > 0 && (
            <div className="flex items-center gap-3 rounded-lg border bg-muted/50 px-4 py-2">
              <span className="text-sm font-medium">{selected.size} selected</span>
              <Button
                size="sm"
                variant="destructive"
                onClick={() => bulkDeleteMutation.mutate([...selected])}
                disabled={bulkDeleteMutation.isPending}
              >
                <Trash2 className="mr-2 h-3.5 w-3.5" />
                Delete
              </Button>
              <Button size="sm" variant="ghost" onClick={() => setSelected(new Set())}>
                Clear
              </Button>
            </div>
          )}

          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-10">
                    <Checkbox
                      checked={transactions.length > 0 && selected.size === transactions.length}
                      onCheckedChange={toggleSelectAll}
                    />
                  </TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead className="hidden md:table-cell">Category</TableHead>
                  <TableHead className="hidden md:table-cell">Type</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead className="w-10" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {transactions.map((txn) => (
                  <TableRow key={txn.id} className="cursor-pointer" onClick={() => setEditTxn(txn)}>
                    <TableCell onClick={(e) => e.stopPropagation()}>
                      <Checkbox
                        checked={selected.has(txn.id)}
                        onCheckedChange={() => toggleSelect(txn.id)}
                      />
                    </TableCell>
                    <TableCell className="whitespace-nowrap">{formatDate(txn.date)}</TableCell>
                    <TableCell>{txn.description}</TableCell>
                    <TableCell className="hidden md:table-cell">
                      {txn.category_name ? (
                        <Badge variant="secondary">{txn.category_name}</Badge>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell className="hidden md:table-cell">
                      <Badge variant={txn.transaction_type === "income" ? "default" : "outline"}>
                        {txn.transaction_type}
                      </Badge>
                    </TableCell>
                    <TableCell
                      className={`text-right font-medium ${txn.transaction_type === "income" ? "text-green-600" : "text-red-600"}`}
                    >
                      {txn.transaction_type === "income" ? "+" : "-"}
                      {formatCurrency(txn.amount)}
                    </TableCell>
                    <TableCell onClick={(e) => e.stopPropagation()}>
                      <RowActions
                        onEdit={() => setEditTxn(txn)}
                        onDelete={() => setDeleteTxn(txn)}
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {(data?.next || data?.previous) && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                {totalCount} transaction{totalCount !== 1 ? "s" : ""}
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={!data?.previous}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <span className="text-sm text-muted-foreground">Page {page}</span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={!data?.next}
                  onClick={() => setPage((p) => p + 1)}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </>
      )}

      <AddTransactionDialog
        open={dialogOpen || !!editTxn}
        onOpenChange={(open) => {
          if (!open) {
            setDialogOpen(false);
            setEditTxn(null);
          }
        }}
        editTransaction={editTxn}
      />

      <ConfirmDialog
        open={!!deleteTxn}
        onOpenChange={(open) => !open && setDeleteTxn(null)}
        title="Delete Transaction"
        description={`Are you sure you want to delete "${deleteTxn?.description}"? This action cannot be undone.`}
        onConfirm={() => deleteTxn && deleteMutation.mutate(deleteTxn.id)}
        destructive
        loading={deleteMutation.isPending}
      />

      <DuplicateReview open={dupOpen} onOpenChange={setDupOpen} />
    </div>
  );
}
