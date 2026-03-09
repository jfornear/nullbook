import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";

interface DuplicatePair {
  transaction_a: {
    id: number;
    date: string;
    description: string;
    amount: string;
    account: string | null;
    category: string | null;
  };
  transaction_b: {
    id: number;
    date: string;
    description: string;
    amount: string;
    account: string | null;
    category: string | null;
  };
  confidence: number;
}

interface DuplicateReviewProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function TxnCard({ txn, label }: { txn: DuplicatePair["transaction_a"]; label: string }) {
  return (
    <div className="rounded-md border p-3 space-y-1">
      <div className="text-[10px] text-muted-foreground uppercase font-medium">{label}</div>
      <div className="text-sm font-medium">{txn.description}</div>
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <span>{formatDate(txn.date)}</span>
        <span>{formatCurrency(txn.amount)}</span>
      </div>
      <div className="flex gap-1">
        {txn.account && (
          <Badge variant="outline" className="text-[9px]">
            {txn.account}
          </Badge>
        )}
        {txn.category && (
          <Badge variant="secondary" className="text-[9px]">
            {txn.category}
          </Badge>
        )}
      </div>
    </div>
  );
}

export function DuplicateReview({ open, onOpenChange }: DuplicateReviewProps) {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["transaction-duplicates"],
    queryFn: () =>
      api.get<{ duplicates: DuplicatePair[]; count: number }>(
        "/transactions/transactions/duplicates/"
      ),
    enabled: open,
  });

  const mergeMutation = useMutation({
    mutationFn: (args: { keep_id: number; delete_id: number }) =>
      api.post("/transactions/transactions/merge_duplicates/", args),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transaction-duplicates"] });
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      toast.success("Duplicate merged");
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const pairs = data?.duplicates || [];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Review Duplicates ({pairs.length})</DialogTitle>
          <DialogDescription>
            Transactions that may be duplicates. Merge or dismiss each pair.
          </DialogDescription>
        </DialogHeader>
        {isLoading ? (
          <div className="py-8 text-center text-sm text-muted-foreground">Scanning...</div>
        ) : pairs.length === 0 ? (
          <div className="py-8 text-center text-sm text-muted-foreground">No duplicates found</div>
        ) : (
          <div className="space-y-4">
            {pairs.map((pair) => (
              <div
                key={`${pair.transaction_a.id}-${pair.transaction_b.id}`}
                className="rounded-lg border p-3 space-y-2"
              >
                <div className="flex items-center justify-between">
                  <Badge variant="secondary" className="text-[10px]">
                    {Math.round(pair.confidence * 100)}% match
                  </Badge>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <TxnCard txn={pair.transaction_a} label="Keep" />
                  <TxnCard txn={pair.transaction_b} label="Remove" />
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="default"
                    className="flex-1"
                    onClick={() =>
                      mergeMutation.mutate({
                        keep_id: pair.transaction_a.id,
                        delete_id: pair.transaction_b.id,
                      })
                    }
                    disabled={
                      mergeMutation.isPending &&
                      (mergeMutation.variables?.keep_id === pair.transaction_a.id ||
                        mergeMutation.variables?.delete_id === pair.transaction_b.id)
                    }
                  >
                    Keep Left
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="flex-1"
                    onClick={() =>
                      mergeMutation.mutate({
                        keep_id: pair.transaction_b.id,
                        delete_id: pair.transaction_a.id,
                      })
                    }
                    disabled={
                      mergeMutation.isPending &&
                      (mergeMutation.variables?.keep_id === pair.transaction_b.id ||
                        mergeMutation.variables?.delete_id === pair.transaction_a.id)
                    }
                  >
                    Keep Right
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
