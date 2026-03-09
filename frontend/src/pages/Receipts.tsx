import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Upload, Image, Loader2, Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import { QueryError } from "@/components/shared/QueryError";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { ReceiptDetailSheet } from "@/components/taxes/ReceiptDetailSheet";

interface ReceiptItem {
  id: number;
  image_url: string | null;
  status: string;
  merchant: string;
  date: string | null;
  total_amount: string | null;
  category: string;
  created_at: string;
}

const statusVariant: Record<string, "default" | "secondary" | "outline" | "destructive"> = {
  completed: "default",
  processing: "secondary",
  pending: "outline",
  failed: "destructive",
};

export default function ReceiptsPage() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [selectedReceiptId, setSelectedReceiptId] = useState<number | null>(null);
  const [deleteReceipt, setDeleteReceipt] = useState<ReceiptItem | null>(null);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["receipts", statusFilter],
    queryFn: async () => {
      const params = statusFilter ? `?status=${statusFilter}` : "";
      return api.get<{ results: ReceiptItem[] }>(`/taxes/receipts/${params}`);
    },
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => {
      const formData = new FormData();
      formData.append("image", file);
      return api.upload("/taxes/receipts/", formData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["receipts"] });
      toast.success("Receipt uploaded");
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/taxes/receipts/${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["receipts"] });
      toast.success("Receipt deleted");
      setDeleteReceipt(null);
    },
    onError: (err: Error) => toast.error(err.message),
  });

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file && (file.type.startsWith("image/") || file.type === "application/pdf")) {
      uploadMutation.mutate(file);
    }
  }

  const receipts = data?.results || [];

  if (isError) {
    return <QueryError message={error?.message} onRetry={refetch} />;
  }

  return (
    <div className="space-y-4">
      {/* Upload area */}
      <div
        role="button"
        tabIndex={0}
        className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-6 text-center cursor-pointer hover:border-primary/50 transition-colors"
        onDragOver={(e) => e.preventDefault()}
        onDragEnter={(e) => e.preventDefault()}
        onDrop={handleDrop}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            e.currentTarget.click();
          }
        }}
        onClick={() => {
          const input = document.createElement("input");
          input.type = "file";
          input.accept = "image/*,application/pdf";
          input.onchange = (e) => {
            const file = (e.target as HTMLInputElement).files?.[0];
            if (file) uploadMutation.mutate(file);
          };
          input.click();
        }}
      >
        {uploadMutation.isPending ? (
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        ) : (
          <>
            <Upload className="h-8 w-8 text-muted-foreground mb-2" />
            <div className="text-sm text-muted-foreground">
              Drop receipt image or PDF, or click to upload
            </div>
          </>
        )}
      </div>

      {/* Status filters */}
      <div className="flex flex-wrap gap-1">
        {[null, "completed", "processing", "pending", "failed"].map((s) => (
          <Button
            key={s || "all"}
            variant={statusFilter === s ? "secondary" : "ghost"}
            size="sm"
            className="h-7 text-xs"
            onClick={() => setStatusFilter(s)}
          >
            {s || "All"}
          </Button>
        ))}
      </div>

      {/* Receipt grid */}
      {isLoading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : receipts.length === 0 ? (
        <div className="text-center py-8 text-sm text-muted-foreground">
          No receipts yet. Upload one to get started.
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {receipts.map((r) => (
            <div
              key={r.id}
              className="rounded-lg border overflow-hidden group relative cursor-pointer"
              onClick={() => setSelectedReceiptId(r.id)}
            >
              <div className="aspect-square bg-muted flex items-center justify-center">
                {r.image_url ? (
                  <img
                    src={r.image_url}
                    alt={r.merchant || "Receipt"}
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <Image className="h-8 w-8 text-muted-foreground" />
                )}
              </div>
              <Button
                variant="destructive"
                size="icon"
                className="absolute top-1 right-1 h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={(e) => {
                  e.stopPropagation();
                  setDeleteReceipt(r);
                }}
                aria-label={`Delete receipt from ${r.merchant || "unknown merchant"}`}
              >
                <Trash2 className="h-3 w-3" />
              </Button>
              <div className="p-2">
                <div className="text-xs font-medium truncate">{r.merchant || "Processing..."}</div>
                <div className="flex items-center justify-between mt-1">
                  <span className="text-xs text-muted-foreground">
                    {r.total_amount ? `$${parseFloat(r.total_amount).toFixed(2)}` : "—"}
                  </span>
                  <Badge variant={statusVariant[r.status] || "outline"} className="text-[9px] px-1">
                    {r.status}
                  </Badge>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <ReceiptDetailSheet
        receiptId={selectedReceiptId}
        open={!!selectedReceiptId}
        onOpenChange={(open) => !open && setSelectedReceiptId(null)}
      />

      <ConfirmDialog
        open={!!deleteReceipt}
        onOpenChange={(open) => !open && setDeleteReceipt(null)}
        title="Delete Receipt"
        description={`Delete receipt from ${deleteReceipt?.merchant || "unknown merchant"}? This action cannot be undone.`}
        onConfirm={() => deleteReceipt && deleteMutation.mutate(deleteReceipt.id)}
        destructive
        loading={deleteMutation.isPending}
      />
    </div>
  );
}
