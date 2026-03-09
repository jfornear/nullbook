import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Mail, ExternalLink, AlertTriangle } from "lucide-react";

interface CancellationDraftData {
  subscription_id?: number;
  merchant: string;
  status: string;
  email_subject?: string;
  email_body?: string;
  cancellation_url?: string;
  instructions?: string;
  tracking_id?: string;
  message?: string;
}

const statusConfig: Record<
  string,
  { label: string; variant: "default" | "secondary" | "outline" | "destructive" }
> = {
  draft: { label: "Draft - Confirm to Send", variant: "outline" },
  sent: { label: "Email Sent", variant: "default" },
  manual: { label: "Manual Cancellation Required", variant: "secondary" },
  tracking: { label: "Tracking Cancellation", variant: "secondary" },
  confirmed: { label: "Cancellation Confirmed", variant: "default" },
};

export function CancellationDraft({ data }: { data: unknown }) {
  const d = data as CancellationDraftData;
  const config = statusConfig[d.status] || statusConfig.draft;

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-sm">
            <Mail className="h-4 w-4" />
            Cancel: {d.merchant}
          </CardTitle>
          <Badge variant={config.variant} className="text-xs">
            {config.label}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        {/* Draft Email Preview */}
        {d.email_subject && (
          <div className="rounded-md border p-3 space-y-2">
            <div>
              <span className="text-xs font-medium text-muted-foreground">Subject: </span>
              <span className="text-sm">{d.email_subject}</span>
            </div>
            {d.email_body && (
              <div className="text-xs text-muted-foreground whitespace-pre-wrap border-t pt-2">
                {d.email_body}
              </div>
            )}
          </div>
        )}

        {/* Instructions for manual cancellation */}
        {d.instructions && (
          <div className="rounded-md bg-muted/50 p-3 text-xs text-muted-foreground">
            {d.instructions}
          </div>
        )}

        {/* Message */}
        {d.message && <div className="text-xs text-muted-foreground">{d.message}</div>}

        {/* Cancellation URL */}
        {d.cancellation_url && (
          <a
            href={d.cancellation_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-xs text-blue-600 hover:underline"
          >
            <ExternalLink className="h-3 w-3" />
            Open cancellation page
          </a>
        )}

        {/* Tracking ID */}
        {d.tracking_id && (
          <div className="text-xs text-muted-foreground">
            Tracking ID: <span className="font-mono">{d.tracking_id}</span>
          </div>
        )}

        {/* Confirmation notice for drafts */}
        {d.status === "draft" && (
          <div className="flex items-start gap-2 rounded-md bg-yellow-50 dark:bg-yellow-950/30 p-2.5">
            <AlertTriangle className="h-3.5 w-3.5 text-yellow-600 mt-0.5 shrink-0" />
            <span className="text-xs text-yellow-700 dark:text-yellow-400">
              This is a preview. Confirm to send the cancellation email.
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
