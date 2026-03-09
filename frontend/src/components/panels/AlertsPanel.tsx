import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Info, AlertTriangle, AlertOctagon, CheckCheck, X, Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import type { PaginatedResponse } from "@/types";

interface Alert {
  id: number;
  alert_type: string;
  severity: string;
  title: string;
  message: string;
  is_read: boolean;
  action_url: string | null;
  created_at: string;
}

type SeverityFilter = "all" | "info" | "warning" | "urgent";

const severityConfig: Record<string, { icon: typeof Info; color: string }> = {
  info: { icon: Info, color: "text-blue-500" },
  warning: { icon: AlertTriangle, color: "text-yellow-500" },
  urgent: { icon: AlertOctagon, color: "text-red-500" },
};

export function AlertsContent() {
  const queryClient = useQueryClient();
  const [severityFilter, setSeverityFilter] = useState<SeverityFilter>("all");
  const [unreadOnly, setUnreadOnly] = useState(false);

  const params = new URLSearchParams();
  if (severityFilter !== "all") params.set("severity", severityFilter);
  if (unreadOnly) params.set("unread", "true");
  const qs = params.toString();

  const { data } = useQuery({
    queryKey: ["alerts", severityFilter, unreadOnly],
    queryFn: () => api.get<PaginatedResponse<Alert>>(`/alerts/${qs ? `?${qs}` : ""}`),
  });

  const alerts = data?.results ?? [];
  const isLoading = !data;
  const unreadCount = alerts.filter((a) => !a.is_read).length;
  const readCount = alerts.filter((a) => a.is_read).length;

  const markRead = useMutation({
    mutationFn: (alertId: number) => api.post("/alerts/mark-read/", { alert_ids: [alertId] }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const markAllRead = useMutation({
    mutationFn: () => api.post("/alerts/mark-read/"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const dismissAlert = useMutation({
    mutationFn: (alertId: number) => api.post("/alerts/delete/", { alert_ids: [alertId] }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const clearRead = useMutation({
    mutationFn: () => api.post("/alerts/delete/"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
    },
    onError: (err: Error) => toast.error(err.message),
  });

  return (
    <div>
      <div className="flex flex-wrap items-center gap-2 mb-4">
        {unreadCount > 0 && (
          <Button
            variant="ghost"
            size="sm"
            className="h-7 text-xs gap-1"
            onClick={() => markAllRead.mutate()}
            disabled={markAllRead.isPending}
          >
            <CheckCheck className="h-3 w-3" />
            Mark all read
          </Button>
        )}
        {readCount > 0 && (
          <Button
            variant="ghost"
            size="sm"
            className="h-7 text-xs gap-1 text-red-500"
            onClick={() => clearRead.mutate()}
            disabled={clearRead.isPending}
          >
            <Trash2 className="h-3 w-3" />
            Clear read
          </Button>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        {(["all", "info", "warning", "urgent"] as SeverityFilter[]).map((f) => (
          <Button
            key={f}
            variant={severityFilter === f ? "default" : "outline"}
            size="sm"
            className="h-7 text-xs capitalize"
            onClick={() => setSeverityFilter(f)}
          >
            {f}
          </Button>
        ))}
        <Button
          variant={unreadOnly ? "default" : "outline"}
          size="sm"
          className="h-7 text-xs"
          onClick={() => setUnreadOnly(!unreadOnly)}
        >
          Unread only
        </Button>
      </div>

      <div className="mt-2 space-y-2">
        {isLoading && (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        )}

        {data && alerts.length === 0 && (
          <div className="text-center text-sm text-muted-foreground py-8">
            No alerts at this time.
          </div>
        )}

        {alerts.map((alert) => {
          const config = severityConfig[alert.severity] || severityConfig.info;
          const Icon = config.icon;

          return (
            <div
              key={alert.id}
              className={`flex items-start gap-3 rounded-md border px-3 py-2.5 ${
                !alert.is_read ? "bg-muted/30" : ""
              }`}
            >
              <Icon className={`h-4 w-4 mt-0.5 shrink-0 ${config.color}`} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="text-sm font-medium">{alert.title}</span>
                  {!alert.is_read && (
                    <span className="h-1.5 w-1.5 rounded-full bg-blue-500 shrink-0" />
                  )}
                </div>
                <div className="text-xs text-muted-foreground">{alert.message}</div>
                <div className="flex items-center gap-2 mt-1">
                  <Badge
                    variant={
                      alert.severity === "urgent"
                        ? "destructive"
                        : alert.severity === "warning"
                          ? "outline"
                          : "secondary"
                    }
                    className="text-[10px] capitalize"
                  >
                    {alert.severity}
                  </Badge>
                  <Badge variant="outline" className="text-[10px] capitalize">
                    {alert.alert_type.replace(/_/g, " ")}
                  </Badge>
                  <span className="text-[10px] text-muted-foreground">
                    {formatDate(alert.created_at)}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-1 shrink-0">
                {!alert.is_read && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 text-[10px] px-2"
                    onClick={() => markRead.mutate(alert.id)}
                    disabled={markRead.isPending && markRead.variables === alert.id}
                  >
                    Read
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 text-muted-foreground hover:text-destructive"
                  onClick={() => dismissAlert.mutate(alert.id)}
                  disabled={dismissAlert.isPending && dismissAlert.variables === alert.id}
                >
                  <X className="h-3 w-3" />
                </Button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
