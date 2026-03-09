import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Sun, Moon, CheckCircle2, XCircle, Building2, Mail } from "lucide-react";
import { api } from "@/lib/api";
import { useTheme } from "@/lib/theme";
import type { UserSettings } from "@/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { CategoryRulesSection } from "@/components/transactions/CategoryRulesSection";

const CURRENCIES = ["USD", "EUR", "GBP", "CAD", "AUD", "JPY", "CHF"];
const MONTHS = [
  { value: "1", label: "January" },
  { value: "2", label: "February" },
  { value: "3", label: "March" },
  { value: "4", label: "April" },
  { value: "5", label: "May" },
  { value: "6", label: "June" },
  { value: "7", label: "July" },
  { value: "8", label: "August" },
  { value: "9", label: "September" },
  { value: "10", label: "October" },
  { value: "11", label: "November" },
  { value: "12", label: "December" },
];

interface IntegrationStatus {
  plaid: {
    configured: boolean;
    items: {
      id: number;
      institution_name: string;
      status: string;
      last_synced_at: string | null;
    }[];
  };
  email: {
    configured: boolean;
    accounts: {
      id: number;
      email_address: string;
      provider: string;
      status: string;
      last_synced_at: string | null;
    }[];
  };
  smtp: { configured: boolean };
  llm: { configured: boolean; provider: string; model: string };
  news: { source_count: number };
  onboarding: { has_accounts: boolean; has_transactions: boolean; has_api_key: boolean };
}

