import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Plus } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import type { PaginatedResponse } from "@/types";
import { RowActions } from "@/components/shared/RowActions";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { CreateSubscriptionDialog } from "@/components/subscriptions/CreateSubscriptionDialog";

interface Subscription {
  id: number;
  merchant: string;
  amount: string;
  frequency: string;
  status: string;
  last_charged: string | null;
  next_expected: string | null;
  annual_cost: number;
  cancellation_url: string;
  notes?: string;
}

const statusColor: Record<string, string> = {
  active: "bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-400",
  cancelled: "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-400",
  cancellation_pending: "bg-yellow-100 text-yellow-700 dark:bg-yellow-950 dark:text-yellow-400",
  possibly_cancelled: "bg-orange-100 text-orange-700 dark:bg-orange-950 dark:text-orange-400",
};

function statusLabel(status: string): string {
  return status.replace(/_/g, " ");
}

function groupByStatus(subscriptions: Subscription[]) {
  const groups: Record<string, Subscription[]> = {};
  for (const sub of subscriptions) {
    if (!groups[sub.status]) groups[sub.status] = [];
    groups[sub.status].push(sub);
  }
  return groups;
}

const FREQUENCY_MONTHLY_FACTOR: Record<string, number> = {
  weekly: 52 / 12,
  biweekly: 26 / 12,
  monthly: 1,
  quarterly: 1 / 3,
  semi_annual: 1 / 6,
  annual: 1 / 12,
};

export function SubscriptionsContent() {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editSub, setEditSub] = useState<Subscription | null>(null);
  const [deleteSub, setDeleteSub] = useState<Subscription | null>(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["subscriptions"],
    queryFn: () => api.get<PaginatedResponse<Subscription>>("/transactions/subscriptions/"),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/transactions/subscriptions/${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["subscriptions"] });
      toast.success("Subscription deleted");
      setDeleteSub(null);
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const cancelMutation = useMutation({
    mutationFn: (id: number) =>
      api.patch(`/transactions/subscriptions/${id}/`, { status: "cancellation_pending" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["subscriptions"] });
      toast.success("Subscription marked for cancellation");
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const subscriptions = data?.results ?? [];

  const totalMonthly = subscriptions.reduce((sum, s) => {
    if (s.status === "cancelled") return sum;
    const factor = FREQUENCY_MONTHLY_FACTOR[s.frequency] ?? 1;
    return sum + parseFloat(s.amount) * factor;
  }, 0);

  const totalAnnual = subscriptions.reduce((sum, s) => {
    if (s.status === "cancelled") return sum;
    return sum + (s.annual_cost ?? 0);
  }, 0);

  return (
    <>
      <div className="space-y-4">
        <div className="flex justify-end">
          <Button size="sm" className="h-7 text-xs gap-1" onClick={() => setDialogOpen(true)}>
            <Plus className="h-3 w-3" />
            Add
          </Button>
        </div>
        {isError ? (
          <div className="py-8 text-center text-sm text-muted-foreground">
            Failed to load subscriptions. Try again later.
          </div>
        ) : isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        ) : null}

        {data && (
          <>
            {/* Totals */}
            <div className="flex gap-4">
              <div className="rounded-md border px-4 py-2 flex-1 text-center">
                <div className="text-xs text-muted-foreground">Monthly</div>
                <div className="text-lg font-semibold">{formatCurrency(totalMonthly)}</div>
              </div>
              <div className="rounded-md border px-4 py-2 flex-1 text-center">
                <div className="text-xs text-muted-foreground">Annual</div>
                <div className="text-lg font-semibold">{formatCurrency(totalAnnual)}</div>
              </div>
            </div>

            <Separator />

            {/* Subscriptions grouped by status */}
            {Object.entries(groupByStatus(subscriptions)).map(([status, subs]) => (
              <div key={status}>
                <div className="flex items-center gap-2 mb-2">
                  <span
                    className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium capitalize ${
                      statusColor[status] || "bg-muted text-muted-foreground"
                    }`}
                  >
                    {statusLabel(status)}
                  </span>
                  <span className="text-xs text-muted-foreground">({subs.length})</span>
                </div>
                <div className="space-y-1">
                  {subs.map((sub) => (
                    <div
                      key={sub.id}
                      className="flex items-center justify-between rounded-md border px-3 py-2"
                    >
                      <div>
                        <div className="text-sm font-medium">{sub.merchant}</div>
                        <div className="text-xs text-muted-foreground capitalize">
                          {sub.frequency}
                          {sub.next_expected && ` · Next: ${sub.next_expected}`}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="text-right">
                          <div className="text-sm font-medium">{formatCurrency(sub.amount)}</div>
                          <div className="text-xs text-muted-foreground">
                            {formatCurrency(sub.annual_cost)}/yr
                          </div>
                        </div>
                        <div className="flex items-center gap-1">
                          {sub.status === "active" && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 text-xs px-2"
                              onClick={() => cancelMutation.mutate(sub.id)}
                              disabled={
                                cancelMutation.isPending && cancelMutation.variables === sub.id
                              }
                            >
                              Cancel
                            </Button>
                          )}
                          <RowActions
                            onEdit={() => setEditSub(sub)}
                            onDelete={() => setDeleteSub(sub)}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}

            {subscriptions.length === 0 && (
              <div className="text-center text-sm text-muted-foreground py-8">
                No subscriptions detected yet. Ask the assistant to scan your transactions.
              </div>
            )}
          </>
        )}
      </div>

      <CreateSubscriptionDialog
        open={dialogOpen || !!editSub}
        onOpenChange={(open) => {
          if (!open) {
            setDialogOpen(false);
            setEditSub(null);
          }
        }}
        editSubscription={editSub}
      />

      <ConfirmDialog
        open={!!deleteSub}
        onOpenChange={(open) => !open && setDeleteSub(null)}
        title="Delete Subscription"
        description={`Delete ${deleteSub?.merchant}? This action cannot be undone.`}
        onConfirm={() => deleteSub && deleteMutation.mutate(deleteSub.id)}
        destructive
        loading={deleteMutation.isPending}
      />
    </>
  );
}
