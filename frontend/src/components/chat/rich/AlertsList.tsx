import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Info, AlertTriangle, AlertOctagon, Bell } from "lucide-react";
import { formatDate } from "@/lib/utils";

interface Alert {
  id: number;
  type: string;
  severity: string;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

interface AlertsListData {
  alerts: Alert[];
  total: number;
}

const severityConfig: Record<
  string,
  { icon: typeof Info; color: string; badge: "default" | "secondary" | "destructive" | "outline" }
> = {
  info: {
    icon: Info,
    color: "text-blue-500",
    badge: "secondary",
  },
  warning: {
    icon: AlertTriangle,
    color: "text-yellow-500",
    badge: "outline",
  },
  urgent: {
    icon: AlertOctagon,
    color: "text-red-500",
    badge: "destructive",
  },
};

export function AlertsList({ data }: { data: unknown }) {
  const d = data as AlertsListData;

  if (!d.alerts || d.alerts.length === 0) {
    return (
      <Card>
        <CardContent className="py-4 text-center text-sm text-muted-foreground">
          No alerts at this time.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-sm">
            <Bell className="h-4 w-4" />
            Alerts ({d.total})
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        {d.alerts.map((alert) => {
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
                  <Badge variant={config.badge} className="text-[10px] capitalize">
                    {alert.severity}
                  </Badge>
                  <span className="text-[10px] text-muted-foreground">
                    {formatDate(alert.created_at)}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
