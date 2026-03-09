import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { Mail, Plus, CheckCircle2, XCircle, RefreshCw, Trash2, AlertCircle } from "lucide-react";
import { api, emailApi } from "@/lib/api";
import type { PaginatedResponse } from "@/types";
import { formatDistanceToNow } from "date-fns";
import { RowActions } from "@/components/shared/RowActions";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { CreateEmailRuleDialog } from "@/components/email/CreateEmailRuleDialog";

interface EmailAccount {
  id: number;
  provider: string;
  email_address: string;
  status: string;
  last_synced_at: string | null;
  error_message?: string;
}

interface EmailRule {
  id: number;
  name: string;
  from_pattern: string;
  subject_pattern: string;
  has_attachment?: boolean;
  action: string;
  is_active: boolean;
}

export function EmailContent() {
  const queryClient = useQueryClient();
  const [connectOpen, setConnectOpen] = useState(false);

  const [imapForm, setImapForm] = useState({
    email_address: "",
    imap_host: "imap.gmail.com",
    imap_port: "993",
    username: "",
    password: "",
  });
  const [ruleDialogOpen, setRuleDialogOpen] = useState(false);
  const [editRule, setEditRule] = useState<EmailRule | null>(null);
  const [deleteRule, setDeleteRule] = useState<EmailRule | null>(null);

  const { data: accountsData, isLoading: loadingAccounts } = useQuery({
    queryKey: ["email-accounts"],
    queryFn: () => api.get<PaginatedResponse<EmailAccount>>("/email-sync/accounts/"),
  });

  const { data: rulesData, isLoading: loadingRules } = useQuery({
    queryKey: ["email-rules"],
    queryFn: () => api.get<PaginatedResponse<EmailRule>>("/email-sync/rules/"),
  });

  const connectImap = useMutation({
    mutationFn: () =>
      emailApi.connectImap({
        ...imapForm,
        imap_port: parseInt(imapForm.imap_port, 10),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["email-accounts"] });
      toast.success("Email account connected");
      setConnectOpen(false);
      setImapForm({
        email_address: "",
        imap_host: "imap.gmail.com",
        imap_port: "993",
        username: "",
        password: "",
      });
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const syncNow = useMutation({
    mutationFn: (accountId: number) => emailApi.syncNow(accountId),
    onSuccess: () => toast.success("Email sync started"),
    onError: (err: Error) => toast.error(err.message),
  });

  const disconnectAccount = useMutation({
    mutationFn: (accountId: number) => emailApi.disconnect(accountId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["email-accounts"] });
      toast.success("Email account disconnected");
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const deleteRuleMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/email-sync/rules/${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["email-rules"] });
      toast.success("Rule deleted");
      setDeleteRule(null);
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const toggleRuleMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: number; is_active: boolean }) =>
      api.patch(`/email-sync/rules/${id}/`, { is_active }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["email-rules"] });
    },
    onError: (err: Error) => toast.error(err.message),
  });

  const isLoading = loadingAccounts || loadingRules;
  const accounts = accountsData?.results ?? [];
  const rules = rulesData?.results ?? [];

  const statusIcon = (s: string) => {
    if (s === "active") return <CheckCircle2 className="h-4 w-4 text-green-600 shrink-0" />;
    if (s === "error") return <AlertCircle className="h-4 w-4 text-yellow-600 shrink-0" />;
    return <XCircle className="h-4 w-4 text-red-600 shrink-0" />;
  };

  return (
    <>
      <div className="space-y-4">
        {isLoading && (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        )}

        {!isLoading && (
          <>
            {/* Connected Accounts */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium">Connected Accounts</h3>
                <Button
                  variant="outline"
                  size="sm"
                  className="h-7 text-xs gap-1"
                  onClick={() => setConnectOpen(true)}
                >
                  <Plus className="h-3 w-3" />
                  Connect
                </Button>
              </div>
              {accounts.length === 0 ? (
                <div className="rounded-md border border-dashed p-6 text-center">
                  <Mail className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
                  <div className="text-sm text-muted-foreground">No email accounts connected</div>
                  <div className="text-xs text-muted-foreground mt-1">
                    Connect your email to scan for receipts and subscriptions
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    className="mt-3"
                    onClick={() => setConnectOpen(true)}
                  >
                    Connect Email
                  </Button>
                </div>
              ) : (
                <div className="space-y-1">
                  {accounts.map((acct) => (
                    <div
                      key={acct.id}
                      className="flex items-center justify-between rounded-md border px-3 py-2"
                    >
                      <div className="flex items-center gap-2">
                        {statusIcon(acct.status)}
                        <div>
                          <div className="text-sm font-medium">{acct.email_address}</div>
                          <div className="text-xs text-muted-foreground capitalize">
                            {acct.provider}
                            {acct.last_synced_at && (
                              <>
                                {" "}
                                · Last scan:{" "}
                                {formatDistanceToNow(new Date(acct.last_synced_at), {
                                  addSuffix: true,
                                })}
                              </>
                            )}
                            {acct.status === "error" && acct.error_message && (
                              <span className="text-yellow-600"> · {acct.error_message}</span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        <Badge
                          variant={acct.status === "active" ? "default" : "destructive"}
                          className="text-[10px] capitalize"
                        >
                          {acct.status}
                        </Badge>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 w-7 p-0"
                          onClick={() => syncNow.mutate(acct.id)}
                          disabled={
                            (syncNow.isPending && syncNow.variables === acct.id) ||
                            acct.status === "disconnected"
                          }
                          title="Sync now"
                        >
                          <RefreshCw
                            className={`h-3.5 w-3.5 ${syncNow.isPending && syncNow.variables === acct.id ? "animate-spin" : ""}`}
                          />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 w-7 p-0 text-muted-foreground hover:text-destructive"
                          onClick={() => disconnectAccount.mutate(acct.id)}
                          disabled={
                            disconnectAccount.isPending && disconnectAccount.variables === acct.id
                          }
                          title="Disconnect"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <Separator />

            {/* Email Rules */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium">Email Rules</h3>
                <Button
                  variant="outline"
                  size="sm"
                  className="h-7 text-xs gap-1"
                  onClick={() => setRuleDialogOpen(true)}
                >
                  <Plus className="h-3 w-3" />
                  Add Rule
                </Button>
              </div>
              {rules.length === 0 ? (
                <div className="text-sm text-muted-foreground text-center py-4">
                  No email rules configured. Add rules to automatically process receipts from email.
                </div>
              ) : (
                <div className="space-y-1">
                  {rules.map((rule) => (
                    <div
                      key={rule.id}
                      className="flex items-center justify-between rounded-md border px-3 py-2"
                    >
                      <div>
                        <div className="text-sm font-medium">{rule.name}</div>
                        <div className="text-xs text-muted-foreground">
                          {rule.from_pattern && `From: ${rule.from_pattern}`}
                          {rule.from_pattern && rule.subject_pattern && " · "}
                          {rule.subject_pattern && `Subject: ${rule.subject_pattern}`}
                          {" · "}Action: {rule.action.replace(/_/g, " ")}
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 text-[10px] px-2"
                          onClick={() =>
                            toggleRuleMutation.mutate({ id: rule.id, is_active: !rule.is_active })
                          }
                          disabled={toggleRuleMutation.isPending}
                        >
                          <Badge
                            variant={rule.is_active ? "default" : "outline"}
                            className="text-[10px]"
                          >
                            {rule.is_active ? "Active" : "Inactive"}
                          </Badge>
                        </Button>
                        <RowActions
                          onEdit={() => setEditRule(rule)}
                          onDelete={() => setDeleteRule(rule)}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* Connect Email Dialog */}
      <Dialog
        open={connectOpen}
        onOpenChange={(v) => {
          if (!v) setConnectOpen(false);
        }}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Connect Email</DialogTitle>
            <DialogDescription>
              Enter your IMAP server details. For Gmail, use an App Password.
            </DialogDescription>
          </DialogHeader>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              connectImap.mutate();
            }}
            className="space-y-3 pt-2"
          >
            <div className="space-y-2">
              <Label htmlFor="email_address">Email Address</Label>
              <Input
                id="email_address"
                placeholder="you@gmail.com"
                value={imapForm.email_address}
                onChange={(e) => {
                  const addr = e.target.value;
                  setImapForm((f) => {
                    const host = addr.includes("@gmail.com")
                      ? "imap.gmail.com"
                      : addr.includes("@outlook.com") || addr.includes("@hotmail.com")
                        ? "outlook.office365.com"
                        : addr.includes("@yahoo.com")
                          ? "imap.mail.yahoo.com"
                          : addr.includes("@fastmail.com")
                            ? "imap.fastmail.com"
                            : addr.includes("@icloud.com") || addr.includes("@me.com")
                              ? "imap.mail.me.com"
                              : f.imap_host;
                    return { ...f, email_address: addr, imap_host: host, username: addr };
                  });
                }}
                required
              />
            </div>
            <div className="grid grid-cols-3 gap-2">
              <div className="col-span-2 space-y-2">
                <Label htmlFor="imap_host">IMAP Host</Label>
                <Input
                  id="imap_host"
                  placeholder="imap.gmail.com"
                  value={imapForm.imap_host}
                  onChange={(e) => setImapForm((f) => ({ ...f, imap_host: e.target.value }))}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="imap_port">Port</Label>
                <Input
                  id="imap_port"
                  type="number"
                  value={imapForm.imap_port}
                  onChange={(e) => setImapForm((f) => ({ ...f, imap_port: e.target.value }))}
                  required
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="App password"
                value={imapForm.password}
                onChange={(e) => setImapForm((f) => ({ ...f, password: e.target.value }))}
                required
              />
              {imapForm.imap_host === "imap.gmail.com" && (
                <p className="text-xs text-muted-foreground">
                  Use a Gmail App Password, not your Google password.{" "}
                  <a
                    href="https://myaccount.google.com/apppasswords"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="underline"
                  >
                    Generate one here
                  </a>
                </p>
              )}
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => setConnectOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={connectImap.isPending}>
                {connectImap.isPending ? "Connecting..." : "Connect"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      <CreateEmailRuleDialog
        open={ruleDialogOpen || !!editRule}
        onOpenChange={(open) => {
          if (!open) {
            setRuleDialogOpen(false);
            setEditRule(null);
          }
        }}
        editRule={editRule}
      />

      <ConfirmDialog
        open={!!deleteRule}
        onOpenChange={(open) => !open && setDeleteRule(null)}
        title="Delete Email Rule"
        description={`Delete "${deleteRule?.name}"? This action cannot be undone.`}
        onConfirm={() => deleteRule && deleteRuleMutation.mutate(deleteRule.id)}
        destructive
        loading={deleteRuleMutation.isPending}
      />
    </>
  );
}
