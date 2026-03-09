import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Plus, Trash2, Target } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { api } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import type { Goal, PaginatedResponse } from "@/types";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";

function ProgressRing({ pct }: { pct: number }) {
  const r = 20;
  const c = 2 * Math.PI * r;
  const offset = c - (Math.min(pct, 100) / 100) * c;
  const color = pct >= 100 ? "#22c55e" : pct >= 50 ? "#eab308" : "#3b82f6";

  return (
    <svg width="52" height="52" className="shrink-0">
      <circle
        cx="26"
        cy="26"
        r={r}
        fill="none"
        stroke="currentColor"
        strokeWidth="4"
        className="text-muted"
      />
      <circle
        cx="26"
        cy="26"
        r={r}
        fill="none"
        stroke={color}
        strokeWidth="4"
        strokeDasharray={c}
        strokeDashoffset={offset}
        strokeLinecap="round"
        transform="rotate(-90 26 26)"
      />
      <text
        x="26"
        y="26"
        textAnchor="middle"
        dominantBaseline="central"
        className="fill-foreground text-[10px] font-medium"
      >
        {Math.round(pct)}%
      </text>
    </svg>
  );
}

function GoalAmountInput({
  goal,
  onUpdate,
}: {
  goal: Goal;
  onUpdate: (id: number, amount: string) => void;
}) {
  const [value, setValue] = useState(goal.current_amount);
  useEffect(() => {
    setValue(goal.current_amount);
  }, [goal.current_amount]);
  return (
    <div className="mt-2 flex items-center gap-2">
      <Input
        type="number"
        step="0.01"
        className="h-7 text-xs"
        placeholder="Update amount"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onBlur={() => {
          if (value !== goal.current_amount) {
            onUpdate(goal.id, value);
          }
        }}
      />
    </div>
  );
}

export function GoalsContent() {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteGoal, setDeleteGoal] = useState<Goal | null>(null);
  const [name, setName] = useState("");
  const [targetAmount, setTargetAmount] = useState("");
  const [currentAmount, setCurrentAmount] = useState("0");
  const [targetDate, setTargetDate] = useState("");

  const { data, isLoading, isError } = useQuery({
    queryKey: ["goals"],
    queryFn: () => api.get<PaginatedResponse<Goal>>("/transactions/goals/"),
  });

  const createMutation = useMutation({
    mutationFn: (data: Partial<Goal>) => api.post("/transactions/goals/", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["goals"] });
      toast.success("Goal created");
      setDialogOpen(false);
      setName("");
      setTargetAmount("");
      setCurrentAmount("0");
      setTargetDate("");
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/transactions/goals/${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["goals"] });
      toast.success("Goal deleted");
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, current_amount }: { id: number; current_amount: string }) =>
      api.patch(`/transactions/goals/${id}/`, { current_amount }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["goals"] });
      toast.success("Progress updated");
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const goals = data?.results || [];

  function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    createMutation.mutate({
      name,
      target_amount: targetAmount,
      current_amount: currentAmount,
      target_date: targetDate || null,
    });
  }

  return (
    <>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            {goals.length} goal{goals.length !== 1 ? "s" : ""}
          </p>
          <Button size="sm" onClick={() => setDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Add Goal
          </Button>
        </div>

        {isError ? (
          <div className="py-8 text-center text-sm text-muted-foreground">
            Failed to load goals. Try again later.
          </div>
        ) : isLoading ? (
          <div className="space-y-3">
            {[1, 2].map((i) => (
              <div key={i} className="h-20 rounded-lg bg-muted animate-pulse" />
            ))}
          </div>
        ) : goals.length === 0 ? (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" />
                Set financial goals
              </CardTitle>
              <CardDescription>
                Track your savings goals — emergency fund, vacation, home down payment, or anything
                else.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={() => setDialogOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Create your first goal
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {goals.map((goal) => (
              <div key={goal.id} className="rounded-lg border p-3">
                <div className="flex items-center gap-3">
                  <ProgressRing pct={goal.progress_pct} />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium truncate">{goal.name}</div>
                    <div className="text-xs text-muted-foreground">
                      {formatCurrency(goal.current_amount)} / {formatCurrency(goal.target_amount)}
                    </div>
                    {goal.target_date && (
                      <div className="text-[10px] text-muted-foreground">
                        Target: {new Date(goal.target_date).toLocaleDateString()}
                      </div>
                    )}
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 shrink-0"
                    aria-label={`Delete goal: ${goal.name}`}
                    onClick={() => setDeleteGoal(goal)}
                    disabled={deleteMutation.isPending && deleteMutation.variables === goal.id}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
                <GoalAmountInput
                  goal={goal}
                  onUpdate={(id, current_amount) => updateMutation.mutate({ id, current_amount })}
                />
              </div>
            ))}
          </div>
        )}
      </div>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Goal</DialogTitle>
            <DialogDescription>Set a savings target to track your progress.</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="space-y-2">
              <Label>Goal Name</Label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Emergency fund"
                required
              />
            </div>
            <div className="space-y-2">
              <Label>Target Amount</Label>
              <Input
                type="number"
                step="0.01"
                value={targetAmount}
                onChange={(e) => setTargetAmount(e.target.value)}
                placeholder="10000"
                required
              />
            </div>
            <div className="space-y-2">
              <Label>Current Amount</Label>
              <Input
                type="number"
                step="0.01"
                value={currentAmount}
                onChange={(e) => setCurrentAmount(e.target.value)}
                placeholder="0"
              />
            </div>
            <div className="space-y-2">
              <Label>Target Date (optional)</Label>
              <Input
                type="date"
                value={targetDate}
                onChange={(e) => setTargetDate(e.target.value)}
              />
            </div>
            <Button type="submit" className="w-full" disabled={createMutation.isPending}>
              {createMutation.isPending ? "Creating..." : "Create Goal"}
            </Button>
          </form>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={!!deleteGoal}
        onOpenChange={(v) => !v && setDeleteGoal(null)}
        title="Delete Goal"
        description={`Delete "${deleteGoal?.name}"? This cannot be undone.`}
        onConfirm={() => {
          if (deleteGoal) {
            deleteMutation.mutate(deleteGoal.id, {
              onSuccess: () => setDeleteGoal(null),
            });
          }
        }}
        destructive
        loading={deleteMutation.isPending}
      />
    </>
  );
}
