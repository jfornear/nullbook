import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { RefreshCw, CheckCircle2, XCircle, Loader2 } from "lucide-react";

interface SyncItem {
  name: string;
  status: string;
  last_synced?: string | null;
  account_count?: number;
  transaction_count?: number;
  error?: string;
  message?: string;
}

interface SyncStatusData {
  items: SyncItem[];
  message?: string;
  status?: string;
}

const statusIcons: Record<string, typeof CheckCircle2> = {
  success: CheckCircle2,
  synced: CheckCircle2,
  connected: CheckCircle2,
  error: XCircle,
  failed: XCircle,
  syncing: Loader2,
  pending: Loader2,
};

const statusColors: Record<string, string> = {
  success: "text-green-600",
  synced: "text-green-600",
  connected: "text-green-600",
  error: "text-red-600",
  failed: "text-red-600",
  syncing: "text-blue-500",
  pending: "text-muted-foreground",
};

const statusBadgeVariant: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  success: "default",
  synced: "default",
  connected: "default",
  error: "destructive",
  failed: "destructive",
  syncing: "secondary",
  pending: "outline",
};

export function SyncStatus({ data }: { data: unknown }) {
  const d = data as SyncStatusData;

  if (!d.items || d.items.length === 0) {
    return (
      <Card>
        <CardContent className="py-4 text-center text-sm text-muted-foreground">
          {d.message || "No items to display."}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-sm">
          <RefreshCw className="h-4 w-4" />
          Sync Status
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {d.message && <div className="text-xs text-muted-foreground mb-2">{d.message}</div>}

        {d.items.map((item, i) => {
          const Icon = statusIcons[item.status] || CheckCircle2;
          const color = statusColors[item.status] || "text-muted-foreground";
          const badgeVariant = statusBadgeVariant[item.status] || "outline";
          const isSpinning = item.status === "syncing" || item.status === "pending";

          return (
            <div key={i} className="flex items-center gap-3 rounded-md border px-3 py-2.5">
              <Icon className={`h-4 w-4 shrink-0 ${color} ${isSpinning ? "animate-spin" : ""}`} />
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium">{item.name}</div>
                {item.last_synced && (
                  <div className="text-xs text-muted-foreground">
                    Last synced: {item.last_synced}
                  </div>
                )}
                {item.account_count != null && (
                  <div className="text-xs text-muted-foreground">
                    {item.account_count} account{item.account_count !== 1 ? "s" : ""}
                    {item.transaction_count != null && (
                      <span>
                        {" "}
                        / {item.transaction_count} transaction
                        {item.transaction_count !== 1 ? "s" : ""}
                      </span>
                    )}
                  </div>
                )}
                {item.error && <div className="text-xs text-red-600">{item.error}</div>}
                {item.message && (
                  <div className="text-xs text-muted-foreground">{item.message}</div>
                )}
              </div>
              <Badge variant={badgeVariant} className="text-[10px] capitalize shrink-0">
                {item.status}
              </Badge>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