function getPasswordStrength(password: string) {
  if (!password) return { label: "", color: "bg-muted", width: "0%" };
  let score = 0;
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  if (/[A-Z]/.test(password) && /[a-z]/.test(password)) score++;
  if (/\d/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;
  if (score <= 1) return { label: "Weak", color: "bg-red-500", width: "20%" };
  if (score === 2) return { label: "Fair", color: "bg-orange-500", width: "40%" };
  if (score === 3) return { label: "Good", color: "bg-yellow-500", width: "60%" };
  if (score === 4) return { label: "Strong", color: "bg-green-500", width: "80%" };
  return { label: "Very strong", color: "bg-green-600", width: "100%" };
}

function StatusBadge({ ok, label }: { ok: boolean; label: string }) {
  return (
    <div className="flex items-center gap-2">
      {ok ? (
        <CheckCircle2 className="h-4 w-4 text-green-600" />
      ) : (
        <XCircle className="h-4 w-4 text-muted-foreground" />
      )}
      <span className="text-sm">{label}</span>
    </div>
  );
}

export function GeneralSection() {
  const queryClient = useQueryClient();
  const { theme, toggleTheme } = useTheme();
  const [currency, setCurrency] = useState("USD");
  const [fiscalMonth, setFiscalMonth] = useState("1");

  const { data: settings, isLoading } = useQuery({
    queryKey: ["settings"],
    queryFn: () => api.get<UserSettings>("/settings/"),
  });

  useEffect(() => {
    if (settings) {
      setCurrency(settings.currency);
      setFiscalMonth(String(settings.fiscal_year_start));
    }
  }, [settings]);

  const mutation = useMutation({
    mutationFn: (data: Partial<UserSettings>) => api.patch<UserSettings>("/settings/", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settings"] });
      toast.success("Settings saved");
    },
    onError: (err: Error) => toast.error(err.message),
  });

  return (
    <div>
      <div className="flex min-h-[60px] items-center border-b py-3">
        <div className="flex w-full items-center justify-between">
          <span className="text-sm">Appearance</span>
          <div className="flex gap-1.5">
            <Button
              variant={theme === "light" ? "default" : "outline"}
              size="sm"
              className="h-8 rounded-lg"
              onClick={() => theme !== "light" && toggleTheme()}
            >
              <Sun className="mr-1.5 h-4 w-4" />
              Light
            </Button>
            <Button
              variant={theme === "dark" ? "default" : "outline"}
              size="sm"
              className="h-8 rounded-lg"
              onClick={() => theme !== "dark" && toggleTheme()}
            >
              <Moon className="mr-1.5 h-4 w-4" />
              Dark
            </Button>
          </div>
        </div>
      </div>

      <div className="flex min-h-[60px] items-center border-b py-3">
        <div className="flex w-full items-center justify-between">
          <span className="text-sm">Default Currency</span>
          <Select
            value={currency}
            onValueChange={(v) => {
              setCurrency(v);
              mutation.mutate({ currency: v });
            }}
            disabled={isLoading}
          >
            <SelectTrigger className="w-28 h-9 rounded-lg border-transparent bg-transparent hover:bg-accent">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {CURRENCIES.map((c) => (
                <SelectItem key={c} value={c}>
                  {c}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="flex min-h-[60px] items-center border-b py-3">
        <div className="flex w-full items-center justify-between">
          <span className="text-sm">Fiscal Year Start</span>
          <Select
            value={fiscalMonth}
            onValueChange={(v) => {
              setFiscalMonth(v);
              mutation.mutate({ fiscal_year_start: Number(v) });
            }}
            disabled={isLoading}
          >
            <SelectTrigger className="w-36 h-9 rounded-lg border-transparent bg-transparent hover:bg-accent">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {MONTHS.map((m) => (
                <SelectItem key={m.value} value={m.value}>
                  {m.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="pt-4">
        <CategoryRulesSection />
      </div>
    </div>
  );
}

export function IntegrationsSection() {
  const { data: integrations } = useQuery({
    queryKey: ["integration-status"],
    queryFn: () => api.get<IntegrationStatus>("/integrations/status/"),
  });

  if (!integrations) return <div className="text-sm text-muted-foreground">Loading...</div>;

  return (
    <div>
      <div className="border-b py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Building2 className="h-[18px] w-[18px] text-muted-foreground" />
            <span className="text-sm">Bank Accounts (Plaid)</span>
          </div>
          <Badge
            variant={integrations.plaid.configured ? "default" : "outline"}
            className="text-[10px]"
          >
            {integrations.plaid.configured ? "Configured" : "Not configured"}
          </Badge>
        </div>
        {!integrations.plaid.configured && (
          <p className="text-xs text-muted-foreground mt-1.5 ml-[30px]">
            Add PLAID_CLIENT_ID and PLAID_SECRET to your .env file
          </p>
        )}
        {integrations.plaid.items.map((item) => (
          <div key={item.id} className="flex items-center justify-between text-xs mt-1.5 ml-[30px]">
            <span>{item.institution_name}</span>
            <Badge
              variant={item.status === "active" ? "default" : "destructive"}
              className="text-[9px]"
            >
              {item.status}
            </Badge>
          </div>
        ))}
      </div>

      <div className="border-b py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Mail className="h-[18px] w-[18px] text-muted-foreground" />
            <span className="text-sm">Email Scanning</span>
          </div>
          <Badge
            variant={integrations.email.accounts.length > 0 ? "default" : "outline"}
            className="text-[10px]"
          >
            {integrations.email.accounts.length > 0
              ? `${integrations.email.accounts.length} connected`
              : "Not connected"}
          </Badge>
        </div>
        {integrations.email.accounts.length === 0 && (
          <p className="text-xs text-muted-foreground mt-1.5 ml-[30px]">
            Connect your email via IMAP to scan for receipts
          </p>
        )}
        {integrations.email.accounts.map((acct) => (
          <div key={acct.id} className="flex items-center justify-between text-xs mt-1.5 ml-[30px]">
            <span>
              {acct.email_address} ({acct.provider})
            </span>
            <Badge
              variant={acct.status === "active" ? "default" : "destructive"}
              className="text-[9px]"
            >
              {acct.status}
            </Badge>
          </div>
        ))}
      </div>

      <div className="flex min-h-[60px] items-center border-b py-3">
        <StatusBadge
          ok={integrations.llm.configured}
          label={
            integrations.llm.provider === "anthropic"
              ? "Claude AI (Anthropic API)"
              : integrations.llm.provider === "openai"
                ? `OpenAI (${integrations.llm.model})`
                : `Local AI (Ollama - ${integrations.llm.model})`
          }
        />
      </div>
      <div className="flex min-h-[60px] items-center border-b py-3">
        <StatusBadge ok={integrations.smtp.configured} label="Email Sending (SMTP)" />
      </div>
      <div className="flex min-h-[60px] items-center py-3">
        <StatusBadge
          ok={integrations.news.source_count > 0}
          label={`News Sources (${integrations.news.source_count} active)`}
        />
      </div>
    </div>
  );
}

export function SecuritySection() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const { data: integrations } = useQuery({
    queryKey: ["integration-status"],
    queryFn: () => api.get<IntegrationStatus>("/integrations/status/"),
  });

  const passwordMutation = useMutation({
    mutationFn: (data: { current_password: string; new_password: string }) =>
      api.post("/auth/change-password/", data),
    onSuccess: () => {
      toast.success("Password changed");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    },
    onError: (err: Error) => toast.error(err.message),
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      toast.error("Passwords don't match");
      return;
    }
    passwordMutation.mutate({ current_password: currentPassword, new_password: newPassword });
  }

  const strength = getPasswordStrength(newPassword);

  return (
    <div>
      <div className="border-b py-3">
        <div className="rounded-xl bg-muted/50 p-4">
          <p className="text-sm text-muted-foreground">
            Credentials are encrypted at rest using Fernet (AES-128-CBC). Data stays local in
            SQLite.
          </p>
        </div>
      </div>

      {integrations &&
        (integrations.plaid.items.length > 0 || integrations.email.accounts.length > 0) && (
          <div className="border-b py-3">
            <span className="text-xs text-muted-foreground">Stored Tokens</span>
            <div className="mt-2 space-y-1">
              {integrations.plaid.items.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between text-xs rounded-lg border px-3 py-2"
                >
                  <span>Plaid — {item.institution_name}</span>
                  <span className="font-mono text-muted-foreground">****encrypted</span>
                </div>
              ))}
              {integrations.email.accounts.map((acct) => (
                <div
                  key={acct.id}
                  className="flex items-center justify-between text-xs rounded-lg border px-3 py-2"
                >
                  <span>IMAP — {acct.email_address}</span>
                  <span className="font-mono text-muted-foreground">****encrypted</span>
                </div>
              ))}
            </div>
          </div>
        )}

      <div className="py-4">
        <span className="text-sm font-medium">Change Password</span>
        <form onSubmit={handleSubmit} className="mt-3 space-y-3 max-w-sm">
          <Input
            type="password"
            placeholder="Current password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            required
            autoComplete="current-password"
            className="rounded-lg"
          />
          <div className="space-y-1">
            <Input
              type="password"
              placeholder="New password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              minLength={8}
              autoComplete="new-password"
              className="rounded-lg"
            />
            {newPassword && (
              <div className="space-y-1">
                <div className="h-1.5 w-full rounded-full bg-muted">
                  <div
                    className={`h-1.5 rounded-full transition-all ${strength.color}`}
                    style={{ width: strength.width }}
                  />
                </div>
                <p className="text-[10px] text-muted-foreground">{strength.label}</p>
              </div>
            )}
          </div>
          <Input
            type="password"
            placeholder="Confirm new password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            minLength={8}
            autoComplete="new-password"
            className="rounded-lg"
          />
          <Button
            type="submit"
            size="sm"
            className="rounded-lg"
            disabled={passwordMutation.isPending}
          >
            {passwordMutation.isPending ? "Changing..." : "Change Password"}
          </Button>
        </form>
      </div>
    </div>
  );
}

export function SettingsPage() {
  return (
    <div className="space-y-6">
      <GeneralSection />

      <div>
        <h3 className="text-sm font-medium text-muted-foreground border-b pb-2 mb-0">
          Integrations
        </h3>
        <IntegrationsSection />
      </div>

      <div>
        <h3 className="text-sm font-medium text-muted-foreground border-b pb-2 mb-0">Security</h3>
        <SecuritySection />
      </div>

      <div>
        <h3 className="text-sm font-medium text-muted-foreground border-b pb-2 mb-0">Data</h3>
        <DataSection />
      </div>
    </div>
  );
}

export function DataSection() {
  return (
    <div>
      <div className="border-b py-3">
        <div className="rounded-xl bg-muted/50 p-4">
          <p className="text-sm text-muted-foreground">
            Data is stored locally in SQLite. No data leaves your machine except through explicit
            integrations.
          </p>
        </div>
      </div>

      <div className="py-3">
        <span className="text-sm font-medium">Backup &amp; Restore</span>
        <div className="mt-2 text-xs text-muted-foreground space-y-1.5">
          <p>
            <code className="font-mono rounded-md bg-muted px-1.5 py-0.5">make backup</code> —
            Create backup to ~/nullbook-backups/
          </p>
          <p>
            <code className="font-mono rounded-md bg-muted px-1.5 py-0.5">
              make restore ARCHIVE=path.tar.gz
            </code>{" "}
            — Restore from archive
          </p>
        </div>
      </div>
    </div>
  );
}
