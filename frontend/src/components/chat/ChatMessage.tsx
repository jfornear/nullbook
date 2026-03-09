import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { cn } from "@/lib/utils";
import type { Message, ToolResult } from "@/types/chat";
import { Loader2 } from "lucide-react";
import { RichComponentRenderer } from "./rich/RichComponentRenderer";

interface ChatMessageProps {
  message: Message;
  /** Override content for streaming messages */
  streamContent?: string;
  /** Tool results to render inline (streaming) */
  streamToolResults?: ToolResult[];
  /** Tool currently being executed */
  activeToolName?: string;
}

export function ChatMessage({
  message,
  streamContent,
  streamToolResults,
  activeToolName,
}: ChatMessageProps) {
  const isUser = message.role === "user";
  const content = streamContent ?? message.content;
  const toolResults = streamToolResults ?? message.tool_results ?? [];

  return (
    <div className="py-4">
      {/* Role label */}
      <div className="mb-1.5 text-xs font-medium text-muted-foreground">
        {isUser ? "You" : "nullbook"}
      </div>

      {/* Tool execution indicator */}
      {activeToolName && (
        <div className="mb-2 flex items-center gap-2 text-xs text-muted-foreground">
          <Loader2 className="h-3 w-3 animate-spin" />
          <span>{toolNameToLabel(activeToolName)}</span>
        </div>
      )}

      {/* Rich tool result components */}
      {toolResults.length > 0 && (
        <div className="mb-2 space-y-2">
          {toolResults.map((tr) => (
            <RichComponentRenderer key={tr.tool_use_id} data={tr.content} />
          ))}
        </div>
      )}

      {/* Text content */}
      {content && (
        <div
          className={cn(
            "text-sm leading-relaxed",
            isUser && "inline-block max-w-[85%] rounded-2xl bg-muted px-4 py-3"
          )}
        >
          {isUser ? (
            content
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none prose-p:my-1.5 prose-headings:my-2 prose-ul:my-1 prose-ol:my-1 prose-li:my-0.5 prose-pre:my-2 prose-table:my-2">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function toolNameToLabel(name: string): string {
  const labels: Record<string, string> = {
    get_accounts: "Looking up your accounts...",
    query_transactions: "Searching transactions...",
    get_spending_summary: "Analyzing spending...",
    get_dashboard_summary: "Getting dashboard summary...",
    get_portfolio_holdings: "Fetching portfolio...",
    get_portfolio_allocation: "Calculating allocation...",
    get_news_articles: "Loading news...",
    search_security: "Looking up security...",
    get_tax_years: "Checking tax data...",
    // Phase 1: Receipt & Expense tools
    get_receipts: "Loading receipts...",
    create_expense_from_receipt: "Creating expense from receipt...",
    generate_expense_report: "Generating expense report...",
    // Phase 2: Tax Estimation tools
    estimate_taxes: "Calculating tax estimate...",
    compare_filing_statuses: "Comparing filing statuses...",
    // Phase 3: Tax Prep tools
    scan_transactions_for_deductions: "Scanning for deductions...",
    create_deduction_from_transactions: "Creating deduction...",
    get_tax_prep_checklist: "Building tax prep checklist...",
    // Phase 4: Bank sync, Email, Subscriptions, Tax filing, Portfolio
    link_bank_account: "Connecting bank...",
    sync_accounts: "Syncing accounts...",
    connect_email: "Setting up email...",
    scan_email_now: "Scanning email...",
    get_email_receipts: "Finding email receipts...",
    get_subscriptions: "Detecting subscriptions...",
    get_subscription_spending: "Calculating subscription costs...",
    cancel_subscription: "Processing cancellation...",
    track_cancellation: "Tracking cancellation...",
    prepare_tax_filing: "Preparing tax filing...",
    generate_schedule_c: "Generating Schedule C...",
    find_missed_deductions: "Scanning for deductions...",
    export_tax_summary: "Generating tax summary...",
    get_alerts: "Loading alerts...",
    get_portfolio_performance: "Calculating performance...",
  };
  return labels[name] || `Running ${name}...`;
}

export function TypingIndicator() {
  return (
    <div className="py-4">
      <div className="mb-1.5 text-xs font-medium text-muted-foreground">nullbook</div>
      <div className="flex gap-1 py-1">
        <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/40 [animation-delay:0ms]" />
        <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/40 [animation-delay:150ms]" />
        <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/40 [animation-delay:300ms]" />
      </div>
    </div>
  );
}
