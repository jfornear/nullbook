import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { api } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import type { Budget, PaginatedResponse } from "@/types";
import { CreateBudgetDialog } from "@/components/budgets/CreateBudgetDialog";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";

function BudgetProgressBar({ spent, amount }: { spent: number; amount: number }) {
  const pct = amount > 0 ? (spent / amount) * 100 : 0;
  const clamped = Math.min(pct, 100);
  const color = pct >= 100 ? "bg-red-500" : pct >= 80 ? "bg-yellow-500" : "bg-green-500";
  return (
    <div className="space-y-1">
      <div className="h-2 w-full rounded-full bg-muted">
        <div
          className={`h-2 rounded-full transition-all ${color}`}
          style={{ width: `${clamped}%` }}
        />
      </div>
      <div className="flex justify-between text-[10px] text-muted-foreground">
        <span>{formatCurrency(String(spent))} spent</span>
        <span>{Math.round(pct)}%</span>
      </div>
    </div>
  );
}

export function BudgetsContent() {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteBudget, setDeleteBudget] = useState<Budget | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["budgets"],
    queryFn: () => api.get<PaginatedResponse<Budget>>("/transactions/budgets/"),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/transactions/budgets/${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["budgets"] });
      toast.success("Budget deleted");
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const budgets = data?.results || [];

  return (
    <>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            {budgets.length} budget{budgets.length !== 1 ? "s" : ""}
          </p>
          <Button size="sm" onClick={() => setDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Add Budget
          </Button>
        </div>

        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-20 rounded-lg bg-muted animate-pulse" />
            ))}
          </div>
        ) : budgets.length === 0 ? (
          <Card>
            <CardHeader>
              <CardTitle>Set spending limits</CardTitle>
              <CardDescription>
                Create budgets for spending categories to track where your money goes and stay on
                target.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={() => setDialogOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Create your first budget
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {budgets.map((budget) => {
              const spent = parseFloat(budget.spent);
              const amount = parseFloat(budget.amount);
              return (
                <div key={budget.id} className="rounded-lg border p-3 space-y-2">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm font-medium">{budget.category_name}</div>
                      <div className="text-xs text-muted-foreground capitalize">
                        {formatCurrency(budget.amount)} / {budget.period}
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7"
                      aria-label={`Delete budget: ${budget.category_name}`}
                      onClick={() => setDeleteBudget(budget)}
                      disabled={deleteMutation.isPending && deleteMutation.variables === budget.id}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                  <BudgetProgressBar spent={spent} amount={amount} />
                </div>
              );
            })}
          </div>
        )}
      </div>

      <CreateBudgetDialog open={dialogOpen} onOpenChange={setDialogOpen} />

      <ConfirmDialog
        open={!!deleteBudget}
        onOpenChange={(v) => !v && setDeleteBudget(null)}
        title="Delete Budget"
        description={`Delete the ${deleteBudget?.category_name} budget? This cannot be undone.`}
        onConfirm={() => {
          if (deleteBudget) {
            deleteMutation.mutate(deleteBudget.id, {
              onSuccess: () => setDeleteBudget(null),
            });
          }
        }}
        destructive
        loading={deleteMutation.isPending}
      />
    </>
  );
}
